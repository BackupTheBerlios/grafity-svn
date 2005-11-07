import sys
import os
import zlib
import bz2
import StringIO
import time
from qt import *

#-Worksheet.add_column___(wsname, colname)              add a column to a worksheet         WACO
#-Worksheet.del_column___(wsname, colname)              remove a column from a worksheet    WDCO
#-Worksheet.move_column___(wsname, nfrom, nto)          move a column in a worksheet        WMCO
#-Worksheet.rename___(wsname, newname)                                                      WREN

#-Column.change_data___(wsname, colname, where, data)                                       CDAT
#-Column.change_calc___(wsname, colname, calc)                                              CCAL
#-Column.rename___(wsname, colname, newname)                                                CREN

#-Project.add_object___(element)                                                            PADD
#-Project.remove_object___(name)                                                            PREM

#-Graph.rename___(grname, newname)                                                          GREN
#-Graph.add_dataset___(grname, wsname, xname, yname)                                        GADD
#-Graph.remove_dataset___(grname, wsname, xname, yname)                                     GREM
#-Graph.change_dataset_style___(grname, )                                                   GSTY
#-Graph.change_dataset_range___(grname, fr, to)                                             GRAN
# Graph.zoom___(grname, top, bottom, right, left)                                           GZOO
# Graph.change_axis_scale___(grname, axis, scale)                                           GSCA
# Graph.change_axis_title___(grname, axis, title)                                           GATI

# Fit.add_fit_function                                                                      FADD
# Fit.remove_fit_function                                                                   FREM
# Fit.rename_fit_function                                                                   FREN
# Fit.change_parameter_value                                                                FCVA
# Fit.change_fit_setting                                                                    FSET

try: sys.modules['__main__'].splash_message('loading Project')
except: pass

import grafit.lib.ElementTree as xml

from grafit.utils import Observed, Singleton, Settings, AutoCommands

class CommandError (Exception):
    pass

class UndoList(list):
    def __init__(self, *args, **kwds):
        list.__init__(self, *args, **kwds) 
        self.composite = None
        self.compositecount = 0

    def begin_composite(self, composite_command):
        if not project.undo_enabled:
            return 
        self.compositecount += 1
        if self.composite is None:
            self.composite = composite_command

    def end_composite(self):
        if not project.undo_enabled:
            return 
        self.compositecount -= 1
        if self.composite is None:
            return
        if self.compositecount == 0:
            self.append_real(self.composite)
            self.composite = None

    def append(self, command):
        if not project.undo_enabled:
            return 
        if self.composite is not None:
            self.composite.add(command)
            return

        if len(self) == 0:
            self.append_real(command)
            return

        try:
            combi = command.combine(self[-1])
        except TypeError: # cannot combine
#            self.append(self.pop()) #########
            self.append_real(command)
        else: # can combine
            self[-1] = combi

    def append_real(self, value):
        while len(self) > 0 and hasattr(self[-1], 'undone') and self[-1].undone:
            self.pop()
        list.append(self, value)
        project.mainwin.history.insertItem(repr(value), 0)
        if hasattr(value, 'pixmap') and value.pixmap is not None:
            project.mainwin.history.changeItem(value.pixmap, project.mainwin.history.text(0), 0)
        project.mainwin.actions['undo'].setEnabled(True)
        project.modified = True

    def pop(self):
        obj = list.pop(self)
        project.mainwin.actions['undo'].setEnabled(len(self)>0)
        project.mainwin.history.removeItem(0)
        if len(self) == 0:
            project.modified = False
        return obj

    def clear(self):
        while self != []:
            self.pop()

    def update_history(self):
        project.mainwin.history.clear()
        for value in self:
            project.mainwin.history.insertItem(repr(value), 0)
            if hasattr(value, 'pixmap') and value.pixmap is not None:
                project.mainwin.history.changeItem(value.pixmap, project.mainwin.history.text(0), 0)
        if len(self) > 0:
            project.mainwin.actions['undo'].setEnabled(True)

class Project (Observed, Singleton):

    __metaclass__ = AutoCommands
    
    Worksheet_record = []
    Worksheet_recordp = False

    def init (self, main_dict=sys.modules['__main__'].__dict__):
        self.main_dict = main_dict        

        self.worksheets = []
        self.graphs = []
        self.folders = []

        self._undolist = UndoList()
        self._filename = None
        self._modified = False

        self.undo_enabled = True
        self.undolock = 0

    def _get_undolist(self):
        return self._undolist
    def _set_undolist(self, v):
        self._undolist = v
        self._undolist.update_history()
    undolist = property(_get_undolist, _set_undolist)

    def _get_filename(self):
        return self._filename
    def _set_filename(self, value):
        self._filename = value
        self.update_caption()
    filename = property(_get_filename, _set_filename)

    def _get_modified(self):
        return self._modified
    def _set_modified(self, value):
        prev = self._modified
        self._modified = value
        if prev != value:
            self.update_caption()
    modified = property(_get_modified, _set_modified)

    def update_caption(self):
        capt = 'Grafit'
        if self.filename is not None:
            capt += ' [%s]' % self.filename
        if self.modified:
            capt += ' (modified)'
        self.mainwin.setCaption (capt)
 
    def new_worksheet(self, name=None, columns=[]): 
        if name is None:
            name = self.make_worksheet_name()
        work = worksheet.Worksheet (name)
        for col in columns:
            work.add_column(col)
            work[col].extend(20)
        self.add (work)
        return self[name]

    def new_graph(self, name=None):
        if name is None:
            name = self.make_graph_name()
        print >>sys.stderr, 'a'
        gra = graph.Graph(name)
        print >>sys.stderr, 'v'
        self.add(gra)
        return self[name]

    def _add_object__init(cmd, obj):
#            cmd.pixmap = QPixmap(project.datadir + 'pixmaps/newwsheet.png')
#            cmd.element = xml.Element('ProjectAddObject')
        if hasattr(obj, 'tag') and obj.tag in ['Worksheet', 'Graph']:
            cmd.obj = obj
        else:
            cmd.obj = obj.to_element()
#            if hasattr(obj, 'name') and obj.name in [ws.name for ws in project.worksheets + project.graphs]:
#                raise CommandError,  "There is another window with this name"
 
    def _add_object__do(cmd):
        if cmd.obj.tag == 'Worksheet':
            o = worksheet.Worksheet()
        elif cmd.obj.tag == 'Graph':
            o = graph.Graph()
        if isinstance(o, worksheet.Worksheet):
            project.main_dict[o.name] = o
            project.worksheets.append(o)
            project.emit (msg="add_worksheet", wsheet=o)
        elif isinstance(o, graph.Graph):
            project.main_dict[o.name] = o
            project.graphs.append(o)
            project.emit (msg="add_graph", graph=o)
        project.lock_undo()
        o.from_element(cmd.obj)
        project.unlock_undo()
        try:
            cmd.obj.vogel()
        except AttributeError:
            pass
        return cmd

    def _add_object__undo(cmd):
        if cmd.obj.tag == 'Graph':
            name = eval(cmd.obj.get('name'))
        else:
            name = cmd.obj.get('name')
        project.remove(name)
        return cmd

    def _add_object__repr(cmd):
        return  "-> Add %s %s to project" % (cmd.obj.tag, cmd.obj.get('name'))


    def add(self, obj):
        """
        Add an object (Worksheet or Graph) to the project.

        - adds the object's name to the main dictionary
        - adds the object to projects.worksheets or project.graphs
        """
        self.add_object___(obj).do().register()
        try:
           name = obj.name
        except AttributeError:
            name = obj.get('name')
        return self[name]

    def _remove_object__init(cmd, obj):
        cmd.obj = obj.to_element()
        cmd.name = obj.name
 
    def _remove_object__do(cmd):
        self = project
        obj = project[cmd.name]
        if isinstance (obj, graph.Graph):
            self.emit (msg="remove_graph", graph=obj)
            del self.main_dict[obj.name]
            self.graphs.remove(obj)
        elif isinstance (obj, worksheet.Worksheet):
            self.emit (msg="remove_worksheet", wsheet=obj)
            del self.main_dict[obj.name]
            self.worksheets.remove(obj)
        return cmd

    def _remove_object__undo(cmd):
        project.add(cmd.obj)
        return cmd

    def _remove_object__repr(cmd):
        return  "-> Remove %s %s to project" % (cmd.obj.tag, cmd.obj.get('name'))


    def remove (self, obj):
        """
        Remove an object (Worksheet or Graph) from the project.

        removes the object's name to the main dictionary and from
        projects.worksheets or project.graphs
        """
        if obj in [o.name for o in self.worksheets]:
            obj = self.w[obj]
        if obj in [o.name for o in self.graphs]:
            obj = self.g[obj]
        if obj in project.worksheets and len(obj.depend_on_me())>0:
            QMessageBox.information(None, "grafit", 
                        "<b>Cannot remove</b><p>Worksheet is being used")
            return
        self.remove_object___(obj).do().register()

       
    def save (self, filename, compression='gzip', amount=3): 
        """
        Saves the project contents to a file.
        
        compression can be 'gzip', 'bz2' or 'none'
        """
        root = xml.Element ("Project")
        root.set('folders', repr(self.folders))
        for w in self.worksheets:
            root.append (w.to_element())
        for g in self.graphs:
            root.append (g.to_element())

        string = StringIO.StringIO ()
        xml.ElementTree(root).write(string)
        data = string.getvalue()
        string.close()

        f = open (filename, 'w')

        if compression == 'gzip':
            f.write ('GRAPHITEGZ')
            data = zlib.compress (data, amount)
        elif compression == 'bz2':
            f.write ('GRAPHITEBZ')
            data = bz2.compress (data, amount)
        elif compression == 'none':
            f.write ('GRAPHITEUC')

        f.write (data)
        f.close()
        self.filename = filename
        self.modified = False

    def load (self, filename): 
        """
        loads the project from a file.
        """
        import time
        t = time.time()
        f = open (filename)
        header = f.read (10)

        self.mainwin.statusBar().message ("Reading", 1000)
        data = f.read()

        self.mainwin.statusBar().message ("Decompressing", 1000)

        if header == 'GRAPHITEGZ':
            data = zlib.decompress (data)
        elif header == 'GRAPHITEBZ':
            data = bz2.decompress (data)

        self.mainwin.statusBar().message ("Parsing", 1000)

        sio = StringIO.StringIO(data)
        try:
            tree = xml.parse (sio)
        finally:
            f.close()
            sio.close()
        
        self.clear ()
        root = tree.getroot()
        f = root.get('folders')
        if f is not None:
            self.folders = eval(f)
        else:
            self.folders = []

        total = sum([len(l) for l in root.findall('Worksheet') + root.findall('Graph')])
        self.mainwin.progressbar.show()
        project.main_dict['app'].processEvents()
        self.mainwin.progressbar.setTotalSteps(total)
        self.mainwin.progressbar.setProgress(0)
        self.lock_undo()
        try:
            for welem in root.findall ('Worksheet'):
                w = worksheet.Worksheet (welem.get('name'))
                self.add (w)
                project[welem.get('name')].from_element (welem)
                self.mainwin.statusBar().message ("Creating worksheet %s" % welem.get("name"), 1000)
            for ws in self.worksheets:
                for col in ws.columns:
                    if col.calc is not None:
                        col.calc = col._calc
            for gelem in root.findall ('Graph'):
                g = graph.Graph (eval(gelem.get('name')))
                self.add(g)
                project[eval(gelem.get('name'))].from_element (gelem)
                self.mainwin.statusBar().message ("Creating graph %s" % gelem.get("name"), 1000)
            self.modified = False
            self.filename = filename
            if filename in self.mainwin.recent:
                self.mainwin.recent.remove(filename)
            self.mainwin.recent[0:0] = [filename]
            self.mainwin.recent = self.mainwin.recent[0:5]
        finally:
            self.unlock_undo()
            self.mainwin.progressbar.hide()
        self.mainwin.statusBar().message ("Project loaded (%.1f seconds)" % (time.time() - t), 1000)

    def clear (self): 
        """
        Clears project contents
        """
        for n in self.graphs[:] + self.worksheets[:]:
            self.remove (n)
            
        self.undolist.clear()
        self.modified = False
        self.filename = None

    def _get_mainwin (self):
        return self.main_dict['mainwin'];
    def __getitem__ (self, key):
        if key in project.worksheets:
            return key
        if key in project.graphs:
            return key
        if hasattr(key, 'replace'):
            key = key.replace("'", "").replace('"', '')
        try:
            return dict([(w.name, w) for w in project.worksheets + project.graphs])[key]
        except KeyError:
            raise IndexError
    
    mainwin = property(_get_mainwin)
    settings = Settings()

    def used_by(self, worksheet, colname=None):
        used = []
        for gra in self.graphs:
            for das in gra.datasets: 
                if das.worksheet == worksheet and ((colname is None) 
                                                   or (colname in [das.colx, das.coly])):
                    used.append((gra, das))
        return used

    class __Worksheet_finder (object):
        def __getattr__ (self, name):
            return [item for item in project.worksheets if item.name==name][0]
        def __getitem__ (self, key):
            return self.__getattr__ (key)
    w = __Worksheet_finder ()

    class __Graph_finder (object):
        def __getattr__ (self, name):
            return [item for item in project.graphs if item.name==name][0]
        def __getitem__ (self, key):
            return self.__getattr__ (key)
    g = __Graph_finder ()

    def make_worksheet_name(self):
        i = 1
        while 'data'+str(i) in [a.name for a in self.worksheets]:
            i+=1
        return 'data'+str(i)

    def make_graph_name (self):
        i = 1
        while 'graph'+str(i) in [a.name for a in self.graphs]:
            i+=1
        return 'graph'+str(i)

    def lock_undo(self):
        assert self.undolock >= 0
        self.undolock += 1
        self.undo_enabled = False

    def unlock_undo(self):
        assert self.undolock > 0
        self.undolock -= 1
        if self.undolock == 0:
            self.undo_enabled = True

project = Project()

import worksheet
import graph
