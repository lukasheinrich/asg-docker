# -*- python -*-
# @file PyCmt/python/pkgbuild/__init__.py
# @purpose a simple build system
# @author Sebastien Binet <binet@cern.ch>

from __future__ import with_statement

__doc__ = "A simple build system"
__author__ = "Sebastien Binet <binet@cern.ch>"
__version__= "$Revision$"


### imports -------------------------------------------------------------------
import sys
import os
import os.path as osp
import imp
import inspect

from PyCmt.Logging import logging

### globals -------------------------------------------------------------------
msg = logging.getLogger('PkgBuilder')
msg.setLevel(logging.INFO)
#msg.setLevel(logging.VERBOSE)

# FIXME: should be more easily configurable
_DO_RELOCATE = True
#_DO_RELOCATE = False

### utils ---------------------------------------------------------------------
def relpath(path, start=osp.curdir):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    start_list = osp.abspath(start).split(osp.sep)
    path_list = osp.abspath(path).split(osp.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(osp.commonprefix([start_list, path_list]))

    rel_list = [osp.pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return osp.curdir
    return osp.join(*rel_list)
setattr(osp, 'relpath', relpath) # fwd-compat w/ 2.6
del relpath

def safe_symlink(src, dst):
    """a safe version of os.symlink:
    check if the destination `dst` exists (and remove it)
    create a symbolic link pointing to `src` named `dst`
    """
    if osp.exists(dst):
        os.remove(dst)
    return os.symlink(src, dst)
setattr(os, 'safe_symlink', safe_symlink)
del safe_symlink

def _remove(p, ignore_errors=False, onerror=None, msg=msg):
    if not osp.exists(p):
        return
    msg.verbose("removing [%s]...", p)
    import commands as com
    sc,out = com.getstatusoutput("/bin/rm -rf %s" % p)
    if sc:
        msg.error(out)
    """
    if (not osp.isdir(p) or osp.islink(p)):
        os.remove(p)
    else:
        import shutil
        shutil.rmtree(p, ignore_errors=ignore_errors, onerror=onerror)
    """
    
def _mkstemp(*args, **kwargs):
    import tempfile
    fd, fname = tempfile.mkstemp(*args, **kwargs)
    import os
    os.close(fd)
    if os.path.exists(fname):
        os.remove(fname)
    return open(fname, 'w')

def _mkdtemp(*args, **kwargs):
    """wrapper for tempfile.mkdtemp to register the removal of the directory
    """
    import tempfile
    dir_name = tempfile.mkdtemp(*args, **kwargs)
    import atexit, shutil
    ignore_errors = True
    atexit.register(shutil.rmtree, dir_name, ignore_errors)
    return dir_name

def _uncompress(fname, outdir, msg=msg):
    """uncompress the file `fname` under the directory `outdir`
    """
    import os
    assert os.access(fname, os.R_OK), "could not access [%s]" % fname
    fname = os.path.abspath(os.path.realpath(fname))
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    orig_dir = os.getcwd()
    try:
        os.chdir(outdir)
        ext = os.path.splitext(fname)[1][1:] # drop the dot
        if ext in ('gz', 'bz2'):
            import tarfile
            f = tarfile.open(fname, 'r:%s'%ext)
            f.extractall()
        else:
            err = 'extension [%s] not handled (yet?)' % ext
            msg.error(err)
            raise ValueError(err)
    finally:
        os.chdir(orig_dir)

def _cmt_to_autoconf(cmt):
    """translate CMT macros, patterns and such into (a dict of) their
    autoconf counterparts
    """
    f = cmt
    def many(*args):
        return ' '.join(args)
    cmt = lambda x: f(macro_value=x)
    
    cfg_env = {
        'LDFLAGS' : many(cmt('cpplinkflags'),
                         cmt('cmt_installarea_linkopts'),
                         ),
        'LIBS':     cmt('use_linkopts'),
        'CC':       cmt('cc'),
        'compiler': cmt('cc'),
        'gcc-version': cmt('gcc_config_version'),
        'LD':       cmt('cc'),
        'CFLAGS':   many(cmt('cflags'),
                         cmt('cppflags'),
                         cmt('pp_cppflags'),
                         cmt('cppdebugflags')),
        'CXX':      cmt('cpp'),
        'CXXFLAGS': many(cmt('cppflags'),
                         cmt('pp_cppflags'),
                         cmt('cppdebugflags')),
        'FC':       cmt('for'),
        'FCFLAGS':  cmt('fflags'),

        'CPPFLAGS': cmt('includes'),
        }

    # use_linkopts introduces <package>_linkopts which may confuse 'autoconf'
    pkg_name = cmt('package').strip()
    pkg_linkopts = "%s_linkopts" % pkg_name
    pkg_linkopts = cmt(pkg_linkopts)
    if pkg_linkopts != '':
        cfg_env['LIBS'] = cfg_env['LIBS'].replace(pkg_linkopts, ' ')
    
    # clean-up new-lines...:
    # FIXME: be clever ? this might break embedded EOL...
    for k in cfg_env:
        cfg_env[k] = cfg_env[k].replace('\r\n', ' ')
        cfg_env[k] = cfg_env[k].replace('\n', ' ')
        cfg_env[k] = cfg_env[k].strip()
        
    # clean-up the various compiler options...
    for compiler in ('CC', 'CXX', 'FC'):
        cfg_env[compiler] = cfg_env[compiler].replace(
            '-m32', '').strip()
        
    cfg_env['CFLAGS'] = cfg_env['CFLAGS']\
                        .replace("-Woverloaded-virtual ", " ")\
                        .replace("-Wno-deprecated ", " ")\
                        .replace("-shared ", " ")

    cfg_env['CXXFLAGS'] = cfg_env['CXXFLAGS']\
                        .replace("-shared ", " ")

    # hack: remove -Werror as many 3rd-party packages won't compile with it
    cfg_env['CFLAGS'] = cfg_env['CFLAGS']\
                        .replace(" -Werror ", " ")

    cfg_env['CXXFLAGS'] = cfg_env['CXXFLAGS']\
                        .replace(" -Werror ", " ")
    
    # many C modules are buggy otherwise...
    cfg_env['CFLAGS']  += " -fno-strict-aliasing"
    cfg_env['FCFLAGS'] += " -fno-strict-aliasing"
    cfg_env['CXXFLAGS']+= " -fno-strict-aliasing"
    
    
    host_arch = 'x86_64' if 'x86_64' in os.environ['CMTCONFIG'] else 'i686'
    host_plat = 'none'
    if 'linux' in sys.platform:
        host_plat = 'linux'
    elif 'darwin' in sys.platform:
        host_plat = 'darwin'
    else:
        pass
    host = '%s-unknown-%s-%s' % (host_arch, host_plat, 'gnu')
    cfg_env['pkg_host_triple'] = host

    if 'darwin' in sys.platform:
        for k in ('CFLAGS', 'CXXFLAGS'):
            cfg_env[k] = cfg_env[k].replace(' -bundle ', ' ')
            
    # FIXME: HACK !!
    cfg_env['LDFLAGS'] = cfg_env['LDFLAGS'].replace(
        "-Wl,--as-needed", "").replace(
        "-Wl,--no-undefined", "")
    cfg_env['LIBS'] = cfg_env['LIBS'].replace(
        "-Wl,--as-needed", "").replace(
        "-Wl,--no-undefined", "")

    # FIXME
    # another hack: distcc may disturb some autoconf pkgs
    # => disable it by default
    cfg_env['CC'] = cfg_env['CC'].replace('distcc', '').strip()
    cfg_env['CXX']= cfg_env['CXX'].replace('distcc','').strip()
    cfg_env['FC'] = cfg_env['FC'].replace('distcc', '').strip()
    cfg_env['compiler'] = cfg_env['compiler'].replace('distcc', '').strip()
    
    cfg_env['F77'] = cfg_env['FC']
    cfg_env['FFLAGS'] = cfg_env['FCFLAGS']
    
    # sanitize the CPPFLAGS
    cfg_env['CPPFLAGS'] = cfg_env["CPPFLAGS"].replace('"','')

    # sanitize LIBS: remove the <pkg>_linkopts
    cfg_env['LIBS'] = cfg_env['LIBS'].replace(cmt('use_linkopts'), '').strip()

    # remove C++-stuff from CFLAGS
    # this is b/c we include CMT-'cppflags' into CFLAGS
    # (but that's b/c the CMT-'cflags' isnt exhaustive...)
    cfg_env['CFLAGS'] = cfg_env['CFLAGS'].replace(' -include cstdio ',' -include stdio.h ')

    return cfg_env

import contextlib
@contextlib.contextmanager
def _dir_restore(destdir, origdir=None):
    if origdir is None:
        origdir = os.getcwd()
    os.chdir(destdir)
    yield
    os.chdir(origdir)

def cpu_count():
    try:
        import multiprocessing as mp
        return mp.cpu_count()
    except Exception, err:
        return 2
    
def build_package(fname, env=None, msg=msg):
    msg.debug('building [%s]...', fname)

    if env is None:
        env = {}
        
    def plugin_filter(obj):
        if inspect.isfunction(obj):
            return obj.__name__ in ('configure', 'build', 'install')

    pkg_infos = {}
    configure_impl = lambda x: 0
    build_impl = lambda x: 0
    install_impl = lambda x: 0
    
    with open(fname, 'r') as plugin:
        module = imp.load_source(osp.splitext(osp.basename(plugin.name))[0],
                                 plugin.name,
                                 plugin)
        fcts = inspect.getmembers(module, plugin_filter)
        assert (not fcts is None)

        fct = [fct[1] for fct in fcts if fct[0] == 'configure']
        if fct:
            configure_impl = fct.pop(0)

        # mandatory !
        fct = [fct[1] for fct in fcts if fct[0] == 'build']
        build_impl = fct.pop(0)

        fct = [fct[1] for fct in fcts if fct[0] == 'install']
        if fct:
            install_impl = fct.pop(0)

        pkg_infos = dict((k,v)
                         for k,v in inspect.getmembers(module)
                         if k.startswith('pkg_'))
        pkg_infos['pkg_root'] = env.get('pkg_root', osp.dirname(fname))
        pass

    msg.debug('pkg_infos: %s', pkg_infos)
    pkg = PkgBuilder(pkg=pkg_infos, env=env, msg=msg)
    pkg.configure_impl = configure_impl.__get__(pkg)
    pkg.build_impl     = build_impl.__get__(pkg)
    pkg.install_impl   = install_impl.__get__(pkg)
    sc = pkg.pkg_build()
    return sc

### classes -------------------------------------------------------------------

class PkgBuilder(object):
    """
    """

    def __init__(self, pkg, env=None, shell=os, msg=msg):
        self.pkg_infos = pkg.copy()
        self.pkg_name  = pkg['pkg_name']
        self.pkg_ver   = pkg['pkg_ver']
        self.pkg_src   = pkg['pkg_src']

        self.pkg_install_dir = pkg['pkg_install_dir']
        self.pkg_dest_dir    = pkg['pkg_install_dir'] # not a typo
        self.pkg_installarea_dir = pkg['pkg_installarea_dir']
        
        self.pkg_build_dir   = osp.join(pkg['pkg_root'],
                                        env['CMTCONFIG'],
                                        'pkg-build-%s' % self.pkg_name)
        
        import PyCmt.Cmt as Cmt
        self._cmt = Cmt.CmtWrapper()
        self.msg = msg

        self.sh = shell
        self._orig_dir = self.sh.getcwd()

        self.env = env.copy() if isinstance(env, dict) else {}
        for k,v in self.pkg_infos.iteritems():
            self.env[k] = v
        self.env['pkg_install_dir'] = self.pkg_install_dir
        self.env['pkg_build_dir']   = self.pkg_build_dir
        self.env['pkg_dest_dir']    = self.pkg_dest_dir
        
        get = self.cmt
        self.env['CMTINSTALLAREA'] = get(macro_value='CMTINSTALLAREA')
        self.env['tag'] = get(macro_value='tag')
        
        self.env.update(_cmt_to_autoconf(self.cmt))
        
       
        for k in self.env:
            if k.startswith('pkg_'):
                self.msg.debug('expanding [%s] => [%s]', k, self[k])
                setattr(self, k, self[k])
                

    def _prepare_relocate(self):
        """helper method to modify variables to support relocate-able
        installations"""

        if osp.exists(self.pkg_dest_dir):
            _remove(self.pkg_dest_dir)
        os.makedirs(self.pkg_dest_dir)
        self.msg.debug('pkg-install-dir: %s', self.pkg_install_dir)
        self.msg.debug('pkg-dest-dir:    %s', self.pkg_dest_dir)
        return
    
    def _relocate(self):
        verbose = self.msg.verbose
        pkg_install_dir = self.pkg_installarea_dir
        
        verbose("relocating from [%s] to [%s]...",
                self.pkg_dest_dir,
                pkg_install_dir)
        import shutil, glob
        tmp_root = self.pkg_dest_dir # + pkg_install_dir
        to_relocate = []
        for root, dirs, files in os.walk(tmp_root):
            for f in files:
                f = osp.join(root, f)
                _relpath = osp.relpath(f, tmp_root)
                #verbose(" --> [%s]", _relpath)
                to_relocate.append(_relpath)
        for f in to_relocate:
            dest = osp.join(pkg_install_dir, f)
            verbose("[%s] --> [%s]", f, dest)
            _remove(dest, ignore_errors=True)
            if not osp.exists(osp.dirname(dest)):
                os.makedirs(osp.dirname(dest))
            src = osp.join(tmp_root,f)
            delta_dir = osp.relpath(osp.dirname(src),
                                    osp.dirname(osp.realpath(dest)))
            rel_src = osp.join(delta_dir, osp.basename(src))
            verbose("--> symlink: [%s]", src)
            verbose("    symlink: [%s]", rel_src)
            verbose(" delta:      [%s]", delta_dir)
            verbose("    dest:    [%s]", dest)
            with _dir_restore(osp.dirname(dest)):
                try:
                    os.remove(dest)
                except OSError:
                    pass
                try:
                    os.symlink(rel_src,
                               osp.basename(dest))
                except OSError, err:
                    info("could not symlink [%s]:\n%s", dest, err)
                    pass
            if dest.endswith('.la'):
                pass
        return
    
    def run(self, cmd, *args, **kwds):
        if 'PKGBUILD_VERBOSE' in self.env:
            stdout = sys.stdout
        else:
            stdout = self._build_log
        import subprocess as sub
        import functools
        run = sub.check_call
        #run = sub.call
        run = functools.partial(
            run,
            stdout=stdout,
            stderr=stdout,
            env=self.env,
            *args, **kwds
            )
        if isinstance(cmd, str):
            cmd = cmd.split()
        self.msg.debug("==> [%s]", ' '.join(cmd))
        try:
            return run(cmd)
        except sub.CalledProcessError, err:
            self.msg.error('problem executing %s', err.cmd)
            if stdout != sys.stdout:
                self.msg.error('dumping build log:')
                print >> sys.stdout, "="*80
                stdout.flush()
                for l in open(stdout.name):
                    print >> sys.stdout, l,
                print >> sys.stdout, "="*80
            raise

    def _eval(self, name, env=None):
        if env is None:
            env = self.env
        v= self.env[name] % env
        self.env[name] = v
        return v

    def __getitem__(self, n):
        return self._eval(n)
    
    def cmt(self, *args, **kwds):
        cmtdir = osp.join(self.env['pkg_root'],'cmt')
        with _dir_restore(cmtdir):
            return self._cmt.show(*args, **kwds)
        
    def pkg_build(self):
        """the main kitchen-sink method
        """
        msg = self.msg
        msg.info('building [%s-%s]... (%s)',
                 self.pkg_name,
                 self.pkg_ver,
                 self.env['CMTCONFIG'])
        msg.debug('build-dir: [%s]', self.pkg_build_dir)
        msg.debug('install: [%s]', self.pkg_install_dir)
        
        _build_done = osp.join(osp.dirname(self.pkg_build_dir),
                               'pkg-build-%(pkg_name)s.done' % self.env)

        if not osp.exists(_build_done):

            import time
            start = time.asctime()
            self.pre_build()
            self.build()
            self.post_build()
            end   = time.asctime()

            with open(_build_done, 'w') as f:
                f.write('start: %s\n' % start)
                f.write('done:  %s\n' % end)
                f.flush()
                pass

        msg.debug('building [%s-%s]... (%s) [done]',
                  self.pkg_name,
                  self.pkg_ver,
                  self.env['CMTCONFIG'])
        return 0

    def pre_build(self):
        cmtconfig = self.env['CMTCONFIG']
        assert cmtconfig != ''

        pkg_install_dir = self.pkg_install_dir
        # here we should get a snapshot of directory's content
        if osp.exists(self.pkg_install_dir):
            _remove(self.pkg_install_dir, ignore_errors=True)
            self.msg.verbose('removed [%s]', self.pkg_install_dir)
        else:
            self.msg.verbose('no such dir [%s]', self.pkg_install_dir)
            
        self.sh.makedirs(self.pkg_install_dir)

        # clean-up 'pkg-build-myname'
        if osp.exists(self.pkg_build_dir):
            _remove(self.pkg_build_dir, ignore_errors=True)
            self.msg.verbose('removed [%s]', self.pkg_build_dir)
        else:
            self.msg.verbose('no such dir [%s]', self.pkg_build_dir)
            
        self.sh.makedirs(self.pkg_build_dir)
        self.sh.chdir(self.pkg_build_dir)

        _build_log = osp.join(osp.dirname(self.pkg_build_dir),
                              'pkg-build-%(pkg_name)s.log' % self.env)
        self._build_log = open(_build_log, 'a')
        self.msg.debug('logging build into [%s]', self._build_log.name)

        if _DO_RELOCATE:
            self._prepare_relocate()
        return

    def build(self):
        self.fetch_src()
        self.configure_impl()
        self.build_impl()
        self.install_impl()
        return 0
    
    def post_build(self):
        if _DO_RELOCATE:
            self._relocate()
        # if we are here, then everything succeeded: remove temporary stuff
        sh = self.sh
        sh.chdir(self._orig_dir)
        import shutil
        shutil.rmtree(self.pkg_build_dir)
        self._build_log.flush()
        self._build_log.close()
        sh.remove(self._build_log.name)
        return

    def fetch_src(self):
        msg = self.msg
        pkg_src = self.env['pkg_src']

        if osp.isfile(pkg_src):
            # may raise
            os.symlink(pkg_src,
                       osp.join(self.pkg_build_dir, osp.basename(pkg_src)))

            msg.debug('uncompressing [%s]...', pkg_src)
            _uncompress(pkg_src, self.sh.getcwd(), msg=msg)
        elif osp.isdir(pkg_src):
            # pkg_src is a directory holding the actual sources
            import shutil
            shutil.copytree(
                pkg_src,
                osp.join(self.pkg_build_dir, osp.basename(pkg_src)))
        return
    

