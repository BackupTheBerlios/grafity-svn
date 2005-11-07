import re
import sys
import cPickle as pickle
from sets import Set as set

try:
    sys.modules['__main__'].splash_message('loading Worksheet')
except:
    pass

from qt import *
from qttable import *
from scipy import *

from grafit.column import Column
from grafit.utils import Observed, alfmt
from grafit.import_ascii import import_ascii
from grafit.project import project
from grafit.lib import ElementTree as xml
from grafit.utils import AutoCommands, CompositeCommand


class Worksheet (Observed):
    __metaclass__ = AutoCommands
    
    def __init__(self, name='__new'):
        self._frozen = False
        self._name = name
        self._columns = []
        self.emit (msg='create')
        self._view = None
        self._explorer_item = None
        self._header = []
        self._folder = None
    
    def export_ascii(self, filename):
        """Exports the worksheet data as an ascii file"""
        #TODO write the header also
        io.write_array(filename, self.array)

    def emit(self, *args, **kw):
        if self._frozen:
            return
        return Observed.emit(self, *args, **kw)

    def _get_columns(self):
        return self._columns
    def _set_columns(self, value):
        raise TypeError, 'read-only attribute'
    columns = property(_get_columns, _set_columns)

    def make_colname(self):
        i = 0
        while alfmt(i) in self.column_names:
            i+=1
        return alfmt(i)

    def add_column(self, name = None):
        if (name is None) or (not re.match('^[a-zA-Z]\w*$', name)):
            name = self.make_colname()
        self[name] = []

    def show (self):
        if self._view is not None:
            self._view.show()

    def __repr__(self):
        return "<Worksheet '%s'>" %(self.name,)

    def _get_colnames(self):
        return [c.name for c in self.columns]
    def _set_colnames(self, value):
        raise TypeError, 'read-only attribute'
    column_names = property(_get_colnames, _set_colnames)


    def depend_on_me(self):
        """Graphs and other worksheets which depend on this worksheet."""
        l = []
        for col in self.columns:
            for cdep in col.deps:
                if cdep.worksheet is not self:
                    l.append(cdep.worksheet)
        for gra in project.graphs:
            for das in gra.datasets: 
                if das.worksheet == self:
                    l.append(gra)
        return set(l)

    def __setattr__(self, name, value):
        """Set entire column to a new value"""
        # we keep class attributes and names starting with _ as normal attributes 
        if name.startswith('_') or hasattr(self.__class__, name):
            object.__setattr__(self, name, value)
            return

        # cannot change the data in a calculated column
        if name in self.column_names and self[name].calc is not None:
            return

        # otherwise, make a column
        if isinstance(value, Column) and value.worksheet is self and value.name not in self.column_names:
            col = value
        else:
            col = Column(value, worksheet=self, name=name)

        # create the column if it does not exist
        if name not in self.column_names:
            Worksheet.add_column___(self.name, name).do().addto(project.undolist)

        # we can set calc with worksheet.col = 'data1.B + 3'
        if isinstance(value, str):
            self[name].calc = value
        elif len(col) > 0: # ignore
            # clear column
            project.lock_undo()
            try:
                self[name][0:len(self[name])] = nan
            finally: project.unlock_undo()

            # set column
            self[name][:len(col)] = col[:len(col)]

        # update columns that depend on this one
        for c in col.deps:
            c.calculate() 

        self.emit (msg='update_data', column=col)


    ########## add column command
    ####################################################

    def _add_column__do(cmd):
        project[cmd.worksheet].columns.append(Column([], worksheet=project[cmd.worksheet], name=cmd.name))
        project[cmd.worksheet].emit (msg='update_size')
        if project[cmd.worksheet]._view is not None:
            project[cmd.worksheet]._view.set_column_name(len(project[cmd.worksheet].columns)-1, cmd.name)
        return cmd

    def _add_column__undo(cmd):
        del project[cmd.worksheet][cmd.name]
        return cmd

    def _add_column__repr(cmd):
        return "> Add a column named %s to the worksheet %s" % (cmd.name, cmd.worksheet)

    def _add_column__init(cmd, worksheet, name):
        cmd.worksheet, cmd.name = worksheet, name
        if name in project[worksheet].column_names:
            raise NameError

    ####################################################

    def _del_column__init(cmd, wsname, colname):
        cmd.wsname, cmd.colname = wsname, colname

    def _del_column__do(com):
        ws = project[com.wsname]
        col = ws[com.colname]
        com.data = col.data
        com.calc = col.calc

        for wsheet in project.worksheets:
            for column in wsheet.columns:
                if col in column.deps:
                    column.deps.remove (col)

        del ws.columns[ws.column_names.index(com.colname)]
        ws.emit (msg='update_size')
        if ws._view is not None: ws._view.update_column_names()
        return com

    def _del_column__undo(cmd):
        project[cmd.wsname][cmd.colname] = cmd.data
        project[cmd.wsname][cmd.colname].calc = cmd.calc
        return cmd

    ####################################

    def _move_column__init(cmd, wsname, fr, to):
        cmd.wsname, cmd.fr, cmd.to = wsname, fr, to

    def _move_column__do(cmd):
        ws = project[cmd.wsname]
        col = ws.columns[cmd.fr]
        del ws.columns[cmd.fr]
        ws.columns.insert(cmd.to, col)

        ws.emit (msg='update_data')
        if ws._view is not None: ws._view.update_column_names()
        return cmd

    def _move_column__undo(cmd):
        cmd.to, cmd.fr = cmd.fr, cmd.to
        cmd.do()
        cmd.to, cmd.fr = cmd.fr, cmd.to
        return cmd

    def _move_column__repr(cmd):
        return "> Move column in worksheet %s" % (cmd.wsname)

    ####################################

    def _rename__init(cmd, wsname, newname):
        cmd.old, cmd.new = wsname, newname

    def _rename__do(cmd):
        self = project[cmd.old]
        name = cmd.new
#        if not re.match('^[a-zA-Z]\w*$', name):
#            raise NameError, "Invalid name for worksheet: %s" % name

        use = project.used_by(self)

        oldname = self._name
        self._name = name

        for graph, das in use:
            das.wsname = name
        for graph, das in use:
            graph.legend.update()

        if self._view is not None:
            self._view.setCaption(self.name)
        if self._explorer_item is not None:
            self._explorer_item.setText(0, self.name)
 
        if self in project.worksheets:
            try:
                del project.main_dict[oldname]
            except KeyError:
                pass
            project.main_dict[self.name] = self

        project.lock_undo()
        try:
            for col in self.columns:
                for cdep in col.deps:
                    patt = r'\b%s\.%s\b' % (oldname, col.name)
                    repl = '%s.%s' % (self.name, col.name)
                    cdep.calc = re.sub (patt, repl, cdep.calc)
        finally:
            project.unlock_undo()

        return cmd

    def _rename__undo(cmd):
        cmd.old, cmd.new = cmd.new, cmd.old
        cmd.do()
        cmd.old, cmd.new = cmd.new, cmd.old
        return cmd


    def _get_name(self):
        return self._name
    def _set_name(self, name):
        if self not in project.worksheets:
            self._name = name
        else:
            self.rename___(self.name, name).do().register()
 
    name = property(_get_name, _set_name)




    def move_column(self, cfrom, cto):
        self.move_column___(self.name, cfrom, cto).do().register()

    def __getitem__(self, item):
        if str(item) in self.column_names:
            return [c for c in self.columns if c.name == str(item)][0]
        elif type(item) in (int, slice):
            return self.columns[item]
        elif hasattr(item, '__len__') and not item.__class__ in [str, unicode]:
            return [self[i] for i in item]
        else:
            raise AttributeError

    def __setitem__(self, item, value):
        if isinstance(item, int):
            setattr(self, self.column_names[item], value)
        else:
            setattr(self, item, value)

    def __delitem__(self, item):
        delattr(self, item)

    def __getattr__(self, name):
        try:
            ind = self.column_names.index(name)
        except ValueError:
            return object.__getattribute__(self, name)
        else:
            c = self.columns[ind]
            if project.Worksheet_recordp:
                project.Worksheet_record.append (c)
            return c
        
    def __delattr__(self, name):
        if name in self.column_names:
            col = self[name]
            if len(col.deps) > 0:
                QMessageBox.information(None, "grafit", 
                            "<b>Cannot remove</b><p>Column %s is being used by another one" % (com.colname,))
                return

            if len(project.used_by(self, col.name)) > 0:
                QMessageBox.information(None, "grafit", 
                            "<b>Cannot remove</b><p>Column %s is being used in a graph" % (col.name,))
                return

            Worksheet.del_column___(self.name, name).do().register()
        else:
            del self.__dict__[name]


    def copy(self, fromx, fromy, tox, toy):
        arr = concatenate([ar[fromy:toy] for ar in self[fromx:tox]])
        arr.shape = (tox-fromx, toy-fromy)
        return transpose(arr)

    def cut(self, fromx, fromy, tox, toy):
        self.freeze()
        comm = CompositeCommand(name=('Cut from worksheet %s' % self.name),
                                pixmap=QPixmap(project.datadir + 'pixmaps/cut.png'))
        if self in project.worksheets:
            project.undolist.begin_composite(comm)
        try:
            data = self.copy(fromx, fromy, tox, toy)
            self.clear(fromx, fromy, tox, toy)
        finally:
            if self in project.worksheets:
                project.undolist.end_composite()
        self.unfreeze()
        return data

    def clear(self, fromx, fromy, tox, toy):
        comm = CompositeCommand(name=('Clear from worksheet %s' % self.name),
                                pixmap=QPixmap(project.datadir + 'pixmaps/delete.png'))
        if self in project.worksheets:
            project.undolist.begin_composite(comm)
        try:
            for col in range(fromx, tox):
                self.columns[col][fromy:toy] = nan
        finally:
            if self in project.worksheets:
                project.undolist.end_composite()
        self.emit (msg='update_data')

    def paste(self, fromx, fromy, data):
        self.freeze()
        comm = CompositeCommand(name=('Paste to worksheet %s' % self.name),
                                pixmap=QPixmap(project.datadir + 'pixmaps/paste.png'))
        if self in project.worksheets:
            project.undolist.begin_composite(comm)
        try:
            for i in range(data.shape[1]):
                if fromx+i < len(self.columns):
                    self.columns[fromx+i][fromy:fromy+data.shape[0]] = data[:,i]
        finally:
            if self in project.worksheets:
                project.undolist.end_composite()
        self.emit (msg='update_data')
        self.unfreeze()

    def _get_array(self):
        if len(self.columns) == 0:
            return array([])
        maxlen = max([len(c) for c in self.columns])
        sha =(len(self.column_names), maxlen)
        z = zeros(sha, 'd')
        for i, c in enumerate(self.columns):
            c.extend(maxlen)
            for j in range(maxlen):
                z[i,j] = c[j]
        return transpose(z)

    def _set_array(self, data):
        print >>sys.stderr, data.shape
        if len(data.shape) < 2:
            return
        for i in xrange(data.shape[1]):
            self[alfmt(i)] = data[:,i]

    array = property(_get_array, _set_array)

    def to_element(self):
        # we should:
        # - save all the data in one go (faster and easier)
        # - use tostring/fromstring (much faster)
        elem = xml.Element("Worksheet")
        elem.set("name", self.name)
        elem.set("header", repr(self._header))
        elem.set("folder", repr(self._folder))
        for col in self.columns:
            if col.calc is not None:
                celem = xml.SubElement(elem, "CalcColumn")
                celem.set("name", col.name)
                celem.text = col.calc
            else:
                celem = xml.SubElement(elem, "Column")
                celem.set("name", col.name)
                celem.text = repr(pickle.dumps(col[:]))
                #celem.text = repr(col.data.tostring())
                celem.text = repr(pickle.dumps(col[:]))
        return elem
    
    def from_element(self, elem):
        self.name = elem.get("name")
        try:
            self._header = eval(elem.get("header"))
        except:
            pass
        try:
            self._folder = eval(elem.get("folder"))
        except:
            pass
        self.freeze()
        prog =  project.mainwin.progressbar.progress()
        for celem in elem:
            if celem.tag == 'CalcColumn':
                self[celem.get('name')] = []
                self[celem.get('name')]._calc = celem.text
            elif celem.tag == 'Column':
                safedict = {"__builtins__": { 'True':True, 'False':False, 'None':None}}
                #self[celem.get("name")] = fromstring(eval(celem.text, safedict), 'd')
                self[celem.get("name")] = pickle.loads(eval(celem.text, safedict))
        project.mainwin.progressbar.setProgress(prog+len(elem))
        self.unfreeze()
        if self._view is not None:
            self._view.update_column_names()

    def freeze(self):
        self._frozen = True

    def unfreeze(self):
        self._frozen = False
        self.emit (msg='update_size')
        self.emit (msg='update_data')
        if self._view is not None: 
            self._view.update_column_names()

    def import_ascii(self, filename, **kwds):
        self.array, self._header = import_ascii(filename, **kwds)
#        for i in range(arr.shape[1]):
#            self[alfmt(i)]  = arr[:,i]

    def vogel(self):
        if self._view is None:
            return
        self._view.setWFlags(Qt.WDestructiveClose)
        self._view.close()

    def __len__(self):
        return len(self.columns)

    def selected_columns(self):
        return [col for col in range(len(self.columns)) if self._view._table.isColumnSelected (col, True)]



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
                self.table.worksheet.on_header_context_menu_requested(event)
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
        self.headeredit.setText(self.worksheet.worksheet[self.editing_header].name)
        self.headeredit.grabKeyboard()

    def on_rename_column(self):
        tryname = str(self.headeredit.text())
        try:
            self.worksheet.worksheet[self.editing_header].name = tryname
        except:
            pass
        self.headeredit.releaseKeyboard()
        self.headeredit.hide()

#    def createEditor(self, row, col, initFromCell):
#        self.editor = QLineEdit(self.viewport())
#        if initFromCell:
#            self.editor.setText(self.text(row, col))
#            return self.editor
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
            brush = cg.brush(QColorGroup.Base)
            painter.setPen(cg.text())

        painter.fillRect(0, 0, w, h, brush)

        pen = QPen(painter.pen())
#        painter.setPen(QPen(self.style().styleHint(QStyle.SH_Table_GridLineColor, self)))
#        painter.drawLine(w-1, 0, w-1, h-1)
#        painter.drawLine(0, h-1, w-1, h-1)
        painter.setPen(pen)

        try:
            column = self.worksheet.worksheet.columns[col]
            val = column[row]
            if isnan(val):
                st = ''
            elif hasattr(column, 'error'):
                try:
                    st = '%.*g +/- %g' % (column.precision, val, 
                                        column.error[row])
                except TypeError:
                    try:
                        st = '%.*g +/- %g' % (column.precision, val, column.error)
                    except:
                        st = '%.*g' % (column.precision, val)
            else:
                st = '%.*g' % (column.precision, val)
            if column.calc is not None:
                painter.setPen (Qt.blue)
            else:
                painter.setPen (Qt.black)
            painter.drawText(4, 0, w-4, h, 0, st)
        except:
            pass

    def setCellContentFromEditor(self, row, col):
        try:
            value = eval(str(self.cellWidget(row, col).text()).replace('{', 'array([').replace('}','])'),
                         project.main_dict)
            if isinstance (value, str):         # set calc
                self.worksheet.worksheet[col].calc = value
            elif hasattr(value, '__len__') or isinstance(value, ArrayType): # set whole column
                self.worksheet.worksheet[col] = array(value, Float)
            else:                               # set cell
                self.worksheet.worksheet[col][row] = float(value)
        except:
            self.worksheet.worksheet[col][row] = nan

class WorksheetView (QWidget):
    def __init__(self, worksheet, parent = None):
        if parent is None:
            parent = project.mainwin.workspace

        self.worksheet = worksheet
        self.worksheet._view = self

        name = worksheet.name

        QWidget.__init__(self, parent, name)
        self.setCaption(name)
        self.worksheet.addobserver (self.observe)

        layout = QHBoxLayout(self,0,0)
        self._table = GTable(self, self, None)
        layout.addWidget(self._table)

        self.setIcon(QPixmap(project.datadir + 'pixmaps/wsheet.png'))
        self.resize(240, 300)

        self._context_menu = QPopupMenu(self._table)
        self._context_menu.insertItem('Delete', self.context_menu_del)
        self._context_menu.insertItem('Sort Column', self.context_menu_sort_column)
        self._context_menu.insertItem('Sort Worksheet', self.context_menu_sort_worksheet)
        self._context_menu.insertItem('Export ASCII...', self.context_menu_export_ascii)

        self._initial_dict = list(self.__dict__.keys())

        self.update_size ()
        self.update_column_names ()
        self.update_data ()

    def observe (self, obj, **arg):
        msg = arg['msg']
        if msg == 'update_size':
            self.update_size()
        elif msg == 'update_data':
            if 'column' in arg:
                self.update_data(arg['column'])
            else:
                self.update_data()
        elif msg == 'update_column_names':
            if 'column' in arg:
                self.update_column_names(arg['column'])
            else:
                self.update_column_names()

    def context_menu_del(self):
        del self.worksheet[self.worksheet[self._context_column].name]

    def context_menu_sort_column(self):
        ind = self.worksheet[self._context_column].sort_indices()
        self.worksheet[self._context_column] = take(self.worksheet[self._context_column], ind)
        
    def context_menu_export_ascii(self):
        qfd = QFileDialog (project.mainwin)
        qfd.setMode (QFileDialog.AnyFile)
        if qfd.exec_loop() != 1:
            return False
        else:
            self.worksheet.export_ascii(str(qfd.selectedFile()))

    def context_menu_sort_worksheet(self):
        self.worksheet.freeze()
        comm = CompositeCommand(name=('Sort Worksheet'), pixmap=QPixmap(project.datadir + 'pixmaps/wsheet.png'))
        if self in project.worksheets:
            project.undolist.begin_composite(comm)

        try:
            ind = self.worksheet[self._context_column].sort_indices()
            for column in [c.name for c in self.worksheet.columns if c.calc is None]:
                self.worksheet[column] = self.worksheet[column][ind]
        finally:
             self.worksheet.unfreeze()
             if self in project.worksheets:
                project.undolist.end_composite()
        
    def on_header_context_menu_requested(self, event):
        header = self._table.hh
        self._context_column = header.sectionAt(event.x() + header.offset())
        self._context_menu.popup(event.globalPos())

    def update_size(self):
        if self.worksheet._frozen: return
        numcols = len(self.worksheet.columns)
        if numcols == 0:
            numrows = 0
        else:
            numrows = max([x.real_len() for x in self.worksheet.columns])
        for col in self.worksheet.columns:
            col.extend(numrows)
        if numrows != self._table.numRows():
            self._table.setNumRows(numrows)
        if numcols != self._table.numCols():
            self._table.setNumCols(numcols)

    def set_column_name(self, index, name):
        if self.worksheet._frozen: return
        self._table.horizontalHeader().setLabel(index, name)

    def get_column_name(self, index):
        return str(self._table.horizontalHeader().label(index))

    def update_column_names(self, column = None):
        if self.worksheet._frozen: return
        if column is not None:
            self._table.horizontalHeader().setLabel(self.worksheet.column_names.index(column.name), 
                                                    column.name)
        else:
            for i, col in enumerate(self.worksheet.columns):
                self._table.horizontalHeader().setLabel(i, self.worksheet[i].name)
#        try:
#            project.mainwin.explorer_del_item(self.worksheet)
#        except AttributeError:
#            pass
#        else:
#            project.mainwin.explorer_add_item(self.worksheet)

    def update_data(self, column = None):
        if self.worksheet._frozen: 
            return
        if column is not None:
            column = column.name
        for graph, dataset in project.used_by(self.worksheet, column):
            dataset.update()
            graph.redraw()
        self._table.updateContents()

    def show(self):
        self.update()
        QWidget.show(self)

    def copy_selected(self):
        sel = self._table.selection(self._table.currentSelection())
        fromx, tox, fromy, toy = sel.leftCol(), sel.rightCol(), sel.topRow(), sel.bottomRow()
        return self.worksheet.copy(fromx, fromy, tox+1, toy+1)

    def cut_selected(self):
        sel = self._table.selection(self._table.currentSelection())
        fromx, tox, fromy, toy = sel.leftCol(), sel.rightCol(), sel.topRow(), sel.bottomRow()
        return self.worksheet.cut(fromx, fromy, tox+1, toy+1)

    def clear_selected(self):
        sel = self._table.selection(self._table.currentSelection())
        fromx, tox, fromy, toy = sel.leftCol(), sel.rightCol(), sel.topRow(), sel.bottomRow()
        self.worksheet.clear(fromx, fromy, tox+1, toy+1)

    def paste_selected(self, data):
        sel = self._table.selection(self._table.currentSelection())
        fromx, tox, fromy, toy = sel.leftCol(), sel.rightCol(), sel.topRow(), sel.bottomRow()
        self.worksheet.paste(fromx, fromy, data)
