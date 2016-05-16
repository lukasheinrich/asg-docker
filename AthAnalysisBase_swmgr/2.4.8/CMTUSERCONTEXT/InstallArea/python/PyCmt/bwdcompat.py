import subprocess

### monkey-patch subprocess (fwd compat w/ py-3.x) ----------------------------
def getstatusoutput(cmd, *popenargs, **kwargs):
    if isinstance(cmd, basestring):
        cmd = cmd.split()
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    kwargs['stdout'] = subprocess.PIPE
    p = subprocess.Popen(cmd, *popenargs, **kwargs)
    sc = p.returncode
    if sc is None:
        sc = 0
    fd = p.stdout
    out= ''.join(list(fd.readlines()))
    if out[-1:] == '\n': out = out[:-1]
    return sc,out
subprocess.getstatusoutput = getstatusoutput
del getstatusoutput

def getstatus(cmd, *popenargs, **kwargs):
    return subprocess.getstatusoutput(cmd, *popenargs, **kwargs)[0]
subprocess.getstatus = getstatus
del getstatus

def getoutput(cmd, *popenargs, **kwargs):
    return subprocess.getstatusoutput(cmd, *popenargs, **kwargs)[1]
subprocess.getoutput = getoutput
del getoutput
### ---------------------------------------------------------------------------
