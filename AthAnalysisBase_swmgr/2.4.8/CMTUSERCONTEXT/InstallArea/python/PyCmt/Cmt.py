## @author: Sebastien Binet
## @file :  Cmt.py
## @purpose: a little wrapper around cmt.exe to provide fast(er) access to the
##           list of clients of a given package. It also provides a mean to
##           retrieve all these clients...
from __future__ import with_statement

__version__ = "$Revision$"
__author__  = "Sebastien Binet"

import os
import commands
import re
import sys
import subprocess
from string import rstrip

### monkey-patch subprocess (fwd compat w/ py-3.x) ----------------------------
import PyCmt.bwdcompat
### ---------------------------------------------------------------------------


from PyCmt.Decorators import memoize
import PyCmt.Logging as L

class CmtOptions(object):
    ## the 'raw' names of the various Athena offline projects
    ## -> note I am discarding AtlasPoint1, tdaq, dqm, LCGCMT and GAUDI
    OfflineProjects = [
        "AtlasCore",
        "DetCommon",
        "AtlasConditions",
        "AtlasEvent",
        "AtlasReconstruction",
        "AtlasTrigger",
        "AtlasAnalysis",
        "AtlasSimulation",
        "AtlasHLT",
        "AtlasOffline",
        "AtlasProduction",
        ]

    ## number of spaces in the output of the 'cmt show uses' to represent
    ## hierarchichal dependency
    deltaIndent = 2
    pass

class CmtStrings:
    CMTPATH        = 'CMTPATH'
    CMTPROJECTPATH = 'CMTPROJECTPATH'
    CMTDIR         = 'cmt'
    CMTVERSIONFILE = 'version.cmt'
    CMTREQFILE     = 'requirements'
    CMTPROJFILE    = 'project.cmt'
    CMTSITE        = 'CERN'
    RELEASEROOT    = '/afs/cern.ch/atlas/software/builds'
    ATLASVERSION   = 'AtlasVersion'
    pass

class PkgNode(object):
    def __init__(self, pkg):
        object.__init__(self)
        self._pkg  = pkg
        self._deps = {}
        return

    def addDep(self, pkgName):
        self._deps[pkgName] = 1
        return

    def cmtPkg(self):
        return self._pkg
    
    def keys(self):
        return self._deps.keys()

    def deps(self):
        return self.keys()
    
    def __repr__(self):
        return repr(self._deps)

class PkgTree(object):

    def __init__(self):
        object.__init__(self)
        self._pkgs = {}
        self._types= {}
        return

    def addPkg(self, pkg, pkg_type = 1):
        self._types[pkg.name] = pkg_type
        if self._pkgs.has_key( pkg.name ):
            return
        self._pkgs[pkg.name] = PkgNode(pkg)
        return

    def getPkg(self, pkgName):
        return self._pkgs[pkgName]

    def pkgs(self):
        return self._pkgs

    def types(self):
        return self._types

    def __getitem__(self, n):
        return self._pkgs.__getitem__ (n)
    def __setitem__(self, n, v):
        return self._pkgs.__setitem__ (n,v)
    
    pass # PkgTree


def lineDecoder( line ):
    depLine   = re.compile( "#\s*?use.*?")
    if not re.match( depLine, line ):
        return (None, None)

    athenaDep = re.compile( "#(?P<PkgIndent>\s*?)use (?P<PkgName>\w*) (?P<PkgVers>.*?) (?P<PkgPath>.*?) (.*?)" )
    gaudiDep  = re.compile( "#(?P<PkgIndent>\s*?)use (?P<PkgName>\w*) (?P<PkgVers>.*)" )
    l = re.match( athenaDep, line ) or \
        re.match( gaudiDep,  line )
    if l:
        pkgIndent = l.group('PkgIndent')
        pkgName   = l.group('PkgName')
        pkgVers   = l.group('PkgVers')
        try:
            pkgPath = l.group('PkgPath')
        except:
            pkgPath = None
            pass
    else:
        raise RuntimeError, "No decoding !!"
    return (len(pkgIndent)-1, CmtPkg( pkgName, pkgVers, pkgPath ))

def buildDepGraph( fileName, pkgDb, msg ):
    """ Build the dependency graph """
    pkgTree = PkgTree()
    pkgs = []
    cmtFile = open( os.path.expanduser(os.path.expandvars(fileName)), 'r' )
    for l in cmtFile.readlines():
        l = l.strip()
        indent, pkg = lineDecoder( l )
        if not pkg:
            continue
        msg.verbose( "found [%3i] [%s]", indent, pkg.name )

        # try to retrieve the 'right' version from the pkg Db
        if pkgDb.has_key(pkg.name): pkg = pkgDb[pkg.name]
        else: msg.warning( "[%s] is not in pkgDb !!", pkg.name )
            
        pkgTree.addPkg( pkg )
        pkgs.append( { 'indent':indent, 'pkg': pkg } )
        if indent == 0:
            continue
        for p in reversed(pkgs):
            pIndent    = p['indent']
            parentName = p['pkg'].name
            msg.verbose( "   processing [%3i] [%s]", pIndent, parentName )
            if pIndent == indent - CmtOptions.deltaIndent:
                pkgTree.getPkg(parentName).addDep( pkg.name )
                msg.verbose( "   ==> [%s] depends on [%s]",
                             parentName, pkg.name )
                break
            pass
        pass
    return pkgTree

def buildPkgDb( fileName, msg ):

    pattern = re.compile(r'use (?P<PkgName>.*?) (?P<PkgVersion>.*?) (?P<PkgPath>.*?) [(].*[)]')
    cmtFile = open( os.path.expanduser(os.path.expandvars(fileName)), 'r' )
    pkgDb = { }
    for l in cmtFile:
        l = l.strip()
        
        l = re.match( pattern, l )
        if l:
            pkgName = l.group('PkgName')
            pkgVers = l.group('PkgVersion')
            pkgPath = l.group('PkgPath')  
            msg.debug( "found [%s] [%s] [%s]", pkgName, pkgVers, pkgPath )
            pkgDb[pkgName] = CmtPkg( pkgName, pkgVers, pkgPath )
            pass
    
    return pkgDb

def extract_uses(fname, msg):
    cmtFile = open(os.path.expanduser(os.path.expandvars(fname)), 'r')
    pkgDb = { }
    for l in cmtFile:
        if not l.startswith('use '):
            continue
        l = l.strip()
        pkg = l[len('use '):].split()
        if len(pkg) >= 1:
            pkg_name = pkg[0].strip()
            pkg_vers = '*'
            if len(pkg) >= 2:
                pkg_vers = pkg[1].strip()
            pkg_path  = ''
            if len(pkg)==3:
                pkg_path = pkg[2].strip()    
            msg.debug("found [%s] [%s] [%s]", pkg_name, pkg_vers, pkg_path)
            cmtpkg = CmtPkg(pkg_name, pkg_vers, pkg_path)
            pkgDb[cmtpkg.full_name] = cmtpkg
            pass
        else:
            msg.error('unexpected line content: %s', pkg)
    return pkgDb
    
class CmtPkg(object):
    def __init__( self,
                  pkgName,
                  pkgVersion = None,
                  pkgPath    = '',
                  projName   = None):
        object.__init__(self)
        self.name = pkgName
        self.version = pkgVersion
        self.path    = pkgPath
        self.project = projName
        return

    @property
    def full_name(self):
        return self.fullName()
    
    def fullName(self):
        return os.path.join(self.path, self.name)
    
    def __repr__(self):
        return '<CmtPkg(name=%s, version=%s)>' % (self.full_name, self.version)

    def __str__( self ):
       s = [ "Package: %s" % self.name,
             "Version: %s" % self.version,
             "Path:    %s" % self.path ]
       return os.linesep.join(s)
    
class CmtProject(object):
    def __init__(self, path=None, version=None):
        self.path    = path
        self.version = version
        self.parents = []
        self.children= []

    @property
    def name(self):
        import os.path as osp
        return osp.basename(osp.dirname(self.path))

    def __repr__(self):
        return '<CmtProject(name=%s, version=%s)>' % (self.name, self.version)

    def __str__( self ):
        s = [ "Project:  %s" % self.name,
              "Version:  %s" % self.version,
              "Path:     %s" % self.path,
              "Parents:  %s" % self.parents,
              "Children: %s" % self.children]
        from os import linesep
        return linesep.join(s)
            
class CmtWrapper(object):
    """
    A python wrapper around CMT
    """

    def __init__(self, lvl = L.logging.INFO, shell=None):
        object.__init__(self)
        self.msg = L.logging.getLogger("Cmt")
        self.msg.setLevel(lvl)
        if shell is None:
            self.shell = subprocess
        else:
            self.shell = shell
        sc,self.bin = self.shell.getstatusoutput("which cmt.exe")

        # make sure we have a correct and sound CMT environment
        assert len(self.projects())>0, "no projects found: corrupted CMT environment ?"
        assert len(self.projects_dag())>0, "empty projects-DAG tree: corrupted CMT environment ?"
        
        return

    def check_out(self, pkgFullName, pkgVersion = None):
        """check a package out of the source repository
         `pkgFullName` the complete and full path name to that pkg.
                       e.g: 'Control/AthenaKernel'
         `pkgVersion`  if specified, retrieve that version from the repo.
                       leave it to None to retrieve the HEAD or trunk.
        """
        args = pkgFullName
        cmd  = "%s co %s" % ( self.bin, pkgFullName )
        if pkgVersion != None:
            cmd = "%s co -r %s %s" % ( self.bin, pkgVersion, pkgFullName )
            pass
        
        sc,out = self.shell.getstatusoutput( "%s" % cmd )
        if sc != 0:
            self.msg.warning( "Problem doing 'cmt co' !" )
            self.msg.warning( "Failed to issue [%s]" % cmd )
            self.msg.warning( out )
            pass
        else:
            self.msg.info( "## %s [OK]" % pkgFullName )
        return
    # bwd compat
    checkOut = check_out
    
    @memoize
    def projects(self):
        return [ p.path for p in self.project_tree().itervalues() ]

    @memoize
    def projects_tree(self):
        """return an (unordered) tree of all the projects"""
        dec = re.compile(r"(?P<ProjIndent>\s*?)"\
                          "(?P<ProjName>[-_.\w]*?) "\
                          "(?P<ProjVersion>[-_.\w/]*?) "\
                          "[(]in (?P<ProjPath>.*?)[)]"\
                          "(?P<ProjData>.*)" )
        #from collections import defaultdict
        proj_tree = {} #defaultdict(CmtProject)
        projs = []

        out = self.show (projects='')
        for l in out.splitlines():
            o = dec.match(l)
            if o is None:
                self.msg.warning("!! discarding: !!")
                self.msg.warning(repr(l))
                continue
            g = o.group
            self.msg.debug("%s %s %s %s [%s]",
                           g('ProjIndent'),
                           g('ProjName'),
                           g('ProjVersion'),
                           g('ProjPath'),
                           g('ProjData'))
            if g('ProjName') == 'CMTHOME':
                # ignore that guy, it is a special (pain in the neck) one
                # see bug #75846
                # https://savannah.cern.ch/bugs/?75846
                continue
            if g('ProjName') == 'CMTUSERCONTEXT':
                # ignore similar to CMTHOME above
                continue
            projs.append([len(g('ProjIndent')),
                          g('ProjName'),
                          g('ProjVersion'),
                          g('ProjPath'),
                          g('ProjData').strip().split()])

        for i,iproj in enumerate(projs):
            try:
                proj = proj_tree[iproj[1]]
            except KeyError:
                proj = proj_tree[iproj[1]] = CmtProject()
            proj.version = iproj[2]
            proj.path    = iproj[3]

            ###################################################################
            ### hack for cmt-v21 ###
            ### in cmt-21 the top-level 'current' project does't have
            ### any dep against the other projects
            if len(iproj[-1])==1 and iproj[-1][0] == "(current)":
                try:
                    proj.children.append(projs[i+1][1])
                except IndexError:
                    pass
                continue
            ### End-of-hack ###
            ###################################################################
            
            for data in iproj[-1]:
                if data.startswith('P='):
                    parent_name=data[2:]
                    if not parent_name in proj.parents:
                        proj.parents.append(parent_name)
                elif data.startswith('C='):
                    child_name = data[2:]
                    if not child_name in proj.children:
                        proj.children.append(child_name)
                else:
                    pass
        return proj_tree
    project_tree = projects_tree
    
    @memoize
    def project_deps (self, proj_name):
        "return the list of projects a given project is depending upon"
        proj_tree = self.project_tree()
        deps = set()
        def _collect_children (projs, proj_name, visited=None):
            if visited is None:
                visited=set([proj_name])
            for c in projs[proj_name].children:
                if c in visited:
                    continue
                visited.add (c)
                yield c
                for i in _collect_children (projs, c, visited):
                    yield i
        deps = set([c for c in _collect_children (proj_tree, proj_name)])
        return list(deps)

    @memoize
    def project_release (self, proj_name):
        """helper method to return the xyzRelease for a given project
        this is to handle some idiosyncracies of different projects
        """
        if proj_name == "LCGCMT":         return "LCG_Release"
        elif proj_name == "dqm-common":   return "DQMCRelease"
        elif proj_name == "tdaq-common":  return "TDAQCRelease"
        #elif proj_name == "GAUDI":        return "GaudiRelease"
        else:
            return "%sRelease"%proj_name

    @memoize
    def projects_dag(self):
        """return the (flatten) directed acyclic graph of all the
        currently used project(name)s
        """
        tree = self.project_tree()
        root = [n for n,p in tree.iteritems() if len(p.parents)==0]
        assert len(root)>=1, \
               "project tree inconsistency (found [%i] root(s))" % (len(root),)
        root = tree[root.pop()] # may raise.

        def iter_tree(pkg):
            yield pkg
            for n in pkg.children:
                for j in iter_tree(tree[n]):
                    yield j

        # keep a context around to prevent from building dups
        projs = []
        for proj in iter_tree(root):
            if proj not in projs:
                projs.append(proj)
        return projs
    # bwd compat
    project_dag = projects_dag

    @memoize
    def release_metadata(self, project=None):
        """return
        """
        return
    
    @memoize
    def find_pkg(self, name):
        """Find CMT package by (leaf)name.

        Return: CmtPkg or None if not found
        """
        import os
        osp = os.path
        # Loop over all *Release/cmt/requirements files
        for proj in self.projects_dag():
            reqpath = os.path.join(proj.path,
                                   self.project_release(proj.name),
                                   CmtStrings.CMTDIR,
                                   CmtStrings.CMTREQFILE)
            if os.path.exists(reqpath):
                pkgs = open(reqpath, 'r').readlines()
                pkgs = (l.strip() for l in pkgs)
                pkgs = (l for l in pkgs if l.startswith('use '))
                pkgs = (l[len('use '):] for l in pkgs)
                pkgs = (l.split() for l in pkgs if name in l)
                for fields in pkgs:
                    if len(fields)>0 and fields[0]==name:
                        if len(fields)==3:
                            return CmtPkg(fields[0],fields[1],fields[2])
                        elif len(fields)==2:
                            return CmtPkg(fields[0],fields[1],"")

    @memoize
    def get_pkg_version(self, fullPkgName):
        """Return the package tag in the current release for `fullPkgName`.

        Return: Tag or None
        """
        _cmd = "%s show versions %s" % (self.bin, fullPkgName)
        self.msg.debug('running [%s]...', _cmd)
        p = self.shell.Popen(_cmd, stdout = subprocess.PIPE, shell=True)
        
        version = None
        testArea = os.environ.get("TestArea")
        for cmtline in p.stdout:
            if (testArea and cmtline.find(testArea)!=-1): continue
            version = cmtline.split(" ")[1]
            break

        return version

    
    def get_latest_pkg_tag(self, fullPkgName):
        """Return the most recent SVN tag of the package.

        Return: Tag or None on error
        """
        ## This is not really CMT related but fits nicely in this module anyways
        
        svnroot = os.environ.get("SVNROOT")
        if svnroot==None:
            self.msg.error("SVNROOT is not set.")
            return None

        _cmd = "svn ls %s" % os.path.join(svnroot, fullPkgName, "tags")
        if fullPkgName.startswith('Gaudi'):
            _cmd = "svn ls %s" % os.path.join(svnroot, 'tags', fullPkgName)
        self.msg.debug('running [%s]...', _cmd)        
        p = subprocess.Popen(_cmd, shell = True,
                             stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        tags = p.communicate()[0].splitlines()
        if len(tags)==0 or p.returncode!=0: return None

        pkg_name = os.path.basename(fullPkgName)

        # enforce atlas convention of tags (pkgname-xx-yy-zz-aa)
        tags = [t for t in tags if t.startswith(pkg_name)]
        latest_tag = rstrip(tags[-1],"/\n ")
        return latest_tag

    def show_clients(self, pkgName):
        """return the list of clients of a given `pkgName` CMT package
        Note: `pkgName` is the leaf name of a package (not its fullname)
        """
        if pkgName.count(os.sep):
            raise RuntimeError, "pkgName contains a %s !!" % os.sep
        clientList = []

        proj_deps = self.project_deps('AtlasOffline') + ['AtlasOffline']
        #proj_deps = ['AtlasOffline']
        self.msg.info( "building dependencies..." )
        self.msg.info( "projects used: %r", proj_deps )
        
        projReleases = [self.project_release(p) for p in proj_deps ]
        ## create a temporary directory containing a CMT package 'use'-ing
        ## all <AtlasProject>Release packages
        import tempfile
        tmpRoot = tempfile.mkdtemp()
        cwd = os.getcwd()
        os.chdir( tmpRoot )
        cmtTmpDir = os.path.join( "Dep%s" % pkgName, "cmt" )
        if not os.path.exists( cmtTmpDir ):
            os.makedirs( cmtTmpDir )
        os.chdir( cmtTmpDir )

        with open( 'requirements', 'w' ) as req:
            print >> req, "package Dep%s" % pkgName
            print >> req, ""
            print >> req, "author DependenciesViewer"
            print >> req, ""
            for p in projReleases:
                print >> req, "use %s %s-*" % (p,p)
            print >> req, ""
            req.flush()

        if 0:
            print "+"*80
            with open('requirements', 'r') as req:
                for l in req:
                    print l,
            print "+"*80
                
        with open('version.cmt', 'w') as cmt_version:
            print >> cmt_version, "Dep%s-00-00-00" % (pkgName,)
            print >> cmt_version, ""
            cmt_version.flush()

        _cmd = "%s config >& /dev/null" % self.bin
        self.msg.debug('running [%s]...', _cmd)
        sc = self.shell.check_call(_cmd, shell=True)
        if sc:
            raise RuntimeError(
                "could not configure Dep%s package" % (pkgName,)
                )

        f_use_name = os.path.join(tmpRoot,cmtTmpDir,pkgName)
        f_use_name = "%s.cmt" % f_use_name
        _cmd =  "%s show uses > %s" % (self.bin, f_use_name)# pkgName)
        self.msg.debug('running [%s]...', _cmd)
        sc = self.shell.call(_cmd, shell=True)
        if sc:
            self.msg.warning("problem running command [%s]", _cmd)
            self.msg.warning("(ignoring it as I am resilient)")
        del f_use_name
        
        self.msg.info( "building packages db..." )
        pkgDb   = buildPkgDb( "%s.cmt" % pkgName, self.msg )

        self.msg.info( "building packages dependency tree..." )
        pkgTree = buildDepGraph( "%s.cmt" % pkgName, pkgDb, self.msg )
        
        os.chdir( cwd )
        
        pkgs = pkgTree.pkgs()
        keys = sorted(pkgs.keys())
        for k in keys:
            self.msg.verbose("-> %s: %s",k,pkgs[k].deps())
            if pkgName in pkgs[k].deps() and not k in clientList and \
               not k in projReleases :
                client = pkgTree.getPkg(k).cmtPkg()
                clientList.append( client )
                self.msg.info( "=> [%s] (%s)",
                               client.fullName(), client.version )
                pass
        import shutil
        shutil.rmtree( tmpRoot )
        
        self.msg.info( "Found [%i] clients for [%s]",
                       len(clientList), pkgName )
        return clientList
    # bwd compat
    showClients = show_clients
    
    def slowShowClients(self, pkgName):
        if pkgName.count(os.sep):
            raise RuntimeError, "pkgName contains a %s !!" % os.sep
        clientList = []

        projects = self.projects()

        ## now we can actually retrieve the list of clients
        cmd = "%s show clients %s" % ( self.bin, pkgName )
        sc,out = self.shell.getstatusoutput( "%s" % cmd )
        if sc != 0:
            self.msg.warning( "Problem during [%s]" % cmd )
            self.msg.warning( out )
            return clientList

        pattern = re.compile(r'# (?P<PkgName>.*?) (?P<PkgVersion>.*?) (?P<PkgPath>.*?) [(]use version (?P<UsedPkgVersion>.*?)[)]')
        for l in out.splitlines():
            match = re.match(pattern, l)
            if not match:
                continue
            pkgPath = match.group('PkgPath')
            for proj in projects:
                pkgPath = pkgPath.replace( proj, "" )
            if pkgPath.startswith(os.sep):
                pkgPath = pkgPath[1:]
            cmtPkg = CmtPkg( match.group('PkgName'),
                             match.group('PkgVersion'),
                             pkgPath )
            clientList.append(cmtPkg)
            pass

        self.msg.info( "Found [%i] clients for [%s]",
                       len(clientList), pkgName )
        return clientList

    def show(self, **kw):
        cmd = "%s show " % self.bin
        cmd = cmd + " ".join( "%s %s" % (k, kw[k]) for k in kw.keys() )

        # only capture the stdout as stderr may have spurious ERRORs
        # from wrong CMT environment or CMT-phase-of-the-moon pb...
        with open(os.devnull, 'w') as devnull:
            sc,out = self.shell.getstatusoutput(cmd, stderr=devnull)

        if sc != 0:
            self.msg.warning( "Problem during [%s]" % cmd )
            self.msg.warning( out )
        return out
        
class CmtMgr(object):
    """a simple class to manage CMT environments"""
    def __init__(self,
                 project_name=None,
                 cmt_root=None,
                 cmt_version='v1r22',
                 asetup=None,
                 tags='16.0.0,gcc43,opt',
                 verbose=False):
        import os
        if project_name is None:
            project_name = os.getenv('AtlasProject', 'AtlasOffline')
        if cmt_root is None and os.getenv('CMTROOT'):
            cmt_setup = os.path.join(os.getenv('CMTROOT'), 'mgr', 'setup.sh')
        else:
            cmt_setup = os.path.join(cmt_root, cmt_version, 'mgr', 'setup.sh')
        if not os.path.exists(cmt_setup):
            raise OSError, "no such file [%s]"%cmt_setup

        if asetup is None:
            asetup = '/afs/cern.ch/atlas/software/dist/AtlasSetup'
        self._asetup_root = asetup
        
        self.verbose = verbose
        
        self.project = project_name
        import tempfile
        self.top_dir = tempfile.mkdtemp()
        from . import pyshell as ps
        self.sh = ps.LocalShell()
        # setup AtlasSetup
        self.sh.environ['AtlasSetup'] = self._asetup_root
        self._asetup_sh = os.path.join(self._asetup_root,
                                       'scripts', 'asetup.sh')
        
        orig_dir = self.sh.getcwd()
        self._create_asetup_cfg(tags)

    def _create_asetup_cfg(self, tags):
        
        self.sh.chdir(self.top_dir)

        asetup_cfg_name = os.path.join(self.top_dir, '.asetup.cfg')
        import textwrap
        asetup_cfg = open(asetup_cfg_name, "w")
        asetup_cfg.write(
            textwrap.dedent("""\
            [defaults]
            #default32 = True
            opt = True
            gcc43default = True
            lang = C
            hastest = True           # to prepend pwd to cmtpath
            pedantic = True
            runtime = True
            setup = True
            os = slc5
            #project = AtlasOffline  # offline is already the default
            save = True
            #standalone = False   # prefer build area instead of kit-release
            #standalone = True    # prefer release area instead of build-area
            testarea=<pwd>        # have the current working directory be the testarea
            """)
            )
        asetup_cfg.flush()
        asetup_cfg.close()

        # source-ing
        args = ' '.join([
            '--input=%s' % (asetup_cfg_name,),
            tags
            ])
        sc = self.sh.source(self._asetup_sh,
                            args=args)
        if sc:
            print "**ERROR** while running 'asetup %s'" % args
            
        sc,out = self.sh.getstatusoutput('cmt show path')
        if sc:
            print "**ERROR** while running cmd=[%s]:\n%s"%(cmt_setup,
                                                           out)
        else:
            # if self.verbose:
            #     print "$ cmt show path:\n%s\n===EOF===" % out
            pass
        
        return
    
def get_tag_diff(ref, chk, verbose=False):
    """return the list of tag differences between 2 releases
    """
    mgrs = {}
    cmts = {}

    if verbose:
        print "::: setup reference env. [%s]..." % ref
    mgrs['ref'] = CmtMgr(project_name='reference_rel', tags=ref,
                         verbose=verbose)
    cmts['ref'] = CmtWrapper(shell=mgrs['ref'].sh)

    if verbose:
        print "::: setup check env. [%s]..." % chk
    mgrs['chk'] = CmtMgr(project_name='check_rel', tags=chk,
                         verbose=verbose)
    cmts['chk'] = CmtWrapper(shell=mgrs['chk'].sh)

    # list of packages for each ref/chk
    pkgdb = {}
    # diff for each ref/chk
    cmt_diffs = {}
    diffs = []
    
    for rel in ('ref', 'chk'):
        cmt = cmts[rel]
        pkgdb[rel] = {}
        
        for proj in reversed(cmt.projects_dag()):
            reldata = os.listdir(proj.path)
            reldata = [p for p in reldata if p.endswith('Release')]
            if len(reldata) != 1:
                continue
            reldata = reldata[0]
            reldata = os.path.join(proj.path, reldata, 'cmt', 'requirements')
            if not os.path.exists(reldata):
                continue
            uses = extract_uses(reldata, msg=cmt.msg)
            for p in uses:
                pname = proj.name
                if pname.startswith('Atlas'):
                    pname = pname[len('Atlas'):]
                uses[p].project = pname
            pkgdb[rel].update(uses)

    def cmp_pkgs(a, b):
        diffs = {}
        pkg_fullnames = sorted(pkgdb[a].keys())
        for pkg_fullname in pkg_fullnames:
            if not (pkg_fullname in pkgdb[b]):
                diffs[pkg_fullname] = {a: pkgdb[a][pkg_fullname],
                                       b: CmtPkg('None',
                                                 'None-00-00-00',
                                                 '-')}
            else:
                a_vers = pkgdb[a][pkg_fullname].version
                b_vers = pkgdb[b][pkg_fullname].version
                if a_vers != b_vers:
                    diffs[pkg_fullname] = {a: pkgdb[a][pkg_fullname],
                                           b: pkgdb[b][pkg_fullname]}
        return diffs
    # first compare the list of packages registered in the reference
    cmt_diffs.update(cmp_pkgs(a='ref', b='chk'))
    # then compare the reverse
    cmt_diffs.update(cmp_pkgs(a='chk', b='ref'))

    if verbose:
        print "::: found [%i] tags which are different" % (len(cmt_diffs),)
    if len(cmt_diffs) == 0:
        return cmt_diffs

    fmt = "%-15s %-15s | %-15s %-15s | %-45s"
    if verbose:
        print fmt % ("ref", "ref-project", "chk", "chk-project", "pkg-name")
        print "-"*120
    pkg_fullnames = sorted(cmt_diffs.keys())
    for pkg_fullname in pkg_fullnames:
        diff = cmt_diffs[pkg_fullname]
        if (not 'ref' in diff or
            not 'chk' in diff):
            print "** err **: pkg-fullname [%s] keys: %s" % (pkg_fullname, diff.keys())
        pkg = diff['ref']
        if pkg.name == 'None':
            pkg = diff['chk']
        full_name = pkg.full_name
        out = dict(ref=diff['ref'].version.replace(pkg.name+'-',''),
                   chk=diff['chk'].version.replace(pkg.name+'-',''),
                   ref_proj=diff['ref'].project or 'N/A',
                   chk_proj=diff['chk'].project or 'N/A',
                   full_name=full_name)
        diffs.append(out)
        if verbose:
            print fmt % (out['ref'], out['ref_proj'],
                         out['chk'], out['chk_proj'],
                         out['full_name'])

    if verbose:
        print "-"*120
        print "::: found [%i] tags which are different" % (len(diffs),)

    return diffs
    
