import sys, os

sys.modules['__main__'].splash.message('loading ui_worksheet_view')
from qt import *
from qttable import *
from grafity.arrays import clip, nan, arange, log10, isnan
from grafity.settings import DATADIR

from grafity import Worksheet

def getpixmap(name, pixmaps={}):
    if name not in pixmaps:
        pixmaps[name] = QPixmap(os.path.join(DATADIR, 'data', 'images', '16', name+'.png'))
    return pixmaps[name]

class HeaderToolTip(QToolTip):
    def __init__(self, header, worksheet, group=None):
        QToolTip.__init__(self, header,group)
        self.worksheet = worksheet

    def maybeTip (self, p):
        header = self.parentWidget()
        if header.orientation() == Qt.Horizontal:
            section = header.sectionAt(p.x())
        else:
            section = header.sectionAt(p.y())

        c = self.worksheet.columns[section]

        d = ', '.join(col.fullname for col in c.dependencies)
        tipString = '<b>column:</b> %s<br><b>expr:</b> <i>%s</i><br><b>deps:</b> %s' % (c.name, c.expr, d)

        self.tip(header.sectionRect(section), tipString, "This is a section in a header")



class WorksheetView(QTabWidget):
    def __init__(self, parent, mainwin, worksheet):
        QTabWidget.__init__(self, parent)
        self.mainwin, self.worksheet = mainwin, worksheet

        self.setTabShape(self.Triangular)
        self.setTabPosition(self.Bottom)

        self.table = GTable(self.worksheet, self)
        self.addTab(self.table, 'worksheet')

        self.frozen = False

        self.update_size()
        self.update_column_names()

        self.worksheet.connect('data-changed', self.on_data_changed)
        self.worksheet.connect('rename-column', self.update_column_names)

        self.worksheet.connect('rename', self.on_rename)
        self.setCaption(self.worksheet.fullname)
        self.setWFlags(Qt.WDestructiveClose)

        self.tip = HeaderToolTip(self.table.horizontalHeader(), self.worksheet)
        self.setIcon(getpixmap('worksheet'))
        self.resize(400, 400)
    
    def closeEvent(self, event):
        event.accept()
        self.worksheet._view = None

    def on_rename(self, *args, **kwds):
        self.setCaption(self.worksheet.fullname)

    def on_data_changed(self):
        self.update_size()
        self.update_column_names()
        self.update_data()

    def update_size(self):
        if self.frozen: 
            return

        if self.worksheet.nrows != self.table.numRows():
            self.table.setNumRows(self.worksheet.nrows)
        if self.worksheet.ncolumns != self.table.numCols():
            self.table.setNumCols(self.worksheet.ncolumns)

    def update_column_names(self, *args):
        if self.frozen: 
            return
        for i, name in enumerate(self.worksheet.column_names):
            self.table.horizontalHeader().setLabel(i, name)

    def update_data(self, column = None):
        if self.frozen: 
            return
#        if column is not None:
#            column = column.name
#        for graph, dataset in project.used_by(self.worksheet, column):
#            dataset.update()
#            graph.redraw()
        self.table.updateContents()

    def on_newcolumn_clicked(self):
        self.worksheet[self.worksheet.suggest_column_name()] = [nan]*30

    def on_delcolumn_clicked(self):
        for c in self.selected_columns:
            self.worksheet.remove_column(self.worksheet.column_names[c])

    def on_left_clicked(self):
        sel = self.selected_columns
        for c in sorted(sel):
            self.worksheet.swap_columns(c, c-1)

        self.selected_columns = [c-1 for c in sel]

    def on_right_clicked(self):
        sel = self.selected_columns
        for c in sorted(sel, reverse=True):
            self.worksheet.swap_columns(c, c+1)

        self.selected_columns = [c+1 for c in sel]

    def on_first_clicked(self):
        sel = self.selected_columns
        for n, c in enumerate(sorted(sel)):
            self.worksheet.move_column(c, n)

        self.selected_columns = range(len(sel))

    def on_last_clicked(self):
        sel = self.selected_columns
        for n, c in enumerate(sorted(sel, reverse=True)):
            self.worksheet.move_column(c, len(self.worksheet.columns)-1-n)

        self.selected_columns = [len(self.worksheet.columns)-c-1 for c in range(len(sel))]

    def get_selected_columns(self):
        return [col for col in range(len(self.worksheet.columns)) if self.table.isColumnSelected(col, True)]
    def set_selected_columns(self, columns):
        self.table.clearSelection(False)
        for c in columns:
            self.table.selectColumn(c)
    selected_columns = property(get_selected_columns, set_selected_columns)

    def on_header_context_menu_requested(self, event):
        print >>sys.stderr, "sod off!"

        

class HeaderEventHandler(QObject):
    def __init__(self, table):
        QObject.__init__(self, table)
        self.table = table

    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if event.button() == Qt.LeftButton:
                self.table.on_edit_header()
                return True
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                self.table.worksheet._view.on_header_context_menu_requested(event)
                return True
        return False


class GTable(QTable):
    def __init__(self, ws, parent=None, name=None):
        QTable.__init__(self, parent, name)
        self.worksheet = ws
        self.widget_dict = {}
        self.setFocusStyle(QTable.FollowStyle)
        self.connect(self.horizontalHeader(), SIGNAL("pressed(int)"), self.on_header_pressed)

        self.headeredit = QLineEdit(self.horizontalHeader())
        self.headeredit.hide()
        self.connect(self.headeredit, SIGNAL("returnPressed()"), self.on_rename_column)
        self.connect(self.headeredit, SIGNAL("lostFocus()"), self.on_rename_column)

        self.horizontalHeader().installEventFilter(HeaderEventHandler(self))
        self.hh = self.horizontalHeader()

        self.editor = None

    def on_header_pressed(self, section):
        if self.headeredit.isVisible():
            self.headeredit.releaseKeyboard()
            self.headeredit.hide()
        self.editing_header = section

    def on_edit_header(self):
        srect = self.horizontalHeader().sectionRect(self.editing_header)
        self.headeredit.move(srect.left(), srect.top())
        self.headeredit.resize(srect.width(), srect.height())
        self.headeredit.show()
        self.headeredit.setFocus()
        self.headeredit.setText(self.worksheet[self.editing_header].name)
        self.headeredit.grabKeyboard()

    def on_rename_column(self):
        self.headeredit.releaseKeyboard()
        self.headeredit.hide()
        tryname = unicode(self.headeredit.text())
        self.worksheet[self.editing_header].name = tryname

    def createEditor(self, row, col, initFromCell):
        editor = QTable.createEditor(self, row, col, initFromCell)
        if initFromCell:
            if self.worksheet[col].expr == '':
                editor.setText(self.text(row, col))
            else:
                editor.setText("'%s'"%self.worksheet[col].expr)

        return editor
#    
#    def cellWidget(self, row, col):
#        if row == self.currEditRow() and col == self.currEditCol():
#            return self.editor
#        return None
#
#    def endEdit(self, row, col, accept, replace):
#        QTable.endEdit(self, row, col, accept, replace)
#        self.editor = None

    def resizeData(self, i):
        pass

    def item(self, i, j):
        return None

    def setItem(self, i, j, item):
        pass

    def clearCell(self, i, j):
        return None

    def activateNextCell(self):
        if self.currentRow() == self.numRows()-1:
            self.setNumRows(self.numRows() + 10)
        QTable.activateNextCell(self)

    def paintCell(self, painter, row, col, cr, selected, cg=None):
        if cg is None:
            cg = self.colorGroup()

        w = cr.width()
        h = cr.height()

        if selected:
            brush = cg.brush(QColorGroup.Highlight)
            painter.setPen(cg.highlightedText())
        else:
            if self.worksheet[col].expr != '':
                brush = QBrush(QColor(230, 230, 255))
            else:
                brush = cg.brush(QColorGroup.Base)
            painter.setPen(cg.text())

        painter.fillRect(0, 0, w, h, brush)

        pen = QPen(painter.pen())
#        painter.setPen(QPen(self.style().styleHint(QStyle.SH_Table_GridLineColor, self)))
        painter.setPen(QPen(Qt.gray))
        painter.drawLine(w-1, 0, w-1, h-1)
        painter.drawLine(0, h-1, w-1, h-1)
        painter.setPen(pen)

        painter.drawText(4, 0, w-4, h, 0, self.text(row, col))

    def text(self, row, col):
        val = self.worksheet.columns[col][row]
        if isnan(val):
            st = ''
        else:
            st = str(val)
        return st

    def setCellContentFromEditor(self, row, col):
        text = unicode(self.cellWidget(row, col).text())
        try:
            f = float(text)
        except ValueError:
            if text[0]==text[-1]=="'" or text[0]==text[-1]=='"':
                self.worksheet[col].expr = text[1:-1]
            else:
                try:
                    self.worksheet[col] = self.worksheet.evaluate(text)
                except ValueError:
                    print >>sys.stderr, "error"
        else:
            self.worksheet[col][row] = f
