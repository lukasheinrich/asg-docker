# @file: pyshell/localshell.py

"""Talk programmatically to a local shell, via pseudo-terminal"""

# stdlib imports
import os, pty, sys
import logging

# project imports
import basicshell

### data ----------------------------------------------------------------------
__all__ = [
    'LocalShell',
    ]
msg = logging.getLogger ('LocalShell')
if len(msg.handlers) == 0:
    logging.basicConfig()

### helpers -------------------------------------------------------------------
class _EnvMapping (object):
    """helper class to get and put environment variables"""
    def __init__ (self, sh):
        self.shell = sh
    def __getitem__ (self, key):
        value = self.shell.getenv (key)
        if not value:
            raise KeyError, key
        return value
    def __setitem__ (self, key, value):
        self.shell.putenv (key, value)
    def has_key (self, key):
        try:
            return not not self.shell.getenv (key)
        except KeyError:
            return False
    def items (self):
        d = {}
        sc, out = self.shell.getstatusoutput ('env')
        if sc:
            return d
        import re
        pat = re.compile (r'(?P<EnvKey>.*?)=(?P<EnvValue>.*)')
        for l in out.splitlines():
            if l.count('=') <= 0:
                continue
            m = re.match (pat, l)
            if m is None:
                print "::: [%s]"%l
                raise RuntimeError ("err")
            assert m is not None, "%s"%m
            m = m.groupdict()
            d[m['EnvKey']] = m['EnvValue']
        return d
    
class _PathMapping (object):
    """helper class to mimic os.path"""
    def __init__ (self, sh):
        self.shell = sh
    def exists (self, path):
        status, output = self.shell.getstatusoutput('/bin/ls -ld '+path)
        return not status
    def __getattr__ (self, name):
        try:
            msg.debug ('selecting [%s] from os.path...', name)
            return os.path.__dict__[name]
        except KeyError:
            raise AttributeError, name

### local shell class ---------------------------------------------------------
class LocalShell (basicshell.BasicShell):
    """implementation of a local programmatic shell.
    """

    def __init__ (self):
        """setup shell and read loop"""

        # start a working shell and connect through a pseudo-terminal
        pid, fd = pty.fork()

        if pid == 0:                                                # child
            os.execv ('/bin/sh', ['sh'])

        # maintain front process state
        self.interactive = 0

        # environmental control
        self.environ = _EnvMapping (self)

        # mimic os.path
        self.path = _PathMapping (self)
        
        # base class setup
        super (LocalShell, self).__init__ (fd, pid, r'\S+> ') # parent
        #basicshell.BasicShell.__init__ (self, fd, pid, r'\S+> ') # parent


        # store the current work directory
        self.cwd = ''
        self.getcwd()
        

    # skip commands
    def command (self, cmd):
        pass

    def run (self, cmd, verbose=False):
        """shorthand for `getstatusoutput` with check of status
        """
        if verbose:
            sc = self.system (cmd)
            if sc:
                err = 'could not run [%s] (sc=%d)'%(cmd,sc)
                msg.error (err)
                raise RuntimeError (err)
        else:
            sc,out = self.getstatusoutput (cmd)
            if sc:
                err = 'could not run [%s]:\n%s'%(cmd,out)
                msg.error (err)
                raise RuntimeError (err)
        pass

    def prompt (self, prompt):
        """manage multiple prompts"""
        if prompt != basicshell.PROMPT:
            self.interactive = 1
        else:
            self.interactive = 0

    def write (self, text):
        """dump output"""
        sys.stdout.write (text)

    def getcwd (self):
        """get the current directory.
        Similar to `os.getcwd()`
        """

        # this protects against programming errors, not against races
        if not self.lock.locked():
            stat, out = self.getstatusoutput ('pwd')
            if stat != 0:
                raise OSError, 'could not determine current directory'

            self.cwd = out.strip()
        return self.cwd

    def chdir (self, dir):
        """change the current working directory.
        Similar to `os.chdir()`
        """
        if self.cwd == dir or not dir or self.interactive:
            return

        # preliminary reset of cef
        if dir[0] != os.sep:
            self.cwd = os.path.normpath (os.path.join(self.cwd, dir))
        else:
            self.cwd = dir

        if self.system ('cd '+dir) != 0:
            raise OSError, 'can\'t enter [%s]'%dir

        # reset current working directory cache
        self.getcwd()

    def mkdir (self, dir):
        """create `dir` in the current working directory.
        Similar to `os.mkdir()`
        """
        if self.system ('mkdir -p '+dir) != 0:
            raise OSError, 'can\'t create [%s]'%dir

    def remove (self, fn):
        """remove `fn` from the current working directory.
        Similar to `os.remove()`
        """
        if self.system ('rm -f '+fn) != 0:
            raise OSError, 'can\'t remove [%s]'%fn
        
    def symlink (self, src, dst):
        """make a symlink to `src` named `dst`.
        Similar to `os.symlink()`
        """
        if self.system ('/bin/ln -sf %s %s'%(src, dst)):
            raise OSError, 'can\'t symlink [%s] as [%s]' % (src, dst)

    def getenv (self, name):
        """get an environment variable"""
        stat, out = self.getstatusoutput ('echo $%s'%name)

        # env may contain an error message if the envvar does not exist
        if stat == 0:
            return out.strip() # strip new line
        return ''

    def putenv (self, name, value):
        """set an environment variable"""
        if self.shellc == 'c':
            status = self.system ('setenv %s %s' % (name, value))
        else:
            status = self.system ('export %s=%s' % (name, value))
        return status

    def unsetenv (self, name):
        """remove an environment variable"""
        if self.shellc == 'c':
            status = self.system ('unsetenv '+name)
        else:
            status = self.system ('unset '+name)
        return status

    def getstatusoutput (self, cmd, *args, **kwd):
        """execute a command and return its status and output as a tuple.
        Similar to `commands.getstatusoutput()`
        """

        # turn echo off, start with a fresh output buff
        self.set_echo (onoff=0)
        self.reset_buffer()

        # execute command, output will be collected in the buffer
        status = self.system (cmd)

        # done: copy buffer and reset
        buf = self.buffer
        self.set_echo (onoff=1)
        self.reset_buffer()

        return status, buf.strip()

    # use `os` for all other shell functionalities
    def __getattr__ (self, name):
        try:
            msg.debug ('selecting [%s] from os...', name)
            return os.__dict__[name]
        except KeyError:
            raise AttributeError, name

    def __eq__ (self, other):
        return repr(self) == repr(other)
    
    
##     def while_waiting (self):
##         msg.debug ("waiting for lock...")
        
