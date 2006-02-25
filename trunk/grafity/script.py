from grafity.signals import HasSignals
from grafity.actions import action_from_methods, action_from_methods2, StopAction, action_list
from grafity.project import Item, wrap_attribute, register_class, create_id

class Script(Item, HasSignals):
    def __init__(self, project, name=None, parent=None, location=None):
        Item.__init__(self, project, name, parent, location)

    default_name_prefix = 'script'
    text = wrap_attribute('text')

register_class(Script, 'scripts[name:S,id:S,parent:S,text:S]')
