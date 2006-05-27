import sys
import re

from dispatch import dispatcher

from grafity.base.squirrel import Item, Attr, Container
from grafity.base.arrays import MkArray, transpose, array, asarray
from grafity.base.items import ProjectItem

import grafity.base.arrays as arrays

class Column(Item):
    name = Attr.Text()
    number = Attr.Integer()
    expr = Attr.Text()
    data = MkArray()
    
    def __init__(self, *args):
        Item.__init__(self, *args)

    def initialize(self, *args):
        Item.initialize(self, *args)
        self.dependencies = set()
        self.worksheet = self._parent
#        self.do_set_expr(self.expr)

    def __setitem__(self, key, value):
        self.data[key] = value
        dispatcher.send('data-changed', sender=self)

    def __getitem__(self, key):
        return self.data[key]

    def __eq__(self, other):
        return hasattr(self, 'oid') and hasattr(other, 'oid') and self.oid == other.oid

    def __repr__(self):
        return repr(self.data)

    def _validate__name(self, name):
        print >>sys.stderr, name
        return name

    def _after__name(self, name):
        pass

    def _validate__expr(self, expr):
        print >>sys.stderr, self.do_set_expr(expr)
        return expr

    def _validate__data(self, data):
        print >>sys.stderr, "data"
        return data

    def _after__data(self, data):
        print >>sys.stderr, "data"

    __str__ = __repr__

    def __add__(self, other): return arrays.add(self.data, arrays.asvarray(other))
    __radd__ = __add__
    def __sub__(self, other): return arrays.subtract(self.data, arrays.asvarray(other))
    def __rsub__(self, other): return arrays.subtract(arrays.asvarray(other), self.data)
    def __mul__(self, other): return arrays.multiply(self.data, arrays.asvarray(other))
    __rmul__ = __mul__
    def __div__(self, other): return arrays.divide(self.data, arrays.asvarray(other))
    def __rdiv__(self, other): return arrays.divide(arrays.asvarray(other), self.data)
    def __pow__(self,other): return arrays.power(self.data, arrays.asvarray(other))

    def __len__(self):
        return len(self.data)

    def __ioldnit__(self, worksheet, ind):
        self.data = worksheet.data.columns[ind]
        self.worksheet = worksheet
        MkArray.__init__(self, worksheet.data.columns, worksheet.data.columns.data, ind)
        self.worksheet.connect('set-parent', self.on_ws_set_parent)

    def reload(self, ind):
        MkArray.__init__(self, self.worksheet.data.columns, self.worksheet.data.columns.data, ind)
        self.data = self.worksheet.data.columns[ind]

    def do_set_expr(self, expr):
        # find dependencies and error-check expression
        #try:
        data = asarray(self.worksheet.evaluate(expr))
#        except Exception, ar:
       # x.    print >>sys.stderr, '*****************', ar
       #     raise UserWarning, False
        self.depdict = self.analyze_expression(expr)
        newdep = set(self.depdict.values())

        # set dependencies
        for column in newdep - self.dependencies:
            print >>sys.stderr, "add", column.name
            dispatcher.connect(self.calculate, signal='data-changed', sender=column)
            dispatcher.connect(self.on_dep_rename, signal='rename', sender=column)
        for column in self.dependencies - newdep:
            print >>sys.stderr, "rem", column.name
            dispatcher.disconnect(self.calculate, signal='data-changed', sender=column)
            dispatcher.disconnect(self.on_dep_rename, signal='rename', sender=column)
        newdepws = set(d.worksheet for d in newdep)
        depws = set(d.worksheet for d in self.dependencies)
        for worksheet in newdepws - depws:
            dispatcher.connect(self.on_dep_ws_rename, signal='fullname-changed', sender=worksheet)
            dispatcher.connect(self.on_dep_ws_rename, signal='rename', sender=worksheet)
        for worksheet in depws - newdepws:
            dispatcher.disconnect(self.on_dep_ws_rename, signal='fullname-changed', sender=worksheet)
            dispatcher.disconnect(self.on_dep_ws_rename, signal='rename', sender=worksheet)
        self.dependencies = newdep

        if expr != '':
            # set data without triggering an action
            self.data[:] = data
        dispatcher.send(sender=self, signal='data-changed')
        dispatcher.send(sender=self.worksheet, signal='data-changed')
        return True

    def undo_set_expr(self, state):
        self.do_set_expr(None, state['old'], setstate=False)
        if 'olddata' in state:
            MkArray.__setitem__(self, slice(None), state['olddata'])

    def redo_set_expr(self, state):
        self.do_set_expr(None, state['new'], setstate=False)


    def get_expr(self):
        return self.data.expr.decode('utf-8')


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

    def update_expression(self, *args, **kwds):
        if self.expr == '':
            return

        expr = self.expr
        oldexpr = expr

        for depstr, col in self.depdict.iteritems():
            if col.worksheet == self.worksheet:
                name = col.name
            elif col.worksheet.parent == self.worksheet.parent:
                name = '.'.join([col.worksheet.name, col.name])
            else:
                name = '.'.join([col.worksheet.fullname, col.name])
            expr = re.sub(r'\b%s\b(?!\()'%depstr, name, expr)
        if oldexpr != expr:
            print >>sys.stderr, "updating expression from %s to %s" % (oldexpr, expr)
            self.expr = expr
 
    def on_dep_rename(self, col, oldname, newname): self.update_expression()
    def on_dep_ws_rename(self, name, item=None): self.update_expression()
    def on_ws_set_parent(self, parent): self.update_expression()
                


class Worksheet(ProjectItem):
    columns = Container(Column)

    def __init__(self, *args):
        ProjectItem.__init__(self, *args)

    def __items__(self):
        return dict((c.name, c) for c in self.columns)

    def __getattr__(self, name):
        if name in self.column_names:
            return self[name]
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        try:
            if name.startswith('_'):
                return object.__setattr__(self, name, value)
            object.__getattribute__(self, name)
        except AttributeError:
            if name not in self.column_names:
                self.add_column(name)
            self[name] = value
        else:
            return object.__setattr__(self, name, value)

#        if name.startswith('_') or hasattr(self.__class__, name) \
#                                or name in self.__dict__ \
#                                or has:
#        else:

    def __delattr__(self, name):
        if name in self.column_names:
            self.remove_column(name)
        else:
            object.__delattr__(self, name)

    def column_index(self, name):
        return self.data.columns.select(*[{'name': n.encode('utf-8')} for n in self.column_names]).find(name=name.encode('utf-8'))

    def add_column(self, name=None):
        if name is None:
            name = suggest_column_name()
        c = self.columns.create()
        c.worksheet = self
        c.name = name
        return c

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

#    remove_column = action_from_methods2('worksheet_remove_column', remove_column, 
#                                          undo_remove_column)

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
        dispatcher.send('data-changed', sender=self)

#    def __repr__(self):
#        return '<Worksheet %s%s>' % (self.name, '(deleted)'*self.id.startswith('-'))


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


    def evaluate(self, expression):
        if expression == '':
            return []
        project = self._project
        worksheet = self

        namespace = {}
        namespace.update(arrays.__dict__)
        namespace['top'] = project.top
#        namespace['here'] = project.this
        namespace['this'] = self
        namespace['up'] = self.folder.folder
        namespace.update(dict([(c.name, c) for c in self.columns]))
        namespace.update(dict([(i.name, i) for i in self.folder.contents()]))

        try:
            result = eval(expression, namespace)
        except:
            raise ValueError, expression

        return result


