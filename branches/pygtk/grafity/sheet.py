import pygtk
pygtk.require('2.0')
import gtk

import sys
sys.path.append('..')
import grafity


#class Sheet(gtk.DrawingArea):
class Sheet(gtk.Fixed):
    def __init__(self, worksheet, *args, **kwds):
#        gtk.DrawingArea.__init__(self, *args, **kwds)
        gtk.Fixed.__init__(self, *args, **kwds)

        self.worksheet = worksheet
        self.firstrow = 0
        self.firstcol = 0

        self.CELL_HEIGHT = 20
        self.CELL_WIDTH = 70

        self.wheat = self.get_colormap().alloc_color("#cdc7b0")
        self.linec = self.get_colormap().alloc_color("#c7c7c7")
        self.lineh = self.get_colormap().alloc_color("#c3bd98")
        self.black = self.get_colormap().alloc_color("black")
        self.white = self.get_colormap().alloc_color("white")

        self.set_events(gtk.gdk.EXPOSURE_MASK
                        | gtk.gdk.LEAVE_NOTIFY_MASK
                        | gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.POINTER_MOTION_HINT_MASK)


        self.connect("configure_event", self.configure_event)
        self.connect("expose_event", self.expose_event)

 
        
    def configure_event(self, widget, event):
        x, y, width, height = widget.get_allocation()
        return True

    def expose_event(self, widget, event):
        x, y, width, height = event.area
        _, _, totalw, totalh = self.get_allocation()

        gc = widget.get_style().fg_gc[gtk.STATE_NORMAL]

        gc.foreground = self.white
        widget.window.draw_rectangle(gc, True, x, y, width, height)
        pangolayout = widget.create_pango_layout("")
        nlines = 10

        # left header
        for i in range(1, nlines+1):
            gc.foreground = widget.wheat
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, 0, i*self.CELL_HEIGHT, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)
            gc.foreground = widget.lineh
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False, 0, i*self.CELL_HEIGHT, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)

            gc.foreground = widget.black
            pangolayout.set_text(str(i-1))
            widget.window.draw_layout(gc, 0, i*self.CELL_HEIGHT, pangolayout)

        # top header
        for i in range(0, len(self.worksheet.columns)):
            gc.foreground = widget.wheat
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, (i+1)*self.CELL_WIDTH, 0, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)
            gc.foreground = widget.lineh
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False, (i+1)*self.CELL_WIDTH, 0, 
                                         self.CELL_WIDTH, self.CELL_HEIGHT)

            gc.foreground = widget.black
            pangolayout.set_text(self.worksheet.column_names[i])
            widget.window.draw_layout(gc, (i+1)*self.CELL_WIDTH, 0, pangolayout)

        # cells
        for col in range(0, len(self.worksheet.columns)):
            for line in range(0, nlines):
                gc.foreground = widget.linec
                gc.line_width = 1
                widget.window.draw_rectangle(gc, False, (col+1)*self.CELL_WIDTH, 
                                             (line+1)*self.CELL_HEIGHT, 
                                             self.CELL_WIDTH, self.CELL_HEIGHT)
                gc.foreground = widget.black
                pangolayout.set_text(str(self.worksheet[col][line]).replace('nan', ''))
                widget.window.draw_layout(gc, (col+1)*self.CELL_WIDTH, 
                                          (line+1)*self.CELL_HEIGHT, pangolayout)

        gc.foreground = widget.black
        gc.line_width = 1
        return False


def main():
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_name ("Test Input")

    vbox = gtk.VBox(False, 0)
    window.add(vbox)

    window.connect("destroy", lambda w: gtk.main_quit())

    # Create the drawing area
    p = grafity.Project()
    w = p.new(grafity.Worksheet, 'test')
    w.a = [1,2,3]
    w.b = [2,4,5]
    w.c = [3,2,1]
    sheet = Sheet(w)

    sheet.b = b = gtk.Entry()

#    b.connect_object("clicked", lambda b: b.destroy(), b)

    self = sheet

    sheet.set_size_request(200, 200)
    sheet.put(b, 70, 70)

    evtbox = gtk.EventBox()
    evtbox.add(sheet)
    vbox.pack_start(evtbox, True, True, 0)

    # .. And a quit button
    button = gtk.Button("Quit")
    vbox.pack_start(button, False, False, 0)

    button.connect_object("clicked", lambda w: w.destroy(), window)

    evtbox.set_events(gtk.gdk.EXPOSURE_MASK
                    | gtk.gdk.LEAVE_NOTIFY_MASK
                    | gtk.gdk.BUTTON_PRESS_MASK
                    | gtk.gdk.POINTER_MOTION_MASK
                    | gtk.gdk.POINTER_MOTION_HINT_MASK)
    def motion_notify(widget, event):
        print >>sys.stderr, "button_press_event", event
    evtbox.connect("button_press_event", motion_notify)

    window.show_all()

    gtk.main()

    return 0

if __name__ == "__main__":
    main()
