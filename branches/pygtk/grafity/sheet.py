import pygtk
pygtk.require('2.0')
import gtk

import sys
sys.path.append('..')
import grafity


#class Sheet(gtk.DrawingArea):
class Sheet(object):
    def __init__(self, worksheet):
#        gtk.DrawingArea.__init__(self, *args, **kwds)
        self.evtbox = gtk.EventBox()
        self.widget = gtk.Fixed()
        self.evtbox.add(self.widget)
        self.evtbox.show()
        self.widget.show()

        self.worksheet = worksheet
        self.firstrow = 0
        self.firstcol = 0

        self.CELL_HEIGHT = 20
        self.CELL_WIDTH = 70

        self.wheat = self.widget.get_colormap().alloc_color("#cdc7b0")
        self.linec = self.widget.get_colormap().alloc_color("#c7c7c7")
        self.lineh = self.widget.get_colormap().alloc_color("#c3bd98")
        self.black = self.widget.get_colormap().alloc_color("black")
        self.white = self.widget.get_colormap().alloc_color("white")

        self.widget.set_events(gtk.gdk.EXPOSURE_MASK)
        self.widget.connect("configure_event", self.configure_event)
        self.widget.connect("expose_event", self.expose_event)

        self.evtbox.set_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.POINTER_MOTION_MASK)

        def motion_notify(widget, event):
            self.editor.show()
            self.editor.grab_focus()
            print event.x - 70

        self.evtbox.connect("button_press_event", motion_notify)

        self.editor = gtk.Entry()
        self.editor.set_size_request(self.CELL_WIDTH, self.CELL_HEIGHT)

        self.widget.put(self.editor, 70, 80)

    def configure_event(self, widget, event):
        x, y, width, height = widget.get_allocation()
        return True

    def expose_event(self, widget, event):
        x, y, width, height = event.area
        _, _, totalw, totalh = widget.get_allocation()

        gc = widget.get_style().fg_gc[gtk.STATE_NORMAL]

        gc.foreground = self.white
        widget.window.draw_rectangle(gc, True, x, y, width, height)
        pangolayout = widget.create_pango_layout("")
        nlines = 10

        # left header
        for i in range(1, nlines+1):
            gc.foreground = self.wheat
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, 0, i*self.CELL_HEIGHT, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)
            gc.foreground = self.lineh
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False, 0, i*self.CELL_HEIGHT, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)

            gc.foreground = self.black
            pangolayout.set_text(str(i-1))
            widget.window.draw_layout(gc, 0, i*self.CELL_HEIGHT, pangolayout)

        # top header
        for i in range(0, len(self.worksheet.columns)):
            gc.foreground = self.wheat
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, (i+1)*self.CELL_WIDTH, 0, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)
            gc.foreground = self.lineh
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False, (i+1)*self.CELL_WIDTH, 0, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)

            gc.foreground = self.black
            pangolayout.set_text(self.worksheet.column_names[i])
            widget.window.draw_layout(gc, (i+1)*self.CELL_WIDTH, 0, pangolayout)

        # cells
        for col in range(0, len(self.worksheet.columns)):
            for line in range(0, nlines):
                gc.foreground = self.linec
                gc.line_width = 1
                widget.window.draw_rectangle(gc, False, (col+1)*self.CELL_WIDTH, 
                                             (line+1)*self.CELL_HEIGHT, 
                                             self.CELL_WIDTH, self.CELL_HEIGHT)
                gc.foreground = self.black
                pangolayout.set_text(str(self.worksheet[col][line]).replace('nan', ''))
                widget.window.draw_layout(gc, (col+1)*self.CELL_WIDTH, 
                                          (line+1)*self.CELL_HEIGHT, pangolayout)

        gc.foreground = self.black
        gc.line_width = 1
        return False


def main():
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_name ("Test Input")
    window.connect("destroy", lambda w: gtk.main_quit())

    vbox = gtk.VBox(False, 0)
    window.add(vbox)
    vbox.show()

    p = grafity.Project()
    w = p.new(grafity.Worksheet, 'test')
    w.a = [1,2,3]*1000
    w.b = [2,4,5]
    w.c = [3,2,1]

    sheet = Sheet(w)
    sheet.evtbox.set_size_request(200, 200)
    vbox.pack_start(sheet.evtbox, True, True, 0)
    sheet.evtbox.show()

    button = gtk.Button("Quit")
    vbox.pack_start(button, False, False, 0)
    button.connect_object("clicked", lambda w: w.destroy(), window)
    button.show()

    window.show()

    gtk.main()

    return 0

if __name__ == "__main__":
    main()
