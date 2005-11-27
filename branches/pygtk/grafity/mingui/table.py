import wx
import wx.grid

from base import Widget
from signals import HasSignals


class _xTableData(wx.grid.PyGridTableBase):
    def __init__(self, data):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data
        self.data.connect('modified', self.ResetView)

        self.normal_attr = wx.grid.GridCellAttr()
        self.normal_attr.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

    def GetNumberRows(self):
        return self.data.get_n_rows()

    def GetNumberCols(self):
        return self.data.get_n_columns()

#    def IsEmptyCell(self, row, col):
#        return self.get_data(col, row) is None

    def GetValue(self, row, col):
        return self.data.get_data(col, row)

    def SetValue(self, row, col, value):
        self.data.set_data(col, row, value)

    def label_edited(self, column, name):
        if hasattr(self.data, 'label_edited'):
            self.data.label_edited(column, name)        

    def ResetView(self, view=None):
        """
        Reset the grid view. Call this to update the grid 
        if rows and columns have been added or deleted
        """
        if view is None:
            view = self.GetView()
        
        view.BeginBatch()
        
        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), 
             wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), 
             wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED), ]:
            
            if new < current:
                msg = wx.grid.GridTableMessage(self, delmsg, new, current-new)
                view.ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(self, addmsg, new-current)
                view.ProcessTableMessage(msg)
                self.UpdateValues(view)

        view.EndBatch()

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

        # update the scrollbars and the displayed part of the grid
        view.AdjustScrollbars()
        view.ForceRefresh()

    def UpdateValues(self, view):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        view.ProcessTableMessage(msg)

    def GetColLabelValue(self, col):
        return self.data.get_column_name(col)

    def GetRowLabelValue(self, row):
        return self.data.get_row_name(row)

class _xLabelEditor(wx.TextCtrl, HasSignals):
    def __init__(self, parent, column):
        wx.TextCtrl.__init__(self, parent, -1, parent.GetTable().data.get_column_name(column), 
                             style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
        self.parent, self.column = parent, column
        self.destroyed = False

        rect = parent.CellToRect(0, column)
        self.SetSize((rect[2], parent.GetColLabelSize()))
        self.SetPosition(parent.CalcScrolledPosition(parent.GetRowLabelSize()+rect[0], 0))
        self.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

        self.SetFocus()

    def on_enter(self, evt):
        self.parent.GetTable().label_edited(self.column, self.GetValue())
        if not self.destroyed:
            self.destroyed = True
            self.Destroy()

    def on_kill_focus(self, evt):
        if not self.destroyed:
            self.destroyed = True
            self.Destroy()

class _xGrid(wx.grid.Grid):
    def __init__(self, parent, data, table):
        wx.grid.Grid.__init__(self, parent, -1)
        self.table = table

        self.SetLabelFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.SetDefaultRowSize(20, False)

        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightDown)  
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)  
#        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)    
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelLeftClick)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.OnLabelLeftDClick)

        if data is not None:
            self.set_data(data)

    def set_data(self, data):
        table = _xTableData(data)
        data.connect('modified', self.set_attrs)

        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done.  Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)
        self.set_attrs()


    def set_attrs(self):
        for c in range(self.GetTable().data.get_n_columns()):
            attr = wx.grid.GridCellAttr()
            attr.SetBackgroundColour(self.GetTable().data.get_background_color(c))
            self.SetColAttr(c, attr)

    def OnLabelLeftDClick(self, evt):
        evt.Skip()
        if evt.GetRow() != -1:
            return
        if hasattr(self.GetTable().data, 'label_edited'):
            self.edit = _xLabelEditor(self, evt.GetCol())

    def OnMouseWheel(self, evt):
        evt.Skip()

    def OnLabelLeftClick(self, evt):
#        pass
        evt.Skip()
        
    def OnRangeSelect(self, evt):
#        print evt, type(evt)
#        if evt.Selecting():
        evt.Skip()

    def OnKeyDown(self, evt):
        if evt.KeyCode() != wx.WXK_RETURN:
            evt.Skip()
            return
        if evt.ControlDown():   # the edit control needs this key
            evt.Skip()
            return

        self.DisableCellEditControl()

        if not self.MoveCursorDown(True): 
            # add a new row
            self.GetTable().worksheet[self.GetGridCursorCol()][self.GetTable().GetNumberRows()] = nan

    def OnRightDown(self, event):
        self.table.emit('right-clicked', event.GetRow(), event.GetCol())
        event.Skip()

    def OnDblClick(self, event):
        self.table.emit('double-clicked', event.GetRow(), event.GetCol())
        event.Skip()

class Table(Widget, _xGrid):
    def __init__(self, place, data=None, **kwds):
        _xGrid.__init__(self, place[0], data, self)
        Widget.__init__(self, place, **kwds)

    def selected_columns():
        def fget(self):
            return self._widget.GetSelectedCols()
        def fset(self, cols):
            self._widget.ClearSelection()
            for c in cols:
                self._widget.SelectCol(c, True)
        return locals()
    selected_columns = property(**selected_columns())


