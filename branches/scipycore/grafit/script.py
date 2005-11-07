import sys
sys.path.append('..')
import Image
import mingui as gui
# to get started with demo:
# - html widget
# - python code widget
# - tree widget

def on_item_activated(item):
    print item

def handler(*args, **kwds):
    print args, kwds

@gui.Command.from_function('callable', 'callit', 'close', type='check')
def callable(*args, **kwds):
    print 'called!'

class Panel(gui.Box):
    def __init__(self, place, position):
        self.pos = position
        if position in ['left', 'right']:
            orientation = 'vertical'
            tbo = 'horizontal'
        elif position in ['top', 'bottom']:
            orientation = 'horizontal'
            tbo = 'vertical'
        self.orientation = orientation

        gui.Box.__init__(self, place, tbo)
        self.contents = []
        self.toolbar = gui.Toolbar(self.place(stretch=0), orientation)
        print self.toolbar.size
        self.splitter = place[0]

    def _add(self, widget, image=None, **opts):
        if image is not None:
            self.contents.append(widget)
            widget._command = self.callback(widget)
            self.toolbar.append(widget._command)
        gui.Box._add(self, widget, **opts)
        if image is not None:
            self.layout.Hide(widget)

    def callback(self, widget):
        image = gui.base._text_img_wxbitmap('whatever', 
                                            gui.images.images['close'][16,16],
                                            rotate=self.orientation == 'vertical')
        @gui.Command.from_function('callable', 'callit', image, type='check')
        def callable(on):
            sz = self.toolbar.size[self.orientation=='horizontal']
            if on:
                for win in self.contents:
                    if win!=widget:
                        win._command.state = False
                self.layout.Show(widget)
                self.splitter.resize_child(self, 100+sz)
            else:
                self.layout.Hide(widget)
                self.splitter.resize_child(self, sz)
        return callable

def main():
    gui.images.register('close', Image.open('../data/images/close.png'))
    gui.images.register_dir('../data/images/')

    win = gui.Window(title='Mingui doc/demo', size=(640, 480))
    gui.base.app.mainwin = win
    box = gui.Box(win.place(), 'vertical')

    split = gui.Splitter(box.place(), 'vertical')

    panel = Panel(split.place(width=100), 'top')
    btn = gui.Button(panel.place(image='close'), 'arse')
    tree = gui.Tree(panel.place(image='open'), columns=['Topics'])
    root = gui.TreeNode()
    child = gui.TreeNode()
    root.append(child)
    tree.append(root)
    panel.toolbar.Realize()

    split2 = gui.Splitter(split.place(), 'horizontal')
    panel2 = Panel(split2.place(width=100), 'left')
    btn = gui.Button(panel2.place(image='close'), 'arse')
    panel2.toolbar.Realize()

    book = gui.Notebook(split2.place())
    html = gui.Html(book.place(label='text'))
    html.SetPage('html/index.html')
    code = gui.Text(book.place(label='code'), multiline=True, text='hello!')
    demo = gui.Box(book.place(label='demo'))

    button = gui.Button(demo.place(expand=False, stretch=0), 'button')
    toggle = gui.Button(demo.place(expand=False, stretch=0), 'button', toggle=True)
    toggle.connect('toggled', handler)
    toggle.connect('clicked', handler)

    bar = gui.Menubar(win.place())
    menu = gui.Menu(bar, 'Foo')
    menu.append(callable)

    toggle.text = 'aaa'


    def on_changed():
        split.resize_child(tree, 100)
        

    btn = gui.Button(box.place(stretch=0), 'Close', 
                     connect={'clicked': win.close})
    btn = gui.Button(box.place(stretch=0), 'Change', 
                     connect={'clicked': on_changed})

    gui.run(win)

if __name__ == '__main__':
    main()
