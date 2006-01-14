import os
import sys
import platform
import ConfigParser
import logging

log = logging.getLogger('settings')

if platform.system() == 'Windows':
#    from win32com.shell import shell, shellcon
    # 1. we should use CSIDL_LOCAL_APPDATA instead if we have large files
    # 2. does this work?  os.environ['APPDATA']
#    appdata = shell.SHGetPathFromIDList(shell.SHGetSpecialFolderLocation(0, shellcon.CSIDL_APPDATA))
    appdata = os.environ['APPDATA']
    USERDATADIR = os.path.join(appdata, 'grafity')
if platform.system() == 'Linux':
    USERDATADIR = os.path.expanduser('~/.grafity')


if not os.path.exists(USERDATADIR):
    os.mkdir(USERDATADIR)

for subdir in ['functions', 'scripts']:
    dir = os.path.join(USERDATADIR, subdir)
    if not os.path.exists(dir):
        os.mkdir(dir)

log.info('User data directory is %s', USERDATADIR)

DATADIR = os.path.normpath(os.path.abspath(os.path.dirname(sys.argv[0]))+'/../') + '/'

log.info('Data directory is %s', DATADIR)

class Settings(object):
    def __init__(self, filename):
        self.filename = filename
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.filename)
        log.info('Reading settings file %s', self.filename)

    def write(self):
        self.config.write(open(self.filename, 'w'))
        log.info('Writing settings file %s', self.filename)

    def set(self, section, key, value):
        if section not in self.config.sections():
            self.config.add_section(section)
        self.config.set(section, key, value)
        log.info('Setting option %s/%s', section, key)
        self.write()

    def get(self, section, key):
        log.info('Getting option %s/%s', section, key)
        try:
            return self.config.get(section, key)
        except ConfigParser.NoSectionError:
            return None

settings = Settings(os.path.join(USERDATADIR,'grafity.cfg'))
