import sys

from grafit.signals import HasSignals
from grafit.arrays import nan, array
from grafit.worksheet import Worksheet

import mingui as gui

NORMAL_COL_BGCOLOR = (255, 255, 255)
AUTO_COL_BGCOLOR = (220, 220, 255)

class TableData(HasSignals):
    def __init__(self, worksheet):
        self.worksheet = worksheet
        self.worksheet.connect('data-changed', self.on_data_changed)

    def on_data_changed(self): self.emit('modified')
    def get_n_columns(self): return self.worksheet.ncolumns
    def get_n_rows(self): return self.worksheet.nrows
    def get_column_name(self, col): return self.worksheet.column_names[col]
    def label_edited(self, col, value): self.worksheet.columns[col].name = value
    def get_row_name(self, row): return str(row)
    def get_data(self, col, row): return str(self.worksheet[col][row]).replace(repr(nan), '')
    def get_background_color(self, col): 
        return (AUTO_COL_BGCOLOR, NORMAL_COL_BGCOLOR)[self.worksheet[col].expr == '']
    def set_data(self, col, row, value): 
        try:
            f = float(value)
        except ValueError:
            try:
                self.worksheet[col] = self.worksheet.evaluate(value)
            except ValueError:
                print >>sys.stderr, "error"
        else:
            self.worksheet[col][row] = f


class WorksheetView(gui.Box):
    def __init__(self, place, worksheet, **kwds):
        gui.Box.__init__(self, place, **kwds)
        self.worksheet = worksheet

        self.worksheet.connect('rename', self.on_rename)

    def setup(self):
        for cmd, method in {
            'new-column': self.on_new_column,
            'insert-row': self.on_new_column,
            'move-left': self.on_move_left,
            'move-right': self.on_move_right,
            'move-first': self.on_move_first,
            'move-last': self.on_move_last,
        }.iteritems():
            self.commands[cmd].connect('activated', method)
        
        self.table = self.find('table')
        self.table.connect('right-clicked', self.on_right_clicked)
        self.table.connect('double-clicked', self.on_double_clicked)

        #XXX
        self.table.DisableDragRowSize()
        self.table.set_data(TableData(self.worksheet))

    def __iiiiinit__(self, parent, worksheet, **place):
        gui.Box.__init__(self, parent, 'horizontal', **place)

        self.worksheet = worksheet
        self.toolbar = gui.Toolbar(self, orientation='vertical', stretch=0)

        self.toolbar.append(gui.Command('New column', 'Create a new column', self.on_new_column, 'stock_insert-columns.png'))
        self.toolbar.append(gui.Command('Insert row', 'Insert row', self.on_insert, 'table-insert-row.png'))
        self.toolbar.append(gui.Command('Delete column', 'Delete a column', self.on_new_column, 'stock_delete-column.png'))

        self.toolbar.append(None)

        self.toolbar.append(gui.Command('Move left', 'Move columns to the left', self.on_move_left, '16/left.png'))
        self.toolbar.append(gui.Command('Move right', 'Move columns to the right', self.on_move_right, '16/right.png'))
        self.toolbar.append(gui.Command('Move to first', '', self.on_move_first, '16/first.png'))
        self.toolbar.append(gui.Command('Move to last', '', self.on_move_last, '16/last.png'))

        self.table = gui.Table(self, TableData(self.worksheet))
        self.table.connect('right-clicked', self.on_right_clicked)
        self.table.connect('double-clicked', self.on_double_clicked)

        self.object = self.worksheet
        self.worksheet.connect('rename', self.on_rename)

    def selection(self):
        blocks = []
        for (t,l), (b,r) in zip(self.table._widget.GetSelectionBlockTopLeft(), 
                                self.table._widget.GetSelectionBlockBottomRight()):
            blocks.append(array([self.worksheet.columns[col][t:b+1] for col in range(l, r+1)]))

        for (r,c) in self.table._widget.GetSelectedCells():
            blocks.append(array([[self.worksheet.columns[c][r]]]))

        return blocks

    def on_rename(self, name, item=None):
        self.parent._widget.SetPageText(self.parent.pages.index(self), name)

    def on_move_left(self):
        sel = self.table.selected_columns
        for c in sorted(sel):
            self.worksheet.swap_columns(c, c-1)

        self.table.selected_columns = [c-1 for c in sel]

    def on_move_right(self):
        sel = self.table.selected_columns
        for c in sorted(sel, reverse=True):
            self.worksheet.swap_columns(c, c+1)

        self.table.selected_columns = [c+1 for c in sel]

    def on_move_first(self):
        sel = self.table.selected_columns
        for n, c in enumerate(sorted(sel)):
            self.worksheet.move_column(c, n)

        self.table.selected_columns = range(len(sel))

    def on_move_last(self):
        sel = self.table.selected_columns
        for n, c in enumerate(sorted(sel, reverse=True)):
            self.worksheet.move_column(c, len(self.worksheet.columns)-1-n)

        self.table.selected_columns = [len(self.worksheet.columns)-c-1 for c in range(len(sel))]

    def on_new_column(self):
        self.worksheet[self.worksheet.suggest_column_name()] = [nan]*20

    def on_right_clicked(self, row, col):
        menu = gui.Menu()
        menu.append(gui.Command('Set value', 'setvalue', self.on_set_value, 'stock_edit.png'))
        menu.append(gui.Command('Insert row', 'insert', self.on_insert, 'table-insert-row.png'))
        menu.append(gui.Command('Delete', 'delete', self.on_set_value, 'stock_delete.png'))
        self.clickcell = row, col
        self.table._widget.PopupMenu(menu._menu)

    def on_double_clicked(self, row, col):
        self.clickcell = row, col
        self.on_set_value()

    def on_close(self):
        self.parent.delete(self)


    def on_insert(self):
        self.insert(self.table._widget.GetGridCursorRow())

    def insert(self, n):
        for col in self.worksheet:
            col[n+1:] = col[n:]
            col[n] = nan

    def on_set_value(self):
        row, col = self.clickcell

        dlg = gui.Dialog(None)
        box = gui.Box(dlg, 'vertical', stretch=1)
        editor = gui.PythonEditor(box)
        auto = gui.Checkbox(box, 'Auto', stretch=0)
        btnbox = gui.Box(box, 'horizontal', stretch=0)
        ok = gui.Button(btnbox, 'OK', stretch=0)
        cancel = gui.Button(btnbox, 'Cancel', stretch=0)
        cancel.connect('clicked', dlg.close)
        ok.connect('clicked', dlg.close)

        expr = self.worksheet[col].expr

        auto.state = not expr == ''
        editor.text = expr

        dlg._widget.ShowModal()

        Worksheet.record = set()
        if auto.state:
            self.worksheet[col].expr = editor.text
        else:
            self.worksheet[col].expr = ''
            if editor.text.strip() != '':
                try:
                    self.worksheet[col] = self.worksheet.evaluate(editor.text)
                except ValueError:
                    print >>sys.stderr, "error"
        Worksheet.record = None

        dlg._widget.Destroy()
