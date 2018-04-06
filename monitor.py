# -*- coding: utf-8 -*-

import codecs
import json
import os
import re
import time
import traceback
from hashlib import md5
from queue import Queue  # , Empty
from threading import Thread, Lock

import win32con
import wx
import wx.adv
import webbrowser

import win32file
from icon import ei

VER = '1.4'
APP_NAME = 'MiniMoni'
GITHUB = 'https://github.com/lpzzz/file_monitor/releases'
# ICON_FILE = os.path.join(os.getcwd(), 'monitor.ico')
MSG_ABOUT = (
    ' :D\n\n'
    '\'+\' : added new file or folder\n'
    '\'-\' : removed file or folder\n'
    '\'*\' : updated file\n'
    '\'<\' : rename from __ to something\n'
    '\'>\' : rename from something to __\n'
)


class TextDisplay(wx.Frame):

    def __init__(self, parent, title, *, size=(500, 200), encoding='utf-8', q=None):
        self.ti: TrayIcon = None  # Tray Icon
        super(TextDisplay, self).__init__(parent, title=title, size=size)
        # self.SetIcon(wx.Icon(wx.Bitmap(ICON_FILE)))
        self.SetIcon(ei.GetIcon())
        self.openfile = os.path.join(os.getcwd(), 'log/')
        self.ecd = encoding
        self.print_id = 0
        self.show_balloon = True

        self.create_menubar()
        self.create_textctrl()
        # self.statusbar = self.CreateStatusBar()
        self.Bind(wx.EVT_ICONIZE, self.on_iconize)

    def create_textctrl(self):
        self.textctrl = wx.TextCtrl(self, id=-1, value='', style=wx.TE_READONLY | wx.TE_MULTILINE,)
        self.textctrl.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas'))

    def create_menubar(self):
        bar = wx.MenuBar()
        menu_file = wx.Menu()
        menu_preference = wx.Menu()
        bar.Append(menu_file, 'File')
        bar.Append(menu_preference, 'Preference')

        #       'File' Menu
        item_open = menu_file.Append(wx.ID_OPEN, 'Open', '')
        self.Bind(wx.EVT_MENU, self.on_open, item_open)
        item_save = menu_file.Append(wx.ID_SAVE, 'Save as', '')
        self.Bind(wx.EVT_MENU, self.on_save, item_save)
        item_clear = menu_file.Append(wx.MenuItem(menu_file, id=-1, text='Clear', kind=wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, self.on_clear, item_clear)
        menu_file.AppendSeparator()
        item_exit = menu_file.Append(wx.ID_EXIT, 'Exit', 'Termanate the program')
        self.Bind(wx.EVT_MENU, self.on_exit, item_exit)

        #       'Preference' Menu
        item_font = menu_preference.Append(wx.MenuItem(menu_preference, id=-1, text='Font', kind=wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, self.on_font, item_font)
        item_hide = menu_preference.Append(wx.MenuItem(menu_preference, id=-1, text='Hide', kind=wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, self.on_hide, item_hide)
        menu_preference.AppendSeparator()
        item_update = menu_preference.Append(wx.MenuItem(menu_preference, id=-1, text=f'ver.{VER}', kind=wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, self.on_update, item_update)
        item_about = menu_preference.Append(wx.ID_ABOUT, 'About', '')
        self.Bind(wx.EVT_MENU, self.on_about, item_about)

        self.SetMenuBar(bar)

    def on_open(self, e):
        with wx.FileDialog(self, 'Choose a file', defaultFile=self.openfile, wildcard='*.*',
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:  # explorer
            if dlg.ShowModal() == wx.ID_CANCEL:
                return

            self.print_id = 0
            self.openname = dlg.GetFilename()
            self.opendir = dlg.GetDirectory()
            self.openfile = os.path.join(self.opendir, self.openname)

            with codecs.open(self.openfile, 'r', encoding=self.ecd) as f:
                _str = f.read()

            self.textctrl.Clear()
            self.textctrl.AppendText(_str)

    def on_save(self, e):
        with wx.FileDialog(self, 'Save as', defaultFile=self.openfile, wildcard='*.*',
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return

            self.savename = dlg.GetFilename()
            self.savedir = dlg.GetDirectory()
            self.savefile = os.path.join(self.savedir, self.savename)

            with codecs.open(self.savefile, 'w', encoding=self.ecd) as f:
                f.write(self.textctrl.GetValue())

            dlg = wx.MessageDialog(self, 'Saved successfully', '', wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            # self.textctrl.Clear()

    def on_clear(self, e):
        self.textctrl.Clear()

    def on_font(self, e):
        with wx.FontDialog(self, wx.FontData()) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return

            data = dlg.GetFontData()
            Font = data.GetChosenFont()
            print(Font)
            self.textctrl.SetFont(Font)

    def on_iconize(self, e):
        if self.IsIconized():
            self.on_hide(e)

    def on_hide(self, e):
        if self.IsShown():
            self.Show(False)
            self.ti = TrayIcon(self)  # argment 'self' equals the instance

    def on_about(self, e):
        with wx.MessageDialog(self, MSG_ABOUT, 'TIPS', wx.OK) as dlg:
            dlg.ShowModal()  # create and show the msgbox

    def on_update(self, e):
        webbrowser.open(GITHUB, new=0, autoraise=True)

    def on_exit(self, e):
        try:
            self.ti.Destroy()
        except AttributeError:
            pass
        except RuntimeError:
            pass
        self.Destroy()


class TrayIcon(wx.adv.TaskBarIcon):

    def __init__(self, td, show_balloon=False, stray=False):
        self.td: TextDisplay = td  # Text Display
        super(TrayIcon, self).__init__()
        # self.SetIcon(wx.Icon(wx.Bitmap(ICON_FILE)), APP_NAME)
        self.SetIcon(ei.GetIcon(), APP_NAME)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_restore)
        if self.td.show_balloon:
            _str = ''
            if stray:
                _str = 'MiniMoni started.\n'
            self.ShowBalloon(':D', _str + 'Double click to restore window.', msec=5000)
            self.td.show_balloon = False

    def CreatePopupMenu(self):
        menu_tray = wx.Menu()
        item_restore = menu_tray.Append(wx.MenuItem(menu_tray, id=-1, text='Restore', kind=wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, self.on_restore, item_restore)
        item_update = menu_tray.Append(wx.MenuItem(menu_tray, id=-1, text=f'ver.{VER}', kind=wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, self.on_update, item_update)
        menu_tray.AppendSeparator()
        item_exit = menu_tray.Append(wx.ID_EXIT, 'Exit')
        self.Bind(wx.EVT_MENU, self.on_exit, item_exit)
        return menu_tray

    def on_restore(self, e):
        if not self.td.IsShown():
            self.td.Show(True)
            self.td.Iconize(False)
            self.td.Raise()
        self.Destroy()

    def on_update(self, e):
        webbrowser.open(GITHUB, new=0, autoraise=True)

    def on_exit(self, e):
        try:
            self.td.Destroy()
        except AttributeError:
            pass
        except RuntimeError:
            pass
        self.Destroy()


class App(wx.App):

    def OnInit(self):
        self.current_path = os.getcwd()
        if not self.precheck():
            return False
        self.strcache = ''
        #       default setting
        interv = 0
        path_list = [self.current_path]
        ecd = 'utf-8'
        size = (500, 200)
        stray = True

        try:
            with codecs.open(os.path.join(self.current_path, 'setting.json'), encoding='utf-8') as f:
                setting = json.load(f)
                interv = setting.get('interval', 1)  # currently no use
                path_list = setting.get('path_you_watch', self.current_path)
                ecd = setting.get('encoding', 'utf-8-sig')
                size = setting.get('frame_size', (500, 200))
                stray = setting.get('stay_to_tray', True)

        except json.decoder.JSONDecodeError:
            self.warning(traceback.format_exc(), 'WARNING: Using default setting')

        self.td = TextDisplay(None, APP_NAME, encoding=ecd, size=size)

        for i in range(len(path_list)):
            wpath = path_list[i]
            _date = time.strftime('%Y%m%d')
            _path = md5(wpath.encode('utf8')).hexdigest()
            wcode = f'{_date}_{_path}'

            if os.path.exists(wpath):
                path_list[i] = (os.path.join(wpath), wcode)
            else:
                self.warning(f'path {wpath} cannot be found', 'WARNING')
                return False

            self.ecd = ecd
            print(wpath)
            print(wcode)
            log_file = os.path.join(self.current_path, 'log', wcode+'.csv')
            if not os.path.isfile(log_file):
                with codecs.open(log_file, 'w', encoding=ecd) as f:
                    f.write(wpath + '\n')

        self.queue = Queue()  # currently no use
        self.lock = Lock()

        thread_list = list()
        # i = 0
        for wpath, wcode in path_list:
            # i += 1
            thread_moni = Thread(target=self.monitor, args=(wpath, wcode, interv))
            thread_moni.daemon = True
            thread_list.append(thread_moni)
            thread_moni.start()

        if stray:
            self.td.Show(False)
            self.td.ti = TrayIcon(self.td, stray=True)
            stray = False
        else:
            self.td.Show(True)

        return True

    def precheck(self):
        setting_path = os.path.join(self.current_path, 'setting.json')
        if not os.path.exists(setting_path) or not os.path.isfile(setting_path):
            with codecs.open(setting_path, 'w', encoding='utf-8') as f:
                self.current_path = self.current_path.replace('\\', '/')
                f.write(
                    '{\n'
                    '    \"path_you_watch\":\n'
                    '    [\n'
                    f'        \"{self.current_path}\"\n'
                    '    ],\n'
                    '    \"encoding\": \"utf-8-sig\",\n'
                    '    \"frame_size\": [500, 200],\n'
                    '    \"start_to_tray\": true\n'
                    '}\n'
                )
        log_path = os.path.join(self.current_path, 'log')
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        elif os.path.isfile(log_path):
            self.warning('Cannot make directory \"log\"')
            return False
        return True

    def warning(self, content: str, title: str='WARNING'):
        w = wx.Frame(None, id=-1)
        with wx.MessageDialog(w, content, title, wx.OK) as dlg:
            dlg.ShowModal()
        w.Destroy()

    def monitor(self, wpath: str, wcode: int, interv: int):
        ACTIONS = {
            1: '+',  # create
            2: '-',  # delete
            3: '*',  # update
            4: '<',  # rename
            5: '>'   # rename to
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
            time.sleep(interv)
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
                None
            )
            for action, filename in results:

                pattern = f'^(\S*)(.csv)$'
                if re.match(pattern, filename) is None:  # exclude the log file being used

                    time_str = time.strftime('%Y%m%d%H%M%S')
                    act_str = ACTIONS.get(action, '?')
                    f_str = f'{time_str},{act_str},{filename}'

                    self.lock.acquire()
                    if self.td.print_id != wcode:
                        self.strcache += wpath + '\n'
                        self.td.textctrl.AppendText(wpath + '\n')
                        self.td.print_id = wcode
                    self.strcache += f_str + '\n'   # output
                    self.td.textctrl.AppendText(f_str + '\n')
                    self.lock.release()

                    self.action_log(time_str, act_str, filename, wcode)

    def action_log(self, time_str: str, act_str: str, filename: str, wcode: int):
        log_file = os.path.join(os.getcwd(), 'log', wcode+'.csv')
        with codecs.open(log_file, 'a', encoding=self.ecd) as f:
            f.write(f'{time_str},{act_str},{filename}\n')


def controler():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    controler()
