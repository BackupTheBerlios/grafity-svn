import sys
import sets

from grafity import Worksheet, Folder

from grafity.graph_dataset import Style
from grafity.signals import HasSignals

from grafity.arrays import nan, isfinite, asarray
from grafity.util import flatten

from grafity.settings import DATADIR

import mingui as gui

class LegendModel(HasSignals):
    def __init__(self, graph):
        self.graph = graph
        self.graph.connect('add-dataset', self.on_modified)
        self.graph.connect('add-function', self.on_modified)
        self.graph.connect('remove-dataset', self.on_modified)
        self.graph.connect('shape-changed', self.on_modified)

    def on_modified(self, dataset=None):
        self.emit('modified')

    def get(self, row, column): return str(self[row])
    def get_image(self, row): 
        if hasattr(self[row], "_legend_wxbitmap"):
            return self[row]._legend_wxbitmap
        else:
            return 'folder'
    def __len__(self): return len(self.graph.datasets)
    def __getitem__(self, row): return self.graph.datasets[row]


class GraphView(gui.Box):
    def __init__(self, place, graph, **args):
        gui.Box.__init__(self, place, **args)
        self.graph = graph

    def setup(self):
        self.glwidget = self.find('gl-widget')

        #FIXME
        for grid in self.findall('grid*'):
            grid.layout.AddGrowableCol(2)
        for grid in self.findall('agrid*'):
            grid.layout.AddGrowableCol(1)

        self.graph.connect('redraw', self.glwidget.redraw)
        self.graph.connect('object-doubleclicked', self.on_object_doubleclicked)
        self.graph.connect('right-clicked', self.on_right_clicked)

        self.glwidget.connect('initialize-gl', self.graph.init)
        self.glwidget.connect('resize-gl', self.graph.reshape)
        self.glwidget.connect('paint-gl', self.graph.display)
        self.glwidget.connect('button-pressed', self.graph.button_press)
        self.glwidget.connect('button-released', self.graph.button_release)
        self.glwidget.connect('button-doubleclicked', self.graph.button_doubleclick)
        self.glwidget.connect('mouse-moved', self.graph.button_motion)
        self.glwidget.connect('key-down', self.graph.key_down)

        self.legend = self.find('legend')
        self.legend.data = LegendModel(self.graph)
        self.legend.connect('selection-changed', self.on_legend_select)

        self.style = self.find('style-panel')


    def __binit__(self, parent, graph, **place):
        gui.Box.__init__(self, parent, 'horizontal', **place)
        self.graph = graph

        tbbox = gui.Box(self, 'horizontal', stretch=0)

        def set_graph_mode(mode):
            def _set(): 
                self.graph.prev_mode = self.graph.mode
                self.graph.mode = mode

                import wx
                cur = {'arrow': wx.CURSOR_ARROW,
                       'hand': wx.CURSOR_HAND,
                       'zoom': wx.CURSOR_MAGNIFIER,
                       'range': wx.CURSOR_SIZEWE,
                       'd-reader': wx.CURSOR_CROSS,
                       's-reader': wx.CURSOR_CROSS,
                       'draw-text': wx.CURSOR_IBEAM,
                       'draw-line': wx.CURSOR_PENCIL,
                       'none': wx.CURSOR_NONE }[mode]
                self.glwidget.SetCursor(wx.StockCursor(cur))
                self.graph.emit('redraw')
            return _set

        graph.show()

        self.toolbar = gui.Toolbar(tbbox, orientation='vertical', stretch=1)
        self.toolbar.append(gui.Command('Arrow', '', set_graph_mode('arrow'), 'arrow.png', type='radio'))
        self.toolbar.append(gui.Command('Hand', '', set_graph_mode('hand'), 'hand.png', type='radio'))
        self.toolbar.append(gui.Command('Zoom', '', set_graph_mode('zoom'), 'zoom.png', type='radio'))
        self.toolbar.append(gui.Command('Range', '', set_graph_mode('range'), 'range.png', type='radio'))
        self.toolbar.append(gui.Command('Data reader', '', set_graph_mode('d-reader'), 'dreader.png', type='radio'))
        self.toolbar.append(gui.Command('Screen reader', '', set_graph_mode('s-reader'), 'sreader.png', type='radio'))
        self.toolbar.append(None)
        self.toolbar.append(gui.Command('Line', '', set_graph_mode('draw-line'), 'stock_draw-line.png'))
        self.toolbar.append(gui.Command('Text', '', set_graph_mode('draw-text'), 'stock_draw-text.png'))
        self.toolbar.append(None)
        self.toolbar.append(gui.Command('Select all datasets', '', self.on_selectall, 'stock_select-all.png'))


        self.toolbar.Realize()

#        self.closebar = gui.Toolbar(tbbox, stretch=0)
#        self.closebar.append(gui.Command('Close', 'Close this worksheet', 
#                                        self.on_close, 'close.png'))
#        self.closebar.Realize()

        self.panel = gui.MainPanel(self)
        self.box = gui.Splitter(self.panel, 'vertical', proportion=0.8)
        self.scrolled = gui.Scrolled(self.box)
        self.glwidget = gui.OpenGLWidget(self.scrolled)
        self.glwidget.min_size = (400, 200)


        self.graphdata = GraphDataPanel(self.graph, self, self.panel.right_panel, 
                                        page_label='Data', page_pixmap='worksheet.png')
        self.style = GraphStylePanel(self.graph, self, self.panel.right_panel, 
                                     page_label='Style', page_pixmap='style.png')
        self.axes = GraphAxesPanel(self.graph, self, self.panel.right_panel, 
                                   page_label='Axes', page_pixmap='axes.png')
        self.fit = GraphFunctionsPanel(self.graph.functions[0].func, self.graph, 
                                       self.panel.right_panel,
                                       page_label='Fit', page_pixmap='function.png')
        self.panel.right_panel.toolbar.Realize()

        self.graph.connect('request-cursor', self.on_request_cursor)

        self.object = self.graph
        self.graph.connect('rename', self.on_rename)
        self.legend.connect('right-click', self.on_legend_right_click)

    def on_legend_right_click(self, item):
        if item == -1:
            return
        item = self.legend.data[item]
        menu = gui.Menu()
        menu.append(gui.Command('Hide', '', object))
        menu.append(gui.Command('Show', '', object))
        menu.append(gui.Command('Show Only', '', object))
        menu.append(None)
        menu.append(gui.Command('Remove', '', object))
        menu.append(None)
        menu.append(gui.Command('Select All', '', object))
        self.legend.PopupMenu(menu._menu)

    def on_rename(self, name, item=None):
        self.parent.SetPageText(self.parent.pages.index(self), name)

    def on_selectall(self):
        self.legend.setsel(xrange(len(self.graph.datasets)))

    def on_object_doubleclicked(self, obj):
        from prop import Editor
        e = Editor(self, DATADIR+'/data/resources.xrc', obj)
        e.Show()

    def on_right_clicked(self, obj):
        print >>sys.stderr, obj
        menu = gui.Menu()
        menu.append(gui.Command('Delete', 'delete', object, 'open.png'))
        self.glwidget.parent.parent.PopupMenu(menu._menu)

    def on_request_cursor(self, cursor):
        import wx
        cur = {'arrow': wx.CURSOR_ARROW,
               'hand': wx.CURSOR_HAND,
               'zoom': wx.CURSOR_MAGNIFIER,
               'range': wx.CURSOR_SIZEWE,
               'd-reader': wx.CURSOR_CROSS,
               's-reader': wx.CURSOR_CROSS,
               'none': wx.CURSOR_NONE }[cursor]
        self.glwidget.SetCursor(wx.StockCursor(cur))

    def on_legend_select(self):
        self.style.on_legend_selection()

    def on_new_column(self):
        pass

    def on_close(self):
        self.glwidget.disconnect('initialize-gl', self.graph.init)
        self.glwidget.disconnect('resize-gl', self.graph.reshape)
        self.glwidget.disconnect('paint-gl', self.graph.display)

        self.glwidget.disconnect('button-pressed', self.graph.button_press)
        self.glwidget.disconnect('button-released', self.graph.button_release)
        self.glwidget.disconnect('mouse-moved', self.graph.button_motion)

        self.graph.disconnect('redraw', self.glwidget.redraw)

        self.parent.delete(self)


class GraphAxesPanel(gui.Box):
    def __cinit__(self, graph, view, parent, **place):
        gui.Box.__init__(self, parent, "vertical", **place)
        self.graph, self.view = graph, view

        xframe = gui.Frame(self, 'vertical', title='X axis', stretch=0.)
        grid = gui.Grid(xframe, 4, 2, expand=False)
        grid.layout.AddGrowableCol(1)
        gui.Label(grid, 'Title', pos=(0,0))
        self.x_title = gui.Text(grid, pos=(0,1))
        self.x_title.text = self.graph.xtitle
        self.x_title.connect(['enter', 'kill-focus'], self.on_x_title)
        gui.Label(grid, 'From', pos=(1,0))
        x_from = gui.Text(grid, pos=(1,1))
        gui.Label(grid, 'To', pos=(2,0))
        x_to = gui.Text(grid, pos=(2,1))
        gui.Label(grid, 'Type', pos=(3,0))
        x_type = self.x_type = gui.Choice(grid, pos=(3,1))
        x_type.append('Linear')
        x_type.append('Logarithmic')
        x_type.value = ['linear', 'log'].index(self.graph.xtype)
        x_type.connect('select', lambda value: self.on_set_xtype(value), True)

        yframe = gui.Frame(self, 'vertical', title='Y axis', stretch=0.)
        grid = gui.Grid(yframe, 4, 2, expand=False)
        grid.layout.AddGrowableCol(1)
        gui.Label(grid, 'Title', pos=(0,0))
        self.y_title = gui.Text(grid, pos=(0,1))
        self.y_title.text = self.graph.ytitle
        self.y_title.connect(['enter', 'kill-focus'], self.on_y_title)
        gui.Label(grid, 'From', pos=(1,0))
        y_from = gui.Text(grid, pos=(1,1))
        gui.Label(grid, 'To', pos=(2,0))
        y_to = gui.Text(grid, pos=(2,1))
        gui.Label(grid, 'Type', pos=(3,0))
        y_type = self.y_type = gui.Choice(grid, pos=(3,1))
        y_type.append('Linear')
        y_type.append('Logarithmic')
        y_type.value = ['linear', 'log'].index(self.graph.ytype)
        y_type.connect('select', lambda value: self.on_set_ytype(value), True)

        for w in [self.x_title, x_from, x_to, x_type, self.y_title, y_from, y_to, y_type]:
            w.min_size = (10, w.min_size[1])

    def on_x_title(self):
        self.graph.xtitle = self.x_title.text

    def on_y_title(self):
        self.graph.ytitle = self.y_title.text
        
    def on_set_xtype(self, value):
        self.graph.xtype = ['linear', 'log'][value]
        self.x_type.value = ['linear', 'log'].index(self.graph.xtype)

    def on_set_ytype(self, value):
        self.graph.ytype = ['linear', 'log'][value]
        self.y_type.value = ['linear', 'log'].index(self.graph.xtype)

###############################################################################
# style panel                                                                 #
###############################################################################

class GraphStylePanel(gui.Box):
    def setup(self):
        self.symbol = self.find('symbol')
        for symbol in Style.symbols:
            self.symbol.append(symbol+'.png')
        self.symbol.value = 0
        self.symbol.connect('select', lambda value: self.on_select_property('symbol', value), True)

        self.color = self.find('color')
        for color in Style.colors:
            self.color.append(self.color.create_colored_bitmap((20, 10), color))
        self.color.value = 0
        self.color.connect('select', lambda value: self.on_select_property('color', value), True)

        self.symbol_size = self.find('size')
        self.symbol_size.value = 5
        self.symbol_size.connect('modified', lambda value: self.on_select_property('symbol_size', value), True)

        self.line_type = self.find('line_type')
        for t in Style.line_types:
            self.line_type.append(t)
        self.line_type.value = 0
        self.line_type.connect('select', lambda value: self.on_select_property('line_type', value), True)

        self.line_style = self.find('line_style')
        for p in Style.line_styles:
            self.line_style.append(p)
        self.line_style.value = 0
        self.line_style.connect('select', lambda value: self.on_select_property('line_style', value), True)

        self.line_width = self.find('line_width')
        self.line_width.value = 1
        self.line_width.connect('modified', lambda value: self.on_select_property('line_width', value), True)

        self.settings = [self.symbol, self.color, self.symbol_size, 
                                 self.line_type, self.line_style, self.line_width]

        for widget in self.settings:
            widget.check = self.find('check:'+widget.name)
            widget.label = self.find('label:'+widget.name)

#        maxminw = max([w.label.GetBestSize()[0] for w in self.settings])
#
#        for widget in self.settings:
#            widget.check.connect('modified', lambda state, widget=widget: self.on_check(widget, state), True)
#            widget.label.min_size = (maxminw, widget.label.min_size[1])
#
        self.multi = self.find('multi')
        self.multi.value = 0
        self.multi.connect('select', self.on_select_multi)

        self.view = self.rfind('graph-view')
        self.graph = self.view.graph


    def on_legend_selection(self):
        datasets = [self.view.legend.data[i] for i in self.view.legend.selection]
        self.graph.selected_datasets = datasets

        if len(datasets) == 0:
            return

        style = datasets[0].style
        self.color.value = Style.colors.index(style.color)
        self.symbol.value = Style.symbols.index(style.symbol)
        self.symbol_size.value = style.symbol_size
        self.line_type.value = Style.line_types.index(style.line_type)
        self.line_style.value = Style.line_styles.index(style.line_style)
        self.line_width.value = style.line_width

        if len(datasets) > 1:
            if self.multi.value == 0: # identical
                self.show_checks(True)
                for control in self.settings:
                    control.check.state = len(set(getattr(d.style, control.name) 
                                              for d in datasets)) == 1
                    control.active = control.label.active = control.check.state

            elif self.multi.value == 1: # series
                self.show_checks(False)
                self.symbol_grid.layout.Show(self.color.check)
                self.symbol_grid.layout.Layout()

                for control in self.settings:
                    control.active = control.label.active = control.check.state = False

                colors = [Style.colors.index(d.style.color) for d in datasets]
                c0 = colors[0]
                self.color.check.state = colors == [c % len(Style.colors) for c in range(c0, c0+len(colors))]
                self.color.active = self.color.label.active = self.color.check.state
        else:
            for control in self.settings:
                control.active = control.label.active = True
            self.show_checks(False)

    def on_select_multi(self, sel):
        self.on_legend_selection()

    def on_check(self, widget, state):
        widget.active = state
        widget.label.active = state
        self.on_select_property(widget.name, widget.value)

    def show_checks(self, visible):
        for w in [self.symbol,self.color,self.symbol_size]:
            self.find('grid1').layout.Show(w.check, visible)
        for w in [self.line_type, self.line_style, self.line_width]:
            self.find('grid2').layout.Show(w.check, visible)
        self.find('grid1').layout.Layout()
        self.find('grid2').layout.Layout()

    def on_select_property(self, prop, value):
        datasets = [self.graph.datasets[s] for s in self.view.legend.selection]
        if len(datasets) == 1:
            setattr(datasets[0].style, prop, value)
        elif self.multi.value == 0:
            for d in datasets:
                setattr(d.style, prop, value)
        elif self.multi.value == 1:
            for i, d in enumerate(datasets):
                d.style.color = (value + i) % len(Style.colors)


###############################################################################
# data panel                                                                  #
###############################################################################

class WorksheetListModel(HasSignals):
    def __init__(self, folder):
        self.folder = folder
        self.update()
        self.folder.connect("modified", self.update)

    def update(self, item=None):
        self.contents = [self.folder.parent]*(self.folder!=self.folder.project.top) + \
                            [o for o in self.folder.contents() if isinstance(o, (Worksheet, Folder))]
        self.emit('modified')

    # ListModel protocol
    def get(self, row, column): 
        if self.contents[row] == self.folder.parent:
            return '../'
        return self.contents[row].name + '/'*isinstance(self.contents[row], Folder)
    def get_image(self, row): 
        obj = self.contents[row]
        if isinstance(obj, Worksheet):
            return 'worksheet'
        elif isinstance(obj, Folder):
            return ['folder', 'up'][obj == self.folder.parent]
    def __len__(self): return len(self.contents)
    def __getitem__(self, row):
        print row
        return self.contents[row]

class ColumnListModel(HasSignals):
    def __init__(self):
        self.colnames = []

    def set_worksheets(self, worksheets):
        if Folder in (type(w) for w in worksheets) or len(worksheets) == 0:
            self.colnames = []
        else:
            print worksheets
            self.colnames = list(reduce(set.intersection, (set(w.column_names) for w in worksheets)))
        if len(self.colnames) > 0:
            self.colnames.sort(lambda a, b: cmp(worksheets[0].column_names.index(a), worksheets[0].column_names.index(b)))
        self.emit('modified')

    def get(self, row, column): return self.colnames[row]
    def get_image(self, row): return None
    def __len__(self): return len(self.colnames)
    def __getitem__(self, row): return self.colnames[row]

class GraphDataPanel(gui.Box):
    def setup(self):
        self.view = self.rfind('graph-view')
        self.graph = self.view.graph
        self.project = self.graph.project
        self.folder = None

        self.worksheet_list = self.find('worksheet-list')
        self.worksheet_list.data = WorksheetListModel(self.project.top)
        self.worksheet_list.connect('selection-changed', self.on_wslist_select)
        self.worksheet_list.connect('item-activated', self.on_item_activated)

        self.x_list = self.find('x-list')
        self.x_list.data = ColumnListModel()
        self.y_list = self.find('y-list')
        self.y_list.data = ColumnListModel()

        self.view.commands['add-dataset'].connect('activated', self.on_add)
        self.view.commands['remove-dataset'].connect('activated', self.on_remove)

        
#        self.toolbar.append(gui.Command('Add', 'Add datasets to the graph', 
#                                       self.on_add, 'add.png'))
#        self.toolbar.append(gui.Command('Remove', 'Remove datasets from the graph', 
#                                       self.on_remove, 'remove.png'))
        
    def on_item_activated(self, obj):
        if isinstance(obj, Folder):
            self.worksheet_list.data = WorksheetListModel(obj)

    def on_wslist_select(self):
        selection = [self.worksheet_list.data[ind] for ind in self.worksheet_list.selection]
        self.x_list.data.set_worksheets(selection)
        self.y_list.data.set_worksheets(selection)

    def set_current_folder(self, folder):
        self.folder = folder
        self.worksheet_list.data = WorksheetListModel(folder)

    def on_add(self):
        for ws in self.worksheet_list.selection:
            worksheet = self.worksheet_list.data[ws]
            for x in self.x_list.selection:
                for y in self.y_list.selection:
                    self.graph.add(worksheet[self.x_list.data[x]], 
                                   worksheet[self.y_list.data[y]])

    def on_remove(self):
        for d in [self.graph.datasets[s] for s in self.view.legend.selection]:
            self.graph.remove(d)

from functions import *

def efloat(f):
    try:
        return float(f)
    except:
        return nan

class GraphFunctionsPanel(gui.Box):
    def __init__(self, func, graph, parent, **place):
        gui.Box.__init__(self, parent, 'vertical', **place)
        self.graph = graph
        self.toolbar = gui.Toolbar(self, stretch=0)

        self.scroll = gui.Scrolled(self)
        self.box = gui.Box(self.scroll, 'vertical')
        self.toolbar.append(gui.Command('Add term', '', self.do_add, 'function.png'))
        self.toolbar.append(gui.Command('Fit properties', '', self.do_configure, 'properties.png'))
        self.toolbar.append(gui.Command('Fit', '', self.do_fit, 'manibela.png'))
        self.toolbar.append(gui.Command('Save parameters', '', 
                            self.do_fit, 'pencil.png'))
        self.toolbar.Realize()

        self.set_function(func)

    def do_configure(self):
        from util import Bunch
        class fitoptions(Bunch, HasSignals):
            pass
        b = fitoptions(wsheet='', extra='', weighting=0, maxiter=50, sstol='0', partol='0')
        from prop import Editor
        e = Editor(self, DATADIR+'/data/resources.xrc', b)
        b.emit('modified')
        e.ShowModal()
        print b.__dict__


    def do_fit(self):
        data = self.graph.selected_datasets[0]
        lock = []
        for t in self.function.terms:
            for c in t._lock:
                lock.append(c.state)

        ind = data.active_data()

        self.function.fit(data.xx[ind], data.yy[ind], lock, 50)

#        for t in self.function.terms:
#            for i, txt in enumerate(t._text):
#                txt.text = str(t.parameters[i])
        self.function.emit('modified')

    def clear(self):
        pass

    def do_add(self):
        f = FunctionsWindow()
        f.connect('function-activated', self.on_function_activated)
        f.show()

    def set_function(self, f):
        self.function = f
        self.function.connect('add-term', self.on_add_term)
        self.function.connect('remove-term', self.on_remove_term)
        self.function.connect('modified', self.on_modified_f)
        self.clear()
        for term in self.function:
            self.on_add_term(term)

    def on_modified_f(self):
        for t in self.function.terms:
            for i, txt in enumerate(t._text):
                txt.text = str(t.parameters[i])

    def on_add_term(self, term):
        box = gui.Box(self.box, 'vertical', expand=True, stretch=0)
        bpx = gui.Box(box, 'horizontal', expand=True, stretch=0)
        term._butt = gui.Button(bpx, term.name, toggle=True)
        term._butt.connect('toggled', lambda on: self.on_toggled(term, on), True)
        term._butt.connect('double-clicked', lambda: self.on_btn_doubleclicked(term), True)
        t = gui.Toolbar(bpx, expand=False, stretch=0)
        term._act = gui.Command('x', '', lambda checked: self.on_use(term, checked), 'down.png', type='check')
        t.append(term._act)
        t.append(gui.Command('x', '', lambda: self.on_close(term), 'close.png'))
        t.Realize()
        term._box = box
        term._tx = None

        self.create_parambox(term)
        if sum((hasattr(t, '_butt') and t._butt.state) for t in self.function.terms) == 0:
            self.function.terms[0]._butt.state = True
            self.graph.selected_function = self.function.terms[0]

        term._act.state = True


    def on_btn_doubleclicked(self, term):
        if term._tx is None:
            term._tx = gui.Text(term._butt.parent.parent, align='center')

            term._tx.SetPosition(term._butt.GetPosition())
            term._tx.SetSize(term._butt.GetSize())

            term._tx.connect('enter', lambda: self.on_done(term), True)
            term._tx.connect('kill-focus', lambda: self.on_done(term), True)
            term._tx.min_size = (1,1)

        term._tx.show()
        term._tx.text = term.name
        term._tx.SetFocus()

    def on_done(self, term):
        if term._tx is None:
            return
        t = term._tx
        term._tx = None

        term.name = t.text
        t.Destroy()
        term._butt.text = term.name

    def on_toggled(self, term, on):
        if sum(t._butt.state for t in self.function.terms) == 0:
            term._butt.state = True
            self.graph.selected_function = term
        else:
            for t in self.function.terms:
                t._butt.state = False
            term._butt.state = True
            self.graph.selected_function = term

    def create_parambox(self, term):
        parambox = gui.Grid(term._box, len(term.parameters), 3, expand=True)
        parambox.layout.AddGrowableCol(1)
        term._text = []
        term._lock = []
        for n, par in enumerate(term.function.parameters):
            gui.Label(parambox, par, pos=(n, 0))
            text = gui.Text(parambox, pos=(n, 1))
            text.connect('character', lambda char: self.on_activate(term, n, char), True)
            text.connect('kill-focus', lambda: self.on_activate(term, n), True)
            text.text = str(term.parameters[n])
            term._text.append(text)
            lock = gui.Checkbox(parambox, pos=(n, 2))
            term._lock.append(lock)
        term._parambox = parambox

        self.updat()

    def on_activate(self, term, n, char=13):
        if char != 13:
            return
        for t in self.function.terms:
            t.parameters = [efloat(txt.text) for txt in t._text]
        self.function.emit('modified')

    def delete_parambox(self, term):
        term._parambox.Close()
        term._parambox.Destroy()
        term._parambox = None
        self.updat()
 
    def on_remove_term(self, term):
        term._box.Close()
        term._box.Destroy()
        self.updat()
        
    def on_function_activated(self, f):
        n = 0
        while 'f%d'%n in [t.name for t in self.function.terms]:
            n+= 1
        self.function.add(f.name, 'f%d'%n)

    def on_close(self, f):
        self.function.remove(self.function.terms.index(f))
        if len(self.function.terms) != 0 and sum(t._butt.state for t in self.function.terms) == 0:
            self.function.terms[0]._butt.state = True
            self.graph.selected_function = self.function.terms[0]

    def on_use(self, f, isit):
        if isit:
            if f._parambox is None:
                self.create_parambox(f)
        else:
            self.delete_parambox(f)
        f.enabled = isit
        self.updat()
        self.function.emit('modified')

    def updat(self):
        s = self.parent.GetSize()
        self.parent._widget.SetSize((s[0]+1, s[1]))
        self.parent._widget.SetSize(s)
