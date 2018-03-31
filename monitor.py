# -*- coding: utf-8 -*-

import codecs
import json
import os
# import sys
import time
from hashlib import md5
from queue import Queue  # , Empty
from threading import Thread

import win32con
import wx
import wx.adv

import win32file

APP_NAME = 'minimoni'
ICON_FILE = os.path.join(os.getcwd(), 'icon.png')
MSG_ABOUT = (
    ' :D\n\n'
    '\'+\' : added new file or folder\n'
    '\'-\' : removed file or folder\n'
    '\'*\' : updated file\n'
    '\'<\' : rename from __ to something\n'
    '\'>\' : rename from something to __\n'
)


class TextDisplay(wx.Frame):

    def __init__(self, parent, title, ecd):
        wx.Frame.__init__(self, parent, title=title, size=(300, 200))
        self.textctrl = wx.TextCtrl(self, id=-1, value='', style=wx.TE_READONLY | wx.TE_MULTILINE,)
        self.textctrl.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas'))
        self.Show(True)
        # self.CreateStatusBar()
        self.q = Queue
        self.openfile = os.path.join(os.getcwd(), 'log/')
        self.ecd = ecd
        self.reading_mode = True
        self.about = MSG_ABOUT
        self.ishide = False

        # set menu contents
        filemenu = wx.Menu()
        menu_open = filemenu.Append(wx.ID_OPEN, 'Open', ' ')
        menu_save = filemenu.Append(wx.ID_SAVE, 'Save as', ' ')
        menu_clear = filemenu.Append(wx.MenuItem(filemenu, id=102, text='Clear', kind=wx.ITEM_NORMAL))
        filemenu.AppendSeparator()
        menu_exit = filemenu.Append(wx.ID_EXIT, 'Exit', 'Termanate the program')

        optionmenu = wx.Menu()
        menu_font = optionmenu.Append(wx.MenuItem(optionmenu, id=101, text='Font', kind=wx.ITEM_NORMAL))
        optionmenu.AppendSeparator()
        menu_about = optionmenu.Append(wx.ID_ABOUT, 'About', '')

        # create menu bar
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, 'File')
        menuBar.Append(optionmenu, 'option')
        self.SetMenuBar(menuBar)

        # bind events to buttons
        self.Bind(wx.EVT_MENU, self.on_open, menu_open)
        self.Bind(wx.EVT_MENU, self.on_save, menu_save)
        self.Bind(wx.EVT_MENU, self.on_font, menu_font)
        self.Bind(wx.EVT_MENU, self.on_clear, menu_clear)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)

        # iconize and close event
        self.Bind(wx.EVT_ICONIZE, self.on_iconize)
        self.Bind(wx.EVT_CLOSE, self.on_exit)

        # show
        self.Show(True)
        self.create_taskbar_icon()

    def create_taskbar_icon(self):
        self.tbi = wx.adv.TaskBarIcon()
        self.tbi.SetIcon(wx.Icon(wx.Bitmap(ICON_FILE)), APP_NAME)

        # set menu contents
        traymenu = wx.Menu()
        menu_restore = traymenu.Append(wx.MenuItem(traymenu, id=201, text='Restore', kind=wx.ITEM_NORMAL))
        traymenu.AppendSeparator()
        menu_exit = traymenu.Append(wx.ID_EXIT, 'Exit', 'Termanate the program')
        self.traymenu = traymenu

        # bind events to buttons
        self.tbi.Bind(wx.adv.EVT_TASKBAR_RIGHT_DOWN, self.on_taskbar_right_down)
        self.tbi.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_restore)
        self.tbi.Bind(wx.EVT_MENU, self.on_restore, menu_restore)
        self.tbi.Bind(wx.EVT_MENU, self.on_exit, menu_exit)

    # Handlers

    def on_taskbar_right_down(self, e):
        # print('!!!')
        self.tbi.PopupMenu(self.traymenu)

    def on_restore(self, e):
        if not self.IsShown():
            self.Iconize(False)
            self.Show(True)
            # print('shown')

    def on_iconize(self, e):
        if self.IsIconized():
            if self.IsShown():
                self.Show(False)
                # print('hided')

    def on_font(self, e):
        if e.GetId() == 101:
            with wx.FontDialog(self, wx.FontData()) as dlg:
                if dlg.ShowModal() == wx.ID_CANCEL:
                    return

                data = dlg.GetFontData()
                Font = data.GetChosenFont()
                print(Font)
                self.textctrl.SetFont(Font)

    def on_clear(self, e):
        if e.GetId() == 102:
            self.textctrl.Clear()

    def on_about(self, e):
        with wx.MessageDialog(self, self.about, 'TIPS', wx.OK) as dlg:
            dlg.ShowModal()  # create and show the msgbox

    def on_exit(self, e):
        if 'tbi' in self.__dict__:
            self.tbi.Destroy()
        self.Destroy()

    def on_open(self, e):
        with wx.FileDialog(self, 'Choose a file', defaultFile=self.openfile, wildcard='*.*',
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:  # explorer
            if dlg.ShowModal() == wx.ID_CANCEL:
                return

            self.reading_mode = True
            self.openname = dlg.GetFilename()
            self.opendir = dlg.GetDirectory()
            self.openfile = os.path.join(self.opendir, self.openname)

            with codecs.open(self.openfile, 'r', encoding=self.ecd) as f:
                _str = f.read()

            self.textctrl.Clear()
            self.textctrl.AppendText(_str)
            # self.textctrl.AppendText('test1')
            # self.textctrl.AppendText('test2')

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
            self.textctrl.Clear()
            # self.textctrl.AppendText(u'Welcome')

    def monitor(self, interv: int, wpath: str, out_q: Queue, wcode: str):
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
                time_str = time.strftime('%Y%m%d%H%M')
                act_str = ACTIONS.get(action, '?')
                f_str = f'{time_str},{act_str},{filename}\n'

                if self.reading_mode:
                    self.textctrl.AppendText(wpath + '\n')
                    self.reading_mode = False

                self.textctrl.AppendText(f_str)   # output
                self.action_log(time_str, act_str, filename, wcode)

    def action_log(self, time_str: str, act_str: str, filename: str, watch_code: str=0):
        _file = os.path.join(os.getcwd(), 'log', watch_code+'.csv')
        with codecs.open(_file, 'a', encoding=self.ecd) as f:
            f.write(f'{time_str},{act_str},{filename}\n')


class App(wx.App):
    def OnInit(self):
        current_path = os.getcwd()
        interv, wpath = 0, current_path
        with codecs.open(os.path.join(current_path, 'setting.json'), encoding='utf-8') as f:
            setting = json.load(f)
            interv = setting.get('interval', 1)
            wpath = setting.get('path', current_path)
            ecd = setting.get('encoding', 'utf-8-sig')
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
            with codecs.open(_file, 'w', encoding=ecd) as f:
                f.write(wpath + '\n')

        q = Queue()  # currently no use
        td = TextDisplay(None, APP_NAME, ecd)
        t_moni = Thread(target=td.monitor, args=(interv, wpath, q, wcode))
        t_moni.daemon = True
        t_moni.start()
        return True


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item


def controler():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    controler()
