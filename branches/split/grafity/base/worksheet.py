import sys
import re

from dispatch import dispatcher

from grafity.core.storage import Item, Attr, Container
from grafity.core.arrays import MkArray, transpose, array, asarray
from grafity.base.items import ProjectItem

import grafity.core.arrays as arrays

class Column(Item):
    name = Attr.Text()
    number = Attr.Integer()
    expr = Attr.Text()
    data = MkArray()
    
#    def __init__(self):
#        Item.__init__(self)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __eq__(self, other):
        return hasattr(self, 'oid') and hasattr(other, 'oid') and self.oid == other.oid


class Worksheet(ProjectItem):
    columns = Container(Column)

    def __init__(self):
        ProjectItem.__init__(self)

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
        c.name = name
        return c

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

#    add_column = action_from_methods2('worksheet/add_column', add_column, add_column_undo,
#                                       redo=add_column_redo)

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
