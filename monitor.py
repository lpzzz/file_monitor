# -*- coding: utf-8 -*-

from threading import Thread
from queue import Queue, Empty
from hashlib import md5
import os
import sys
import time
import json
import codecs
import win32file
import win32con

def action_log(time_str: str, act_str: str, filename: str, watch_code: str=0):
    _file = os.path.join(os.getcwd(), 'log', watch_code+'.csv')
    with codecs.open(_file, 'a', encoding='utf-8-sig') as f:
        f.write(f'{time_str},{act_str},{filename}\n')

def monitor(interv: int, wpath: str, in_q: Queue, wcode: str):
    ACTIONS = {
    1: '+', # create
    2: '-', # delete
    3: '*', # update
    4: '<', # rename
    5: '>'  # rename to
    }

    FILE_LIST_DIRECTORY = 0x0001
    print('Watching changes in', wpath)
    hDir = win32file.CreateFile(
    wpath,
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
            act_str = ACTIONS.get(action, '?')
            print(f'{time_str} {act_str} {filename}')
            action_log(time_str, act_str, filename, watch_code=wcode)



def controler():
    current_path = os.getcwd()
    interv, wpath = 1, current_path
    with codecs.open(os.path.join(current_path, 'setting.json'), encoding='utf-8') as f:
        setting = json.load(f)
        interv = setting.get('interval', 1)
        wpath = setting.get('path', current_path)
        if os.path.exists(wpath):
            wpath = os.path.join(wpath)
        else:
            raise FileNotFoundError

    _date = time.strftime('%Y%m%d')
    _path = md5(wpath.encode('utf8')).hexdigest()
    wcode = f'{_date}_{_path}'
    print(wpath)
    print(wcode)
    _file = os.path.join(os.getcwd(), 'log', wcode+'.csv')
    if not os.path.isfile(_file):
        with codecs.open(_file, 'w', encoding='utf-8-sig') as f:
            f.write(wpath + '\n')

    q = Queue() # currently no use
    t_moni = Thread(target=monitor, args=(interv, wpath, q, wcode))
    t_moni.daemon = True
    t_moni.start()
    _in = ''
    while _in != 'exit':
        _in = input()



if __name__ == '__main__':
    controler()
