import unittest

from TVSubscribeBot import TVSubscribeBot
from TextSubmitter import DEFAULT_USER, DEFAULT_CHAT


class TestTVSubscribeBot(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = TVSubscribeBot()
        self.bot.handle_text('/sub login bazinga123 zzjzzj0123')

    def test_search(self):
        """/sub search <channel> <program> [detail] [startDate] [startTime] [findFirstMatch]"""
        basecmd = '/sub search '
        args_nomatch = [
            # 'フジテレビ 无匹配',
        ]
        args_single = [
            # normal
            # '"011 ＮＨＫ総合１・東京" "うたコン　生放送！Ｋｉｎｇ　＆　Ｐｒｉｎｃｅ・前川・清塚"',
            # # wildcard
            # 'NHK*1?東京 "うたコン　生放送！King　＆　Ｐｒｉｎｃｅ・前川・清塚"',
            # # wildcard
            # '"011 ＮＨＫ総合１・東京" "うたコン　生放送！King*前川?清塚"',
            # # wildcard
            # 'NHK*1?東京 "うたコン　生放送！King*前川?清塚"',
            # # detail
            # 'フジテレビ 世にも奇妙な物語 detail=奇妙な世界の扉が開く',
            # 'ＮＨＫ総合１・東京 【連続テレビ小説】らんまん findFirstMatch=1',
            # set time and date
            # 'フジテレビ ノンストップ！ startDate=20230620',
            # 'フジテレビ ノンストップ！ startDate=20230620 startTime=0950',
            # '* * detail=ＭＣバナナマン startDate=20230620 startTime=0950 findFirstMatch=1',
            # findFirstMatch
            # 'フジテレビ ノンストップ! findFirstMatch=1',
            # same day
            # 'フジテレビ ディノスＴＨＥストア findFirstMatch=true startDate=20230618',
            # excludeProgram
            # 'ＮＨＫ総合１・東京 【連続テレビ小説】らんまん excludeProgram=[再] findFirstMatch=1',
        ]
        args_multiple = [
            # 'ＮＨＫ総合１・東京 【連続テレビ小説】らんまん',
            # 'ＮＨＫ総合１・東京 【連続テレビ小説】らんまん excludeProgram=[再]',
            # '1?東京 列島ニュース',
            # '* 列島ニュース',
            'フジテレビ/ ノンストップ! startTime=0950',
            # same day
            # 'フジテレビ/ ディノスＴＨＥストア startDate=20230618',
            # same time
            # 'フジテレビ/ ディノスＴＨＥストア startTime=0425',
            # detail
            # '* * 通販のディノスが自信を持ってお届けする',
            # excludeProgram
            # '* 世にも奇妙な物語 excludeProgram=[再]',
        ]
        for cmd in args_nomatch:
            print(cmd)
            retmsg = self.bot.handle_text(basecmd + cmd)
            print(retmsg)
            print('\n')
            self.assertEqual(retmsg, '没有找到匹配的节目！')

        for cmd in args_single:
            print(cmd)
            retmsg = self.bot.handle_text(basecmd + cmd)
            print(retmsg)
            print('\n')
            self.assertIsNot(retmsg, '')
            self.assert_single_msg(retmsg)

        for cmd in args_multiple:
            print(cmd)
            retmsg = self.bot.handle_text(basecmd + cmd)
            print(retmsg)
            print('\n')
            self.assertIsNot(retmsg, '')
            self.assert_multiple_msg(retmsg)

    def assert_single_msg(self, msg):
        msgs = msg.split('\n\n')
        self.assertEqual(len(msgs), 1)

    def assert_multiple_msg(self, msg):
        msgs = msg.split('\n\n')
        self.assertGreater(len(msgs), 1)

    def test_epg(self):
        retmsg = self.bot.handle_text('/sub search * 列島ニュース')
        print(retmsg)
        # self.bot._subscribers[DEFAULT_CHAT].get

    def test_search_single(self):
        basecmd = '/sub search '
        cmd = '"NHK*BS1/" "ＢＳ１スペシャル「沖縄戦争孤児」"'
        retmsg = self.bot.handle_text(basecmd + cmd)
        print(basecmd + cmd)
        print(retmsg)
        self.assert_single_msg(retmsg)

    def test_subscribe(self):
        ret = self.bot.handle_text('/sub now "NHK*BS1/" "ＢＳ１スペシャル「沖縄戦争孤児」"')
        print(ret)

        ret = self.bot.handle_text('1')
        print(ret)


if __name__ == '__main__':
    unittest.main()