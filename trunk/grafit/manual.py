import sys

import mingui as gui
from signals import HasSignals

import cElementTree as et

class ElementTreeNode(HasSignals):
    """Adapter from an Element to a Tree node"""
    def __init__(self, elem, isroot=False):
        self.element = elem

    def __iter__(self):
        for item in self.element:
            yield ElementTreeNode(item)
    
    def __str__(self): return self.element.tag
    def get_pixmap(self): return '16/folder.png'

def main():
    gui.xml.merge('grafit.mgx')
    win = gui.xml.build('mainwin')

    tree = win.find('tree')
    r = ElementTreeNode(et.parse('gui.xml').getroot())
    tree.append(r)

    def hello():
        print 'hello'

    gui.commands['file-new'].connect('activated', hello)
    win.find('bouton').connect('clicked', hello)
    win.find('html').LoadPage('test.html')

    gui.run(win)

if __name__ == '__main__':
    main()
