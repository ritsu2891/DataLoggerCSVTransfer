import pathlib
import datetime
import re
import shutil
import time
import copy
import gettext
import os
import textwrap
from logging import basicConfig, getLogger, DEBUG
from argparse import ArgumentParser, RawDescriptionHelpFormatter

def argParseLocalize(Text):
    Text = Text.replace("usage", "使い方")
    Text = Text.replace("show this help message and exit", "このヘルプ画面を出して終了します")
    Text = Text.replace("positional arguments", "指定位置引数（必須）")
    Text = Text.replace("optional arguments", "オプション引数")
    Text = Text.replace("error:", "エラー:")
    Text = Text.replace("the following arguments are required:", "以下の引数が必要です:")
    return Text
gettext.gettext = argParseLocalize
logger = getLogger(__name__)
latestCsvDatetime = None


# 冒頭の表示
def welcome():
    text = textwrap.dedent("""
    /*--------------------------------------------.
    　データロガーの最新CSVファイル自動コピースクリプト
    　(c) 2019, Ritsuki KOKUBO (dev.rpaka)
    `---------------------------------------------*/

    監視を開始します.....
    終了するには Ctrl-C を入力してください
    """)
    print(text)


# 引数のパース
def parser():
    description = "データロガーの最新CSVファイル自動コピースクリプト\n(c) 2019, Ritsuki KOKUBO (dev.rpaka)"
    usage = 'python {} TARGET_PATH DEST_PATH FILE_NAME [--help] [--interval 1] [--debug] '\
            .format(__file__)
    argparser = ArgumentParser(description=description, usage=usage, formatter_class=RawDescriptionHelpFormatter)
    argparser.add_argument('TARGET_PATH', type=str,
                           help='監視対象のディレクトリ')
    argparser.add_argument('DEST_PATH', type=str,
                           help='出力対象のディレクトリ')
    argparser.add_argument('FILE_NAME', type=str,
                           help='出力ファイル名')
    argparser.add_argument('-i', '--interval', type=int,
                           default=3,
                           help='データ探索間隔(秒) [デフォルト: 3]')
    argparser.add_argument('-d', '--debug',
                           action='store_true',
                           help='デバッグモード')

    args = argparser.parse_args()

    if args.debug:
        os.environ['ENV'] = 'DEBUG'

    return args


# 出力先の存在確認
def checkDestPath(destPath):
    if not destPath.exists():
        raiseErrorMsg("出力対象パスが存在しません: {}".format(destPath.as_posix()))
    if not destPath.is_dir():
        raiseErrorMsg("出力対象パスがフォルダではありません: {}".format(destPath.as_posix()))


# エラー時メッセージ
def raiseErrorMsg(msg):
    print("{}: エラー: {}".format(__file__, msg))
    exit(1)


# 各階層における最新フォルダ・ファイルの決定
def detectTarget(targetPath, pathFmt, dtFmt, searchFolder):
    res = None

    # 対象ディレクトリの全フォルダ・ファイルを取得
    targetCandidates = list(targetPath.glob('*'))

    # 命名規則に合致するファイル・フォルダを残す
    matched = []
    for targetCandidate in targetCandidates:
        # フォルダを検索しているのにフォルダじゃない、ファイルを検索しているのにファイルじゃない場合はスキップ
        if targetCandidate.is_dir() ^ searchFolder:
            continue
        # フォーマットと合わなければスキップ
        regexRes = re.match(pathFmt, targetCandidate.name)
        if regexRes == None:
            continue

        # datetimeオブジェクトを生成
        dtObj = datetime.datetime.strptime(regexRes.group(), dtFmt)

        matched = matched + [{ 'dt': dtObj, 'path': targetCandidate }]

    # 日付順に並び替え
    if (len(matched) > 0):
        res = sorted(matched, key=lambda x:x['dt'], reverse=True)
    else:
        res = None
    return res

if __name__ == '__main__':
    # 引数パース・検証
    args = parser()
    logger.debug(args)
    targetPath = pathlib.Path(args.TARGET_PATH)
    destPath = pathlib.Path(args.DEST_PATH)
    destFileName = args.FILE_NAME
    checkDestPath(destPath)

    # ログレベル設定
    if (os.getenv('ENV') == 'DEBUG'):
        basicConfig(level=DEBUG)

    # パラメータ
    nDeep = 3
    pathFmt = ["^\d{2}-\d{2}-\d{2}", "^\d{2}_\d{2}_\d{2}", "^\d{6}-\d{6}"]
    dtFmt = ["%y-%m-%d", "%H_%M_%S", "%y%m%d-%H%M%S"]
    isFolder = [True, True, False]
    latestDt = None

    # タイトルメッセージ表示
    welcome()

    # 監視ループ
    while True:
        _targetPath = copy.copy(targetPath)
        res = None

        for i in range(nDeep):
            res = detectTarget(_targetPath, pathFmt[i], dtFmt[i], isFolder[i])
            if res == None:
                break
            _targetPath = _targetPath.joinpath(res[0]["path"].name)

        if res != None and (latestDt == None or latestDt < res[0]["dt"]):
            print("● 新しいデータを発見しました： {}".format(_targetPath.as_posix()))
            latestDt = res[0]["dt"]
            shutil.copy2(_targetPath.as_posix(), destPath.joinpath(destFileName).as_posix())
        else:
            logger.debug("新しいデータは見つかりませんでした")

        time.sleep(args.interval)