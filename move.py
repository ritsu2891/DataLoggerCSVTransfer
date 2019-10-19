import pathlib
import datetime
import re
import shutil
import time
from argparse import ArgumentParser

latestCsvDatetime = None

def _detectTarget(targetPath, pathFmt, dtFmt, searchFolder):
    res = None

    # 対象ディレクトリの全フォルダ・ファイルを取得
    targetCandidates = list(pathlib.Path(targetPath).glob('*'))

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

        matched = matched + [{ 'dt': dtObj, 'name': targetCandidate.name }]

    # 日付順に並び替え
    if (len(matched) > 0):
        res = sorted(matched, key=lambda x:x['dt'], reverse=True)
    else:
        res = None
    return res

def parser():
    usage = 'Usage: python {} TARGET_PATH DEST_PATH FILE_NAME [--debug] [--help]'\
            .format(__file__)
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument('TARGET_PATH', type=str,
                           help='監視対象のディレクトリ')
    argparser.add_argument('DEST_PATH', type=str,
                           help='出力対象のディレクトリ')
    argparser.add_argument('FILE_NAME', type=str,
                           help='出力ファイル名')
    argparser.add_argument('-d', '--debug',
                           action='store_true',
                           help='デバッグモード')
    args = argparser.parse_args()
    return args

if __name__ == '__main__':
    args = parser()
    print(args)

    targetPath = args.TARGET_PATH
    destPath = args.DEST_PATH
    destFileName = args.FILE_NAME

    interval = 3

    pathFmt = ["^\d{2}-\d{2}-\d{2}", "^\d{2}_\d{2}_\d{2}", "^\d{6}-\d{6}"]
    dtFmt = ["%y-%m-%d", "%H_%M_%S", "%y%m%d-%H%M%S"]
    isFolder = [True, True, False]

    latestDt = None

    print("監視を開始します.....")
    print("終了するには Ctrl-C を入力してください")

    while True:

        _targetPath = targetPath
        res = None

        for i in range(3):
            res = _detectTarget(_targetPath, pathFmt[i], dtFmt[i], isFolder[i])
            if res == None:
                break
            __targetPath = _targetPath + res[0]["name"]
            _targetPath = __targetPath + "/"

        if res != None and (latestDt == None or latestDt < res[0]["dt"]):
            print("● 新しいデータを発見しました：　{}".format(__targetPath))
            latestDt =  res[0]["dt"]
            shutil.copy2(__targetPath, destPath + destFileName)

        time.sleep(interval)