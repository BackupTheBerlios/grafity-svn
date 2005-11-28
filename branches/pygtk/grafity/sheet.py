import pygtk
pygtk.require('2.0')
import gtk
import pango

import sys
sys.path.append('..')
import grafity

class Sheet(object):
    def __init__(self, worksheet):
        self.table = gtk.Table(2, 2, False)
        self.evtbox = gtk.EventBox()
        self.widget = gtk.Fixed()
        self.evtbox.add(self.widget)
        self.evtbox.show()
        self.widget.show()

        self.hadjust = gtk.Adjustment(3, 1, 10, 1, 2, 2)
        self.hadjust.connect('value_changed', self.adj_changed)
        self.hscroll = gtk.HScrollbar(self.hadjust)

        self.vadjust = gtk.Adjustment(3, 1, 10, 1, 2, 2)
        self.vadjust.connect('value_changed', self.adj_changed)
        self.vscroll = gtk.VScrollbar(self.vadjust)

        self.hscroll.show()
        self.vscroll.show()
        self.hadjust.set_value(6)

        print self.hadjust.lower, self.hadjust.upper

        self.table.attach(self.evtbox, 0, 1, 0, 1)
        self.table.attach(self.hscroll, 0, 1, 1, 2, gtk.FILL|gtk.EXPAND, 0)
        self.table.attach(self.vscroll, 1, 2, 0, 1, 0, gtk.FILL|gtk.EXPAND)
        self.table.show()

        self.mainwidget = self.table

        self.worksheet = worksheet
        self.firstrow = 3
        self.firstcol = 0

        self.CELL_HEIGHT = 20
        self.CELL_WIDTH = 70
        self.LHEADER = 70
        self.THEADER = 20

        self.wheat = self.widget.get_colormap().alloc_color("#d4cfca")
        self.linec = self.widget.get_colormap().alloc_color("#c7c7c7")
        self.lineh = self.widget.get_colormap().alloc_color("#c0b5a9")
        self.black = self.widget.get_colormap().alloc_color("black")
        self.white = self.widget.get_colormap().alloc_color("white")

        self.widget.set_events(gtk.gdk.EXPOSURE_MASK)
        self.widget.connect("configure_event", self.configure_event)
        self.widget.connect("expose_event", self.expose_event)

        self.evtbox.set_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.POINTER_MOTION_MASK)
        self.evtbox.connect("button_press_event", self.on_button_press_event)

        self.editor = gtk.Entry()
        self.editor.set_size_request(self.CELL_WIDTH, self.CELL_HEIGHT)
        self.widget.put(self.editor, 70, 80)

    def adj_changed(self, adjust):
        if adjust == self.hadjust:
            print 'h', adjust.value
        elif adjust == self.vadjust:
            print 'v', adjust.value

    def coord_to_cell(self, x, y):
        return (int(x - self.LHEADER)/self.CELL_WIDTH, 
                int(y - self.THEADER)/self.CELL_HEIGHT)

    def cell_origin(self, col, row):
        return (self.LHEADER + col*self.CELL_WIDTH,
                self.THEADER + row*self.CELL_HEIGHT)

    def on_button_press_event(self, widget, event):
        self.widget.move(self.editor, 
                         *self.cell_origin(*self.coord_to_cell(event.x, event.y)))
        self.editor.show()
        self.editor.grab_focus()


    def configure_event(self, widget, event):
        x, y, width, height = widget.get_allocation()
        return True

    def expose_event(self, widget, event):
        x, y, width, height = event.area
        _, _, totalw, totalh = widget.get_allocation()

        self.lastrow = int(totalh-self.CELL_HEIGHT)/self.CELL_HEIGHT + self.firstrow
        self.lastcol = min(int(totalw-self.CELL_WIDTH)/self.CELL_WIDTH+1 + self.firstcol, len(self.worksheet.columns))

        self.hadjust.lower = 0
#        self.hadjust.upper = (self.lastcol - self.firstcol)/float(len(self.worksheet.columns))
        self.hadjust.upper = 30
        self.hadjust.value = 21
        self.hadjust.emit('changed')

        gc = widget.get_style().fg_gc[gtk.STATE_NORMAL]

        gc.foreground = self.white
        widget.window.draw_rectangle(gc, True, x, y, width, height)
        pangolayout = widget.create_pango_layout("")
        pangolayout.set_alignment(pango.ALIGN_RIGHT)
        gc.foreground = self.lineh
        widget.window.draw_rectangle(gc, True, 0, 0,
                                     self.CELL_WIDTH, self.CELL_HEIGHT)
        # left header
        for i in range(1, self.lastrow):
            gc.foreground = self.wheat
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, 0, i*self.CELL_HEIGHT, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)
            gc.foreground = self.lineh
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False, 0, i*self.CELL_HEIGHT, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)

            gc.foreground = self.black
            pangolayout.set_text(str(i-1+self.firstrow))
            _, _, w, h  = pangolayout.get_pixel_extents()[1]
            widget.window.draw_layout(gc, (self.CELL_WIDTH-w)/2, 
                                          i*self.CELL_HEIGHT + (self.CELL_HEIGHT-h)/2, pangolayout)

        # top header
        for i in range(0, self.lastcol):
            gc.foreground = self.wheat
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, (i+1)*self.CELL_WIDTH, 0, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)
            gc.foreground = self.lineh
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False, (i+1)*self.CELL_WIDTH, 0, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)

            gc.foreground = self.black
            pangolayout.set_text(self.worksheet.column_names[i+self.firstcol])
            _, _, w, h  = pangolayout.get_pixel_extents()[1]
            widget.window.draw_layout(gc, (i+1)*self.CELL_WIDTH+(self.CELL_WIDTH-w)/2, 
                                          (self.CELL_HEIGHT-h)/2, pangolayout)

        # cells
        for col in range(0, self.lastcol):
            for line in range(0, self.lastrow):
                gc.foreground = self.linec
                gc.line_width = 1
                widget.window.draw_rectangle(gc, False, (col+1)*self.CELL_WIDTH, 
                                             (line+1)*self.CELL_HEIGHT, 
                                             self.CELL_WIDTH, self.CELL_HEIGHT)
                gc.foreground = self.black
                pangolayout.set_text(str(self.worksheet[col+self.firstcol][line+self.firstrow]).replace('nan', ''))
                _, _, w, h  = pangolayout.get_pixel_extents()[1]
                widget.window.draw_layout(gc, (col+1)*self.CELL_WIDTH + (self.CELL_WIDTH-w-5), 
                                          (line+1)*self.CELL_HEIGHT + (self.CELL_HEIGHT-h)/2, pangolayout)

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
    w.b = [2,4,5, 5.5]
    w.c = [3,2,1,3.3]

    sheet = Sheet(w)
    vbox.pack_start(sheet.mainwidget, True, True, 0)

    button = gtk.Button("Quit")
    vbox.pack_start(button, False, False, 0)
    button.connect_object("clicked", lambda w: w.destroy(), window)
    button.show()

    window.show()

    gtk.main()

    return 0

if __name__ == "__main__":
    main()
