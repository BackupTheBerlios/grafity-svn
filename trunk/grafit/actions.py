"""
Action / Undo framework
"""

import signals
import sys

class NoMoreActionsError(Exception):
    pass

class Action(signals.HasSignals):
    """
    Abstract base class for actions.
    
    Derived classes must override do() and undo(), and optionally combine().

    do() and undo() are replaced with wrappers that emit the appropriate signal.
    One can use actions in a one-liner like:

    FooAction(param1, param2).do_and_register()
    """

    def __init__(self):
        self.done = False
    
    def do(self):
        """
        Do whatever the action does.
        This automatically emits 'done'.
        """
        raise NotImplementedError

    def undo(self):
        """
        Undo whatever the action does.
        This automatically emits 'undone'.
        """
        raise NotImplementedError

    def do_and_register(self):
        """Shorthand for action.do(); action_register()."""
        ret = self.do()
        self.register()
        return ret

    def combine(self, action):
        """
        Merge `action` into self. 
        Returns True if succesful, False if a combination is not possible
        """
        return False

    def register(self):
        """Add the action to the global action list."""
        action_list.add(self)

    def _do_wrapper(self):
        """Wraps the `do` method emitting `done`"""
        ret = self.real_do()
        self.done = True
        self.emit('done')
        return ret

    def _undo_wrapper(self):
        """Wraps the `undo` method emitting `undone`"""
        ret = self.real_undo()
        self.done = False
        self.emit('undone')
        return ret

    class __metaclass__(type):
        def __init__(cls, name, bases, dct):
            # replace 'do' and 'undo' by their wrappers
            cls.real_do, cls.do  = cls.do, cls._do_wrapper
            cls.real_undo, cls.undo  = cls.undo, cls._undo_wrapper

    def __str__(self):
        return self.__class__.__name__


class CompositeAction(Action):
    """A series of actions treated as a single action."""
    def __init__(self):
        Action.__init__(self)
        self.actionlist = []

    def add(self, action):
        """Add a action to the list."""
        if len(self.actionlist) == 0:
            self.actionlist.append(action)
            return
        elif self.actionlist[-1].combine(action):
            pass
        else:
            self.actionlist.append(action)

    def do(self):
        for com in self.actionlist:
            com.real_do()

    def undo(self):
        for com in self.actionlist[::-1]:
            com.real_undo()


class ActionList(signals.HasSignals):
    """A action list, implementing undo/redo."""

    def __init__(self):
        self.actions = []
        self.composite =  None
        self.enabled = True

    def add(self, action):
        """Add a action to the list."""
        if not self.enabled:
            return 

        while len(self.actions) > 0 and not self.actions[-1].done:
            self.pop()

        if self.composite is not None:
            self.composite.add(action)
        else:
            if len(self.actions) == 0:
                self.actions.append(action)
            elif self.actions[-1].combine(action):
                pass
            else:
                self.actions.append(action)
#            print >>sys.stderr, 'X', action
            self.emit('added', action=action)

    def pop(self):
        """Remove the last action from the list."""
        if not self.enabled:
            return
        com = self.actions.pop()
        self.emit('removed', action=com)

    def clear(self):
        """Empty the list."""
        while self.actions != []:
            self.pop()

    def redo(self):
        """Redo the last action that was undone."""
        com = False
        for com in self.actions:
            if not com.done:
                break
        if com and not com.done:
            e = self.enabled
            self.disable()
            try:
                com.do()
            finally:
                if e:
                    self.enable()
            self.emit('modified')
        else:
            raise NoMoreActionsError

    def can_undo(self):
        com = False
        for com in self.actions[::-1]:
            if com.done:
                break
        return com and com.done

    def can_redo(self):
        com = False
        for com in self.actions:
            if not com.done:
                break
        return com and not com.done

    def undo(self):
        """Undo the last action that was done."""
        com = False
        for com in self.actions[::-1]:
            if com.done:
                break
        if com and com.done:
            e = self.enabled
            self.disable()
            try:
                com.undo()
            finally:
                if e:
                    self.enable()
            self.emit('modified')
        else:
            raise NoMoreActionsError

    def begin_composite(self, composite):
        """Begin a composite action.

        Actions added to the list until end_composite is called
        will be added to the composite action instead of the list.
        """
        if not self.enabled:
            return 
        self.composite = composite 

    def end_composite(self):
        """End a composite action.

        Returns the completed action."""
        if not self.enabled:
            return 
        ret = self.composite
        self.composite = None
        return ret

    def disable(self):
        """Disallow adding and removing items."""
        self.enabled = False
        self.emit('disabled')

    def enable(self):
        """Enable adding and removing items."""
        self.enabled = True
        self.emit('enabled')

class StopAction(Exception):
    pass


def action_from_methods(name, do, undo, redo=None, cleanup=None, combine=None):
    """Create a action from a bunch of methods of another object.
    
    If a redo() method is given, it is called instead of do() if
    the action has been undone before.

    If a cleanup() method is given, it is called when the action
    object is deleted.

    The undo(), redo() and cleanup() methods are called with a single
    argument: the first return value of the do() method.
    """
    def replace_init(selb, *args, **kwds):
        class ActionFromMethod(Action):
            def __init__(self):
                self.args, self.kwds = args, kwds
                self.__done = False

            def do(self):
                if not self.__done or redo is None:
                    ret = do(selb, *self.args, **self.kwds)
                    if isinstance(ret, tuple) and len(ret) > 1:
                        self.state = ret[0]
                        ret = ret[1:]
                        if isinstance(ret, tuple) and len(ret) == 1:
                            ret = ret[0]
                    else:
                        self.state = ret
                        ret = None
                    self.__done = True
                else:
                    return redo(selb, self.state)
                return ret

            def undo(self):
                return undo(selb, self.state)

            def combine(self, cmd):
                if combine is not None:
                    return combine(self, self.state, cmd.state)
                else:
                    return False

            if cleanup is not None:
                def __del__(self):
                    cleanup(selb, self.state)

        ActionFromMethod.__name__ = name
        com = ActionFromMethod()
        try:
            ret = com.do_and_register()
            return ret
        except StopAction, retval:
#            print >>sys.stderr, "comand stopped"
            return retval
    return replace_init


def action_from_methods2(name, do, undo, redo=None, cleanup=None, combine=None):
    """Create a action from a bunch of methods of another object.
    
    If a redo() method is given, it is called instead of do() if
    the action has been undone before.

    If a cleanup() method is given, it is called when the action
    object is deleted.
    """
    def replace_do(obj, *args, **kwds):
        class ActionFromMethod(Action):
            def __init__(self):
                self.args, self.kwds = args, kwds
                self.__done = False
                self.state = {}

            def do(self):
                if not self.__done or redo is None:
                    self.__done = True
                    return do(obj, self.state, *self.args, **self.kwds)
                else:
                    return redo(obj, self.state)

            def undo(self):
                return undo(obj, self.state)

            def combine(self, cmd):
                if combine is not None:
                    return combine(self, self.state, cmd.state)
                else:
                    return False

            if cleanup is not None:
                def __del__(self):
                    cleanup(obj, self.state)

        ActionFromMethod.__name__ = name
        com = ActionFromMethod()
        try:
            ret = com.do_and_register()
            return ret
        except StopAction, retval:
            return retval
    replace_do.__name__ = do.__name__
    return replace_do

# global action list
action_list = ActionList()
undo = action_list.undo
redo = action_list.redo
