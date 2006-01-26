import sys
import re

try:
   sys.modules['__main__'].splash.message('loading worksheet')
except:
    pass

from grafity.signals import HasSignals
from grafity.actions import action_from_methods, action_from_methods2, StopAction, action_list
from grafity.project import Item, wrap_attribute, register_class, create_id
from grafity.arrays import MkArray, transpose, array, asarray

import grafity.arrays as arrays

class Column(MkArray, HasSignals):
    def __init__(self, worksheet, ind):
        self.data = worksheet.data.columns[ind]
        self.worksheet = worksheet
        MkArray.__init__(self, worksheet.data.columns, worksheet.data.columns.data, ind)
        self.dependencies = set()

    def reload(self, ind):
        MkArray.__init__(self, self.worksheet.data.columns, self.worksheet.data.columns.data, ind)
        self.data = self.worksheet.data.columns[ind]

    def set_name(self, name):
        prevname = self.data.name
        self.data.name = name.encode('utf-8')
        self.emit('rename', self, prevname, name)
        self.worksheet.emit('rename-column', self, prevname, name)
    def get_name(self):
        return self.data.name.decode('utf-8')
    name = property(get_name, set_name)

    def get_fullname(self):
        return self.worksheet.fullname+'.'+self.name
    fullname = property(get_fullname)

    def do_set_expr(self, state, expr, setstate=True):
        # find dependencies and error-check expression
        try:
            data = asarray(self.worksheet.evaluate(expr))
        except Exception, ar:
            print >>sys.stderr, '*****************', ar
            raise StopAction, False
        self.depdict = self.analyze_expression(expr)
        newdep = set(self.depdict.values())

        # set dependencies
        for column in newdep - self.dependencies:
            column.connect('data-changed', self.calculate)
            column.connect('rename', self.on_dep_rename)
        for column in self.dependencies - newdep:
            column.disconnect('data-changed', self.calculate)
            column.disconnect('rename', self.on_dep_rename)
        self.dependencies = newdep

        # action state
        if setstate:
            state['old'], state['new'] = self.expr, expr
            if self.expr == '':
                state['olddata'] = self[:]

        self.data.expr = expr.encode('utf-8')
        if expr != '':
            # set data without triggering a action
            MkArray.__setitem__(self, slice(None), data)
        self.worksheet.emit('data-changed')
        self.emit('data-changed')
        return True

    def undo_set_expr(self, state):
        self.do_set_expr(None, state['old'], setstate=False)
        if 'olddata' in state:
            MkArray.__setitem__(self, slice(None), state['olddata'])

    def redo_set_expr(self, state):
        self.do_set_expr(None, state['new'], setstate=False)

    set_expr = action_from_methods2('worksheet/column-expr', 
                                     do_set_expr, undo_set_expr, redo=redo_set_expr)

    def get_expr(self):
        return self.data.expr.decode('utf-8')

    expr = property(get_expr, set_expr)

    def calculate(self):
        self[:] = self.worksheet.evaluate(self.expr)

    def analyze_expression(self, expr):
        idents = re.findall(r'\b([a-zA-Z_][\w\.]*)\b(?!\()', expr)
        wsnames = ['.'.join(ident.split('.')[:-1]) for ident in idents]
        worksheets = [self.worksheet.evaluate(name) for name in wsnames]
        for i, w in enumerate(worksheets):
            if w == []:
                worksheets[i] = self.worksheet
        columns = [ident.split('.')[-1] for ident in idents]
        deps = [getattr(w, c) for w, c in zip(worksheets, columns)]
        depdict = dict(zip(idents, deps))
        return depdict

    def on_dep_rename(self, col, oldname, newname):
        expr = self.expr
        oldexpr = expr
        for depstr, depcol in self.depdict.iteritems():
            if depcol == col:
                if col.worksheet == self.worksheet:
                    name = newname
                elif col.worksheet.parent == self.worksheet.parent:
                    name = '.'.join(col.worksheet.name, col.name)
                else:
                    name = '.'.join(col.worksheet.fullname, col.name)
                expr = re.sub(r'\b%s\b(?!\()'%depstr, newname, expr)
        self.expr = expr

    def set_id(self, id):
        self.data.id = id
    def get_id(self):
        return self.data.id
    id = property(get_id, set_id)

    def __setitem__(self, key, value):
        prev = self[key]
        MkArray.__setitem__(self, key, value)
        self.worksheet.emit('data-changed')
        self.emit('data-changed')
        return [key, value, prev]

    def undo_setitem(self, state):
        key, value, prev = state
        self[key] = prev

    def __eq__(self, other):
        return self.id == other.id

    __setitem__ = action_from_methods('column_change_data', __setitem__, undo_setitem)


class Worksheet(Item, HasSignals):
    def __init__(self, project, name=None, parent=None, location=None):
        self.__attr = False

        Item.__init__(self, project, name, parent, location)

        self.columns = []

        if location is not None:
            for i in range(len(self.data.columns)):
                if not self.data.columns[i].name.startswith('-'):
                    self.columns.append(Column(self, i))

        self.__attr = True

    def __items__(self):
        return dict((c.name, c) for c in self.columns)

    def move_column(self, state, src=None, dest=None):

        if src is None and dest is None:
            src, dest = state['columns']
        else:
            if src==dest or dest<0 or src<0 or dest>=len(self.columns) or src>=len(self.columns):
                raise StopAction, False
            state['columns'] = (src, dest)

        for i in range(src, dest, cmp(dest,src)):
            self.swap_columns(i, i+cmp(dest, src), nocomm=True)

        self.emit('data-changed')

    def undo_move_column(self, state):
        dest, src = state['columns']
        for i in range(src, dest, cmp(dest,src)):
            self.swap_columns(i, i+cmp(dest, src), nocomm=True)
        self.emit('data-changed')

    move_column = action_from_methods2('move column', move_column, undo_move_column)


    def swap_columns(self, state, i=None, j=None, nocomm=False):
        if i is None and j is None:
            i, j = state['columns']
        else:
            if i==j or i<0 or j<0 or i>=len(self.columns) or j>=len(self.columns):
                raise StopAction, False
            state['columns'] = (i, j)
        
        # swap rows in database
        # columns[i], columns[j] = columns[j], columns[i] will not work
        # (at least with metakit 2.4.9.3), so we have to do this explicitly
        tmp = self.data.columns.append()
        self.data.columns[tmp] = self.data.columns[i]
        self.data.columns[i] = self.data.columns[j]
        self.data.columns[j] = self.data.columns[tmp]
        del self.data.columns[tmp]
        
        # swap column objects
        self.columns[i], self.columns[j] = self.columns[j], self.columns[i]
        self.columns[i].reload(i)
        self.columns[j].reload(j)

        if nocomm:
            raise StopAction, True

        self.emit('data-changed')

        return True

    swap_columns = action_from_methods2('worksheet/swap-columns', swap_columns, swap_columns)

    def evaluate(self, expression):
        if expression == '':
            return []
        project = self.project
        worksheet = self

        namespace = {}
        namespace.update(arrays.__dict__)
        namespace['top'] = project.top
        namespace['here'] = project.this
        namespace['this'] = self
        namespace['up'] = self.parent.parent
        namespace.update(dict([(c.name, c) for c in self.columns]))
        namespace.update(dict([(i.name, i) for i in self.parent.contents()]))

        try:
            result = eval(expression, namespace)
        except:
            raise ValueError

        return result

    def __getattr__(self, name):
        if name in self.column_names:
            return self[name]
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name.startswith('_') or hasattr(self.__class__, name) \
                                or name in self.__dict__ or not self.__attr:
            return object.__setattr__(self, name, value)
        else:
            if name not in self.column_names:
                self.add_column(name)
            self[name] = value

    def __delattr__(self, name):
        if name in self.column_names:
            self.remove_column(name)
        else:
            object.__delattr__(self, name)

    def column_index(self, name):
        return self.data.columns.select(*[{'name': n.encode('utf-8')} for n in self.column_names]).find(name=name.encode('utf-8'))

    def add_column(self, state, name):
        ind = self.data.columns.append(name=name.encode('utf-8'), id=create_id(), data='')
        self.columns.append(Column(self, ind))
        self.emit('data-changed')
        state['obj'] = self.columns[-1]
        return name

    def add_column_undo(self, state):
        col = state['obj']
        col.id = '-'+col.id
        self.columns.remove(col)
        self.emit('data-changed')

    def add_column_redo(self, state):
        col = state['obj']
        col.id = col.id[1:]
        self.columns.append(col)
        self.emit('data-changed')

    add_column = action_from_methods2('worksheet/add_column', add_column, add_column_undo,
                                       redo=add_column_redo)

    def remove_column(self, state, name):
        ind = self.column_index(name)
        if ind == -1:
            raise NameError, "Worksheet does not have a column named %s" % name
        else:
            col = self.columns[ind]
            col.name = '-'+col.name
            del self.columns[ind]
            self.emit('data-changed')
            state['col'], state['ind'] = col, ind
            return (col, ind), None

    def undo_remove_column(self, state):
        col, ind = state['col'], state['ind']
        col.name = col.name[1:]
        self.columns.insert(ind, col)
        self.emit('data-changed')

    remove_column = action_from_methods2('worksheet_remove_column', remove_column, 
                                          undo_remove_column)

    def get_ncolumns(self):
        return len(self.columns)
    ncolumns = property(get_ncolumns)

    def get_nrows(self):
        try:
            return max([len(c) for c in self.columns])
        except ValueError:
            return 0
    nrows = property(get_nrows)

    def set_array(self, arr):
        if len(arr.shape) != 2:
            raise TypeError, "Array must be two-dimensional"

        for column in arr:
            name = self.suggest_column_name()
            self[name] = column

    def get_array(self):
        return array(self.columns)

    array = property(get_array, set_array)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.columns[key]
        elif isinstance(key, basestring) and key in self.column_names:
            return self.columns[self.column_names.index(key)]
        else:
            raise IndexError

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.columns[key][:] = value
        elif isinstance(key, basestring):
            if key not in self.column_names:
                self.add_column(key)
            self.columns[self.column_names.index(key)][:] = value
        else:
            raise IndexError
        self.emit('data-changed')

    def __repr__(self):
        return '<Worksheet %s%s>' % (self.name, '(deleted)'*self.id.startswith('-'))


    def get_column_names(self):
        return [c.name for c in self.columns]
    column_names = property(get_column_names)

    def __iter__(self):
        for column in self.columns:
            yield column

    def suggest_column_name(self):
        def num_to_alpha(n):
            alphabet = 'abcdefghijklmnopqrstuvwxyz'
            name = ''
            n, ypol = n//len(alphabet), n%len(alphabet)
            if n == 0:
                return alphabet[ypol]
            name = num_to_alpha(n) + alphabet[ypol]
            return name

        i = 0
        while num_to_alpha(i) in self.column_names:
            i+=1
        return num_to_alpha(i)

    def export_ascii(self, f):
        for row in xrange(self.nrows):
            for col in xrange(self.ncolumns):
                f.write(str(self.columns[col][row]))
                f.write('\t')
            f.write('\n')

    default_name_prefix = 'sheet'

register_class(Worksheet, 'worksheets[name:S,id:S,parent:S,columns[name:S,id:S,data:B,expr:S]]')
