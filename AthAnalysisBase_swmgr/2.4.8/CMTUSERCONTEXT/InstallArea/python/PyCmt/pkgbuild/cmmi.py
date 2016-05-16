# a set of defaults for configure-make-makeinstall packages

import os
import os.path as osp

from PyCmt.pkgbuild import cpu_count

pkg_name = "<not there>"
pkg_ver  = "0.0"
pkg_src  = "%(pkg_root)s/src/%(pkg_name)s-%(pkg_ver)s.tar.gz"
pkg_installarea_dir = "%(CMTINSTALLAREA)s/%(CMTCONFIG)s"
pkg_install_dir = "%(pkg_root)s/%(CMTCONFIG)s/pkg-build-install-%(pkg_name)s"

def configure(self):
    sh  = self.sh
    msg = self.msg
    env = self.env

    msg.debug('configure...')
    sh.chdir("%(pkg_build_dir)s/%(pkg_name)s-%(pkg_ver)s" % env)

    cmd = [
        "./configure",
        "--prefix=%(pkg_install_dir)s" % env,
        "--host=%(pkg_host_triple)s" % env
        ]
    self.run(cmd)

def build(self):
    sh  = self.sh
    msg = self.msg
    env = self.env

    msg.debug('make...')
    sh.chdir("%(pkg_build_dir)s/%(pkg_name)s-%(pkg_ver)s" % env)

    cmd = "make -j%i" % cpu_count()

    self.run(cmd)
    
def install(self):
    sh  = self.sh
    msg = self.msg
    env = self.env

    msg.debug('make install...')
    sh.chdir("%(pkg_build_dir)s/%(pkg_name)s-%(pkg_ver)s" % env)

    cmd = "make install"
    self.run(cmd)
    
