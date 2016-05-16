# a set of defaults for distutils-based packages

import os
import os.path as osp

from PyCmt.pkgbuild import cpu_count

# fix-up distutils, see bug #51501
import platform
if platform.architecture()[0] == '32bit':
    import distutils.sysconfig as ds
    ds.get_config_vars()['CFLAGS'] += ' -m32'
    ds.get_config_vars()['LDSHARED'] += ' -m32'
del platform

import sys
python_config_version = "%i.%i" % sys.version_info[:2]

pkg_name = "<not there>"
pkg_ver  = "0.0"
pkg_src  = "%(pkg_root)s/src/%(pkg_name)s-%(pkg_ver)s.tar.gz"
pkg_installarea_dir = "%(CMTINSTALLAREA)s/%(CMTCONFIG)s"
pkg_install_dir = "%(pkg_root)s/%(CMTCONFIG)s/pkg-build-install-%(pkg_name)s"

def configure(self):
    sh  = self.sh
    msg = self.msg
    env = self.env

    env['F77']= env['FC']
    env['LDFLAGS'] += " ".join([self.cmt(macro_value="Python_linkopts"),
                               "-shared"])

    if 'darwin' in sys.platform:
        env['LDFLAGS'] = env['LDFLAGS'].replace('-shared', '')

    # FIXME
    # setup.py does not honour the cross-compilation
    # correctly, at least at link time...
    if '-m32' in self.cmt(macro_value='cppflags'):
        env['CC'] += ' -m32'
        env['CXX'] += ' -m32'
        pass

    #env['CFLAGS'] += ' -std=c99'
    
    msg.debug('configure...')
    sh.chdir("%(pkg_build_dir)s/%(pkg_name)s-%(pkg_ver)s" % env)

    includes = self.cmt(macro_value="includes")
    ppcmd = self.cmt(macro_value="ppcmd")
    includes = [inc.strip() for inc in includes.split(ppcmd) if inc.strip()]
    includes = ":".join(includes).replace('"','')
    env['includes'] = includes

    from textwrap import dedent
    site_cfg = open("site.cfg", "a")
    site_cfg.write(dedent("""\
    [DEFAULT]
    library_dirs = %(LD_LIBRARY_PATH)s:/usr/lib:/lib
    include_dirs = %(includes)s
    fcompiler    = %(FC)s
    
    """ % env))
    site_cfg.flush()
    site_cfg.close()
    del site_cfg
    return

def build(self):
    sh  = self.sh
    msg = self.msg
    env = self.env

    # for python-eggs
    import os.path as osp
    os.environ['PYTHON_EGG_CACHE'] = osp.join(
        "%(pkg_build_dir)s/%(pkg_name)s-%(pkg_ver)s"%env,
        '.python-eggs'
        )

    msg.debug('build...')
    sh.chdir("%(pkg_build_dir)s/%(pkg_name)s-%(pkg_ver)s" % env)

    cmd = [
        "python",
        "setup.py",
        "build"
        ]
    self.run(cmd)

def install(self):
    sh  = self.sh
    msg = self.msg
    env = self.env

    msg.debug('install...')
    sh.chdir("%(pkg_build_dir)s/%(pkg_name)s-%(pkg_ver)s" % env)

    platlib = "%(pkg_install_dir)s/lib/python" % env + \
                   python_config_version
    purelib = "%(pkg_install_dir)s/lib/python" % env + \
                   python_config_version
    bindir  = "%(pkg_install_dir)s/bin" % env

    import os
    for d in (platlib, purelib, bindir):
        if not os.path.exists(d):
            os.makedirs(d)
            
    cmd = [
        "python",
        "setup.py",
        "install",
        "--force",
        "--root=%(pkg_install_dir)s" % env,
        ## '--install-platlib=%s' % platlib,
        ## '--install-purelib=%s' % purelib,
        ## '--install-scripts=%s' % bindir,
        '--install-platlib=lib/python%s' % python_config_version,
        '--install-purelib=lib/python%s' % python_config_version,
        '--install-scripts=bin',
        '--install-data=lib/python%s' % python_config_version,
        ]
    self.run(cmd)
    
