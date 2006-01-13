import sys

import gtk
import pango
import numarray

sys.path.append('..')
import grafity


class Sheet(gtk.Table):
    def __init__(self, worksheet):
        self.worksheet = worksheet

        gtk.Table.__init__(self, 2, 2, False)

        self.table = self
        self.evtbox = gtk.EventBox()
        self.widget = gtk.Fixed()
        self.evtbox.add(self.widget)
        self.evtbox.show()
        self.widget.show()

        self.hadjust = gtk.Adjustment(3, 1, 10, 1, 70, 350)
        self.hadjust.connect('value_changed', self.on_adjustment_changed)
        self.hscroll = gtk.HScrollbar(self.hadjust)
        self.vadjust = gtk.Adjustment(3, 1, 10, 1, 20, 200)
        self.vadjust.connect('value_changed', self.on_adjustment_changed)
        self.vscroll = gtk.VScrollbar(self.vadjust)
        self.hscroll.show()
        self.vscroll.show()

        self.table.attach(self.evtbox, 0, 1, 0, 1)
        self.table.attach(self.hscroll, 0, 1, 1, 2, gtk.FILL|gtk.EXPAND, 0)
        self.table.attach(self.vscroll, 1, 2, 0, 1, 0, gtk.FILL|gtk.EXPAND)
        self.table.show()

        self.editor = gtk.Entry()
        self.editor.connect('activate', self.on_entry_activate)
        self.widget.put(self.editor, 0, 0)

        
        # colors
        alloc_color = self.widget.get_colormap().alloc_color
        self.header_fg = alloc_color("#d4cfca")
        self.linec = alloc_color("#c7c7c7")
        self.header_line = alloc_color("#c0b5a9")
        self.black = alloc_color("black")
        self.white = alloc_color("white")
        self.sel_bg = alloc_color("#e6e6fa")
        self.sel_header = alloc_color("#b9b38f")

        # connect events
        self.widget.set_events(gtk.gdk.EXPOSURE_MASK)
        self.widget.connect("configure_event", self.configure_event)
        self.widget.connect("expose_event", self.expose_event)
        self.widget.connect("size_allocate", self.on_resize)

        self.evtbox.set_events(gtk.gdk.BUTTON_PRESS_MASK |
                               gtk.gdk.BUTTON_RELEASE_MASK | 
                               gtk.gdk.POINTER_MOTION_MASK |
                               gtk.gdk.KEY_PRESS_MASK)
        self.evtbox.connect("button_press_event", self.on_button_press_event)
        self.evtbox.connect("button_release_event", self.on_button_release_event)
        self.evtbox.connect("motion_notify_event", self.on_motion_notify_event)
        self.evtbox.connect_after("key_press_event", self.on_key_press_event)
        self.evtbox.set_flags(gtk.CAN_FOCUS)

        self.column_widths = {}
        self.row_height = 20
        self.left_header = 80
        self.top_header = 20

        for i, c in enumerate(self.worksheet.columns):
            self.column_widths[c] = 40 + i*20

        self.update_widths()

        self.firstrow = 0
        self.firstcol = 0

        self.originx = 0
        self.originy = 0

        self.resizing_column = None
        self.dragging_selection = False
        self.active_cell = (0, 0)
        self.selection = (0, 0, 1, 1)
        self.edit_cell = None

    def on_entry_activate(self, entry):
        col, row = self.edit_cell
        self.worksheet[col][row] = float(entry.get_text())
        entry.hide()
        self.evtbox.grab_focus()
        self.edit_cell = None

    def on_key_press_event(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        print "Key %s (%d) was pressed" % (keyname, event.keyval)
        return False

    def on_button_press_event(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            col, row = self.coord_to_cell(event.x, event.y)
            x, y = self.cell_origin(col, row)
            self.widget.move(self.editor, x, y)
            self.editor.set_size_request(self.left_header + self.sumwidths[col]-x, self.row_height)
            self.editor.set_text(str(self.worksheet[col][row]).replace('nan', ''))
            self.editor.show()
            self.editor.grab_focus()
            self.edit_cell = (col, row)
        else:
            self.editor.hide()
            self.evtbox.grab_focus()
            self.edit_cell = None
            for i, w, c in zip(range(self.worksheet.ncolumns), self.sumwidths, self.worksheet.columns):
                if w-3 < event.x-self.left_header < w+3 and event.y < self.top_header:
                    self.resizing_column = i
                    break
            else:
                self.resizing_column = None
                cell = self.coord_to_cell(event.x, event.y)
                self.selection = (cell[0], cell[1], cell[0]+1, cell[1]+1)
                self.widget.queue_draw()
                self.dragging_selection = True

    def on_button_release_event(self, widget, event):
        self.resizing_column = None
        self.dragging_selection = False

    def on_motion_notify_event(self, widget, event):
        if self.dragging_selection:
            cell = self.coord_to_cell(event.x, event.y)
            selection = (self.selection[0], self.selection[1], cell[0]+1, cell[1]+1)
            if self.selection != selection:
                self.selection = selection
                self.widget.queue_draw()
            
        elif self.resizing_column is None:
            for i, w, c in zip(range(self.worksheet.ncolumns), self.sumwidths, self.worksheet.columns):
                if w-2 < event.x-self.left_header < w+2 and event.y < self.top_header:
                    watch = gtk.gdk.Cursor(gtk.gdk.SB_H_DOUBLE_ARROW)
                    self.widget.window.set_cursor(watch)
                    break
            else:
                watch = gtk.gdk.Cursor(gtk.gdk.ARROW)
                self.widget.window.set_cursor(watch)
        else:
            start = ([0] + list(self.sumwidths[:-1]))[self.resizing_column]
            width = max(event.x - start - self.left_header, 50)
            self.column_widths[self.worksheet.columns[self.resizing_column]] = width
            self.widget.queue_draw_area(*self.widget.get_allocation())
           

    def update_widths(self):
        self.widths = list(self.column_widths[c] for c in self.worksheet.columns)
        self.sumwidths = numarray.cumsum(self.widths)

    def on_resize(self, widget, allocation):
        """called when the window is resized"""
        pass

    def on_adjustment_changed(self, adjust):
        """called when one of the scrollbars is changed"""
        if adjust == self.hadjust:
            if self.originx != int(adjust.value):
                self.originx = int(adjust.value)
                self.widget.queue_draw()
        elif adjust == self.vadjust:
            if self.originy != int(adjust.value):
                self.originy = int(adjust.value)
                self.widget.queue_draw()

    def coord_to_cell(self, x, y):
        """Find the cell where the point (x,y) is located"""
        try:
            col = list((self.left_header - self.originx + self.sumwidths)>x).index(1)
        except ValueError:
            col = self.worksheet.ncolumns
        row = max(int(y + self.originy - self.top_header)/self.row_height, 0)
        return col, row

    def cell_origin(self, col, row):
        """The coordinates of the top left corner of the cell (col,row)""" 
        col_start = [0] + list(self.sumwidths)
        return (self.left_header + col_start[col] - self.originx,
                self.top_header + row*self.row_height - self.originy)

    def configure_event(self, widget, event):
        return True

    def expose_event(self, widget, event):
        x, y, width, height = event.area
        _, _, totalw, totalh = self.widget.get_allocation()

        self.update_widths()

        if totalw-self.left_header > self.sumwidths[-1] - self.originx and self.originx>0:
            self.originx = max(self.left_header + self.sumwidths[-1] - totalw, 0)

        self.firstcol, self.firstrow = self.coord_to_cell(0,0)
        self.lastcol, self.lastrow = self.coord_to_cell(totalw,totalh)
        self.lastcol = min(self.lastcol + 1, self.worksheet.ncolumns)
        self.lastrow += 1

        # adjustments
        self.hadjust.lower = 0
        self.hadjust.upper = self.sumwidths[-1]
        self.hadjust.value = self.originx
        self.hadjust.page_size = min(totalw - self.left_header, self.sumwidths[-1])

        self.vadjust.lower = 0
        self.vadjust.upper = self.worksheet.nrows*self.row_height
        self.vadjust.value = self.originy
        self.vadjust.page_size = min(totalh - self.row_height, self.worksheet.nrows*self.row_height)

        self.hadjust.emit('changed')
        self.vadjust.emit('changed')

        # draw stuff
        gc = widget.get_style().fg_gc[gtk.STATE_NORMAL]
        gc.foreground = self.white

        widget.window.draw_rectangle(gc, True, x, y, width, height)
        pangolayout = widget.create_pango_layout("")
        pangolayout.set_alignment(pango.ALIGN_RIGHT)

        col_start = [0] + list(self.sumwidths)

        # selection
        gc.line_width = 1
        cfrom, rfrom, cto, rto = self.selection
        xs = int(col_start[cfrom] + self.left_header - self.originx)
        xe = int(col_start[cto] + self.left_header - self.originx)
        ys = int(self.top_header + rfrom * self.row_height - self.originy)
        ye = int(self.top_header + rto * self.row_height - self.originy)

        gc.foreground = self.sel_bg
        widget.window.draw_rectangle(gc, True, xs, ys, xe-xs, ye-ys)

        gc.foreground = self.black
#        widget.window.draw_rectangle(gc, False, xs-1, ys-1, xe-xs+2, ye-ys+2)
        widget.window.draw_rectangle(gc, False, xs+1, ys+1, xe-xs-2, ye-ys-2)
#        gc.foreground = self.white
        widget.window.draw_rectangle(gc, False, xs, ys, xe-xs, ye-ys)


        # cells
        for col in range(self.firstcol, self.lastcol):
            for line in range(self.firstrow, self.lastrow):
                gc.foreground = self.linec
                gc.line_width = 1
                x = int(col_start[col] + self.left_header - self.originx)
                y = int(self.top_header + line * self.row_height - self.originy)
                widget.window.draw_rectangle(gc, False, x, y, int(self.widths[col]), self.row_height)

                gc.foreground = self.black
                pangolayout.set_text(str(self.worksheet[col][line]).replace('nan', ''))
                _, _, w, h  = pangolayout.get_pixel_extents()[1]
                widget.window.draw_layout(gc, int(x + self.widths[col]-w-5), y + (self.row_height-h)/2, pangolayout)

        # left header
        for row in range(self.firstrow, self.lastrow):
            if row in range(self.selection[1], self.selection[3]):
                gc.foreground = self.sel_header
                fmt = "<b>%s</b>"
            else:
                gc.foreground = self.header_fg
                fmt = "%s"
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, 
                                         0, self.top_header + row * self.row_height - self.originy, 
                                         self.left_header, self.row_height)

            gc.foreground = self.header_line
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False,
                                         0, self.top_header + row * self.row_height - self.originy, 
                                         self.left_header, self.row_height)

            gc.foreground = self.black
            pangolayout.set_markup(fmt % str(row))
            _, _, w, h  = pangolayout.get_pixel_extents()[1]
            widget.window.draw_layout(gc, 
                                      int((self.left_header-w)/2),
                                      int(self.top_header + row*self.row_height - self.originy + (self.row_height-h)/2), 
                                      pangolayout)

        # top header
        for col in range(self.firstcol, self.lastcol):
            if col in range(self.selection[0], self.selection[2]):
                gc.foreground = self.sel_header
                fmt = "<b>%s</b>"
            else:
                gc.foreground = self.header_fg
                fmt = "%s"
            gc.line_width = 1
            widget.window.draw_rectangle(gc, True, 
                                         int(self.left_header + col_start[col]-self.originx), 0,
                                         int(self.widths[col]), self.top_header)

            gc.foreground = self.header_line
            gc.line_width = 2
            widget.window.draw_rectangle(gc, False,
                                         int(self.left_header + col_start[col]-self.originx), 0,
                                         int(self.widths[col]), self.top_header)

            gc.foreground = self.black
            pangolayout.set_markup(fmt % self.worksheet.column_names[col])
            _, _, w, h  = pangolayout.get_pixel_extents()[1]
            widget.window.draw_layout(gc, int(self.left_header + col_start[col] - self.originx + (self.widths[col]-w)/2),
                                          int((self.row_height-h)/2), pangolayout)

        gc.foreground = self.header_line
        widget.window.draw_rectangle(gc, True, 0, 0,
                                     self.left_header, self.top_header)


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
    w.a = numarray.arange(1000)
    w.b = [2,4,5, 5.5]
    w.c = [3,2,1,3.3]
    w.d = 2*w.a
    w.e = w.b * w.c

    sheet = Sheet(w)
    vbox.pack_start(sheet, True, True, 0)

#    button = gtk.Button("Quit")
#    vbox.pack_start(button, False, False, 0)
#    button.connect_object("clicked", lambda w: w.destroy(), window)
#    button.show()

    window.show()

    gtk.main()

    return 0

if __name__ == "__main__":
    main()
