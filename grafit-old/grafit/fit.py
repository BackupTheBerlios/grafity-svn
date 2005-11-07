import os
import sys

sys.modules['__main__'].splash_message('loading Fit')

from qt import *
from scipy import *

import grafit.lib.ElementTree as xml

from grafit.utils import flatten, splitlist, EventHandler, connectevents, pyget, pyset, Page, Command
from grafit.project import project
from grafit.lib.mimetex import mimetex
from grafit.lib.odr import Model, RealData, ODR
from grafit.function import decorate, function_class_from_function, FitFunction

sum = __builtins__['sum']

#
# Commands

loaded_functions = []

def register_fit_function(func):
    loaded_functions.append(func)
    

class ChangeFitDatasets(Command):
    """Change the list of datasets used in fitting"""
    def __init__(self, graph, old, new):
        self.graph, self.old, self.new = graph.name, [d.index() for d in old], [d.index() for d in new]

    def do(self):
        graph = project[self.graph]
        graph.fitwin.destroy_ui()
        graph.fitdatasets = [graph.datasets[n] for n in self.new]
        graph.fitwin.build_ui()
        graph.redraw()
        graph.legend.update()

    def undo(self):
        graph = project[self.graph]
        graph.fitwin.destroy_ui()
        graph.fitdatasets = [graph.datasets[n] for n in self.old]
        graph.fitwin.build_ui()
        graph.redraw()
        graph.legend.update()


# We want to emit this command when:
# * the user changes a parameter from the ui
# * the user moves a function from the ui
# * a fit finishes
class ChangeParameterValue(Command):
    """Change the values of the fit parameters"""
    accumulate = False
    def __init__(self, fitwin, flat, prev):
        self.fitwin, self.flat, self.prev = fitwin, flat, prev

    def do(self):
        self.fitwin.params_flat_to_func(self.flat)
        self.fitwin.params_func_to_ui()
        self.fitwin.graph.update_function_curves()

    def undo(self):
        self.fitwin.params_flat_to_func(self.prev)
        self.fitwin.params_func_to_ui()
        self.fitwin.graph.update_function_curves()

    def combine(self, command):
        if self.accumulate:
            command.flat = self.flat
            return command
        else:
            raise TypeError

class RenameFunctionCommand(Command):
    def __init__(self, fitwin, func, prev, name):
        self.fitwin, self.func, self.name, self.prev = fitwin, func, name, prev

    def do(self):
        self.func.inst_name = self.name
        self.func.func_btn.setText(self.name)

    def undo(self):
        self.func.inst_name = self.prev
        self.func.func_btn.setText(self.prev)

class ChangeParameterSharing(Command):
    def __init__(self, fitwin, func, prev, flat):
        self.fitwin, self.func, self.flat, self.prev = fitwin, func, flat, prev

    def do(self):
        self.func.varshare = self.flat
        self.fitwin.rebuild_ui ()

    def undo(self):
        self.func.varshare = self.prev
        self.fitwin.rebuild_ui ()

    def __repr__(self):
        return "Change parameter sharing in function %s" % self.func.name

class AddFitFunctionCommand(Command):
    """Add a term to the fit function
    
    fitwin - the fit window
    id - the function id (index in available_functions)
    place - the order in the fit window
    """
    def __init__(self, fitwin, func, place):
        self.fitwin, self.func, self.place = fitwin, func, place

    def do(self):
        self.fitwin.destroy_ui()
        self.fitwin.add_function(self.func)
        self.fitwin.build_ui()

    def undo(self):
        self.fitwin.destroy_ui()
        self.fitwin.remove_function(self.place)
        self.fitwin.build_ui()

class RemoveFitFunctionCommand(Command):
    """Remove a term from the fit function"""
    def __init__(self, fitwin, func, place):
        self.fitwin, self.func, self.place = fitwin, func, place

    def do(self):
        self.fitwin.destroy_ui()
        self.fitwin.functions.remove(self.func)
        self.fitwin.build_ui()

    def undo(self):
        self.fitwin.destroy_ui()
        self.fitwin.functions.insert(self.place, self.func)
        self.fitwin.build_ui()

def fitfunction (*args):
    if len(args) == 3:
        niter, actred, wss = args
        project.mainwin.statusBar().message ('Fitting: Iteration %d, xsqr=%g, reduced by %g' % (niter, wss, actred))
        project.mainwin.progressbar.setProgress(niter*10, 0)
        project.main_dict['app'].processEvents()
        return
    else:
        params, x = args
    fitdatasets = FitWindow.inst.graph.fit_datasets()
    fsdizes = [len(d.x()) for d in fitdatasets]
    xreal = map (Numeric.array, splitlist (x, fsdizes))

    y = []
    FitWindow.inst.params_flat_to_func (params)
    for i, xx in enumerate(xreal):
        for fn in FitWindow.inst.functions:
            fn.load (fitdatasets[i].curveid)
        y.append (FitWindow.inst.call(xx))
    ret = concatenate (y)
    if FitWindow.inst.graph.fitwin.wmethod == 2:
        try:
            return Numeric.log(ret) # logarithmic fit
        except:
            print >>sys.stderr, 'Math range error (den Vogel)'
            return zeros(ret.shape, 'f')
    else:
        return ret # linear fit

from sets import Set as set

class SelectFunctionWindow(QDialog):
    def __init__(self, graph, parent):
        QDialog.__init__(self, parent, "SelectFunction", True)
        self.graph = graph
        layout = QVBoxLayout(self)
        self.tbox = QHBox(self)
        layout.addWidget(self.tbox)
        self.bbox = QHBox(self)
        layout.addWidget(self.bbox)
        self.lbox = QVBox(self.tbox)
        self.clist = QListBox(self.lbox)
        self.clist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.flist = QListBox(self.lbox)
        self.flist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.info = QLabel(self.tbox)
        self.info.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.info.setMinimumSize(QSize(200, 300))
        self.info.setAlignment(QLabel.AlignTop | QLabel.AlignLeft)

        self.clist.insertStrList(list(set(self.graph.fitwin.function_categories.values())))
        self.connect(self.clist, SIGNAL("highlighted(int)"), self.on_clist_selected)
        self.connect(self.flist, SIGNAL("highlighted(int)"), self.on_flist_selected)
        self.connect(self.flist, SIGNAL("doubleClicked(QListBoxItem*)"), self.on_flist_doubleclicked)
#        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
#        self.setMinimumSize(QSize(500, 500))

    def on_clist_selected(self, sel):
        self.sel = str(self.clist.text(sel))
        self.flist.clear()
        self.flist.insertStrList([k for k in self.graph.fitwin.function_categories.keys() if self.graph.fitwin.function_categories[k] == self.sel])
        
    def on_flist_selected(self, sel):
        if self.sel == 'Basic': self.sel = ''
        f = [u for u in self.graph.fitwin.available_functions if u.name == self.sel + '/'*(not self.sel=='') \
                                + str(self.flist.text(sel))][0]
        info = "<h3>%s</h3><p>" % str(self.flist.text(sel))
        if hasattr(f, "desc"):
            info += f.desc + "<p>"

        info += "<i>Equation:</i><p>"
        if hasattr(f, 'pixmap') and f.pixmap is not None:
            info += '<img src="%s"/>' % (f.name+'_tex',)

        info += "<p><i>Parameters:</i> <ul>"
        for p in f.args:
            info += "<li><i>%s</i></li>" % p
        info += "</ul>"

        self.info.setText(info)

    def on_flist_doubleclicked(self, item):
        if self.sel == 'Basic': self.sel = ''
        f = [u for u in self.graph.fitwin.available_functions if u.name == self.sel + '/'*(not self.sel=='') \
                                + str(item.text())][0]
        self.graph.fitwin.add_function(self.graph.fitwin.available_functions.index(f))
        self.graph.fitwin.rebuild_ui()

        
class FitWindow (QVBox):
    inst = None

    def __init__ (self, grap, prnt):
        QVBox.__init__(self, prnt)

        self.graph = grap

        layout = self

        self.btnframe = QHBox(layout)

        self.addbtn = QToolButton(self.btnframe)
        self.addbtn.setAutoRaise(1)

        self.propsbtn = QToolButton(self.btnframe)
        self.propsbtn.setAutoRaise(1)

        self.execbtn = QToolButton(self.btnframe)
        self.execbtn.setAutoRaise(1)

        self.savebtn = QToolButton(self.btnframe)
        self.savebtn.setAutoRaise(1)

        self.funcframescroll = QScrollView(layout)
        self.funcframescroll.setVScrollBarMode(QScrollView.AlwaysOn)
        self.funcframescroll.setHScrollBarMode(QScrollView.AlwaysOff)

        pal = QPalette(self.funcframescroll.palette())
        cg = QColorGroup(pal.active())
        cg.setColor(QColorGroup.Dark,cg.background())
        pal.setActive(cg)
        self.funcframescroll.setPalette(pal)

        self.funcframe = QFrame (self.funcframescroll)
        self.funcframe.setMaximumSize (100, 3100)
        self.funcframescroll.setMinimumSize (120, 0)
        self.funcframescroll.setMaximumSize (120, 32000)
        self.funcframescroll.addChild (self.funcframe)

        self.frameLayout = QVBoxLayout(self.funcframe,2,6)

        self.addbtn.setIconSet (QIconSet(QPixmap(project.datadir + 'pixmaps/function.png')))
        self.propsbtn.setIconSet (QIconSet(QPixmap(project.datadir + 'pixmaps/properties.png')))
        self.execbtn.setIconSet (QIconSet(QPixmap(project.datadir + 'pixmaps/crank.png')))
        self.savebtn.setIconSet (QIconSet(QPixmap(project.datadir + 'pixmaps/pencil.png')))
        QToolTip.add(self.addbtn, "Add fit function")
        QToolTip.add(self.propsbtn, "Fit settings")
        QToolTip.add(self.execbtn, "Start fit")
        QToolTip.add(self.savebtn, "Save fit results")
        self.connect(self.propsbtn, SIGNAL("clicked()"), self.fit_properties)
        self.connect(self.addbtn, SIGNAL("clicked()"), self.addbtn_clicked)
        self.connect(self.execbtn, SIGNAL("clicked()"), self.fit)
        self.connect(self.savebtn, SIGNAL("clicked()"), self.pencil)

        self.functionsmenu = QPopupMenu ()
        self.functionsmenu.popups = {}
#        self.addbtn.setPopup (self.functionsmenu)
#        self.addbtn.setPopupDelay (1)

        self.btngrp = QButtonGroup ()
        self.btngrp.setExclusive (True)
        self.connect(self.btngrp, SIGNAL("clicked(int)"), self.on_func_btn_toggled)
        self.selected_function = None

        self.closebtngrp = QButtonGroup ()
        self.connect(self.closebtngrp, SIGNAL("clicked(int)"), self.on_func_close_clicked)
        self.closebtngrp.setExclusive (False)

        self.functions = []
        self.extra_properties = []

        self.renaming_function = None

        self.setup_functions()

        self.maxiter = 50
        self.wmethod = 0
        self.resultsws = 'fitresults'

    def addbtn_clicked(self):
        s = SelectFunctionWindow(self.graph, project.mainwin)
        s.show()


    def to_element(self):
        elem = xml.Element ('FitWindow')
        pyset(elem, "datasets", [d.index() for d in self.graph.fit_datasets()])
        pyset(elem, "names", [f.name for f in self.functions])
        pyset(elem, "varshares", [f.varshare for f in self.functions])
        pyset(elem, "params", self.params_func_to_flat())
        pyset(elem, "inst_names", [f.inst_name for f in self.functions])
        pyset(elem, "extra_properties", self.extra_properties)
        pyset(elem, "max_iterations", self.maxiter)
        pyset(elem, "resultsws", self.resultsws)
        return elem

    def from_element(self, elem):
        self.destroy_ui()
        self.functions = []
        try:
            instnames = pyget(elem, "inst_names")
        except:
            instnames = [None for f in pyget(elem, "names")]

        try:
            self.extra_properties = pyget(elem, "extra_properties")
        except:
            pass

        try:
            self.maxiter = pyget(elem, "max_iterations")
        except:
            pass

        try:
            self.resultsws = pyget(elem, "resultsws")
        except:
            pass

        for name, varshare, instname in zip(pyget(elem, "names"), pyget(elem, "varshares"), instnames):
            try:
                id = [f.name for f in self.available_functions].index(name)
            except ValueError: # function not available
                print >>sys.stderr, "Function not available: %s" % (name,)
                continue
            func = function_class_from_function(self.available_functions[id])()
            func.varshare = varshare
            func.inst_name = instname
            self.functions.append(func)
        self.graph.fitdatasets = [self.graph.datasets[i] for i in pyget(elem, "datasets")]
        self.params_flat_to_func(pyget(elem, "params")[0])
        self.build_ui()

    def setup_functions(self):
        self.fmodules = []
        self.available_functions = []
        self.function_categories = {}
        self.funcnames = [fn[0:-3] for fn in os.listdir(project.datadir + 'functions') if fn.endswith ('.py')]
        
        self.functionsmenu.clear()
        for f in loaded_functions:
            self.add_available_function(f)
        for i, name in enumerate(self.funcnames):
            module = __import__('functions/' + name)
            if hasattr(module, 'functions'):
                for func in module.functions:
                    self.add_available_function(func)

    def add_available_function(self, func):
        decorate(func)
        num = len(self.available_functions)
        path = func.name.split('/')
        if len(path) == 1: # no category
            self.functionsmenu.insertItem(func.name, self.on_func_menu_activated, 0, num)
            self.function_categories[path[0]] = 'Basic'
        elif len(path) == 2:
            for id in [self.functionsmenu.idAt(i) for i in xrange(self.functionsmenu.count())]:
                if self.functionsmenu.text(id) == path[0]:
                    menu = self.functionsmenu.popups[path[0]]
                    break
            else:
                self.functionsmenu.popups[path[0]] = menu = QPopupMenu()
                self.functionsmenu.insertItem(path[0], menu)
            menu.insertItem(path[1], self.on_func_menu_activated, 0, num)

            self.function_categories[path[1]] = path[0]

        if hasattr(func, 'tex'):
            func.pixmap = mimetex(func.tex)
            if func.pixmap is not None:
                QMimeSourceFactory.defaultFactory().setPixmap(func.name+'_tex', func.pixmap)
        self.available_functions.append(func)
        

#----------------------------------------------------------------------------------------------------
# Function widgets

    def add_function_widgets (self, id):
        """build the function widgets for a function"""
        f = self.functions[id]
        f.layout = QGridLayout(None,1,1,0,0)

        # button
        f.func_btn = QPushButton (self.funcframe)
        if hasattr(f, 'tex'):
            QToolTip.add(f.func_btn, '%s<br><hr><img src="%s">' % (f.name, f.name+'_tex',))
        f.func_btn.setToggleButton (1)
        if f.inst_name is not None:
            f.func_btn.setText (f.inst_name)
        else:
            f.func_btn.setText ('function')
        f.layout.addMultiCellWidget (f.func_btn,0,0,0,1)
        self.btngrp.insert (f.func_btn)
        f.func_btn.show()
        f.func_btn.installEventFilter(EventHandler (f.func_btn, self.make_function_button_event(id)))
        
        f.renameme = QLineEdit(self.funcframe)
        f.layout.addMultiCellWidget (f.renameme,0,0,0,1)
        self.connect(f.renameme, SIGNAL("returnPressed()"), self.on_function_renamed)
        self.connect(f.renameme, SIGNAL("lostFocus()"), self.on_function_renamed)
    
        connectevents(f.renameme, self.on_renameme_event)
        f.renameme.hide()

        f.closebtn = QToolButton (self.funcframe)
        f.closebtn.setText ('x')
        f.closebtn.setGeometry(QRect(0,0,20,20))
        f.closebtn.setAutoRaise(1)
        self.closebtngrp.insert (f.closebtn)
        f.layout.addMultiCellWidget (f.closebtn,0,0,2,2)
        f.closebtn.show()

        f.var_names = []
        f.var_edit = []
        f.var_lock = []

        # e.g. with params=['a', 'b', 'c', 'd', 'e'] and a,c,d shared:
        # [[a], [b1, b2, b3], [c], [d], [e1, e2, e2]]

        last = 1
        for i, item in enumerate(f.params):
            f.var_names.append ([])
            f.var_edit.append ([])
            f.var_lock.append ([])
            if f.varshare[i]:
                jvals = [0]
            else:
                jvals = range (len(self.graph.fitdatasets))
            for j in jvals:
                f.var_names[i].append (None)
                if j==0:
                    f.var_names[i][j] = QToolButton(self.funcframe)
                    f.var_names[i][j].setGeometry(QRect(180,80,40,21))
                    f.var_names[i][j].setToggleButton(1)
                    f.var_names[i][j].setUsesTextLabel(0)
                    f.var_names[i][j].setAutoRaise(1)
                    f.var_names[i][j].setText(item)
                    f.var_names[i][j].setOn (not f.varshare[i])
                    self.connect (f.var_names[i][j], SIGNAL("toggled(bool)"), self.on_varname_toggled)
                else:
                    f.var_names[i][j] = QLabel (self.funcframe)
                    f.var_names[i][j].setText(item)
                f.layout.addWidget(f.var_names[i][j], last, 0)
                f.var_names[i][j].show()
            
                f.var_edit[i].append (None)
                f.var_edit[i][j] = QLineEdit(self.funcframe)
                f.var_edit[i][j].setValidator(QDoubleValidator(f.var_edit[i][j]))
                f.var_edit[i][j].setFrameShape(QLineEdit.Box)
                f.var_edit[i][j].setFrameShadow(QLineEdit.Plain)
                f.var_edit[i][j].setLineWidth(1)
                self.connect (f.var_edit[i][j], SIGNAL("returnPressed()"), self.on_ui_changed)
                self.connect (f.var_edit[i][j], SIGNAL("lostFocus()"), self.on_ui_changed)
                f.layout.addWidget(f.var_edit[i][j], last,1)
                f.var_edit[i][j].show()

                f.var_lock[i].append (None)
                f.var_lock[i][j] = QCheckBox(self.funcframe)
                f.var_lock[i][j].setText(QString.null)
                f.layout.addWidget(f.var_lock[i][j],last,2)
                self.connect (f.var_lock[i][j], SIGNAL("toggled(bool)"), self.on_ui_changed)
                f.var_lock[i][j].show()
                last += 1

        self.frameLayout.addLayout(f.layout)

    def on_renameme_event(self, event):
        if isinstance(event, QFocusEvent):
            if event.lostFocus():
                self.functions[self.renaming_function].func_btn.show()
                self.functions[self.renaming_function].renameme.releaseKeyboard()
                self.functions[self.renaming_function].renameme.hide()
                self.renaming_function = None
                return True
        return False

    def del_function_widgets (self, id):
        f = self.functions[id]
        self.btngrp.remove (f.func_btn)
        f.func_btn.close()
        del f.func_btn
        self.closebtngrp.remove (f.closebtn)
        f.closebtn.close()
        del f.closebtn
        for w in flatten(f.var_names): w.close(); del w
        for w in flatten(f.var_edit): w.close(); del w
        for w in flatten(f.var_lock): w.close(); del w
        self.frameLayout.removeItem (f.layout)
        del f.layout

    def make_function_button_event(self, id):
        def handler(event):
            return self.on_function_button_event(id, event)
        return handler

    def on_function_button_event(self, id, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if self.renaming_function is not None:
                self.functions[self.renaming_function].func_btn.show()
                self.functions[self.renaming_function].renameme.releaseKeyboard()
                self.functions[self.renaming_function].renameme.hide()
            self.functions[id].func_btn.hide()
            self.functions[id].renameme.show()
            self.functions[id].renameme.setText(self.functions[id].func_btn.text())
            self.functions[id].renameme.grabKeyboard()
            self.renaming_function = id
        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            def fit_curve_to_graph():
                self.add_fit_curve_to_graph(id)
            self._fit_curve_to_graph = fit_curve_to_graph

            menu = QPopupMenu(self)
            menu.insertItem('Add fit curve to graph', fit_curve_to_graph)
            menu.popup(QPoint(event.globalX(), event.globalY()))

        return False

    def on_function_renamed(self):
        self.functions[self.renaming_function].func_btn.show()
        name = str(self.functions[self.renaming_function].renameme.text())
        project.undolist.append(RenameFunctionCommand(self, self.functions[self.renaming_function], 
                                        self.functions[self.renaming_function].inst_name, name))
        self.functions[self.renaming_function].inst_name = name
        self.functions[self.renaming_function].func_btn.setText(name)
        self.functions[self.renaming_function].renameme.releaseKeyboard()
        self.functions[self.renaming_function].renameme.hide()
        self.renaming_function = None

#----------------------------------------------------------------------------------------------------
# Function parameters


    def params_ui_to_func (self):
        """get parameters and locks from ui and write to functions"""
        params = []
        locks = []
        for fn in self.functions:
            fpar = []
            flck = []
            for i, p in enumerate (fn.params):
                if fn.varshare[i]:
                    try:
                        value = float(str(fn.var_edit[i][0].text()))
                    except ValueError: # empty or invalid string
                        value = getattr(fn, fn.params[i])
                    fpar.append ([value]*len(self.graph.fit_datasets()))
                    flck.append ([fn.var_lock[i][0].isOn()]*len(self.graph.fit_datasets()))
                else:
                    try:
                        values = [float(str(v.text())) for v in fn.var_edit[i]]
                    except ValueError: # empty or invalid string
                        values = [getattr(fn, fn.params[i])*len(self.graph.fit_datasets())]
                    fpar.append (values)
                    flck.append ([v.isOn() for v in fn.var_lock[i]])
            params.append (fpar)
            locks.append( flck )
        for n, ds in enumerate(self.graph.fit_datasets()):
            for i, fn in enumerate(self.functions):
                fn.load(ds.curveid)
                try:
                    fn.set_params ([p[n] for p in params[i]])
                    fn.locked = [l[n] for l in locks[i]]
                    fn.save(ds.curveid)
                except:
                    pass

    def params_func_to_ui (self):
        """update ui with function parameters and locks"""
        for d, ds in enumerate(self.graph.fit_datasets()):
            for n, fn in enumerate(self.functions):
                fn.load(ds.curveid)
                for i, p in enumerate (fn.get_params()):
                    if fn.varshare[i]:
                        fn.var_edit[i][0].setText ("%.3g" % p)
                        fn.var_lock[i][0].setOn (fn.is_locked (i))
                    else:
                        fn.var_edit[i][d].setText ("%.3g" % p)
                        fn.var_lock[i][d].setOn (fn.is_locked (i))

    def params_flat_to_func (self, flat):
        """update function parameters from a flat list"""
        # first split according to functions
        nshared = [sum(f.varshare) for f in self.functions]
        ntotal = [len(f.params) for f in self.functions]
        ndatasets = len(self.graph.fit_datasets())
        fsizes = [s+(t-s)*ndatasets for s,t in zip(nshared,ntotal)]
        fparams = splitlist (flat, fsizes)

        # then split by variable
        for fn, fparam in zip (self.functions, fparams):
            dparams = []
            vsizes = map (lambda x: x and 1 or ndatasets, fn.varshare)
            vparams = splitlist (fparam, vsizes)
            for d in range(ndatasets):
                dp = []
                for j, vparam in enumerate(vparams):
                    if fn.varshare [j]:
                        dp.append (vparam[0]) 
                    else:
                        try:
                            dp.append (vparam[d])
                        except:
                            print >>sys.stderr, d
                dparams.append (dp)
            for dparam, ds in zip(dparams, self.graph.fit_datasets()):
                fn.load(ds.curveid)
                fn.set_params (dparam)                
                fn.save(ds.curveid)
        
    def params_func_to_flat (self):
        """flat list of function parameters and locks"""
        flat = []
        lock = []
        for fn in self.functions:
            for i,p in enumerate(fn.params):
                if fn.varshare[i]:
                    flat.append (getattr(fn, p))
                    lock.append (fn.is_locked (i))
                else:
                    for ds in self.graph.fit_datasets():
                        fn.load (ds.curveid)
                        flat.append (getattr(fn, p))
                        lock.append (fn.is_locked (i))
        return (flat, lock)

    def flat_names (self):
        names = []
        for fnum, fn in enumerate(self.functions):
            if fn.inst_name is not None:
                fname = fn.inst_name
            else:
                fname = 'f'+str(fnum)
            for i,p in enumerate(fn.params):
                if fn.varshare[i]:
                    names.append (fname + '_' + p)
                else:
                    for ds in self.graph.fit_datasets():
                        names.append (fname + '_' + p + str(ds.index()))
        return names


#----------------------------------------------------------------------------------------------------
# Events

    def add_function(self, id):
        if isinstance(id, int) and self.available_functions[id] is not None:
            func = function_class_from_function(self.available_functions[id])()
        elif isinstance(id, FitFunction):
            func = id
        self.functions.append(func)
        project.undolist.append(AddFitFunctionCommand(self, func, len(self.functions)-1))

    def remove_function(self, id):
        project.undolist.append(RemoveFitFunctionCommand(self, self.functions[id], id))
        self.functions.remove (self.functions[id])

    def on_func_menu_activated (self, id):
        self.add_function(id)
        self.rebuild_ui()

    def on_ui_changed (self):
        prev = self.params_func_to_flat()[0]
        self.params_ui_to_func ()
        flat = self.params_func_to_flat()[0]
        project.undolist.append(ChangeParameterValue(self, flat, prev))
        self.graph.update_function_curves ()

    def on_func_btn_toggled (self, id):
        self.selected_function = id
        self.graph.update_function_curves()

    def on_func_close_clicked (self, id):
        self.destroy_ui ()
        self.remove_function(id)
        self.build_ui ()

    def destroy_ui (self):
        for i, f in enumerate(self.functions):
            try:
                self.del_function_widgets (i)
            except:
                pass

        for d in self.graph.fit_datasets ():
            if d.function:
                self.graph.plot.removeCurve (d.function)
                d.function = None
            for id in d.funcs[:]:
                self.graph.plot.removeCurve (id)
                d.funcs.remove (id)

    def build_ui (self):
        for i, f in enumerate(self.functions):
            self.add_function_widgets (i)

        for fds in self.graph.fit_datasets ():
            for func in self.functions:
                id = self.graph.plot.insertCurve (func.name)
                fds.funcs.append (id)
            fds.function = self.graph.plot.insertCurve ('function')
        if self.selected_function is not None and self.selected_function in range(len(self.functions)):
            self.btngrp.setButton (self.selected_function)
        self.params_func_to_ui ()
        self.graph.update_function_curves()


    def rebuild_ui (self):
        self.destroy_ui ()
        self.build_ui ()

    def on_varname_toggled (self, bool):
        if len(self.graph.fitdatasets) < 2:
            for i, f in enumerate(self.functions):
                [w[0].setOn(False) for w in f.var_names]
        else:
            for i, f in enumerate(self.functions):
                uivarshare = [not w[0].isOn() for w in f.var_names]
                if f.varshare != uivarshare:
                    project.undolist.append(ChangeParameterSharing(self, f, f.varshare, uivarshare))
                    f.varshare = uivarshare
        self.rebuild_ui ()
            
#----------------------------------------------------------------------------------------------------
# Fitting

    def call(self, x):
        if len(self.functions) == 0:
            return None
        try:
            return sum ([y.call(x) for y in self.functions])
        except:
            return zeros(x.shape, 'd')

    def fit(self):
        if len(self.graph.fit_datasets()) == 0:
            return
        self.execbtn.setEnabled(False)
        FitWindow.inst = self
        # Model
        model = Model (fitfunction)
        # Data
        fitx = concatenate ([d.x() for d in self.graph.fit_datasets()])
        fity = concatenate ([d.y() for d in self.graph.fit_datasets()])
        if self.wmethod == 0: 
            data = RealData (fitx, fity) # no weigthting
        elif self.wmethod == 1:
            data = RealData (fitx, fity, sy=fity) # statistical
        elif self.wmethod == 2:
            data = RealData (fitx, Numeric.log(fity)) # logarithmic fit
        # Initial values
        beta, lock = self.params_func_to_flat()
        prev = beta[:]
        # Run fit
        odrobj = ODR (data, model, beta0=beta, ifixb=[not x for x in lock], 
                      partol=1e-100, sstol=1e-100, maxit=self.maxiter)
        odrobj.set_job (fit_type=2)
        odrobj.set_iprint (iter=3, iter_step=1)
        try:
            output = odrobj.run()
            # Show results
            flat = self.params_func_to_flat()[0]
            project.undolist.append(ChangeParameterValue(self, flat, prev))
            self.graph.update_function_curves ()
            self.params_func_to_ui ()
        except:
            print 'Fit den Vogel (but no problem)'
        self.execbtn.setEnabled(True)

    def fit_properties (self):
        dlg = Page(self,
            ('Termination Conditions', 
#                ['Tolerance (xsqr)', 
#                 'Tolerance (param)', 
                 ['#Max Iterations']),
            ('Weighting', 
                ['|Weighting method|No Weighting|Statistical|Logarithmic Fit']),
            ('Results', 
                 ['Worksheet', 
                  'Extra properties']))

        dlg['Extra properties'] = ','.join(self.extra_properties)
        dlg['Worksheet'] = self.resultsws
        dlg['Max Iterations']   = self.maxiter
        dlg['Weighting method'] = self.wmethod

        dlg.run()

        self.extra_properties = [st for st in
                                      [s.strip() for s in dlg['Extra properties'].split(',')]
                                 if st != '']
        self.maxiter = dlg['Max Iterations']
        self.wmethod = dlg['Weighting method']
        self.resultsws = dlg['Worksheet']

    def add_fit_curve_to_graph(self, function):
        try:
            project['fitcurves']
        except IndexError, KeyError:
            project.new_worksheet ('fitcurves')

        ws = project['fitcurves']
        id = 0
        while self.graph.name+'_fit_'+str(id)+'X' in ws.column_names:
            id += 1

        if self.graph.xaxis.logscale:
            x = 10.**(Numeric.arange(Numeric.log10(self.graph.xaxis.min),Numeric.log10(self.graph.xaxis.max),
                              (Numeric.log10(self.graph.xaxis.max)-Numeric.log10(self.graph.xaxis.min))/100.))
        else:
            x = Numeric.arange (self.graph.xaxis.min, self.graph.xaxis.max, (self.graph.xaxis.max-self.graph.xaxis.min)/100.)
        ws[self.graph.name+'_fit_'+str(id)+'X'] = x
        ws[self.graph.name+'_fit_'+str(id)+'Y'] = self.functions[function].call(x)
        self.graph.add(ws, self.graph.name+'_fit_'+str(id)+'X',
                           self.graph.name+'_fit_'+str(id)+'Y')

    def pencil (self):
        if self.resultsws not in [w.name for w in project.worksheets]:
            project.new_worksheet(self.resultsws)

        if len(project[self.resultsws]) == 0:
            last = 0
        else:
            last = max([len(c) for c in project[self.resultsws]])

        for name in self.extra_properties:
            value, ok =  QInputDialog.getText ("Grafit", name, QLineEdit.Normal, None, self)
            if ok:
                value = float(str(value))
                if name not in project[self.resultsws].column_names:
                    project[self.resultsws][name] = []
                project[self.resultsws][name][last] = value
        
        for value, name in zip (self.params_func_to_flat()[0], self.flat_names ()):
            if name not in project[self.resultsws].column_names:
                project[self.resultsws][name] = []
            project[self.resultsws][name][last] = value

        for fnum, fn in enumerate(self.functions):
            if hasattr(fn, 'extra'):
                if fn.inst_name is not None:
                    fname = fn.inst_name
                else:
                    fname = 'f'+str(fnum)

                calldict = {}
                calldict.update(project.main_dict)
                calldict.update(fn.__dict__)
                for p, v in fn.extra.iteritems():
                    value = eval(v, calldict)
                    name = fname + '_' + p
     
                    if name not in project[self.resultsws].column_names:
                        project[self.resultsws][name] = []
                    project[self.resultsws][name][last] = value
