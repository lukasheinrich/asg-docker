# @file: pyshell/basicshell.py

"""Talk programmatically to a shell, via a pseudo-terminal"""

import os, re, sys, thread, time
import pty, select
import logging

import vt100
import utils as shell_utils

### data ----------------------------------------------------------------------
__all__ = [
    'BasicShell',
    'wait_for_pattern',
    ]

msg = logging.getLogger ('basicshell')
if len(msg.handlers)==0:
    logging.basicConfig()

PROMPT     = '_PY_SHELL_'
SHELLLIST  = ['csh', 'sh']
SLEEPTIME  = 0.01
PCTIMEOUT  = 0.05
USRTIMEOUT = 10.

### read loops ----------------------------------------------------------------
def wait_for_pattern (fd, timeout, patterns=None, initial_data=''):
    """read data from file descriptor `fd` as it becomes available.
    process it and search for matches among `patterns`.
    return on `timeout` (in seconds) or when a pattern is found.
    some `initial_data` on which to start searching may be given.

    return (<residual data>, <found pattern>)
    """

    if patterns is None:
        patterns = []

    lapsed_time = 0.
    data = initial_data

    while 1:
        # look for any data if no patterns are provided
        if not patterns and 1<len(vt100.filter(data)): # allow for a newline
            return data, None
        elif data:
            # scan for requested patterns in the data
            for pattern in patterns:
                pos = data.find(pattern)
                if 0<=pos:
                    return data[pos+len(pattern)+1:], pattern # found a pattern

        # look for non-blocking reads
        rfds, wfds, xfds = select.select ([fd, 0], [], [], PCTIMEOUT)
        if fd in rfds:
            data = data + os.read (fd, 1024)                  # safe read
        else:
            # check for timeout
            lapsed_time = lapsed_time + PCTIMEOUT + SLEEPTIME
            if timeout <= lapsed_time:
                raise OSError, 'timed out while waiting for data (fd=%d)'%fd

            # wait a bit
            time.sleep (SLEEPTIME)

def _read_dispatch_loop (fd, shell, alt_prompt='', initial_data=''):
    """read data from file descriptor `fd` as it becomes available.
    process it and send it to `shell` for output.
    when a magic prompt (or alternative `alt_prompt` is encountered, `shell` is
    unlocked. Some `initial_data` on which to start feeding the output may be
    given.
    """

    prompt = PROMPT
    if alt_prompt:
        prompt += '|'+alt_prompt
    promptrex = re.compile (prompt)

    try:
        data, cmd_absorbed = initial_data, 0

        while 1:
            rfds, wfds, xfds = select.select ([fd, 0], [], [], PCTIMEOUT)

            if fd in rfds:
                data = data + os.read (fd, 1024)

                eolpos = data.find('\n')
                while 0 <= eolpos:
                    # pre-process the line
                    line = vt100.filter (data[:eolpos])

                    # special care for command lines
                    res = promptrex.match (line)
                    if not res:
                        shell.output (line+os.linesep)
                    else:
                        shell.command (line[len(res.group()):])
                        cmd_absorbed = 1
                        
                    # data leftover and new end of line position
                    data = data[eolpos+1:]
                    eolpos = data.find ('\n')

                # outside line loop, scan for prompt (as start for new input)
                line = vt100.filter (data)
                if line and cmd_absorbed:
                    res = promptrex.match (line)
                    if res:
                        prp = res.group()
                        # allow for prompt printing
                        shell.prompt (prp)
                        shell.lock.release()

                        # put the prompt back for command absorbtion
                        data, cmd_absorbed = prp, 0
            else:
                time.sleep (SLEEPTIME)

    except: #ok on exit, for debugging otherwise
        try:
            import traceback
            traceback.print_exc()
        except ImportError:
            pass

### abstract base class for shells --------------------------------------------
class BasicShell (object):
    """Base class for shells.

    Subclasses need to implement prompt(self, prompt) and write(self, text)
    """

    # setup shell and read loop
    def __init__ (self, master_fd, child_pid, alt_prompt):
        # save file descriptor and process id
        self.master_fd = master_fd
        self.child_pid = child_pid

        # allow only one process at a time
        self.lock = thread.allocate_lock()

        # no wrapped echo until reading starts
        self.echo = 0
        self.bug  = ''    # output buffer

        # guess shell type
        msg.debug ('guessing shell family...')
        os.write (self.master_fd, 'echo $0\n')
        try:
            shellc = wait_for_pattern (self.master_fd, USRTIMEOUT, SHELLLIST)
        except OSError, e:
            msg.debug ('for shell testing: %s', e)
            shellc = ('', 'bash')        # gambling...
        msg.debug ('choosing [%s] shell family', shellc[1])

        # set prompt
        msg.debug ('setting magic prompt...')
        if shellc[1] == 'csh':
            self._shellc = 'c'
            os.write (self.master_fd,
                      'set prompt=%s\nexport TERM=vt100; echo $TERM\n'%PROMPT)
        else:
            self._shellc = ''
            os.write (self.master_fd,
                      'export PS1=%s\nexport TERM=vt100; echo $TERM\n'%PROMPT)

        # empty buffer, there may or may not be a command echo
        try:
            data = '', None
            while data[1] != 'vt100':
                data = wait_for_pattern (self.master_fd, USRTIMEOUT,
                                         patterns=['=vt100', 'vt100'],
                                         initial_data=data[0])
        except OSError, e:
            msg.debug ('for command echo: %s', e)
                
        # remove leading new-lines
        data = data[0].lstrip()

        # start reading continuously
        msg.debug ('setup done, firing up dispatch loop...')
        self.echo = 1
        thread.start_new_thread (_read_dispatch_loop,
                                 (self.master_fd, self, alt_prompt, data))
        msg.debug ('basic shell properly initialized')

    # logout on destruction
    def __del__ (self):
        self._exec ('exit')

    def _exec (self, cmd):
        """execute a command"""
        while not self.lock.acquire (0):
            time.sleep (SLEEPTIME)
        os.write (self.master_fd, cmd+os.linesep)
        
    def _wait_lock (self):
        """wait for the lock to become available"""
        while self.lock.locked():
            self.while_waiting()

    def set_echo (self, onoff):
        """output control"""
        self.echo = not not onoff

    def reset_buffer (self):
        self.buf = ''

    @property
    def buffer (self):
        return self.buf

    def output (self, data):
        """dump output"""
        if self.echo:
            self.write (data)
        else:
            self.buf = self.buf + data

    def system (self, cmd):
        """execute a command and return the status code.
        Similar to `os.system()`, except that there is no subshell
        """

        # execute the command and wait for it to be done
        self._exec (cmd)
        self._wait_lock()

        if not self.interactive:
            # retrieve status code for shell
            echo, buf = self.echo, self.buf
            self.echo, self.buf = 0, ''
            self._exec ('echo $?')
            self._wait_lock()

            try:
                status = int (self.buf)
            except ValueError:
                msg.debug ('process exit status can not be determined')
                status = -1

            self.echo = echo
            self.buf  = buf
        else:
            # no way of really knowing...
            status = 0
            
        # clean-up any waiting taskes
        self.stop_waiting()

        # done
        return status

    def while_waiting (self):
        """wait processing"""
        pass

    def stop_waiting (self):
        pass

    @property
    def shellc (self):
        """return 'c' for csh or '' for bash (or equiv.)"""
        return self._shellc

    def source (self, script, args=''):
        """source environment settings from `script`.
        If `shell` is `os`, then an optional environment `env` can be given.
        
        return 0: all ok
        return 1: `script` can not be located
        return 2: sourcing of `script` failed
        """
        return shell_utils.source (script, shell=self, args=args)
    
            
