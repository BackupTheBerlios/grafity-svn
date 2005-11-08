import sys
sys.path.append('..')
import Image
import mingui as gui
# to get started with demo:
# - html widget
# - python code widget
# - tree widget

def handler(*args, **kwds):
    print args, kwds

@gui.Command.from_function('callable', 'callit', 'close', type='check')
def callable(*args, **kwds):
    print 'called!'

[gui.Window, dict(title='Mingui doc/demo', size=(640, 480)),
    [{}, gui.Box, dict(orientation='vertical'),
        
    ],
]

def main():
    gui.images.register_dir('../data/images/')

    win = gui.Window(title='Mingui doc/demo', size=(640, 480))
    gui.base.app.mainwin = win

    box = gui.Box(win(), 'vertical')
    split = gui.Splitter(box(), 'vertical')

    panel = gui.Panel(split(width=100), 'top')
    btn = gui.Button(panel(image='close'), 'arse')
    tree = gui.Tree(panel(image='open'), columns=['Topics'])
    root = gui.TreeNode()
    tree.append(root)
    child = gui.TreeNode(root)

    panel.toolbar.Realize()

    split2 = gui.Splitter(split(), 'horizontal')
    panel2 = gui.Panel(split2(width=100), 'left')
    btn = gui.Button(panel2(image='close'), 'arse')
    panel2.toolbar.Realize()

    book = gui.Notebook(split2())
    html = gui.Html(book(label='text'))
    html.SetPage(file('test.html').read())
    code = gui.Text(book(label='code'), multiline=True, text='hello!')
    demo = gui.Box(book(label='demo'))

    button = gui.Button(demo(expand=False, stretch=0), 'button')
    toggle = gui.Button(demo(expand=False, stretch=0), 'button', toggle=True,
                        connect={'toggled': handler, 'clicked':handler})

    bar = gui.Menubar(win())
    menu = gui.Menu(bar, 'Foo')
    menu.append(callable)

    toggle.text = 'aaa'


    def on_changed():
        split.resize_child(panel, 100)
        

    btn = gui.Button(box(stretch=0), 'Close', 
                     connect={'clicked': win.close})
    btn = gui.Button(box(stretch=0), 'Change', 
                     connect={'clicked': on_changed})

    gui.run(win)

if __name__ == '__main__':
    main()
