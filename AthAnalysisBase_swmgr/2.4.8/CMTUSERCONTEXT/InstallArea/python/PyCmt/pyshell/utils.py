
# @file: pyshell/utils.py

"""Unix shell information and utilities"""

import logging, os, re
from PyCmt.bwdcompat import subprocess

### data ----------------------------------------------------------------------
__all__ = [
    'BASH', 'CSH',
    'shell_family', 'shell_ext',
    'source',
    ]

BASH = 'bash'
CSH  = 'csh'

msg = logging.getLogger ('shellutils')
if len(msg.handlers)==0:
    logging.basicConfig()

### shell information ---------------------------------------------------------
_shell_prog = {}
def shell_name (shell=os):
    """return name of the `shell`"""
    key = repr (shell)
    if not (key in _shell_prog):
        p = shell.popen ('echo $0')
        fullname = p.readlines()[0][:-1]
        p.close()

        # use of 'sh' is hopefully appropriate
        if fullname in ('/bin/sh', 'sh', '$'):
            if shell.path.islink ('/bin/sh'):
                fullname = shell.readlink ('/bin/sh')

        _shell_prog[key] = shell.path.basename (fullname)

    return _shell_prog[key]

_shell_family = {}
def shell_family (shell=os):
    """return the family of `shell` (either bash, csh or java)"""
    key = repr (shell)
    if not (key in _shell_family):
        if re.search ('csh', shell_name (shell)): #'csh' or 'tcsh'
            _shell_family[key] = CSH
        else:
            _shell_family[key] = BASH
    return _shell_family[key]

_shell_ext = {}
def shell_ext (shell=os):
    """return the extension for `shell`, based on family (.csh or .sh)"""
    key = repr (shell)
    if not (key in _shell_ext):
        if shell_family (shell) == CSH:
            _shell_ext[key] = '.csh'
        else:
            _shell_ext[key] = '.sh'
    return _shell_ext[key]

_shell_no_login_flag = {}
def shell_no_login_flag (shell=os):
    """return the flag that prevents running the login scripts
    on shell startup"""
    key = repr (shell)
    if not (key in _shell_no_login_flag):
        if shell_name(shell) == 'bash':
            _shell_no_login_flag[key] = '--noprofile'
        else:
            _shell_no_login_flag[key] = '-f'
    return _shell_no_login_flag[key]

### env. variables ------------------------------------------------------------
def is_defined (name, env = None):
    """verify the definition of variable `name` in environment `env`.
    return 0: no non-empty value associated with `name`
    return 1: `name` is defined and non-empty
    """
    if env is None:
        env = os.environ
    try:
        return not not env[name]
    except KeyError:
        return 0

def expand (name, shell=os):
    """return the expansion of `name` on the environment of `shell`"""
    return shell.path.expanduser (shell.path.expandvars(name))

### source a file into the shell environment ----------------------------------
def source (script, shell=os, env=None, args=''):
    """source environment settings from `script`.
    If `shell` is `os`, then an optional environment `env` can be given.

    return 0: all ok
    return 1: `script` can not be located
    return 2: sourcing of `script` failed
    """
    global msg
    
    script = expand (script, shell)
    if not shell.path.exists (script):
        script = script + shell_ext (shell)
        if not shell.path.exists (script):
            msg.debug ('script [%s] does not exist', script)
            return 1

    msg.debug ('sourcing [%s]', script)
    if shell is os:
        # the following executes on 'os'
        stat, out = subprocess.getstatusoutput (
            'source '+script+' '+args+' && env')
        # verify success (note CMT workaround...)
        if stat != 0 or len(out)==0 or out.find('No such file')>=0:
            msg.debug ('sourcing of [%s] failed (code %d)\n%s',
                       script, stat, shell.linesep.join(out.splitlines()))
            return 2

        out = re.split (shell.linesep, out)
        envre = re.compile (r'(\S+)\s*=\s*(\S+)')

        # modify the environment (the sub-shell has exited)
        if env is None:
            env = shell.environ

        msg.debug ('setting environment variables...')
        for o in out:
            res = envre.search (o)
            if res:
                g = res.groups()
                env[g[0]] = g[1]

    else:
        # don't know how shell actually behaves,
        # just go for it and cross fingers
        rc = shell.system ('source %s %s' % (script, args))
        if rc:
            return 2

    return 0

    
