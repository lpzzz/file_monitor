from threading import Thread
from queue import Queue, Empty
import os
import sys
import time
import json

import win32file
import win32con

def action_log(time_str: str, act_str: str, filename: str):
    return None

def monitor(interv: int, path_to_watch: str, in_q: Queue):
    ACTIONS = {
    1: "+", # create
    2: "-", # delete
    3: "*", # update
    4: "<", # rename
    5: ">"  # rename to
    }

    FILE_LIST_DIRECTORY = 0x0001
    print('Watching changes in', path_to_watch)
    hDir = win32file.CreateFile(
    path_to_watch,
    FILE_LIST_DIRECTORY,
    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
    None,
    win32con.OPEN_EXISTING,
    win32con.FILE_FLAG_BACKUP_SEMANTICS,
    None
    )
    flag = True
    while flag:

        results = win32file.ReadDirectoryChangesW(
            hDir,
            1024,
            True,
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
            win32con.FILE_NOTIFY_CHANGE_SIZE |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
            win32con.FILE_NOTIFY_CHANGE_SECURITY,
            None,
            None)
        for action, filename in results:
            time_str = time.strftime('%Y%m%d%H%M')
            act_str = ACTIONS.get(action, "?")
            print(f'{time_str} {act_str} {filename}')
            action_log(time_str, act_str, filename)
            # full_filename = os.path.join(path_to_watch, filename)
            # print(full_filename, ACTIONS.get(action, "Unknown"))

    return None


def controler():
    _path = os.getcwd()
    interv, path_to_watch = 1, _path
    with open(_path + '/setting.json') as f:
        setting = json.load(f)
        interv = setting.get('interval', 1)
        path_to_watch = setting.get('path', _path)
    q = Queue() # currently no use
    t_moni = Thread(target=monitor, args=(interv, path_to_watch, q))
    t_moni.daemon = True
    t_moni.start()
    _in = ''
    while _in != 'exit':
        _in = input()
    return None


if __name__ == '__main__':
    controler()
