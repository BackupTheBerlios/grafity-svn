import os

import wx

def request_file_open(parent=None, message="Choose a file", wildcard="All Files|*.*",
                      directory=None):
    if directory is None:
        directory = os.getcwd()
    dlg = wx.FileDialog(parent, message=message, defaultDir=directory,
                        defaultFile="", wildcard=wildcard, 
                        style=wx.OPEN )
    if dlg.ShowModal() == wx.ID_OK:
        return dlg.GetPaths()
    else:
        return None
    dlg.Destroy()

def request_file_save(parent=None, message="Choose a file", wildcard="All Files|*.*",
                      directory=None):
    if directory is None:
        directory = os.getcwd()
    dlg = wx.FileDialog(parent, message=message, defaultDir=directory,
                        defaultFile="", wildcard=wildcard, 
                        style=wx.SAVE )
    if dlg.ShowModal() == wx.ID_OK:
        return dlg.GetPaths()[0]
    else:
        return None
    dlg.Destroy()

def alert_yesnocancel(message='', title=''):
    dlg = wx.MessageDialog(None, message, title,
                           wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
    result = dlg.ShowModal()
    dlg.Destroy()
    if result == wx.ID_YES:
        return 'yes'
    elif result == wx.ID_NO:
        return 'no' 
    elif result == wx.ID_CANCEL:
        return 'cancel'
