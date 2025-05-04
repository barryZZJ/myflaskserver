import inspect
import traceback
import datetime
from pathlib import Path
from typing import Coroutine, TYPE_CHECKING, Union, TypeVar, Callable

from loguru import logger
from telegram.ext import Job

from tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot import DumbApplication, DumbBot, Chat
from tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot import Update, StringArgConverter, ChainCommandHandler
from tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot.ext import ApplicationBuilder, PicklePersistence, PersistenceInput
from tv_subscribe_bot.tvsubscribebot.dumb_bot.dumbbot.ext import MessageHandler, ContextTypes, filters
from tv_subscribe_bot.tvsubscribebot._jobsmapping import JOB_NAME
from tv_subscribe_bot.tvsubscribebot.utils.consts import PERSISTENCE_UPDATE_INTERVAL, JOBKEY_THIS_UPDATE
from tv_subscribe_bot.tvsubscribebot.utils.handlercallbacks import HandlerCallbacks
from tv_subscribe_bot.tvsubscribebot.utils.types import RESULT_TEXT, USER_ID

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

AMOUNTPERSIP = 50  # 每口多少毫升
DEFAULT_DAILY_DRINK_GOAL = 2000 # 默认每日饮水目标（毫升）
DEFAULT_REMINDER_INTERVAL = 30  # 默认提醒间隔时间（分钟）

# 饮水提醒相关常量
job_names: dict[USER_ID, list[JOB_NAME]] = {}
JOB_MORNING_REMINDER_PREFIX = 'drink_reminder_morning_job'  # 饮水提醒任务名
JOB_AFTERNOON_REMINDER_PREFIX = 'drink_reminder_afternoon_job'  # 饮水提醒任务名
KEY_REMINDER_INTERVAL = 'REMINDER_INTERVAL'
REMINDER_MORNING_START = datetime.time(9, 0)  # 早上开始时间
REMINDER_MORNING_END = datetime.time(12, 0)  # 中午结束时间
REMINDER_AFTERNOON_START = datetime.time(14, 0)  # 下午开始时间
REMINDER_AFTERNOON_END = datetime.time(21, 0)  # 晚上结束时间

class DailyDrinkNotifyBot:
    """This class have to run in main thread."""
    def __init__(
        self,
        persistence_filepath: Path,
        update_interval: float = PERSISTENCE_UPDATE_INTERVAL,
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
        # 	6. /mute 关闭提醒一天
        # 	7. /unmute 回复提醒
        # 	8. /off 完全关闭提醒
        # 	9. /on 开启提醒。早9点~12点，14~晚9点，每半小时提醒。job
        # 	10. /status 提醒是否开启
        # self.cmd_handlers_mute = ChainCommandHandler('/mute', self._cmd_mute) # TODO
        # self.cmd_handlers_unmute = ChainCommandHandler('/unmute', self._cmd_unmute) # TODO
        self.cmd_handlers_on = ChainCommandHandler('/on', self._cmd_on)
        self.cmd_handlers_off = ChainCommandHandler('/off', self._cmd_off)
        self.cmd_handlers_status = ChainCommandHandler('/status', self._cmd_status)
        # self.cmd_handlers_report = ChainCommandHandler('/report', self._cmd_report) # TODO
        self.cmd_handlers_today = ChainCommandHandler('/today', self._cmd_today)
        self.cmd_handlers_help = ChainCommandHandler('/help', self._cmd_help)

        self.cmd_handlers_drink = MessageHandler(filters.Regex('^\d+$'), self._cmd_drink)

        self._app.add_handler(self.cmd_handlers_set)
        # self._app.add_handler(self.cmd_handlers_mute)
        # self._app.add_handler(self.cmd_handlers_unmute)
        self._app.add_handler(self.cmd_handlers_on)
        self._app.add_handler(self.cmd_handlers_off)
        self._app.add_handler(self.cmd_handlers_status)
        # self._app.add_handler(self.cmd_handlers_report)
        self._app.add_handler(self.cmd_handlers_today)
        self._app.add_handler(self.cmd_handlers_help)
        self._app.add_handler(self.cmd_handlers_drink)

        # debug_handler = MessageHandler(filters.Regex('debug'), self._debug)
        # self._app.add_handler(debug_handler)

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
        ...

    def listen_forever(self, listen: str = "127.0.0.1", port: int = 18889):
        """Start server"""
        logger.info('listening at {}:{}', listen, port)
        self._app.run(listen, port)

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
            drink_amount = 0

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

            # 获取当前日期
            today = self._key_today
            daily_goal = context.chat_data.setdefault(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)

            # 更新 chat_data 中的饮水记录
            daily_drank_dict = context.chat_data.setdefault(KEY_DAILY_DRANK_DICT, {})
            daily_drank = daily_drank_dict.get(today, 0) + drink_amount
            daily_drank_dict[today] = daily_drank

            context.application.mark_data_for_update_persistence(user_ids=update.effective_user.id)
            # 回复用户
            if daily_drank >= daily_goal:
                await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal} 毫升\n已达成今日饮水目标！", update)
                # 关闭提醒
                await self._remove_reminders(update, context)
            else:
                await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal} 毫升", update)

        except Exception as e:
            logger.error("出错: {}", e)
            await self._callbacks.notify_handle_result(f"无法处理输入！\n{e}", update)

    async def _cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/today - 查看今日饮水情况"""
        chat_data = context.chat_data
        daily_goal = chat_data.setdefault(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)
        today = self._key_today
        daily_drank_dict = chat_data.get(KEY_DAILY_DRANK_DICT, {})
        daily_drank = daily_drank_dict.get(today, 0)

        await self._callbacks.notify_handle_result(f"今日已喝 {daily_drank}/{daily_goal}ml", update)

    async def _cmd_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/on - 开启提醒"""
        # TODO job可能要改成存入jobstore了，否则每次重启都需要手动发送 /on
        chat_data = context.chat_data
        interval = chat_data.setdefault(KEY_REMINDER_INTERVAL, DEFAULT_REMINDER_INTERVAL)
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        job_name_morning = JOB_MORNING_REMINDER_PREFIX + str(user_id)
        job_name_afternoon = JOB_AFTERNOON_REMINDER_PREFIX + str(user_id)

        # job_morning
        if job_name_morning not in job_names.setdefault(user_id, []):
            logger.warning(f"Creating job {job_name_morning}.")
            context.job_queue.run_repeating(
                callback=self._on_reminder,
                interval=interval * 60,
                first=REMINDER_MORNING_START,
                last=REMINDER_MORNING_END,
                data={
                    JOBKEY_THIS_UPDATE: update,
                },
                name=job_name_morning,
                chat_id=chat_id,
                user_id=user_id,
            )
            job_names.setdefault(user_id, []).append(job_name_morning)

        # job_afternoon
        if job_name_afternoon not in job_names.setdefault(user_id, []):
            logger.warning(f"Creating job {job_name_afternoon}.")
            context.job_queue.run_repeating(
                callback=self._on_reminder,
                interval=interval * 60,
                first=REMINDER_AFTERNOON_START,
                last=REMINDER_AFTERNOON_END,
                data={
                    JOBKEY_THIS_UPDATE: update,
                },
                name=job_name_afternoon,
                chat_id=chat_id,
                user_id=user_id,
            )
            job_names.setdefault(user_id, []).append(job_name_afternoon)

        await self._callbacks.notify_handle_result(f"已开启提醒，将在{REMINDER_MORNING_START:%H:%M}~{REMINDER_MORNING_END:%H:%M}、{REMINDER_AFTERNOON_START:%H:%M}~{REMINDER_AFTERNOON_END:%H:%M}之间，每隔{interval}分钟提醒一次！", update)

    async def _cmd_off(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/off - 关闭提醒"""
        await self._remove_reminders(update, context)
        await self._callbacks.notify_handle_result("已关闭饮水提醒", update)

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看当前的提醒状态"""
        user_id = update.effective_user.id
        if len(job_names.setdefault(user_id, [])) != 2:
            await self._callbacks.notify_handle_result("提醒未开启", update)
        else:
            await self._callbacks.notify_handle_result("提醒已开启", update)

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
        daily_drank_dict[self._key_today] = daily_drank

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
        await self._callbacks.notify_handle_result(f"提醒间隔时间已设置为 {minutes} 分钟", update)

    # private utils
    async def _remove_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        for job_name in job_names.get(user_id, []):
            try:
                jobs: tuple[Job] = context.job_queue.get_jobs_by_name(job_name)
                assert len(jobs) >= 1
                job = jobs[0]
                job.schedule_removal()
                logger.info(f"Removing job {job_name}.")
            except (IndexError, AssertionError):
                logger.warning(f"Job {job_name} not found.")


    async def _on_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        """饮水提醒回调函数"""
        update: Update = context.job.data.get(JOBKEY_THIS_UPDATE)

        chat_data = context.chat_data
        daily_goal = chat_data.setdefault(KEY_DAILY_DRINK_GOAL, DEFAULT_DAILY_DRINK_GOAL)
        today = self._key_today
        daily_drank_dict = chat_data.get(KEY_DAILY_DRANK_DICT, {})
        daily_drank = daily_drank_dict.get(today, 0)
        reply_text = f"该喝水了！今日已喝 {daily_drank}/{daily_goal}ml"

        await self._callbacks.notify_handle_result(reply_text, update)

    @property
    def _key_today(self):
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
                minute=(int, 30)
            ),
            '_cmd_today': StringArgConverter('/today - 查看今日饮水情况'),
            '_cmd_report': StringArgConverter(
                '/report <days=7> - 查看统计结果（默认7天）【未实现】',
                days=(int, 7)
            ),
            '_cmd_mute': StringArgConverter('/mute - 关闭提醒一天【未实现】'),
            '_cmd_unmute': StringArgConverter('/unmute - 恢复提醒【未实现】'),
            '_cmd_off': StringArgConverter('/off - 完全关闭提醒'),
            '_cmd_on': StringArgConverter('/on - 开启提醒'),
        }

