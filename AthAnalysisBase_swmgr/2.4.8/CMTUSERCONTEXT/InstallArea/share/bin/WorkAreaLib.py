# @file PyUtils.WorkAreaLib
# @purpose factor out some useful methods out of setupWorkArea for clients
# @author Sebastien Binet

import os, sys
from PyCmt.Logging import logging
from PyCmt.Cmt import CmtPkg, CmtStrings

__version__ = '$Revision$'
__author__  = 'Sebastien Binet'

WORKAREA_VERSION = "WorkArea-00-00-00"

# a list of directory names one should not bother inspecting
_ignore_dir_list = [
    "i686-",
    "x86_64-",
    "CVS",
    ".svn",
    "o..pacman..o",
    "InstallArea",
    ]

def _get_currentpath():
    from PyCmt.Cmt import CmtWrapper
    cmt = CmtWrapper()
    installarea = cmt.show(macro_value='CMTINSTALLAREA')
    prefix = cmt.show(macro_value='cmt_installarea_prefix')
    return installarea.rstrip(prefix).rstrip(os.sep)

def _is_in_ignore_dir_list(pathname):
    return any(map(pathname.count, _ignore_dir_list))

def listCmtDirs( path ):
    """Return the list of paths pointing at 'cmt' directories, accessible
    from the `path` path.
    """

    msg = logging.getLogger( "WorkAreaMgr" )
    
    cmtDirs = []
    
    # fill list of CMT directories
    import os
    import os.path as osp
    for root, dirs, files in os.walk(path):
        for d in dirs[:]:
            if _is_in_ignore_dir_list(d):
                dirs.remove(d)
        for d in dirs:
            if d == CmtStrings.CMTDIR:
                full_name = osp.join(root, d)
                msg.debug("\t==> found %s" % full_name)
                cmtDirs.append(full_name)
    return cmtDirs

def scan( scanDir = os.curdir, suppressList = ["WorkArea"] ):
    """Search for CMT packages in the given directory and walk down the
    directory tree.
    Return the list of found CMT packages.
    """
    msg = logging.getLogger( "WorkAreaMgr" )
    msg.info( "Scanning [%s]" % scanDir )
    
    # return value
    cmtPackages = []
    
    # retrieve all cmt-ised directories in the scan directory
    scanDir = os.path.abspath( scanDir )

    cmtDirs = []
    try:
        cmtDirs = listCmtDirs(scanDir)
    except KeyboardInterrupt:
        msg.warning( "Scanning has been STOPPED ! (by you)" )
        pass
    
    for cmtDir in cmtDirs:
        cmtPkg = createCmtPkg(cmtDir)
        if cmtPkg != None and \
           cmtPkg.name not in suppressList:
            cmtPackages.append( cmtPkg )
        pass
    
    return cmtPackages

def createCmtPkg( cmtDir ):
    """
    the cmtDir is assumed to be of the form Xyz/cmt
    One has also to handle the case with or without version-directory
    """
    msg = logging.getLogger("WorkAreaMgr")
    
    pkgName = None
    # the CMTREQFILE should provide the name of package
    # so we extract it from this file
    try:
        reqFile = open( os.path.join( cmtDir, CmtStrings.CMTREQFILE ), 'r' )
        for line in reqFile.readlines():
            line = line.strip()
            if len(line) > 0  and \
               line[0] != "#" and \
               line.count("package ") > 0:
                pkgName = line.splitlines()[0]\
                          .split("package ")[1]\
                          .replace("\r","")\
                          .split("#")[0]\
                          .strip()
                break
            pass
        reqFile.close()
        del reqFile
    except IOError:
        ## No CMTREQFILE in this directory
        ## ==> not a CMT package then ?
        ## check if there is any CMT project file instead
        if not os.path.exists( os.path.join(cmtDir, CmtStrings.CMTPROJFILE) ):
            msg.warning( "[%s] does NOT contain any '%s' nor '%s' file !!" % \
                         ( cmtDir,
                           CmtStrings.CMTREQFILE,
                           CmtStrings.CMTPROJFILE ) )
        return None

    if pkgName == None:
        msg.warning( "No 'package Foo' stmt in %s of %s" % \
                     ( CmtStrings.CMTREQFILE, cmtDir ) )
        return None
    
    msg.debug( "\t\t==> Analysing [%s]" % cmtDir )
    
    # first we try the no-version-directory case as it is the ATLAS
    # default now.
    if CmtStrings.CMTVERSIONFILE in os.listdir(cmtDir):
        version = open( os.path.join( cmtDir, CmtStrings.CMTVERSIONFILE ),
                        'r' )\
                        .readline()
        version = version.splitlines()[0].strip()
        pkgDir = os.path.split(cmtDir)[0].strip()
        pkgPath = os.path.split(pkgDir)[0].strip()
        pass

    # Now we *MAY* be in the case where:
    # /somePath/MyPkg/MyPkg-00-00-00/cmt
    # or
    # /somePath/MyPkg/v1r2p3/cmt
    # however this is not supported anymore: warn and fallback to previous
    # case anyway (as user might have screwed up)
    else:
        msg.warning("No [%s] file in [%s] directory",
                    CmtStrings.CMTVERSIONFILE,
                    cmtDir)
        msg.warning("Can't reliably infer package version/dir!")
        version = '*'
        pkgDir  = os.path.split(cmtDir)[0].strip()
        pkgPath = os.path.split(pkgDir)[0].strip()
        msg.warning("Will use:")
        msg.warning( "\t\t\t- name    = %s" % pkgName )
        msg.warning( "\t\t\t- version = %s" % version )
        msg.warning( "\t\t\t- path    = %s" % pkgPath )
        pass

    msg.debug( "\t\t\t- name    = %s" % pkgName )
    msg.debug( "\t\t\t- version = %s" % version )
    msg.debug( "\t\t\t- path    = %s" % pkgPath )

    if pkgName.count(os.sep) > 0 :
       msg.warning( "About to create a funny CMT package !" )
       msg.warning( "'PkgName' contains '%s'. Please fix it!" % os.sep )
       msg.warning( "\t- name    = %s" % pkgName )
       msg.warning( "\t- version = %s" % version )
       msg.warning( "\t- path    = %s" % pkgPath )
       # Ok, so, I fix it - but user is warned...
       pkgName = os.path.basename(pkgName)
       pass

    return CmtPkg( pkgName, version, pkgPath )

def createUseList(workAreas, suppressList = ["WorkArea"]):

   msg = logging.getLogger( "WorkAreaMgr" )
   cmtPackages = []
   uses        = []
   
   for workArea in workAreas:
      cmtPackages.extend( scan( workArea, suppressList ) )
      pass

   # Handle duplicate CMT packages:
   pkgs = {}
   duplicates = {}
   for cmtPkg in cmtPackages:
      if not pkgs.has_key(cmtPkg.name):
         pkgs[cmtPkg.name] = cmtPkg
         pass
      else:
         # we found a duplicate...
         # check that the new one has a more recent version
         if pkgs[cmtPkg.name].version < cmtPkg.version:
            pkgs[cmtPkg.name] = cmtPkg
            pass
         duplicates[cmtPkg.name] = pkgs[cmtPkg.name]
         pass
      pass
   if len(duplicates) > 0:
      msg.warning( "Found duplicate(s): (listing the ones we kept)" )
      for k in duplicates.keys():
         msg.warning( "--" )
         msg.warning( " Package: %s" % duplicates[k].name )
         msg.warning( " Version: %s" % duplicates[k].version )
         msg.warning( " Path:    %s" % duplicates[k].path )
         pass
      pass

   del duplicates
   cmtPackages = [ pkg for pkg in pkgs.values() ]
   del pkgs
                      
   msg.info( "Found %i packages in WorkArea" % len(cmtPackages) )
   if len(suppressList) >= 1:
      # -1 because WorkArea is removed by default
      msg.info( "=> %i package(s) in suppression list" % \
                int(len(suppressList) - 1) ) 

   for cmtPkg in cmtPackages:
      # swallow the WorkArea path so we have a "cmt path" to put
      # in the req file
      for workArea in workAreas:
         cmtPkg.path = cmtPkg.path.replace( workArea+os.sep, '' )
         cmtPkg.path = cmtPkg.path.replace( workArea,        '' )
         pass

      if cmtPkg.path.endswith( os.sep ):
         cmtPkg.path = os.path.split(cmtPkg.path)
         pass

      use = "use %s \t%s \t%s -no_auto_imports" % \
            ( cmtPkg.name,
              "*", #cmtPkg.version,
              cmtPkg.path )
      msg.debug( "\t%s" % use )

      uses.append( use )
      pass

   return uses

def _translate_runtimepkg_name(n):
    db = {
        'hlt': 'AtlasHLT',
        'manacore': 'ManaCore',
        'detcommon': 'DetCommon',
        'AthAnalysisBase': 'AthAnalysisBase',
        'AthAnalysisSUSY': 'AthAnalysisSUSY',
        'AthSimulationBase': 'AthSimulationBase'
        }
    if n in db:
        return db[n]
    else:
        o = 'Atlas'+n[0].upper() + n[1:]
        if o.startswith('AtlasAtlas'):
            o = o[len('Atlas'):]
        return o
    
def createWorkArea(workAreas = None, installDir = None,
                   runTimePkg = None, suppressList = None):

    msg = logging.getLogger("WorkAreaMgr")
    if workAreas is None:
        workAreas = []
    if suppressList is None:
       suppressList = [ "WorkArea" ]
    else:
       suppressList.append( "WorkArea" )
       pass

    if runTimePkg is None:
        runTimePkg = os.getenv('AtlasProject', 'AtlasOffline')
        pass
    atlasRunTime = _translate_runtimepkg_name(runTimePkg)
    
    defaultWorkArea = _get_currentpath()
    if len(workAreas) <= 0:
        workAreas = [ defaultWorkArea ]
    if installDir == None:
        installDir = defaultWorkArea
        pass

    msg.info( 80*"#" )
    msg.info( "Creating a WorkArea CMT package under: [%s] " % installDir )

    try:
        installWorkArea( installDir,
                         CmtPkg( "WorkArea", WORKAREA_VERSION, "" ) )
    except Exception,err:
        msg.error( "Could NOT create WorkArea package !!" )
        msg.error( "%r", err)
        msg.info( 80*"#" )
        sys.exit(3)
        
    except :
        msg.error( "Could NOT create WorkArea package !!" )
        msg.info( 80*"#" )
        sys.exit(4)
        
    reqLines = [
        "package WorkArea",
        "",
        "author Sebastien Binet <binet@cern.ch>",
        "",
        "######################################",
        "## Don't edit this file !!          ##",
        "## It is automatically generated... ##",
        "######################################",
        "",
        "## Generic part...",
        "use AtlasPolicy 	 \tAtlasPolicy-*",
        "use %sRunTime \t%sRunTime-*" % (atlasRunTime, atlasRunTime),
        "",
        "branches run python",
        "",
        "## Install the python classes into InstallArea",
        "apply_pattern declare_python_modules files=\"*.py\"",
        "",
        "",
        "## execute the post-install targets...",
        "private ",
        " macro_append all_dependencies \"\\",
        "  post_merge_rootmap \\", 
        "  post_merge_genconfdb \\",
        "  post_build_tpcnvdb \\",
        "\"",
        "end_private",
        "",
        "## Automatically generated part...",
        "" ]

    uses = createUseList(workAreas, suppressList)

    reqLines.extend( uses )
    reqLines.append( "" )
    reqLines.append( "## End of generation." )
    reqLines.append( "## EOF ##" )
    
    reqFile = open( os.path.join( installDir,
                                  "WorkArea",
                                  CmtStrings.CMTDIR,
                                  CmtStrings.CMTREQFILE ),
                    "w" )
    for reqLine in reqLines:
        reqFile.writelines( reqLine + os.linesep )
        pass

    msg.info( "Generation of %s done [OK]" % \
              os.path.join( "WorkArea",
                            CmtStrings.CMTDIR,
                            CmtStrings.CMTREQFILE ) )
    
    reqFile.close()

    msg.info( 80*"#" )
    return

def installWorkArea( installDir, cmtWorkAreaPkg ):
    msg = logging.getLogger("WorkAreaMgr")

    workAreaDir = os.path.join( installDir,  cmtWorkAreaPkg.name )
    cmtDir      = os.path.join( workAreaDir, CmtStrings.CMTDIR   )

    if os.path.exists(installDir):
        if os.access(installDir, os.W_OK):
            if os.path.exists( workAreaDir ):
                if not os.path.exists( cmtDir ):
                    os.mkdir( cmtDir )
                    pass
                pass
            else:
                os.makedirs( os.path.join( workAreaDir, cmtDir ) )
            pass
        else:
            msg.error( "Can't write under [%s] !!" % installDir )
            raise OSError
        pass
    else:
        try:
            os.makedirs(installDir)
            installWorkArea( installDir, cmtWorkAreaPkg )
        except OSError, what:
            msg.error( "Install dir for WorkArea does NOT exist and can't create it !!" )
            raise OSError, what
        pass

    msg.debug( "Creating a consistent version file for the WorkArea pkg..." )
    cmtVersFile = open( os.path.join(cmtDir, CmtStrings.CMTVERSIONFILE), 'w' )
    cmtVersFile.writelines( cmtWorkAreaPkg.version + os.linesep )
    cmtVersFile.close()
    msg.debug( "Create a dummy %s file for the WorkArea pkg..." % CmtStrings.CMTREQFILE ) 
    cmtReqFile = open( os.path.join(cmtDir, CmtStrings.CMTREQFILE), 'w' )
    cmtReqFile.writelines( "package %s %s" % (cmtWorkAreaPkg.name, os.linesep ) )
    cmtReqFile.close()

    msg.debug("creating python directories to workaround CMT bugs...")
    install_area = os.path.join(installDir, 'InstallArea')
    pydirs = [os.path.join(install_area, 'python'),
              os.path.join(install_area, '${CMTCONFIG}', 'lib', 'python')]
    pydirs = [os.path.expandvars(p) for p in pydirs]
    
    for p in pydirs:
        if not os.path.exists(p):
            try:
                os.makedirs(p)
            except OSError, what:
                msg.error('could not create directory [%s]',p)
                msg.error(what)
    msg.debug("creating python directories to workaround CMT bugs... [ok]")
                
    return

