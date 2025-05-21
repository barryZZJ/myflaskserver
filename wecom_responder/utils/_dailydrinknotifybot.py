import inspect
import traceback
import datetime
from pathlib import Path
from typing import Coroutine, TYPE_CHECKING, Union, TypeVar, Callable

import pymongo.errors
import pytz
from loguru import logger
from telegram.ext import Job

from dumbbot.ptbcontrib.ptbcontrib.ptb_jobstores import PTBMongoDBJobStore
from .consts import DB_JOBSTORE
from .tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot import DumbApplication, DumbBot, Chat
from .tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot import Update, StringArgConverter, ChainCommandHandler
from .tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot.ext import ApplicationBuilder, PicklePersistence, PersistenceInput
from .tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot.ext import MessageHandler, ContextTypes, filters
from .tv_subscribe_bot.tvsubscribebot.utils.consts import PERSISTENCE_UPDATE_INTERVAL, JOBKEY_THIS_UPDATE
from .tv_subscribe_bot.tvsubscribebot.utils.handlercallbacks import HandlerCallbacks
from .tv_subscribe_bot.tvsubscribebot.utils.types import RESULT_TEXT

if TYPE_CHECKING:
    from tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot.ext import Application

__all__ = (
    'DailyDrinkNotifyBot',
)

SUCCESSED_IDS = TypeVar('SUCCESSED_IDS', bound=list[int])
FAILED_IDS = TypeVar('FAILED_IDS', bound=list[int])
ALREADY_SUBBED_IDS = TypeVar('ALREADY_SUBBED_IDS', bound=list[int])

KEY_DAILY_DRINK_GOAL = 'DAILY_DRINK_GOAL'
KEY_DAILY_DRANK_DICT = 'DAILY_DRANK_DICT'
KEY_HANDLER_CALLBACKS = 'NOTIFIER_CALLBACKS'

AMOUNTPERSIP = 60  # 每口多少毫升
DEFAULT_DAILY_DRINK_GOAL = 2000 # 默认每日饮水目标（毫升）
DEFAULT_REMINDER_INTERVAL = 30  # 默认提醒间隔时间（分钟）

# 饮水提醒相关常量
JOB_REMINDER_PREFIX = 'drink_reminder_job'  # 饮水提醒任务名
JOB_MUTE_PREFIX = 'drink_mute_job'
KEY_REMINDER_INTERVAL = 'REMINDER_INTERVAL'
REMINDER_MORNING_START = datetime.time(9, 0)  # 早上开始时间
REMINDER_MORNING_END = datetime.time(12, 0)  # 中午结束时间
REMINDER_AFTERNOON_START = datetime.time(14, 0)  # 下午开始时间
REMINDER_AFTERNOON_END = datetime.time(22, 0)  # 晚上结束时间

# jobqueue: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---JobQueue

class DailyDrinkNotifyBot:
    """This class have to run in main thread."""
    def __init__(
        self,
        persistence_filepath: Path,
        update_interval: float = PERSISTENCE_UPDATE_INTERVAL,
        dbfile_jobstore: str = DB_JOBSTORE,
    ):
        # TODO 记录并查询统计结果
        self.persistence = PicklePersistence(
            persistence_filepath,
            store_data=PersistenceInput(callback_data=False),
            update_interval=update_interval,
            single_file=False,
        )
        self._app: Union[DumbApplication, Application] = ApplicationBuilder() \
            .application_class(DumbApplication) \
            .bot(DumbBot()) \
            .persistence(self.persistence) \
            .post_init(self._initialize) \
            .build()

        # https://github.com/python-telegram-bot/ptbcontrib/blob/main/ptbcontrib/ptb_jobstores/README.md
        # make jobs persistent
        self._app.job_queue.scheduler.add_jobstore(
            PTBMongoDBJobStore(
                application=self._app,
                host=dbfile_jobstore,
            )
        )
        # define handlers
        self.cmd_handlers_set = ChainCommandHandler(
            '/set',
            sub_command_handlers=[
                ChainCommandHandler('target', self._cmd_set_target),
                ChainCommandHandler('drank', self._cmd_set_drank),
                ChainCommandHandler('interval', self._cmd_set_interval),
            ]
        )

        # 	1. 直接回复数字，记录今日喝水情况（已喝/目标），1位数则为口数，2位以上为毫升数。或判断“口”、“毫升”、“ml”字眼。一口50毫升
        # 	2. /help 指令提示
        # 	3. /set
        # 		- target <target_ml=2000> 目标毫升数
        # 		- drank <drank_ml> 已喝毫升数
        # 		- interval <minute=30> 提醒间隔（分钟）
        # 	4. /today 今日饮水情况
        # 	5. /report <days=7> 统计一周结果
        # 	6. /mute 关闭提醒一天  job.enabled = False  # Temporarily disable this job
        # 	7. /unmute 回复提醒
        # 	8. /off 完全关闭提醒
        # 	9. /on 开启提醒。早9点~12点，14~晚9点，每半小时提醒。job
        # 	10. /status 提醒是否开启
        self.cmd_handlers_mute = ChainCommandHandler('/mute', self._cmd_mute)
        self.cmd_handlers_unmute = ChainCommandHandler('/unmute', self._cmd_unmute)
        self.cmd_handlers_on = ChainCommandHandler('/on', self._cmd_on)
        self.cmd_handlers_off = ChainCommandHandler('/off', self._cmd_off)
        self.cmd_handlers_status = ChainCommandHandler('/status', self._cmd_status)
        # self.cmd_handlers_report = ChainCommandHandler('/report', self._cmd_report) # TODO
        self.cmd_handlers_today = ChainCommandHandler('/today', self._cmd_today)
        self.cmd_handlers_help = ChainCommandHandler('/help', self._cmd_help)

        self.cmd_handlers_drink = MessageHandler(filters.Regex('^\d+'), self._cmd_drink)

        self._app.add_handler(self.cmd_handlers_set)
        self._app.add_handler(self.cmd_handlers_mute)
        self._app.add_handler(self.cmd_handlers_unmute)
        self._app.add_handler(self.cmd_handlers_on)
        self._app.add_handler(self.cmd_handlers_off)
        self._app.add_handler(self.cmd_handlers_status)
        # self._app.add_handler(self.cmd_handlers_report)
        self._app.add_handler(self.cmd_handlers_today)
        self._app.add_handler(self.cmd_handlers_help)
        self._app.add_handler(self.cmd_handlers_drink)

        self._callbacks: HandlerCallbacks = HandlerCallbacks()


    # app 相关
    async def _initialize(self, application: 'Application'):
        # load persisted bot data
        # remove datas
        # application.drop_chat_data(chat_id)
        # application.drop_user_data(user_id)
        # update persistence now, instead of mark_data_for_update_persistence()
        # application.update_persistence()
        chat_data = dict(application.chat_data)
        user_data = dict(application.user_data)
        logger.debug(f'{chat_data=}')
        logger.debug(f'{user_data=}')
        logger.debug(f'{application.job_queue.jobs()=}')  # 不包含未从数据库加载的job
        ...

    def listen_forever(self, listen: str = "127.0.0.1", port: int = 18889):
        """Start server"""
        logger.info('listening at {}:{}', listen, port)
        try:
            self._app.run(listen, port)
        except (pymongo.errors.ServerSelectionTimeoutError, Exception):
            logger.error('无法连接到jobstore！')
            logger.error(traceback.format_exc())

    # public utils
    def register_callback(self, func: Callable[[RESULT_TEXT, Chat], Coroutine]) -> Callable[[RESULT_TEXT, Chat], Coroutine]:
        """Register coroutine callback for handling result text, can be used as a decorator."""
        return self._callbacks.register_callback(func)

    # handlers
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示帮助信息"""
        usages = [usage.text for usage in self._usages.values()]
        await self._callbacks.notify_handle_result('\n'.join(usages), update)

    async def _cmd_drink(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理饮水记录命令。
        单纯1位数字：表示喝了几口，每口AMOUNTPERSIP=50毫升。
        单纯2位及以上数字：表示毫升数。
        包含“口”、“毫升”或“ml”字眼：根据上下文解析为对应口数或毫升数。
        """
        try:
            # 获取用户输入 一定以数字开头
            user_input = update.effective_message.text.strip()
            drink_amount: int

            # 判断输入内容
            if user_input.isdecimal():
                if len(user_input) == 1:  # 单纯1位数字，按口数计算
                    drink_amount = int(user_input) * AMOUNTPERSIP
                else:  # 2位及以上数字，按毫升数计算
                    drink_amount = int(user_input)
            elif user_input.endswith("口"):
                # 包含“口”，提取数字并按口数计算
                num_sips = int(''.join(filter(str.isdigit, user_input)) or 0)
                drink_amount = num_sips * AMOUNTPERSIP
            elif any(user_input.lower().endswith(unit) for unit in ["毫升", "ml"]):
                # 包含“毫升”或“ml”，提取数字并按毫升数计算
                drink_amount = int(''.join(filter(str.isdigit, user_input)) or 0)
            else:
                await self._callbacks.notify_handle_result("输入格式错误！\n请使用纯数字，或以口、毫升或ml作为单位", update)
                return

            # 获取当前日期
            today = self._key_today()
            daily_goal = context.chat_data.setdefault(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)

            # 更新 chat_data 中的饮水记录
            daily_drank_dict = context.chat_data.setdefault(KEY_DAILY_DRANK_DICT, {})
            daily_drank = daily_drank_dict.get(today, 0) + drink_amount
            daily_drank_dict[today] = daily_drank

            context.application.mark_data_for_update_persistence(user_ids=update.effective_user.id)
            # 回复用户
            if daily_drank >= daily_goal:
                await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal} 毫升\n已达成今日饮水目标！", update)
            else:
                await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal} 毫升", update)

            # 调整job
            user_id = update.effective_user.id
            job_name = JOB_REMINDER_PREFIX + str(user_id)
            interval = context.chat_data.get(KEY_REMINDER_INTERVAL, DEFAULT_REMINDER_INTERVAL)
            self._reschedule_job_interval(context, job_name, interval)

        except Exception as e:
            logger.error("出错: {}", e)
            await self._callbacks.notify_handle_result(f"无法处理输入！\n{e}", update)

    async def _cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/today - 查看今日饮水情况"""
        chat_data = context.chat_data
        daily_goal = chat_data.setdefault(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)
        today = self._key_today()
        daily_drank_dict = chat_data.get(KEY_DAILY_DRANK_DICT, {})
        daily_drank = daily_drank_dict.get(today, 0)

        if daily_drank >= daily_goal:
            await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal} 毫升\n已达成今日饮水目标！", update)
        else:
            await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal} 毫升", update)

    async def _cmd_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/on - 开启提醒"""
        chat_data = context.chat_data
        interval = chat_data.setdefault(KEY_REMINDER_INTERVAL, DEFAULT_REMINDER_INTERVAL)
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        job_name = JOB_REMINDER_PREFIX + str(user_id)

        if not context.job_queue.get_jobs_by_name(job_name):
            logger.warning(f"Creating job {job_name}.")
            job = context.job_queue.run_repeating(
                callback=DailyDrinkNotifyBot._on_reminder,
                interval=interval * 60,
                data={
                    JOBKEY_THIS_UPDATE: update,
                    KEY_HANDLER_CALLBACKS: self._callbacks,
                },
                name=job_name,
                chat_id=chat_id,
                user_id=user_id,
                job_kwargs=dict(
                    id=job_name,
                    replace_existing=True,
                ),
            )
            job.enabled = True  # Enable the job

        next_t = context.job_queue.get_jobs_by_name(job_name)[0].next_t.astimezone(pytz.timezone('Asia/Shanghai'))
        logger.debug(f'now: {datetime.datetime.now()}')
        logger.info(f"{next_t=}")

        reply_text = f'提醒：开启\n' \
            f'提醒间隔：{interval}分钟\n' \
            f'提醒时间：\n{REMINDER_MORNING_START:%H:%M}~{REMINDER_MORNING_END:%H:%M}、{REMINDER_AFTERNOON_START:%H:%M}~{REMINDER_AFTERNOON_END:%H:%M}'
        await self._callbacks.notify_handle_result(reply_text, update)

    async def _cmd_off(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/off - 关闭提醒"""
        self._remove_reminders(update, context)
        await self._callbacks.notify_handle_result("已关闭提醒", update)

    async def _cmd_mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/mute - 关闭提醒一天"""
        user_id = update.effective_user.id
        job_name = JOB_REMINDER_PREFIX + str(user_id)
        if not context.job_queue.get_jobs_by_name(job_name):
            await self._callbacks.notify_handle_result("提醒已关闭，无法暂停", update)
            return
        for job in context.job_queue.get_jobs_by_name(job_name):
            if job.enabled:
                job.enabled = False  # Temporarily disable this job
                # start at tomorrow or 2 days later
                now = datetime.datetime.now()  # 获取当前日期（不含时间）
                today = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)  # 获取当前日期的时间戳
                tomorrow = today + datetime.timedelta(days=1)  # 下一天
                the_other_day = today + datetime.timedelta(days=2)  # 后天

                # 是否达到饮水目标
                today = self._key_today()
                daily_goal = context.chat_data.get(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)
                daily_drank_dict = context.chat_data.get(KEY_DAILY_DRANK_DICT, {})
                daily_drank = daily_drank_dict.get(today, 0)

                if now.time() > REMINDER_AFTERNOON_END or daily_drank >= daily_goal:
                    # 如果已经过了下午的提醒时间，或者已经达成饮水目标，则后天再提醒
                    when = the_other_day
                    await self._callbacks.notify_handle_result("今日提醒已结束，已暂停提醒至后天", update)
                else:
                    # 否则明天再提醒
                    when = tomorrow
                    await self._callbacks.notify_handle_result("已暂停提醒至明天", update)

                context.job_queue.run_once(
                    self._on_enable_job,
                    when=when,
                    data={
                        'job': job
                    },
                    name=JOB_MUTE_PREFIX + str(user_id),
                )
                logger.info(f"Disabled job {job.name} until {when}.")
            else:
                logger.warning(f"Job {job.name} is already disabled.")
                await self._callbacks.notify_handle_result("提醒已经暂停过了", update)

    async def _cmd_unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/unmute - 恢复提醒"""
        user_id = update.effective_user.id
        job_mute_name = JOB_MUTE_PREFIX + str(user_id)
        if not context.job_queue.get_jobs_by_name(job_mute_name):
            logger.warning(f"Job {job_mute_name} is not found.")
            await self._callbacks.notify_handle_result("提醒没有暂停，无需恢复", update)
            return
        job_name = JOB_REMINDER_PREFIX + str(user_id)
        for job_mute in context.job_queue.get_jobs_by_name(job_mute_name):
            job_mute.schedule_removal()
            logger.info(f"Removed mute job {job_mute_name}.")
        if not context.job_queue.get_jobs_by_name(job_name):
            logger.warning(f"Job {job_name} is not found.")
            await self._callbacks.notify_handle_result("提醒已关闭，无法恢复", update)
            return
        for job in context.job_queue.get_jobs_by_name(job_name):
            logger.info(f"Enabling job {job.name}.")
            job.enabled = True
        await self._callbacks.notify_handle_result("已恢复提醒", update)

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看当前的提醒状态"""
        user_id = update.effective_user.id
        job_name = JOB_REMINDER_PREFIX + str(user_id)
        is_on = len(context.job_queue.get_jobs_by_name(job_name)) > 0
        interval = context.chat_data.get(KEY_REMINDER_INTERVAL, DEFAULT_REMINDER_INTERVAL)
        daily_goal = context.chat_data.get(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)
        daily_drank = context.chat_data.get(KEY_DAILY_DRANK_DICT, {}).get(self._key_today(), 0)

        if is_on:
            reply_text = f'今日已喝 {daily_drank}/{daily_goal} 毫升\n' \
                         f'提醒：{"开启" if is_on else "关闭"}\n' \
                         f'提醒间隔时间：{interval}分钟\n' \
                         f'提醒时间：\n{REMINDER_MORNING_START:%H:%M}~{REMINDER_MORNING_END:%H:%M}、{REMINDER_AFTERNOON_START:%H:%M}~{REMINDER_AFTERNOON_END:%H:%M}'
        else:
            reply_text = f'今日已喝 {daily_drank}/{daily_goal} 毫升\n' \
                         f'提醒：{"开启" if is_on else "关闭"}'
        await self._callbacks.notify_handle_result(reply_text, update)

    async def _cmd_set_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/set target <target_ml=DEFAULT_DAILY_DRINK_GOAL> - 设置每日饮水目标（毫升）"""
        currfunc = inspect.currentframe().f_code.co_name
        usage = self._usages[currfunc]
        if not usage.check_arg_len(context.args):
            await self._callbacks.notify_handle_result(usage.text, update)
            return

        try:
            (daily_goal,) = usage.parse_args(context.args)
            assert daily_goal > 0, "饮水目标必须大于 0 毫升"
        except (AssertionError, ValueError, Exception) as e:
            await self._callbacks.notify_handle_result(f"参数错误：{e}\n{usage.text}", update)
            return

        context.chat_data[KEY_DAILY_DRINK_GOAL] = daily_goal
        context.application.mark_data_for_update_persistence(user_ids=update.effective_user.id)
        await self._callbacks.notify_handle_result(f"每日饮水目标已设置为 {daily_goal} 毫升", update)

    async def _cmd_set_drank(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/set drank <drank_ml> - 设置已喝水量（毫升）"""
        currfunc = inspect.currentframe().f_code.co_name
        usage = self._usages[currfunc]
        if not usage.check_arg_len(context.args):
            await self._callbacks.notify_handle_result(usage.text, update)
            return

        try:
            (daily_drank,) = usage.parse_args(context.args)
            assert daily_drank >= 0, "已饮水量不能为负数"
        except (AssertionError, ValueError, Exception) as e:
            await self._callbacks.notify_handle_result(f"参数错误：{e}\n{usage.text}", update)
            return

        daily_goal = context.chat_data.setdefault(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)

        daily_drank_dict = context.chat_data.setdefault(KEY_DAILY_DRANK_DICT, {})
        daily_drank_dict[self._key_today()] = daily_drank

        context.application.mark_data_for_update_persistence(user_ids=update.effective_user.id)
        await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal} 毫升", update)

    async def _cmd_set_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置提醒间隔时间"""
        currfunc = inspect.currentframe().f_code.co_name
        usage = self._usages[currfunc]
        if not usage.check_arg_len(context.args):
            await self._callbacks.notify_handle_result(usage.text, update)
            return

        try:
            (minutes,) = usage.parse_args(context.args)
            assert minutes > 0, "提醒间隔时间必须大于 0 分钟"
        except (AssertionError, ValueError, Exception) as e:
            await self._callbacks.notify_handle_result(f"参数错误：{e}\n{usage.text}", update)
            return

        context.chat_data[KEY_REMINDER_INTERVAL] = minutes
        context.application.mark_data_for_update_persistence(user_ids=update.effective_user.id)
        # 调整job
        user_id = update.effective_user.id
        job_name = JOB_REMINDER_PREFIX + str(user_id)

        if next_t := self._reschedule_job_interval(context, job_name, minutes):
            await self._callbacks.notify_handle_result(f"提醒间隔时间已设置为 {minutes} 分钟，下次提醒时间 {next_t:%H:%M}", update)
        else:
            await self._callbacks.notify_handle_result(f"提醒间隔时间已设置为 {minutes} 分钟", update)

    # private utils
    def _reschedule_job_interval(self, context: ContextTypes.DEFAULT_TYPE, job_name: str, interval: float):
        """Reschedule job with new interval, return None if job not found"""
        if context.job_queue.get_jobs_by_name(job_name):
            context.job_queue.scheduler.reschedule_job(job_id=job_name, trigger='interval', minutes=interval)
            next_t = context.job_queue.get_jobs_by_name(job_name)[0].next_t.astimezone(pytz.timezone('Asia/Shanghai'))
            logger.info(f"Rescheduled job {job_name} with interval {interval} minutes, {next_t=}")
            return next_t
        return None

    def _remove_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        for job in context.job_queue.jobs():
            if job.user_id == user_id:
                job.schedule_removal()
                logger.info(f"Removed job {job.name}.")
        logger.debug(f'{context.job_queue.jobs()=}')

    @staticmethod
    async def _on_reminder(context: ContextTypes.DEFAULT_TYPE):
        """饮水提醒回调函数"""
        logger.debug(f"in reminder job callback, {context.job.enabled=}")
        now = datetime.datetime.now()
        logger.debug(f'{now=}')
        if REMINDER_MORNING_START <= now.time() <= REMINDER_MORNING_END or \
                REMINDER_AFTERNOON_START <= now.time() <= REMINDER_AFTERNOON_END:
            logger.debug('in reminder time')
            # 获取当前日期
            today = DailyDrinkNotifyBot._key_today()
            daily_goal = context.chat_data.setdefault(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)

            # 更新 chat_data 中的饮水记录
            daily_drank_dict = context.chat_data.setdefault(KEY_DAILY_DRANK_DICT, {})
            daily_drank = daily_drank_dict.get(today, 0)
            if daily_drank < daily_goal:
                logger.info('reminder: havn\'t reach daily goal')
                update: Update = context.job.data.get(JOBKEY_THIS_UPDATE)
                reply_text = f"该喝水了！今日已喝 {daily_drank}/{daily_goal}ml"

                await context.job.data.get(KEY_HANDLER_CALLBACKS).notify_handle_result(reply_text, update)

    async def _on_enable_job(self, context: ContextTypes.DEFAULT_TYPE):
        job: Job = context.job.data.get('job')
        if job and not job.removed:
            logger.info(f"Enabling job {job.name}.")
            job.enabled = True

    @staticmethod
    def _key_today():
        """获取今天的日期字符串"""
        return datetime.datetime.now().strftime("%Y-%m-%d")

    # prompts
    @property
    def _usages(self):
        #  https://docs.pydantic.dev/latest/usage/models/#dynamic-model-creation
        return {
            '_cmd_help': StringArgConverter('/help - 显示帮助信息'),
            '_cmd_drink': StringArgConverter('<drink_ml/drink_口数>[口/毫升/ml] - 记录饮水量，如果不带单位，默认个位数表示口数，两位以上表示毫升数'),
            '_cmd_set_target': StringArgConverter(
                f'/set target <target_ml={DEFAULT_DAILY_DRINK_GOAL}> - 设置每日饮水目标（毫升）',
                target_ml=(int, DEFAULT_DAILY_DRINK_GOAL)
            ),
            '_cmd_set_drank': StringArgConverter(
                '/set drank <drank_ml> - 设置已喝水量（毫升）',
                drank_ml=(int,)
            ),
            '_cmd_set_interval': StringArgConverter(
                '/set interval <minute=30> - 设置提醒间隔时间（分钟）',
                minute=(float, 30)
            ),
            '_cmd_today': StringArgConverter('/today - 查看今日饮水情况'),
            '_cmd_report': StringArgConverter(
                '/report <days=7> - 查看统计结果（默认7天）【未实现】',
                days=(int, 7)
            ),
            '_cmd_mute': StringArgConverter('/mute - 关闭提醒一天'),
            '_cmd_unmute': StringArgConverter('/unmute - 恢复提醒'),
            '_cmd_off': StringArgConverter('/off - 完全关闭提醒'),
            '_cmd_on': StringArgConverter('/on - 开启提醒'),
        }

