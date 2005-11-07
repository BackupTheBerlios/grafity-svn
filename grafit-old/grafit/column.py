import sys
import re

sys.modules['__main__'].splash_message('loading Column')

from grafit.utils import Observed
from grafit.project import project
from grafit.utils import AutoCommands

from grafit.graph import Dataset

from scipy import *
from qt import QMessageBox

def different_size_binary_operation(oper):
    """Returns an operation which will work on different sized 1-d arrays"""
    def newoper(x, y):
        try:
            lx = len(x)
            ly = len(y)
        except TypeError:  
            # one of the two is a scalar
            return oper(x, y)
        if (hasattr(x, 'shape') and len(x.shape) == 0) or (hasattr(y, 'shape') and len(y.shape) == 0):
            # one of the two is a zero-dimensional array
            return oper(x, y)
        length = max(lx, ly)
        x = concatenate([x, array([nan]*(length-lx))])
        y = concatenate([y, array([nan]*(length-ly))])
        return oper(x, y)
    return newoper

# XXX: problem: sin(x) + sin(y) fails!

# setup operations to be used by columns

# simple arithmetic operators 
add_d = different_size_binary_operation(add)
subtract_d = different_size_binary_operation(subtract)
multiply_d = different_size_binary_operation(multiply)
divide_d = different_size_binary_operation(divide)
power_d = different_size_binary_operation(power)

# comparison operators
not_equal_d = different_size_binary_operation(not_equal)
less_d = different_size_binary_operation(less)
less_equal_d = different_size_binary_operation(less_equal)
greater_d = different_size_binary_operation(greater)
greater_equal_d = different_size_binary_operation(greater_equal)


class ShapeError(Exception):
    pass

class Column(Observed):
    """One-dimensional array with undefined length,
       and possibly missing data.
    """
    __metaclass__ = AutoCommands

    def __init__ (self, data=None, worksheet=None, name=None):
        if data is None or len(data) == 0:
            data = [nan]

        self.worksheet = worksheet
        self.precision = 6
        self._calc = None        # expression to caluclate, if this is an auto column
        self._deps = []          # columns that depend on this one
        self._name = name

        if hasattr(data, 'mask') and hasattr(data, 'filled'):
            data = data.filled(nan)

        self.data = array(data, Float)

        if len(self.data.shape) != 1:
            raise ShapeError, 'array is wrong shape for column'

################# index functions

    def __getattr__(self, key):
        if self.worksheet is not None and key in self.worksheet.column_names:
            return Dataset(self, self.worksheet[key])
        else:
            return self.__dict__[key]

    def __getitem__(self, key):
        if type(key) == list:
            return take(self.data, key)
        try:
            return self.data[key]
        except IndexError:
            return nan

    def __setslice__(self, i, j, seq):
        self.__setitem__(slice(i,j), seq)

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i,j))

    def __setitem__(self, key, value):
        if self.calc is not None:
            return

        self.change_data___(self.worksheet.name, self.name, key, value).do().register()
        
#    def combine(self, command):
#        if not isinstance(command, WorksheetDataChange):
#            raise TypeError
#        if self.column.name == command.column.name \
#                    and self.column.worksheet == command.column.worksheet \
#                    and self.item == command.item:
#            command.value = self.value
#            return command
#        else:
#            raise TypeError


####################################################
    def _change_data__init(cmd, wsname, colname, key, value):
        cmd.ws, cmd.col, cmd.key, cmd.value = wsname, colname, key, value
        if type(cmd.key) is slice:
            cmd.key = ('s', cmd.key.start, cmd.key.stop, cmd.key.step)
        cmd.prev = None

    def _change_data__do(cmd):
        self = project[cmd.ws][cmd.col]
        key, value = cmd.key, cmd.value
        if type(key) is tuple and key[0] == 's':
            key = slice(key[1], key[2], key[3])

        # adjust size
        if type(key) == slice:
            self.extend(max(key.start, key.stop))
        elif type(key) == list:
            self.extend(max(key) + 1)
        else:
            self.extend(key + 1)
    
        if cmd.prev is None:
            cmd.prev = copy(self[key])
        
#        if isinstance(prev, array):
#            prev.unshare_mask()
#       XXX why did I have this?

        if type(key) == list:
            for k,v in zip(key, value):
                self.data[k] = v
        else:
            self.data[key] = value

        if self.worksheet is not None:
            for dep in self.deps:
                dep.calculate()

            if self.worksheet is not None:
                self.worksheet.emit (msg='update_data', column=self)
        return cmd

    def _change_data__undo(cmd):
        cmd.prev, cmd.value = cmd.value, cmd.prev
        cmd.do()
        cmd.prev, cmd.value = cmd.value, cmd.prev
        return cmd

    def _change_data__repr(cmd):
        return "-> Change data in %s.%s" % (cmd.ws, cmd.col)

################# operators
    def __add__(self, other): return add_d(self.data, asarray(other)) 
    __radd__ = __add__
    def __sub__(self, other): return subtract_d(self.data, asarray(other)) 
    def __rsub__(self, other): return subtract_d(asarray(other), self.data) 
    def __mul__(self, other): return multiply_d(self.data, asarray(other))
    __rmul__ = __mul__
    def __div__(self, other): return divide_d(self.data, asarray(other)) 
    def __rdiv__(self, other): return divide_d(asarray(other), self.data) 
    def __pow__(self,other): return power_d(self.data, asarray(other)) 

#    def __eq__(self,other): return equal(self,other) 
    def __ne__(self,other): return not_equal_d(self.data,asarray(other)) 
    def __lt__(self,other): return less_d(self.data,asarray(other)) 
    def __le__(self,other): return less_equal_d(self.data,asarray(other)) 
    def __gt__(self,other): return greater_d(self.data,asarray(other)) 
    def __ge__(self,other): return greater_equal_d(self.data,asarray(other))

    def __repr__(self):
        return 'Column(' + str(self.data[:len(self)]) + ')'

    def extend(self, length):
        len_extend = length-self.real_len()
        if len_extend <=0:
            return

        self.data = concatenate([self.data, array([nan]*len_extend)])
        for c in self.worksheet.columns:
            if c is not self:
                c.extend(length)
        self.worksheet.emit (msg='update_size', column=self)

    def real_len(self):
        return len(self.data)

    def __len__(self):
        r = range(self.real_len())
        r.reverse()
        for ind in r:
            if isfinite(self[ind]):
                break
        else:
            ind = -1
        return ind+1

    def __iter__(self):
        for index in range(len(self)):
            yield self[index]

#    def append(self, value):
#        self[len(self)] = value

    def sort_indices(self):
        enum = [(b,a) for (a,b) in enumerate(self)]
        enum.sort()
        return [b for (a,b) in enum]

    def index(self):
        return self.worksheet.column_names.index(self.name)

    def _get_name(self):
        return self._name
    def _set_name(self, newname):
        name = self.name
        if newname == name:
            return
        if not re.match('^[a-zA-Z]\w*$', newname):
            QMessageBox.information(None, "grafit", 
                        "<b>Illegal column name</b><p>Column names must start with a letter and consist "
                        "of letters, numbers and underscore (_)<p>")
            return
        if newname in self.worksheet.column_names and name != newname:
            QMessageBox.information(None, "grafit", 
                        "<b>A column with this name already exists</b><p>Please choose another name<p>")
            return

        self.rename___(self.worksheet.name, self.name, newname).do().register()

    name = property(_get_name, _set_name)

    def _rename__init(cmd, ws, old, new):
        cmd.old, cmd.new, cmd.ws = old, new, ws

    def _rename__do(cmd):
        self = project[cmd.ws][cmd.old]
        newname = cmd.new
        name = cmd.old
        
        self._name = newname
        
        project.lock_undo()
        try:
            for cdep in self.deps:
                patt = r'\b%s\.%s\b' % (self.worksheet.name, name)
                repl = '%s.%s' % (self.worksheet.name, newname)
                cdep.calc = re.sub (patt, repl, cdep.calc)
        finally:
            project.unlock_undo()
    
        for graph, dset in project.used_by(self.worksheet, name):
            if dset.colx == name:
                dset.colx = newname
            if dset.coly == name:
                dset.coly = newname
            graph.legend.update()

        if self.worksheet._view is not None:
            self.worksheet._view.set_column_name(self.index(), self.name)
        return cmd

    def _rename__undo(cmd):
        cmd.old, cmd.new = cmd.new, cmd.old
        cmd.do()
        cmd.old, cmd.new = cmd.new, cmd.old
        return cmd


    def calculate (self):
        if self.calc is not None:
#            d.update(dict([(c.name, c) for c in self.worksheet.columns]))
#            try:
#            print >>sys.stderr, self.calc

            try:
                data = eval (self.calc, project.main_dict)
                self.data = array(data, Float)

                if len(self.data.shape) != 1:
                    raise TypeError
            except:
                self.data = array([], Float)
                print >>sys.stderr, "ERROR in calculation of column (ignore this)"

#            except:
#                pass
            if self.worksheet is not None:
                self.worksheet.emit (msg='update_data')
        for dep in self.deps:
            dep.calculate()

    def set_calc (self, expr):
        project.Worksheet_record = []
        project.Worksheet_recordp = True
        try:
            if expr is not None and expr != '':
                eval (expr, project.main_dict)
        except:
            project.Worksheet_recordp = False
            print >>sys.stderr, 'fail'
        else:
            project.Worksheet_recordp = False
            self.set_calc___(self.worksheet.name, self.name, expr).do().register()

####################################################
    def _set_calc__init(com, ws, col, calc):
        com.ws, com.col, com.calc = ws, col, calc
        com.old = project[com.ws][com.col]._calc
#        print >>sys.stderr, com.ws, com.col
#        print >>sys.stderr, len(project[com.ws][com.col])
        com.olddata = project[com.ws][com.col][:len(project[com.ws][com.col])]
#        print >>sys.stderr, project[com.ws][com.col]
####################################################

    def _set_calc__do(com):
        self = project[com.ws][com.col]

        # remove dependencies
        for wsheet in project.worksheets:
            for column in wsheet.columns:
                while self in column.deps:
                    column.deps.remove(self)

        if com.calc is None or com.calc=='':
            self._calc = None
            if self.worksheet is not None:
                self.worksheet.emit (msg='update_data', column=self)
        else:
            project.Worksheet_recordp = False
            self._calc = com.calc
            for col in project.Worksheet_record:
                if self not in col.deps:
                    col.deps.append (self)
            self.calculate()
        return com

    def _set_calc__undo(com):
        self = project[com.ws][com.col]
        self._calc = com.old
        project[com.ws][com.col] = com.olddata
        project[com.ws][com.col]._calc = com.old
        return com
        
    def get_calc (self):
        return self._calc
    calc = property (get_calc, set_calc)

    def set_deps(self, deps): raise TypeError, 'read-only attribute'
    def get_deps(self): return self._deps
    deps = property (get_deps, set_deps)
