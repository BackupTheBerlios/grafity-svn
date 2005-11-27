import gtk
import gtk.glade

#import sys
#sys.path.append('..')
#import grafity

class Widgets(object):
    def __init__(self):
        self.widgets = gtk.glade.XML("grafity.glade")
        signals = { "on_entry1_activate" : self.on_entry1_activate,
                    "on_quit1_activate" : self.on_quit1_activate}
        self.widgets.signal_autoconnect(signals)
        
    def on_entry1_activate(self, widget):
        self.mozillaWidget.load_url(widget.get_text())
        
    def on_quit1_activate(self, widget):
        gtk.main_quit()
        
if __name__ == "__main__":
    widgets = Widgets()
    gtk.main()
