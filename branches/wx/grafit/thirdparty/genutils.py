# -*- coding: utf-8 -*-
"""
General purpose utilities.

This is a grab-bag of stuff I find useful in most programs I write. Some of
these things are also convenient when working at the command line.

$Id: genutils.py,v 1.34 2005/03/18 09:23:48 fperez Exp $"""

#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

#from IPython import Release
#__author__  = '%s <%s>' % Release.authors['Fernando']
#__license__ = Release.license

#****************************************************************************
# required modules
import __main__
import types,commands,time,sys,os,re,shutil
import tempfile
#from IPython.Itpl import Itpl,itpl,printpl
#from IPython import DPyGetOpt

#****************************************************************************
# Exceptions
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

#----------------------------------------------------------------------------
class Stream:
    """Simple class to hold the various I/O streams in Term"""

    def __init__(self,stream,name):
        self.stream = stream
        self.name = name
        try:
            self.fileno = stream.fileno()
        except AttributeError:
            msg = ("Stream <%s> looks suspicious: it lacks a 'fileno' attribute."
                   % name)
            print >> sys.stderr, 'WARNING:',msg
        try:
            self.mode = stream.mode
        except AttributeError:
            msg = ("Stream <%s> looks suspicious: it lacks a 'mode' attribute."
                   % name)
            print >> sys.stderr, 'WARNING:',msg

class Term:
    """ Term holds the file or file-like objects for handling I/O operations.

    These are normally just sys.stdin, sys.stdout and sys.stderr but for
    Windows they can can replaced to allow editing the strings before they are
    displayed."""

    # In the future, having IPython channel all its I/O operations through
    # this class will make it easier to embed it into other environments which
    # are not a normal terminal (such as a GUI-based shell)
    in_s  = Stream(sys.stdin,'cin')
    out_s = Stream(sys.stdout,'cout')
    err_s = Stream(sys.stderr,'cerr')

    # Store the three streams in (err,out,in) order so that if we need to reopen
    # them, the error channel is reopened first to provide info.
    streams = [err_s,out_s,in_s]

    # The class globals should be the actual 'bare' streams for normal I/O to work
    cin  = streams[2].stream
    cout = streams[1].stream
    cerr = streams[0].stream
    
    def reopen_all(cls):
        """Reopen all streams if necessary.

        This should only be called if it is suspected that someting closed
        accidentally one of the I/O streams."""

        any_closed = 0

        for sn in range(len(cls.streams)):
            st = cls.streams[sn]
            if st.stream.closed:
                any_closed = 1
                new_stream = os.fdopen(os.dup(st.fileno), st.mode,0)
                cls.streams[sn] = Stream(new_stream,st.name)
                print >> cls.streams[0].stream, \
                      '\nWARNING:\nStream Term.%s had to be reopened!' % st.name

        # Rebuild the class globals
        cls.cin = cls.streams[2].stream
        cls.cout = cls.streams[1].stream
        cls.cerr = cls.streams[0].stream

    reopen_all = classmethod(reopen_all)

    def set_stdout(cls,stream):
        """Set the stream """
        cls.cout = stream
    set_stdout = classmethod(set_stdout)

    def set_stderr(cls,stream):
        cls.cerr = stream
    set_stderr = classmethod(set_stderr)

# Windows-specific code to load Gary Bishop's readline and configure it
# automatically for the users
# Note: os.name on cygwin returns posix, so this should only pick up 'native'
# windows.  Cygwin returns 'cygwin' for sys.platform.
if os.name == 'nt':
    try:
        import readline
    except ImportError:
        pass
    else:
        try:
            _out = readline.GetOutputFile()
        except AttributeError:
            pass
        else:
            Term.set_stdout(_out)
            Term.set_stderr(_out)
            del _out

#****************************************************************************
# Generic warning/error printer, used by everything else
def warn(msg,level=2,exit_val=1):
    """Standard warning printer. Gives formatting consistency.

    Output is sent to Term.cerr (sys.stderr by default).
    
    Options:
    
    -level(2): allows finer control:
      0 -> Do nothing, dummy function.
      1 -> Print message.
      2 -> Print 'WARNING:' + message. (Default level).
      3 -> Print 'ERROR:' + message.
      4 -> Print 'FATAL ERROR:' + message and trigger a sys.exit(exit_val).

    -exit_val (1): exit value returned by sys.exit() for a level 4
    warning. Ignored for all other levels."""
    
    if level>0:
        header = ['','','WARNING: ','ERROR: ','FATAL ERROR: ']
        print >> Term.cerr, '%s%s' % (header[level],msg)
        if level == 4:
            print >> Term.cerr,'Exiting.\n'
            sys.exit(exit_val)

def info(msg):
    """Equivalent to warn(msg,level=1)."""

    warn(msg,level=1)

def error(msg):
    """Equivalent to warn(msg,level=3)."""

    warn(msg,level=3)

def fatal(msg,exit_val=1):
    """Equivalent to warn(msg,exit_val=exit_val,level=4)."""

    warn(msg,exit_val=exit_val,level=4)

#----------------------------------------------------------------------------
StringTypes = types.StringTypes

# Basic timing functionality

# If possible (Unix), use the resource module instead of time.clock()
try:
    import resource
    def clock():
        """clock() -> floating point number

        Return the CPU time in seconds (user time only, system time is
        ignored) since the start of the process.  This is done via a call to
        resource.getrusage, so it avoids the wraparound problems in
        time.clock()."""
        
        return resource.getrusage(resource.RUSAGE_SELF)[0]
    
    def clock2():
        """clock2() -> (t_user,t_system)

        Similar to clock(), but return a tuple of user/system times."""
        return resource.getrusage(resource.RUSAGE_SELF)[:2]

except ImportError:
    clock = time.clock
    def clock2():
        """Under windows, system CPU time can't be measured.

        This just returns clock() and zero."""
        return time.clock(),0.0

def timings_out(reps,func,*args,**kw):
    """timings_out(reps,func,*args,**kw) -> (t_total,t_per_call,output)

    Execute a function reps times, return a tuple with the elapsed total
    CPU time in seconds, the time per call and the function's output.

    Under Unix, the return value is the sum of user+system time consumed by
    the process, computed via the resource module.  This prevents problems
    related to the wraparound effect which the time.clock() function has.
    
    Under Windows the return value is in wall clock seconds. See the
    documentation for the time module for more details."""

    reps = int(reps)
    assert reps >=1, 'reps must be >= 1'
    if reps==1:
        start = clock()
        out = func(*args,**kw)
        tot_time = clock()-start
    else:
        rng = xrange(reps-1) # the last time is executed separately to store output
        start = clock()
        for dummy in rng: func(*args,**kw)
        out = func(*args,**kw)  # one last time
        tot_time = clock()-start
    av_time = tot_time / reps
    return tot_time,av_time,out

def timings(reps,func,*args,**kw):
    """timings(reps,func,*args,**kw) -> (t_total,t_per_call)

    Execute a function reps times, return a tuple with the elapsed total CPU
    time in seconds and the time per call. These are just the first two values
    in timings_out()."""

    return timings_out(reps,func,*args,**kw)[0:2]

def timing(func,*args,**kw):
    """timing(func,*args,**kw) -> t_total

    Execute a function once, return the elapsed total CPU time in
    seconds. This is just the first value in timings_out()."""

    return timings_out(1,func,*args,**kw)[0]

#****************************************************************************
# file and system

def system(cmd,verbose=0,debug=0,header=''):
    """Execute a system command, return its exit status.

    Options:

    - verbose (0): print the command to be executed.
    
    - debug (0): only print, do not actually execute.

    - header (''): Header to print on screen prior to the executed command (it
    is only prepended to the command, no newlines are added).

    Note: a stateful version of this function is available through the
    SystemExec class."""

    stat = 0
    if verbose or debug: print header+cmd
    sys.stdout.flush()
    if not debug: stat = os.system(cmd)
    return stat

def shell(cmd,verbose=0,debug=0,header=''):
    """Execute a command in the system shell, always return None.

    Options:

    - verbose (0): print the command to be executed.
    
    - debug (0): only print, do not actually execute.

    - header (''): Header to print on screen prior to the executed command (it
    is only prepended to the command, no newlines are added).

    Note: this is similar to genutils.system(), but it returns None so it can
    be conveniently used in interactive loops without getting the return value
    (typically 0) printed many times."""

    stat = 0
    if verbose or debug: print header+cmd
    # flush stdout so we don't mangle python's buffering
    sys.stdout.flush()
    if not debug:
        os.system(cmd)

def getoutput(cmd,verbose=0,debug=0,header='',split=0):
    """Dummy substitute for perl's backquotes.

    Executes a command and returns the output.

    Accepts the same arguments as system(), plus:

    - split(0): if true, the output is returned as a list split on newlines.

    Note: a stateful version of this function is available through the
    SystemExec class."""

    if verbose or debug: print header+cmd
    if not debug:
        output = commands.getoutput(cmd)
        if split:
            return output.split('\n')
        else:
            return output

def getoutputerror(cmd,verbose=0,debug=0,header='',split=0):
    """Return (standard output,standard error) of executing cmd in a shell.

    Accepts the same arguments as system(), plus:

    - split(0): if true, each of stdout/err is returned as a list split on
    newlines.

    Note: a stateful version of this function is available through the
    SystemExec class."""

    if verbose or debug: print header+cmd
    if not cmd:
        if split:
            return [],[]
        else:
            return '',''
    if not debug:
        pin,pout,perr = os.popen3(cmd)
        tout = pout.read().rstrip()
        terr = perr.read().rstrip()
        pin.close()
        pout.close()
        perr.close()
        if split:
            return tout.split('\n'),terr.split('\n')
        else:
            return tout,terr

# for compatibility with older naming conventions
xsys = system
bq = getoutput

class SystemExec:
    """Access the system and getoutput functions through a stateful interface.

    Note: here we refer to the system and getoutput functions from this
    library, not the ones from the standard python library.
    
    This class offers the system and getoutput functions as methods, but the
    verbose, debug and header parameters can be set for the instance (at
    creation time or later) so that they don't need to be specified on each
    call.

    For efficiency reasons, there's no way to override the parameters on a
    per-call basis other than by setting instance attributes. If you need
    local overrides, it's best to directly call system() or getoutput().

    The following names are provided as alternate options:
     - xsys: alias to system
     - bq: alias to getoutput

    An instance can then be created as:
     >>> sysexec = SystemExec(verbose=1,debug=0,header='Calling: ')

    And used as:
     >>> sysexec.xsys('pwd')
     >>> dirlist = sysexec.bq('ls -l')
    """
    
    def __init__(self,verbose=0,debug=0,header='',split=0):
        """Specify the instance's values for verbose, debug and header."""
        setattr_list(self,'verbose debug header split')

    def system(self,cmd):
        """Stateful interface to system(), with the same keyword parameters."""

        system(cmd,self.verbose,self.debug,self.header)

    def shell(self,cmd):
        """Stateful interface to shell(), with the same keyword parameters."""

        shell(cmd,self.verbose,self.debug,self.header)

    xsys = system  # alias

    def getoutput(self,cmd):
        """Stateful interface to getoutput()."""

        return getoutput(cmd,self.verbose,self.debug,self.header,self.split)

    def getoutputerror(self,cmd):
        """Stateful interface to getoutputerror()."""

        return getoutputerror(cmd,self.verbose,self.debug,self.header,self.split)

    bq = getoutput  # alias

#-----------------------------------------------------------------------------
def mutex_opts(dict,ex_op):
    """Check for presence of mutually exclusive keys in a dict.

    Call: mutex_opts(dict,[[op1a,op1b],[op2a,op2b]...]"""
    for op1,op2 in ex_op:
        if op1 in dict and op2 in dict:
            raise ValueError,'\n*** ERROR in Arguments *** '\
                  'Options '+op1+' and '+op2+' are mutually exclusive.'

#-----------------------------------------------------------------------------
def filefind(fname,alt_dirs = None):
    """Return the given filename either in the current directory, if it
    exists, or in a specified list of directories.

    ~ expansion is done on all file and directory names.

    Upon an unsuccessful search, raise an IOError exception."""

    if alt_dirs is None:
        try:
            alt_dirs = get_home_dir()
        except HomeDirError:
            alt_dirs = os.getcwd()
    search = [fname] + list_strings(alt_dirs)
    search = map(os.path.expanduser,search)
    #print 'search list for',fname,'list:',search  # dbg
    fname = search[0]
    if os.path.isfile(fname):
        return fname
    for direc in search[1:]:
        testname = os.path.join(direc,fname)
        #print 'testname',testname  # dbg
        if os.path.isfile(testname):
            return testname
    raise IOError,'File' + `fname` + \
          ' not found in current or supplied directories:' + `alt_dirs`

#----------------------------------------------------------------------------
def target_outdated(target,deps):
    """Determine whether a target is out of date.

    target_outdated(target,deps) -> 1/0

    deps: list of filenames which MUST exist.
    target: single filename which may or may not exist.

    If target doesn't exist or is older than any file listed in deps, return
    true, otherwise return false.
    """
    try:
        target_time = os.path.getmtime(target)
    except os.error:
        return 1
    for dep in deps:
        dep_time = os.path.getmtime(dep)
        if dep_time > target_time:
            #print "For target",target,"Dep failed:",dep # dbg
            #print "times (dep,tar):",dep_time,target_time # dbg
            return 1
    return 0

#-----------------------------------------------------------------------------
def target_update(target,deps,cmd):
    """Update a target with a given command given a list of dependencies.

    target_update(target,deps,cmd) -> runs cmd if target is outdated.

    This is just a wrapper around target_outdated() which calls the given
    command if target is outdated."""

    if target_outdated(target,deps):
        xsys(cmd)

#----------------------------------------------------------------------------
def unquote_ends(istr):
    """Remove a single pair of quotes from the endpoints of a string."""

    if not istr:
        return istr
    if (istr[0]=="'" and istr[-1]=="'") or \
       (istr[0]=='"' and istr[-1]=='"'):
        return istr[1:-1]
    else:
        return istr

#----------------------------------------------------------------------------
def process_cmdline(argv,names=[],defaults={},usage=''):
    """ Process command-line options and arguments.

    Arguments:

    - argv: list of arguments, typically sys.argv.
    
    - names: list of option names. See DPyGetOpt docs for details on options
    syntax.

    - defaults: dict of default values.

    - usage: optional usage notice to print if a wrong argument is passed.

    Return a dict of options and a list of free arguments."""

    getopt = DPyGetOpt.DPyGetOpt()
    getopt.setIgnoreCase(0)
    getopt.parseConfiguration(names)

    try:
        getopt.processArguments(argv)
    except:
        print usage
        warn(`sys.exc_value`,level=4)

    defaults.update(getopt.optionValues)
    args = getopt.freeValues
    
    return defaults,args

#----------------------------------------------------------------------------
def optstr2types(ostr):
    """Convert a string of option names to a dict of type mappings.

    optstr2types(str) -> {None:'string_opts',int:'int_opts',float:'float_opts'}

    This is used to get the types of all the options in a string formatted
    with the conventions of DPyGetOpt. The 'type' None is used for options
    which are strings (they need no further conversion). This function's main
    use is to get a typemap for use with read_dict().
    """

    typeconv = {None:'',int:'',float:''}
    typemap = {'s':None,'i':int,'f':float}
    opt_re = re.compile(r'([\w]*)([^:=]*:?=?)([sif]?)')

    for w in ostr.split():
        oname,alias,otype = opt_re.match(w).groups()
        if otype == '' or alias == '!':   # simple switches are integers too
            otype = 'i'
        typeconv[typemap[otype]] += oname + ' '
    return typeconv

#----------------------------------------------------------------------------
def read_dict(filename,type_conv=None,**opt):

    """Read a dictionary of key=value pairs from an input file, optionally
    performing conversions on the resulting values.

    read_dict(filename,type_conv,**opt) -> dict

    Only one value per line is accepted, the format should be
     # optional comments are ignored
     key value\n

    Args:

      - type_conv: A dictionary specifying which keys need to be converted to
      which types. By default all keys are read as strings. This dictionary
      should have as its keys valid conversion functions for strings
      (int,long,float,complex, or your own).  The value for each key
      (converter) should be a whitespace separated string containing the names
      of all the entries in the file to be converted using that function. For
      keys to be left alone, use None as the conversion function (only needed
      with purge=1, see below).

      - opt: dictionary with extra options as below (default in parens)

        purge(0): if set to 1, all keys *not* listed in type_conv are purged out
        of the dictionary to be returned. If purge is going to be used, the
        set of keys to be left as strings also has to be explicitly specified
        using the (non-existent) conversion function None.

        fs(None): field separator. This is the key/value separator to be used
        when parsing the file. The None default means any whitespace [behavior
        of string.split()].

        strip(0): if 1, strip string values of leading/trailinig whitespace.

        warn(1): warning level if requested keys are not found in file.
          - 0: silently ignore.
          - 1: inform but proceed.
          - 2: raise KeyError exception.

        no_empty(0): if 1, remove keys with whitespace strings as a value.

        unique([]): list of keys (or space separated string) which can't be
        repeated. If one such key is found in the file, each new instance
        overwrites the previous one. For keys not listed here, the behavior is
        to make a list of all appearances.

    Example:
    If the input file test.ini has:
      i 3
      x 4.5
      y 5.5
      s hi ho
    Then:

    >>> type_conv={int:'i',float:'x',None:'s'}
    >>> read_dict('test.ini')
    {'i': '3', 's': 'hi ho', 'x': '4.5', 'y': '5.5'}
    >>> read_dict('test.ini',type_conv)
    {'i': 3, 's': 'hi ho', 'x': 4.5, 'y': '5.5'}
    >>> read_dict('test.ini',type_conv,purge=1)
    {'i': 3, 's': 'hi ho', 'x': 4.5}
    """

    # starting config
    opt.setdefault('purge',0)
    opt.setdefault('fs',None)  # field sep defaults to any whitespace
    opt.setdefault('strip',0)
    opt.setdefault('warn',1)
    opt.setdefault('no_empty',0)
    opt.setdefault('unique','')
    if type(opt['unique']) in StringTypes:
        unique_keys = qw(opt['unique'])
    elif type(opt['unique']) in (types.TupleType,types.ListType):
        unique_keys = opt['unique']
    else:
        raise ValueError, 'Unique keys must be given as a string, List or Tuple'

    dict = {}
    # first read in table of values as strings
    file = open(filename,'r')
    for line in file.readlines():
        line = line.strip()
        if len(line) and line[0]=='#': continue
        if len(line)>0:
            lsplit = line.split(opt['fs'],1)
            try:
                key,val = lsplit
            except ValueError:
                key,val = lsplit[0],''
            key = key.strip()
            if opt['strip']: val = val.strip()
            if val == "''" or val == '""': val = ''
            if opt['no_empty'] and (val=='' or val.isspace()):
                continue
            # if a key is found more than once in the file, build a list
            # unless it's in the 'unique' list. In that case, last found in file
            # takes precedence. User beware.
            try:
                if dict[key] and key in unique_keys:
                    dict[key] = val
                elif type(dict[key]) is types.ListType:
                    dict[key].append(val)
                else:
                    dict[key] = [dict[key],val]
            except KeyError:
                dict[key] = val
    # purge if requested
    if opt['purge']:
        accepted_keys = qwflat(type_conv.values())
        for key in dict.keys():
            if key in accepted_keys: continue
            del(dict[key])
    # now convert if requested
    if type_conv==None: return dict
    conversions = type_conv.keys()
    try: conversions.remove(None)
    except: pass
    for convert in conversions:
        for val in qw(type_conv[convert]):
            try:
                dict[val] = convert(dict[val])
            except KeyError,e:
                if opt['warn'] == 0:
                    pass
                elif opt['warn'] == 1:
                    print >>sys.stderr, 'Warning: key',val,\
                          'not found in file',filename
                elif opt['warn'] == 2:
                    raise KeyError,e
                else:
                    raise ValueError,'Warning level must be 0,1 or 2'

    return dict

#----------------------------------------------------------------------------
def flag_calls(func):
    """Wrap a function to detect and flag when it gets called.

    This is a decorator which takes a function and wraps it in a function with
    a 'called' attribute. wrapper.called is initialized to False.

    The wrapper.called attribute is set to False right before each call to the
    wrapped function, so if the call fails it remains False.  After the call
    completes, wrapper.called is set to True and the output is returned.

    Testing for truth in wrapper.called allows you to determine if a call to
    func() was attempted and succeeded."""
    
    def wrapper(*args,**kw):
        wrapper.called = False
        out = func(*args,**kw)
        wrapper.called = True
        return out

    wrapper.called = False
    wrapper.__doc__ = func.__doc__
    return wrapper

#----------------------------------------------------------------------------
class HomeDirError(Error):
    pass

def get_home_dir():
    """Return the closest possible equivalent to a 'home' directory.

    We first try $HOME.  Absent that, on NT it's $HOMEDRIVE\$HOMEPATH.

    Currently only Posix and NT are implemented, a HomeDirError exception is
    raised for all other OSes. """ #'

    try:
        return os.environ['HOME']
    except KeyError:
        if os.name == 'posix':
            raise HomeDirError,'undefined $HOME, IPython can not proceed.'
        elif os.name == 'nt':
            # For some strange reason, win9x returns 'nt' for os.name.
            try:
                return os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'])
            except:
                try:
                    # Use the registry to get the 'My Documents' folder.
                    import _winreg as wreg
                    key = wreg.OpenKey(wreg.HKEY_CURRENT_USER,
                                       "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                    homedir = wreg.QueryValueEx(key,'Personal')[0]
                    key.Close()
                    return homedir
                except:
                    return 'C:\\'
        elif os.name == 'dos':
            # Desperate, may do absurd things in classic MacOS. May work under DOS.
            return 'C:\\'
        else:
            raise HomeDirError,'support for your operating system not implemented.'

#****************************************************************************
# strings and text

class LSString(str):
    """String derivative with a special access attributes.

    These are normal strings, but with the special attributes:

        .l (or .list) : value as list (split on newlines).
        .n (or .nlstr): original value (the string itself).
        .s (or .spstr): value as whitespace-separated string.
        
    Any values which require transformations are computed only once and
    cached.

    Such strings are very useful to efficiently interact with the shell, which
    typically only understands whitespace-separated options for commands."""

    def get_list(self):
        try:
            return self.__list
        except AttributeError:
            self.__list = self.split('\n')
            return self.__list

    l = list = property(get_list)

    def get_spstr(self):
        try:
            return self.__spstr
        except AttributeError:
            self.__spstr = self.replace('\n',' ')
            return self.__spstr

    s = spstr = property(get_spstr)

    def get_nlstr(self):
        return self

    n = nlstr = property(get_nlstr)

class SList(list):
    """List derivative with a special access attributes.

    These are normal lists, but with the special attributes:

        .l (or .list) : value as list (the list itself).
        .n (or .nlstr): value as a string, joined on newlines.
        .s (or .spstr): value as a string, joined on spaces.

    Any values which require transformations are computed only once and
    cached."""

    def get_list(self):
        return self

    l = list = property(get_list)

    def get_spstr(self):
        try:
            return self.__spstr
        except AttributeError:
            self.__spstr = ' '.join(self)
            return self.__spstr

    s = spstr = property(get_spstr)

    def get_nlstr(self):
        try:
            return self.__nlstr
        except AttributeError:
            self.__nlstr = '\n'.join(self)
            return self.__nlstr

    n = nlstr = property(get_nlstr)

def raw_input_multi(header='', ps1='==> ', ps2='..> ',terminate_str = '.'):
    """Take multiple lines of input.

    A list with each line of input as a separate element is returned when a
    termination string is entered (defaults to a single '.'). Input can also
    terminate via EOF (^D in Unix, ^Z-RET in Windows).

    Lines of input which end in \\ are joined into single entries (and a
    secondary continuation prompt is issued as long as the user terminates
    lines with \\). This allows entering very long strings which are still
    meant to be treated as single entities.
    """

    try:
        if header:
            header += '\n'
        lines = [raw_input(header + ps1)]
    except EOFError:
        return []
    terminate = [terminate_str]
    try:
        while lines[-1:] != terminate:
            new_line = raw_input(ps1)
            while new_line.endswith('\\'):
                new_line = new_line[:-1] + raw_input(ps2)
            lines.append(new_line)
                
        return lines[:-1]  # don't return the termination command
    except EOFError:
        print
        return lines

#----------------------------------------------------------------------------
def raw_input_ext(prompt='',  ps2='... '):
    """Similar to raw_input(), but accepts extended lines if input ends with \\."""

    line = raw_input(prompt)
    while line.endswith('\\'):
        line = line[:-1] + raw_input(ps2)
    return line

#----------------------------------------------------------------------------
def ask_yes_no(prompt,default=None):
    """Asks a question and returns an integer 1/0 (y/n) answer.

    If default is given (one of 'y','n'), it is used if the user input is
    empty. Otherwise the question is repeated until an answer is given.
    If EOF occurs 20 times consecutively, the default answer is assumed,
    or if there is no default, an exception is raised to prevent infinite
    loops.

    Valid answers are: y/yes/n/no (match is not case sensitive)."""

    answers = {'y':1,'n':0,'yes':1,'no':0}
    ans = None
    eofs, max_eofs = 0, 20
    while ans not in answers.keys():
        try:
            ans = raw_input(prompt+' ').lower()
            if not ans:  # response was an empty string
                ans = default
            eofs = 0
        except (EOFError,KeyboardInterrupt):
            eofs = eofs + 1
            if eofs >= max_eofs:
                if default in answers.keys():
                    ans = default
                else:
                    raise
            
    return answers[ans]

#----------------------------------------------------------------------------
class EvalDict:
    """
    Emulate a dict which evaluates its contents in the caller's frame.

    Usage:
    >>>number = 19
    >>>text = "python"
    >>>print "%(text.capitalize())s %(number/9.0).1f rules!" % EvalDict()
    """

    # This version is due to sismex01@hebmex.com on c.l.py, and is basically a
    # modified (shorter) version of:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66018 by
    # Skip Montanaro (skip@pobox.com).

    def __getitem__(self, name):
        frame = sys._getframe(1)
        return eval(name, frame.f_globals, frame.f_locals)

EvalString = EvalDict  # for backwards compatibility
#----------------------------------------------------------------------------
def qw(words,flat=0,sep=None,maxsplit=-1):
    """Similar to Perl's qw() operator, but with some more options.

    qw(words,flat=0,sep=' ',maxsplit=-1) -> words.split(sep,maxsplit)

    words can also be a list itself, and with flat=1, the output will be
    recursively flattened. Examples:

    >>> qw('1 2')
    ['1', '2']
    >>> qw(['a b','1 2',['m n','p q']])
    [['a', 'b'], ['1', '2'], [['m', 'n'], ['p', 'q']]]
    >>> qw(['a b','1 2',['m n','p q']],flat=1)
    ['a', 'b', '1', '2', 'm', 'n', 'p', 'q']    """

    if type(words) in StringTypes:
        return [word.strip() for word in words.split(sep,maxsplit)
                if word and not word.isspace() ]
    if flat:
        return flatten(map(qw,words,[1]*len(words)))
    return map(qw,words)

#----------------------------------------------------------------------------
def qwflat(words,sep=None,maxsplit=-1):
    """Calls qw(words) in flat mode. It's just a convenient shorthand."""
    return qw(words,1,sep,maxsplit)

#-----------------------------------------------------------------------------
def list_strings(arg):
    """Always return a list of strings, given a string or list of strings
    as input."""

    if type(arg) in StringTypes: return [arg]
    else: return arg

#----------------------------------------------------------------------------
def grep(pat,list,case=1):
    """Simple minded grep-like function.
    grep(pat,list) returns occurrences of pat in list, None on failure.

    It only does simple string matching, with no support for regexps. Use the
    option case=0 for case-insensitive matching."""

    # This is pretty crude. At least it should implement copying only references
    # to the original data in case it's big. Now it copies the data for output.
    out=[]
    if case:
        for term in list:
            if term.find(pat)>-1: out.append(term)
    else:
        lpat=pat.lower()
        for term in list:
            if term.lower().find(lpat)>-1: out.append(term)

    if len(out): return out
    else: return None

#----------------------------------------------------------------------------
def dgrep(pat,*opts):
    """Return grep() on dir()+dir(__builtins__).

    A very common use of grep() when working interactively."""

    return grep(pat,dir(__main__)+dir(__main__.__builtins__),*opts)

#----------------------------------------------------------------------------
def idgrep(pat):
    """Case-insensitive dgrep()"""

    return dgrep(pat,0)

#----------------------------------------------------------------------------
def igrep(pat,list):
    """Synonym for case-insensitive grep."""

    return grep(pat,list,case=0)

#----------------------------------------------------------------------------
def indent(str,nspaces=4,ntabs=0):
    """Indent a string a given number of spaces or tabstops.
    
    indent(str,nspaces=4,ntabs=0) -> indent str by ntabs+nspaces.
    """
    if str is None:
        return
    ind = '\t'*ntabs+' '*nspaces
    outstr = '%s%s' % (ind,str.replace(os.linesep,os.linesep+ind))
    if outstr.endswith(os.linesep+ind):
        return outstr[:-len(ind)]
    else:
        return outstr
    
#-----------------------------------------------------------------------------
def native_line_ends(filename,backup=1):
    """Convert (in-place) a file to line-ends native to the current OS.

    If the optional backup argument is given as false, no backup of the
    original file is left.  """

    backup_suffixes = {'posix':'~','dos':'.bak','nt':'.bak','mac':'.bak'}

    bak_filename = filename + backup_suffixes[os.name]

    original = open(filename).read()
    shutil.copy2(filename,bak_filename)
    try:
        new = open(filename,'wb')
        new.write(os.linesep.join(original.splitlines()))
        new.write(os.linesep) # ALWAYS put an eol at the end of the file
        new.close()
    except:
        os.rename(bak_filename,filename)
    if not backup:
        try:
            os.remove(bak_filename)
        except:
            pass
    
#----------------------------------------------------------------------------
def get_pager_cmd(pager_cmd = None):
    """Return a pager command.

    Makes some attempts at finding an OS-correct one."""
    
    if os.name == 'posix':
        default_pager_cmd = 'less -r'  # -r for color control sequences
    elif os.name in ['nt','dos']:
        default_pager_cmd = 'type'

    if pager_cmd is None:
        try:
            pager_cmd = os.environ['PAGER']
        except:
            pager_cmd = default_pager_cmd
    return pager_cmd

#-----------------------------------------------------------------------------
def get_pager_start(pager,start):
    """Return the string for paging files with an offset.

    This is the '+N' argument which less and more (under Unix) accept.
    """

    if pager in ['less','more']:
        if start:
            start_string = '+' + str(start)
        else:
            start_string = ''
    else:
        start_string = ''
    return start_string

#----------------------------------------------------------------------------
def page_dumb(strng,start=0,screen_lines=25):
    """Very dumb 'pager' in Python, for when nothing else works.

    Only moves forward, same interface as page(), except for pager_cmd and
    mode."""

    out_ln  = strng.splitlines()[start:]
    screens = chop(out_ln,screen_lines-1)
    if len(screens) == 1:
        print >>Term.cout, os.linesep.join(screens[0])
    else:
        for scr in screens[0:-1]:
            print >>Term.cout, os.linesep.join(scr)
            ans = raw_input('---Return to continue, q to quit--- ')
            if ans.lower().startswith('q'):
                return
        print >>Term.cout, os.linesep.join(screens[-1])

#----------------------------------------------------------------------------
def page(strng,start=0,screen_lines=0,pager_cmd = None):
    """Print a string, piping through a pager after a certain length.

    The screen_lines parameter specifies the number of *usable* lines of your
    terminal screen (total lines minus lines you need to reserve to show other
    information).

    If you set screen_lines to a number <=0, page() will try to auto-determine
    your screen size and will only use up to (screen_size+screen_lines) for
    printing, paging after that. That is, if you want auto-detection but need
    to reserve the bottom 3 lines of the screen, use screen_lines = -3, and for
    auto-detection without any lines reserved simply use screen_lines = 0.

    If a string won't fit in the allowed lines, it is sent through the
    specified pager command. If none given, look for PAGER in the environment,
    and ultimately default to less.

    If no system pager works, the string is sent through a 'dumb pager'
    written in python, very simplistic.
    """
    
    # Ugly kludge, but calling curses.initscr() flat out crashes in emacs
    TERM = os.environ.get('TERM','dumb')
    if TERM in ['dumb','emacs'] and os.name != 'nt':
        print strng
        return
    # chop off the topmost part of the string we don't want to see
    str_lines = strng.split(os.linesep)[start:]
    str_toprint = os.linesep.join(str_lines)
    num_newlines = len(str_lines)
    len_str = len(str_toprint)
    
    # Dumb heuristics to guesstimate number of on-screen lines the string
    # takes.  Very basic, but good enough for docstrings in reasonable
    # terminals. If someone later feels like refining it, it's not hard.
    numlines = max(num_newlines,int(len_str/80)+1)

    screen_lines_def = 25 # default value if we can't auto-determine

    # auto-determine screen size
    if screen_lines <= 0:
        if TERM=='xterm':
            try:
                import curses
                if hasattr(curses,'initscr'):
                    use_curses = 1
                else:
                    use_curses = 0
            except ImportError:
                use_curses = 0
        else:
            # curses causes problems on many terminals other than xterm.
            use_curses = 0
        if use_curses:
                scr = curses.initscr()
                screen_lines_real,screen_cols = scr.getmaxyx()
                curses.endwin()
                screen_lines += screen_lines_real
                #print '***Screen size:',screen_lines_real,'lines x',\
                #screen_cols,'columns.' # dbg
        else:
                screen_lines += screen_lines_def

    #print 'numlines',numlines,'screenlines',screen_lines  # dbg
    if numlines <= screen_lines :
        #print '*** normal print'  # dbg
        print >>Term.cout, str_toprint
    else:
        # Try to open pager and default to internal one if that fails.
        # All failure modes are tagged as 'retval=1', to match the return
        # value of a failed system command.  If any intermediate attempt
        # sets retval to 1, at the end we resort to our own page_dumb() pager.
        pager_cmd = get_pager_cmd(pager_cmd)
        pager_cmd += ' ' + get_pager_start(pager_cmd,start)
        if os.name == 'nt':
            if pager_cmd.startswith('type'):
                # The default WinXP 'type' command is failing on complex strings.
                retval = 1
            else:
                tmpname = tempfile.mktemp('.txt')
                tmpfile = file(tmpname,'wt')
                tmpfile.write(strng)
                tmpfile.close()
                cmd = "%s < %s" % (pager_cmd,tmpname)
                if os.system(cmd):
                  retval = 1
                else:
                  retval = None
                os.remove(tmpname)
        else:
            try:
                retval = None
                # if I use popen4, things hang. No idea why.
                #pager,shell_out = os.popen4(pager_cmd)
                pager = os.popen(pager_cmd,'w')
                pager.write(strng)
                pager.close()
                retval = pager.close()  # success returns None
            except IOError,msg:  # broken pipe when user quits
                if msg.args == (32,'Broken pipe'):
                    retval = None
                else:
                    retval = 1
            except OSError:
                # Other strange problems, sometimes seen in Win2k/cygwin
                retval = 1
        if retval is not None:
            page_dumb(strng,screen_lines=screen_lines)

#----------------------------------------------------------------------------
def page_file(fname,start = 0, pager_cmd = None):
    """Page a file, using an optional pager command and starting line.
    """

    pager_cmd = get_pager_cmd(pager_cmd)
    pager_cmd += ' ' + get_pager_start(pager_cmd,start)

    try:
        if os.environ['TERM'] in ['emacs','dumb']:
            raise EnvironmentError
        xsys(pager_cmd + ' ' + fname)
    except:
        try:
            if start > 0:
                start -= 1
            page(open(fname).read(),start)
        except:
            print 'Unable to show file',`fname`

#----------------------------------------------------------------------------
def snip_print(str,width = 75,print_full = 0,header = ''):
    """Print a string snipping the midsection to fit in width.

    print_full: mode control:
      - 0: only snip long strings
      - 1: send to page() directly.
      - 2: snip long strings and ask for full length viewing with page()
    Return 1 if snipping was necessary, 0 otherwise."""

    if print_full == 1:
        page(header+str)
        return 0

    print header,
    if len(str) < width:
        print str
        snip = 0
    else:
        whalf = int((width -5)/2)
        print str[:whalf] + ' <...> ' + str[-whalf:]
        snip = 1
    if snip and print_full == 2:
        if raw_input(header+' Snipped. View (y/n)? [N]').lower() == 'y':
            page(str)
    return snip

#****************************************************************************
# lists, dicts and structures

def belong(candidates,checklist):
    """Check whether a list of items appear in a given list of options.

    Returns a list of 1 and 0, one for each candidate given."""

    return [x in checklist for x in candidates]

#----------------------------------------------------------------------------
def uniq_stable(elems):
    """uniq_stable(elems) -> list

    Return from an iterable, a list of all the unique elements in the input,
    but maintaining the order in which they first appear.

    A naive solution to this problem which just makes a dictionary with the
    elements as keys fails to respect the stability condition, since
    dictionaries are unsorted by nature.

    Note: All elements in the input must be valid dictionary keys for this
    routine to work, as it internally uses a dictionary for efficiency
    reasons."""
    
    unique = []
    unique_dict = {}
    for nn in elems:
        if nn not in unique_dict:
            unique.append(nn)
            unique_dict[nn] = None
    return unique

#----------------------------------------------------------------------------
class NLprinter:
    """Print an arbitrarily nested list, indicating index numbers.

    An instance of this class called nlprint is available and callable as a
    function.
    
    nlprint(list,indent=' ',sep=': ') -> prints indenting each level by 'indent'
    and using 'sep' to separate the index from the value. """

    def __init__(self):
        self.depth = 0
    
    def __call__(self,lst,pos='',**kw):
        """Prints the nested list numbering levels."""
        kw.setdefault('indent',' ')
        kw.setdefault('sep',': ')
        kw.setdefault('start',0)
        kw.setdefault('stop',len(lst))
        # we need to remove start and stop from kw so they don't propagate
        # into a recursive call for a nested list.
        start = kw['start']; del kw['start']
        stop = kw['stop']; del kw['stop']
        if self.depth == 0 and 'header' in kw.keys():
            print kw['header']
            
        for idx in range(start,stop):
            elem = lst[idx]
            if type(elem)==type([]):
                self.depth += 1
                self.__call__(elem,itpl('$pos$idx,'),**kw)
                self.depth -= 1
            else:
                printpl(kw['indent']*self.depth+'$pos$idx$kw["sep"]$elem')

nlprint = NLprinter()
#----------------------------------------------------------------------------
def all_belong(candidates,checklist):
    """Check whether a list of items ALL appear in a given list of options.

    Returns a single 1 or 0 value."""

    return 1-(0 in [x in checklist for x in candidates])

#----------------------------------------------------------------------------
def sort_compare(lst1,lst2,inplace = 1):
    """Sort and compare two lists.

    By default it does it in place, thus modifying the lists. Use inplace = 0
    to avoid that (at the cost of temporary copy creation)."""
    if not inplace:
        lst1 = lst1[:]
        lst2 = lst2[:]
    lst1.sort(); lst2.sort()
    return lst1 == lst2

#----------------------------------------------------------------------------
def mkdict(**kwargs):
    """Return a dict from a keyword list.

    It's just syntactic sugar for making ditcionary creation more convenient:
    # the standard way
    >>>data = { 'red' : 1, 'green' : 2, 'blue' : 3 }
    # a cleaner way
    >>>data = dict(red=1, green=2, blue=3)

    If you need more than this, look at the Struct() class."""

    return kwargs

#----------------------------------------------------------------------------
def list2dict(lst):
    """Takes a list of (key,value) pairs and turns it into a dict."""

    dic = {}
    for k,v in lst: dic[k] = v
    return dic

#----------------------------------------------------------------------------
def list2dict2(lst,default=''):
    """Takes a list and turns it into a dict.
    Much slower than list2dict, but more versatile. This version can take
    lists with sublists of arbitrary length (including sclars)."""

    dic = {}
    for elem in lst:
        if type(elem) in (types.ListType,types.TupleType):
            size = len(elem)
            if  size == 0:
                pass
            elif size == 1:
                dic[elem] = default
            else:
                k,v = elem[0], elem[1:]
                if len(v) == 1: v = v[0]
                dic[k] = v
        else:
            dic[elem] = default
    return dic

#----------------------------------------------------------------------------
def flatten(seq):
    """Flatten a list of lists (NOT recursive, only works for 2d lists)."""

    # bug in python??? (YES. Fixed in 2.2, let's leave the kludgy fix in).

    # if the x=0 isn't made, a *global* variable x is left over after calling
    # this function, with the value of the last element in the return
    # list. This does seem like a bug big time to me.

    # the problem is fixed with the x=0, which seems to force the creation of
    # a local name

    x = 0 
    return [x for subseq in seq for x in subseq]

#----------------------------------------------------------------------------
def get_slice(seq,start=0,stop=None,step=1):
    """Get a slice of a sequence with variable step. Specify start,stop,step."""
    if stop == None:
        stop = len(seq)
    item = lambda i: seq[i]
    return map(item,xrange(start,stop,step))

#----------------------------------------------------------------------------
def chop(seq,size):
    """Chop a sequence into chunks of the given size."""
    chunk = lambda i: seq[i:i+size]
    return map(chunk,xrange(0,len(seq),size))

#----------------------------------------------------------------------------
def with(object, **args):
    """Set multiple attributes for an object, similar to Pascal's with.

    Example:
    with(jim,
         born = 1960,
         haircolour = 'Brown',
         eyecolour = 'Green')

    Credit: Greg Ewing, in
    http://mail.python.org/pipermail/python-list/2001-May/040703.html"""

    object.__dict__.update(args)

#----------------------------------------------------------------------------
def setattr_list(obj,alist,nspace = None):
    """Set a list of attributes for an object taken from a namespace.

    setattr_list(obj,alist,nspace) -> sets in obj all the attributes listed in
    alist with their values taken from nspace, which must be a dict (something
    like locals() will often do) If nspace isn't given, locals() of the
    *caller* is used, so in most cases you can omit it.

    Note that alist can be given as a string, which will be automatically
    split into a list on whitespace. If given as a list, it must be a list of
    *strings* (the variable names themselves), not of variables."""

    # this grabs the local variables from the *previous* call frame -- that is
    # the locals from the function that called setattr_list().
    # - snipped from weave.inline()
    if nspace is None:
        call_frame = sys._getframe().f_back
        nspace = call_frame.f_locals

    if type(alist) in StringTypes:
        alist = alist.split()
    for attr in alist:
        val = eval(attr,nspace)
        setattr(obj,attr,val)

#----------------------------------------------------------------------------
def getattr_list(obj,alist,*args):
    """getattr_list(obj,alist[, default]) -> attribute list.

    Get a list of named attributes for an object. When a default argument is
    given, it is returned when the attribute doesn't exist; without it, an
    exception is raised in that case.

    Note that alist can be given as a string, which will be automatically
    split into a list on whitespace. If given as a list, it must be a list of
    *strings* (the variable names themselves), not of variables."""

    if type(alist) in StringTypes:
        alist = alist.split()
    if args:
        if len(args)==1:
            default = args[0]
            return map(lambda attr: getattr(obj,attr,default),alist)
        else:
            raise ValueError,'getattr_list() takes only one optional argument'
    else:
        return map(lambda attr: getattr(obj,attr),alist)
    
#----------------------------------------------------------------------------
def map_method(method,object_list,*argseq,**kw):
    """map_method(method,object_list,*args,**kw) -> list

    Return a list of the results of applying the methods to the items of the
    argument sequence(s).  If more than one sequence is given, the method is
    called with an argument list consisting of the corresponding item of each
    sequence. All sequences must be of the same length.

    Keyword arguments are passed verbatim to all objects called.

    This is Python code, so it's not nearly as fast as the builtin map()."""

    out_list = []
    idx = 0
    for object in object_list:
        try:
            handler = getattr(object, method)
        except AttributeError:
            out_list.append(None)
        else:
            if argseq:
                args = map(lambda lst:lst[idx],argseq)
                #print 'ob',object,'hand',handler,'ar',args # dbg
                out_list.append(handler(args,**kw))
            else:
                out_list.append(handler(**kw))
        idx += 1
    return out_list

#----------------------------------------------------------------------------
# Proposed popitem() extension, written as a method

class NotGiven: pass

def popkey(dct,key,default=NotGiven):
    """Return dct[key] and delete dct[key].

    If default is given, return it if dct[key] doesn't exist, otherwise raise
    KeyError.  """

    try:
        val = dct[key]
    except KeyError:
        if default is NotGiven:
            raise
        else:
            return default
    else:
        del dct[key]
        return val
#*************************** end of file <genutils.py> **********************

