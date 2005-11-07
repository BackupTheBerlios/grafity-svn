from qt import *
from qwt.qplt import *
from grafit.project import project
from grafit.utils import intersection, all_the_same
from grafit.graph import Dataset

colors = [Qt.black, Qt.red, Qt.darkRed, Qt.green, Qt.darkGreen, 
          Qt.blue, Qt.darkBlue, Qt.cyan, Qt.darkCyan, Qt.magenta, Qt.darkMagenta, 
          Qt.yellow, Qt.darkYellow, Qt.gray, Qt.darkGray, Qt.lightGray, Qt.black]

extracolornames = [ 'CadetBlue3', 'CornflowerBlue', 'DarkGoldenrod1',
                    'DarkOliveGreen2', 'DarkOrange1', 'DarkSalmon',
                    'DarkTurquoise', 'DeepPink2', 'DeepSkyBlue1',
                    'DodgerBlue3', 'HotPink', 'HotPink3', 'IndianRed',
                    'LightGreen', 'MediumPurple4', 'MediumViloetRed' ]

colors += [QColor(s) for s in extracolornames]

class autobject(object):
    def __setattr__(self, key, val):
        self.__dict__[key] = val
    def __getattr__(self, key):
        return self.__dict__[key]

class GraphDataPanel(QVBox):
    def __init__(self, parent):
        QVBox.__init__(self, parent)

        buttons = QHBox(self)

        btn1 = QPushButton('add', buttons)
        self.connect(btn1, SIGNAL('clicked()'), self.on_addbtn_clicked)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        btn1 = QPushButton('remove', buttons)
        self.connect(btn1, SIGNAL('clicked()'), self.on_removebtn_clicked)

        QLabel('Worksheet', self)
        self.wslist = QListBox(self)
        self.wslist.setSelectionMode(QListBox.Extended)

        QLabel('X axis', self)
        self.xlist = QListBox(self)
        self.xlist.setSelectionMode(QListBox.Extended)

        QLabel('Y axis', self)
        self.ylist = QListBox(self)
        self.ylist.setSelectionMode(QListBox.Extended)

        self.connect(self.xlist,SIGNAL("doubleClicked(QListBoxItem*)"),self.on_xlist_double_clicked)
        self.connect(self.ylist,SIGNAL("doubleClicked(QListBoxItem*)"),self.on_ylist_double_clicked)
        self.connect(self.wslist,SIGNAL("selectionChanged()"), self.on_wslist_select)

    def open(self):
        self.graph = project.mainwin.active.graph
        self.wslist.clear()
        self.wslist.insertStrList ([a.name for a in project.worksheets])

    def on_wslist_select (self):
        wsheets = [project.w[self.wslist.text(a)] for a in range(self.wslist.count()) if self.wslist.isSelected(a)]
        uniqcols = intersection ([a.column_names for a in wsheets])

        # sort by position in the first selected worksheet
        uniqcols = [(wsheets[0][c].index(), c) for c in uniqcols]
        uniqcols.sort()
        uniqcols = [c[1] for c in uniqcols]

        for list in [self.xlist, self.ylist]:
            list.clear()
            list.insertStrList (uniqcols)

    def on_addbtn_clicked (self):
        wsheets = [project.w[self.wslist.text(a)] for a in range(self.wslist.count()) if self.wslist.isSelected(a)]
        xcols = [self.xlist.text(a).ascii() for a in range(self.xlist.count()) if self.xlist.isSelected(a)]
        ycols = [self.ylist.text(a).ascii() for a in range(self.ylist.count()) if self.ylist.isSelected(a)]
        self.graph.freeze()
        try:
            for worksheet in wsheets:
                for xcol in xcols:
                    for ycol in ycols:
                        self.graph.add (worksheet.name, xcol, ycol)
        finally:
            self.graph.unfreeze()
        
    def on_ylist_double_clicked(self, item):
        ind = self.ylist.index(item)
        selected = [i for i in range(self.ylist.count()) if self.ylist.isSelected(i)]
        if len(selected) == 2 and selected[1] == ind:
            for i in range(self.ylist.count()):
                self.ylist.setSelected(i, i>=selected[0] and (i-selected[0])%(ind-selected[0]) == 0)

    def on_xlist_double_clicked(self, item):
        ind = self.xlist.index(item)
        selected = [i for i in range(self.xlist.count()) if self.xlist.isSelected(i)]
        if len(selected) == 2 and selected[1] == ind:
            for i in range(self.xlist.count()):
                self.xlist.setSelected(i, i>=selected[0] and (i-selected[0])%(ind-selected[0]) == 0)

    def on_removebtn_clicked (self):
        dsets = [a for a in range(self.graph.legend.count()) if self.graph.legend.isSelected(a)]
        dsets.reverse()
        self.graph.freeze()
        try:
            for d in dsets:
                self.graph.remove (self.graph.datasets[d])
        finally:
            self.graph.unfreeze()

class GraphStylePanel(QVBox):
    sel_call = None
    def __init__(self, parent):
        QVBox.__init__(self, parent)

        QLabel('<b>Symbol</b>', self)
        f = QFrame(self)
        f.setFrameShape(QFrame.HLine)
        f.setFrameShadow(QFrame.Sunken)

        ptstyle = QGrid(3, self)


        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sshape_check = QCheckBox(ptstyle)
        QLabel('Shape', ptstyle)
        self.sshape = QComboBox(ptstyle)

        self.sfill_check = QCheckBox(ptstyle)
        QLabel('Fill', ptstyle)
        self.sfill = QComboBox(ptstyle)

        self.ssize_check = QCheckBox(ptstyle)
        QLabel('Size', ptstyle)
        self.ssize = QSpinBox(ptstyle)

        self.scolor_check = QCheckBox(ptstyle)
        QLabel('Color', ptstyle)
        self.scolor = QComboBox(ptstyle)

        QLabel('<b>Line</b>', self)
        f = QFrame(self)
        f.setFrameShape(QFrame.HLine)
        f.setFrameShadow(QFrame.Sunken)

        ptstyle = QGrid(3, self)

        self.ltype_check = QCheckBox(ptstyle)
        QLabel('Type', ptstyle)
        self.ltype = QComboBox(ptstyle)

        self.lstyle_check = QCheckBox(ptstyle)
        QLabel('Style', ptstyle)
        self.lstyle = QComboBox(ptstyle)

        self.lwidth_check = QCheckBox(ptstyle)
        QLabel('Width', ptstyle)
        self.lwidth = QSpinBox(ptstyle)

        box = QHBox(self)
        QLabel('Group', box)
        self.group = QComboBox(box)

        l = QLabel(self)
        l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for c in colors: 
            p = QPixmap()
            p.resize (30, 10)
            p.fill (c)
            self.scolor.insertItem (p)
#            self.lcolor.insertItem (p)

        for l in Dataset.line_styles:
            p = QPixmap()
            p.resize (50, 10)
            paint = QPainter()
            pen = QPen (QColor('black'))
            pen.setStyle (l)
            p.fill (QColor('white'))
            paint.begin(p)
            paint.setPen (pen)
            paint.drawLine (0,5, 30,5)
            paint.end()
            self.lstyle.insertItem (p)

        self.sfill.insertStrList(['open', 'filled'])
        self.ignore_toggle = False
        self.fills = [Qt.NoBrush, Qt.SolidPattern]

        self.series = [(1,10), (0,2), (3, 15), (0, len(colors)),
                       (1, len(Dataset.line_types)), (1, len(Dataset.line_styles)), 
                       (1, 7), (0, len(colors))]

        self.properties = ['symbol_style', 'symbol_fill', 'symbol_size', 'symbol_color',
                           'line_type', 'line_style', 'line_width']
        self.checks = [self.sshape_check, self.sfill_check, self.ssize_check, self.scolor_check,
                       self.ltype_check, self.lstyle_check, self.lwidth_check]
        self.widgets = [self.sshape, self.sfill, self.ssize, self.scolor,
                        self.ltype, self.lstyle, self.lwidth]
        for w in self.checks:
            w.hide()
            self.connect (w, SIGNAL("toggled(bool)"), self.on_checkbox_toggled)


        self.connect(self.sshape,SIGNAL("activated(int)"),self.on_sshape_changed)
        self.connect(self.ssize,SIGNAL("valueChanged(int)"),self.on_ssize_changed)
        self.connect(self.scolor,SIGNAL("activated(int)"),self.on_scolor_changed)
        self.connect(self.sfill,SIGNAL("activated(int)"),self.on_sfill_changed)
        self.connect(self.lstyle,SIGNAL("activated(int)"),self.on_lstyle_changed)
        self.connect(self.lwidth,SIGNAL("valueChanged(int)"),self.on_lwidth_changed)
        self.connect(self.group,SIGNAL("activated(int)"),self.on_group_changed)
        self.connect(self.ltype,SIGNAL("activated(int)"),self.on_ltype_changed)

        self.sshape.insertItem("[none]")
        self.sshape.insertItem("circle")
        self.sshape.insertItem("square")
        self.sshape.insertItem("diamond")
        self.sshape.insertItem("up triangle")
        self.sshape.insertItem("down triangle")
        self.sshape.insertItem("left triangle")
        self.sshape.insertItem("right triangle")
        self.sshape.insertItem("cross")
        self.sshape.insertItem("x")
        self.ltype.insertItem("[none]")
        self.ltype.insertItem("straight")
        self.ltype.insertItem("spline")
        self.group.insertItem("identical")
        self.group.insertItem("series")



    def open(self):
        self.graph = project.mainwin.active.graph
        if self.sel_call is not None:
            try:
                self.disconnect(self.sel_call, SIGNAL('selectionChanged()'), self.on_legend_select)
            except RuntimeError: #object has been deleted
                pass
        self.connect(self.graph.legend, SIGNAL('selectionChanged()'), self.on_legend_select)
        self.sel_call = self.graph.legend

    def on_checkbox_toggled (self, on = True):
        if self.ignore_toggle:
            return
        datasets = [self.graph.datasets[n] for n in range(self.graph.legend.count()) 
                                                  if self.graph.legend.isSelected(n)]
        if len (datasets) == 0:
            return
        elif len (datasets) == 1:
            return

        self.graph.freeze()
        self.graph.begin_properties()

        try:
            for property, check, widget, serie in zip (self.properties, self.checks, self.widgets, self.series):
                if check.isOn ():
                    widget.setEnabled (True)
                    for i, ds in enumerate(datasets):
                        if widget in [self.sshape, self.sfill, self.lstyle, self.ltype, self.scolor]:
                            value = widget.currentItem ()
                        elif widget in [self.ssize, self.lwidth]:
                            value = widget.value ()

                        if self.group.currentItem() == 0:
                            ds.set_curve_style(property, value)
                        elif self.group.currentItem() == 1:
                            r = range (*serie)
                            ds.set_curve_style(property, r[(value + i) % len(r)])
                else:
                    widget.setEnabled (False)
        finally:
            self.graph.end_properties()
            self.graph.unfreeze()

    def on_group_changed (self, grp):
        self.on_legend_select ()

    def check_if_datasets_selected(self):
        datasets = [self.graph.datasets[n] for n in range(self.graph.legend.count()) 
                                                  if self.graph.legend.isSelected(n)]
        if len(datasets)==0:
            QMessageBox.information(self, "grafit", "Please select one or more curves first")
            return False
        return True


    def on_legend_select (self):
        datasets = self.datasets = [self.graph.datasets[n] for n in range(self.graph.legend.count()) 
                                                  if self.graph.legend.isSelected(n)]
#        if not self.isVisible():
#            return
        if self.graph._frozen:
            return

        if len(datasets) == 0:
            return
        elif len(datasets) == 1:  # single dataset selected
            self.group.setEnabled (False)
            for w in self.checks:
                w.hide()

            for w in self.widgets:
                w.setEnabled (True)

            self.dset = datasets[0]

            self.sshape.setCurrentItem (self.dset.symbol_style)
            self.ssize.setValue (self.dset.symbol_size)
            self.scolor.setCurrentItem (self.dset.symbol_color)
            self.sfill.setCurrentItem (self.dset.symbol_fill)

            self.ltype.setCurrentItem (self.dset.line_type)
            self.lwidth.setValue (self.dset.line_width)
#            self.lcolor.setCurrentItem (self.dset.line_color)
            self.lstyle.setCurrentItem (self.dset.line_style)
        else:   # multiple datasets selected
            self.group.setEnabled (True)
            for w in self.checks:
                w.show()

            self.ignore_toggle = True
            for property, check, widget, serie in zip (self.properties, self.checks, self.widgets, self.series):
                styles = [ds.get_curve_style(property) for ds in datasets] 
                r = range (*serie)
                if self.group.currentItem() == 0: # identical
                    if all_the_same (styles):
                        check.setOn (True)
                        widget.setEnabled (True)
                    else:
                        check.setOn (False)
                        widget.setEnabled (False)
                elif self.group.currentItem() == 1: # series
                    if styles[0] in r and styles == [r[(i + r.index(styles[0]))% len(r)] 
                                                                    for i in range(len(styles))]:
                        check.setOn (True)
                        widget.setEnabled (True)
                    else:
                        check.setOn (False)
                        widget.setEnabled (False)
            self.ignore_toggle = False

    def on_sshape_changed (self, shape):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        try:
            if len(self.datasets) == 1:
                self.dset.symbol_style = shape
                if shape != 0 and self.dset.symbol_size == 0:
                    self.dset.symbol_size = 5
                    self.ssize.setValue (5)
            else:
                self.after_property_changed()
        finally:
            self.graph.unfreeze()

    def on_ssize_changed (self, size):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        if len(self.datasets) == 1:
            self.dset.symbol_size = size
        else:
            self.after_property_changed()
        self.graph.unfreeze()
        
    def on_scolor_changed (self, col):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        if len(self.datasets) == 1:
            self.dset.symbol_color = col
        else:
            self.after_property_changed()
        self.graph.unfreeze()

    def on_sfill_changed (self, col):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        if len(self.datasets) == 1:
            self.dset.symbol_fill = col
        else:
            self.after_property_changed()
        self.graph.unfreeze()
        
    def on_ltype_changed (self, col):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        if len(self.datasets) == 1:
            self.dset.line_type = col
        else:
            self.after_property_changed()
        self.graph.unfreeze()
        
    def on_lstyle_changed (self, col):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        if len(self.datasets) == 1:
            self.dset.line_style = col
        else:
            self.after_property_changed()
        self.graph.unfreeze()
        
    def on_lwidth_changed (self, size):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        if len(self.datasets) == 1:
            self.dset.line_width = size
        else:
            self.after_property_changed()
        self.graph.unfreeze()

    def after_property_changed(self):
        if not self.check_if_datasets_selected(): return
        self.graph.freeze()
        self.on_checkbox_toggled ()
        self.graph.unfreeze()

class GraphAxesPanel(QVBox):
    def __init__(self, parent):
        QVBox.__init__(self, parent)

        QLabel('<b>X Axis</b>', self)
        f = QFrame(self)
        f.setFrameShape(QFrame.HLine)
        f.setFrameShadow(QFrame.Sunken)

        grid = QGrid(2, self)

        QLabel('Title', grid)
        self.xtitle = QLineEdit(grid)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        QLabel('From', grid)
        self.xfrom = QLineEdit(grid)

        QLabel('To', grid)
        self.xto = QLineEdit(grid)

        QLabel('Scale', grid)
        self.xscale = QComboBox(grid)
        self.xscale.insertItem('Linear')
        self.xscale.insertItem('Logarithmic')

        QLabel('<b>Y Axis</b>', self)
        f = QFrame(self)
        f.setFrameShape(QFrame.HLine)
        f.setFrameShadow(QFrame.Sunken)

        grid = QGrid(2, self)

        QLabel('Title', grid)
        self.ytitle = QLineEdit(grid)

        QLabel('From', grid)
        self.yfrom = QLineEdit(grid)

        QLabel('To', grid)
        self.yto = QLineEdit(grid)

        QLabel('Scale', grid)
        self.yscale = QComboBox(grid)
        self.yscale.insertItem('Linear')
        self.yscale.insertItem('Logarithmic')

        l = QLabel(self)
        l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.axisid = [QwtPlot.xBottom, QwtPlot.yLeft, QwtPlot.xTop, QwtPlot.yRight]

        self.connect(self.xscale,SIGNAL("activated(int)"),self.on_xscale_changed)
        self.connect(self.xfrom,SIGNAL("returnPressed()"),self.on_xfrom_changed)
        self.connect(self.xfrom,SIGNAL("lostFocus()"),self.on_xfrom_changed)
        self.connect(self.xto,SIGNAL("returnPressed()"),self.on_xto_changed)
        self.connect(self.xto,SIGNAL("lostFocus()"),self.on_xto_changed)
        self.connect(self.xtitle,SIGNAL("returnPressed()"),self.on_xtitle_changed)
        self.connect(self.xtitle,SIGNAL("lostFocus()"),self.on_xtitle_changed)

        self.connect(self.yscale,SIGNAL("activated(int)"),self.on_yscale_changed)
        self.connect(self.yfrom,SIGNAL("returnPressed()"),self.on_yfrom_changed)
        self.connect(self.yfrom,SIGNAL("lostFocus()"),self.on_yfrom_changed)
        self.connect(self.yto,SIGNAL("returnPressed()"),self.on_yto_changed)
        self.connect(self.yto,SIGNAL("lostFocus()"),self.on_yto_changed)
        self.connect(self.ytitle,SIGNAL("returnPressed()"),self.on_ytitle_changed)
        self.connect(self.ytitle,SIGNAL("lostFocus()"),self.on_ytitle_changed)


#----------------------------------------------------------------------------------------------------
# Data tab
#----------------------------------------------------------------------------------------------------
# Axis tab
    
    def open(self):
        self.graph = project.mainwin.active.graph

        self.xtitle.setText(self.graph.xaxis.title)
        self.xfrom.setText(str(self.graph.xaxis.min))
        self.xto.setText(str(self.graph.xaxis.max))
        self.xscale.setCurrentItem(int(self.graph.xaxis.logscale))

        self.ytitle.setText(self.graph.yaxis.title)
        self.yfrom.setText(str(self.graph.yaxis.min))
        self.yto.setText(str(self.graph.yaxis.max))
        self.yscale.setCurrentItem(int(self.graph.yaxis.logscale))

    def on_xscale_changed (self, scale): self.graph.xaxis.logscale = [False, True][scale]
    def on_xfrom_changed (self): self.graph.xaxis.min = float(str(self.xfrom.text()))
    def on_xto_changed (self): self.graph.xaxis.max = float(str(self.xto.text()))
    def on_xtitle_changed (self): self.graph.xaxis.title = str(self.xtitle.text())
    def on_yscale_changed (self, scale): self.graph.yaxis.logscale = [False, True][scale]
    def on_yfrom_changed (self): self.graph.yaxis.min = float(str(self.yfrom.text()))
    def on_yto_changed (self): self.graph.yaxis.max = float(str(self.yto.text()))
    def on_ytitle_changed (self): self.graph.yaxis.title = str(self.ytitle.text())
