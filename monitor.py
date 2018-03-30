# -*- coding: utf-8 -*-

from threading import Thread
from queue import Queue   # , Empty
from hashlib import md5
import os
# import sys
import time
import json
import wx
import codecs
import win32file
import win32con


class MoniFrame(wx.Frame):

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
        self.Show(True)

        # relate events to buttons
        self.Bind(wx.EVT_MENU, self.on_open, menu_open)
        self.Bind(wx.EVT_MENU, self.on_save, menu_save)
        self.Bind(wx.EVT_MENU, self.on_font, menu_font)
        self.Bind(wx.EVT_MENU, self.on_clear, menu_clear)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)

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
        _msg = (
            ' :D\n\n'
            '\'+\' : added new file or folder\n'
            '\'-\' : removed file or folder\n'
            '\'*\' : updated file\n'
            '\'<\' : rename from __ to something\n'
            '\'>\' : rename from something to __\n'
        )

        with wx.MessageDialog(self, _msg, 'TIPS', wx.OK) as dlg:
            dlg.ShowModal()  # create and show the msgbox

    def on_exit(self, e):
        self.Close(True)

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
                action_log(time_str, act_str, filename, self.ecd, watch_code=wcode)


def action_log(time_str: str, act_str: str, filename: str, ecd: str, watch_code: str=0):
    _file = os.path.join(os.getcwd(), 'log', watch_code+'.csv')
    with codecs.open(_file, 'a', encoding=ecd) as f:
        f.write(f'{time_str},{act_str},{filename}\n')


def controler():
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
    app = wx.App(False)
    fr = MoniFrame(None, 'MiniMoni', ecd)
    t_moni = Thread(target=fr.monitor, args=(interv, wpath, q, wcode))
    t_moni.daemon = True
    t_moni.start()
    # input()
    app.MainLoop()


if __name__ == '__main__':
    controler()
