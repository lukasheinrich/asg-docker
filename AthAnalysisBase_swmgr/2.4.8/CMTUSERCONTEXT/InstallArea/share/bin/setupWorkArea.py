#!/usr/bin/env python
#
# @file: setupWorkArea.py
# @purpose: fill the stubs of the WorkArea package so that all the local
#           CMT packages can be recompiled in one go.
# @date: June 2006
# @author: Sebastien Binet

# /!\ Warning /!\
# I am relying on the following assumption:
#  - you have a working Release environment
#     ==> a valid CMTPATH environment variable
#     ==> python-2.4 (this needs to be addressed!!)

# example0:
# ./setupWorkArea.py
# ==> will :
#  - install a CMT package called WorkArea under the first directory found
#    in the CMTPATH environment variable
#  - put use statements for all the CMT packages (recursively) found under
#    the first directory of the CMTPATH environment variable

# example1:
# ./setupWorkArea.py -i ~/Athena/dev -S ~/cmtSuppressList -w $CMTPATH
# ==> will :
#  - install a CMT package called WorkArea under the dir. ~/Athena/dev
#  - put use statements for all the CMT packages (recursively) found under
#    the ':' separated list of paths (=$CMTPATH)
#  - and only if these packages are not found in the cmtSuppressList

# example2:
# ./setupWorkArea.py -s "['Foo']"
# - install a CMT package called WorkArea under the first dir of $CMTPATH
# - put use statements for all the CMT packages (recursively) found under
#   the first dir of $CMTPATH
# - remove any 'use statement' for packages called "Foo"

# example3:
# ./setupWorkArea.py --suppress-list "['Foo']"
# - install a CMT package called WorkArea under the first dir of $CMTPATH
# - put use statements for all the CMT packages (recursively) found under
#   the first dir of $CMTPATH
# - remove any 'use statement' for packages called "Foo"

# example4:
# ./setupWorkArea.py --suppress-list "['Foo']" --runtime Core
# - install a CMT package called WorkArea under the first dir of $CMTPATH
# - put use statements for all the CMT packages (recursively) found under
#   the first dir of $CMTPATH
# - remove any 'use statement' for packages called "Foo"
# - use only the AtlasCoreRunTime environment

# example5:
# ./setupWorkArea.py -r Core
# - install a CMT package called WorkArea under the first dir of $CMTPATH
# - put use statements for all the CMT packages (recursively) found under
#   the first dir of $CMTPATH
# - use only the AtlasCoreRunTime environment

# example6:
# ./setupWorkArea.py -g (or --group-area)
# - install a CMT package called WorkArea under the first dir of $CMTPATH
# - put use statements for all the CMT packages (recursively) found under
#   the first dir of $CMTPATH
# - put use statements for all the CMT packages (recursively) found under
#   the $GroupArea environment variable
# Note that one can specify the ':' separated list of Group areas directories:
# --group-area=${SomeVariable}:${GroupArea}:${SomethingElse}
# -g ${MyGroupArea}

import sys
import os
import getopt
import string

from PyUtils.Logging import logging

__version__ = "$Revision: 1.7 $"

##########################
# recognized user options
##########################
_useropts = 's:i:hl:S:w:r:gv'
_userlongopts = [ 'suppress-list=',  'install-dir=',
                  'help',            'loglevel=',
                  'suppress-file=',
                  'work-area=',
                  'runtime=',
                  'group-area',
                  'version' ]

def _usage():
   print """Accepted command line options (CLI):
   -s, --suppress-list <list> ...  list of package names to ignore.
   -S, --suppress-file <file> ...  path to a file containing the suppress list.
   -i, --install-dir <path>   ...  directory where to install the WorkArea pkg
   -w, --work-area <dir1:d2>  ...  directories under which the packages for the
                                   WorkArea pkg are installed.
   -g, --group-area <dir1:d2> ...  directories under which the packages for the
                                   GroupArea are looked for.
                                   If no argument is given, it will try to
                                   look for the $GroupArea environment
                                   variable.
   -r, --runtime <runtimePkg> ...  runtime package one wants to work with.
                                   Default is AtlasOfflineRunTime.
                                   Allowed values: core, event, conditions,
                                                   simulation, reconstruction,
                                                   trigger, analysis,
                                                   production, point1,
                                                   offline
   -h, --help                 ...  print this help message
   -l, --loglevel <level>     ...  logging level (DEBUG, INFO, WARNING, ERROR, FATAL)
   -v, --version              ...  print version number
   """
   return

#from PyUtils.WorkAreaLib import *
from WorkAreaLib import *

def _processOptions( useropts, userlongopts ):

    log = logging.getLogger("WorkAreaMgr")

    runTimePkgAllowedValues = [ "core",
                                "event",
                                "conditions",
                                "simulation",
                                "reconstruction",
                                "trigger",
                                "analysis",
                                "production",
                                "point1",
                                "tier0",
                                "hlt",
                                "offline",
                                "manacore",
                                ]
    # defaults
    workAreas  = []
    installDir = None
    runTimePkg = None # --> "offline" or what is in .asetup.save's [summary:AtlasProject]
    suppressList = []
    lvl = logging.INFO
    
    try:
        optlist,args = getopt.getopt( sys.argv[1:],
                                      useropts,
                                      userlongopts )
    except getopt.error:
        log.error( "%s" % sys.exc_value )
        _usage()
        sys.exit(2)

    for opt, arg in optlist:
        if opt in ('-h', '--help' ):
            _usage()
            sys.exit()
        elif opt in ('-v', '--version'):
            print WORKAREA_VERSION
            print "By Sebastien Binet"
            sys.exit()
        elif opt in ('-i', '--install-dir'):
            installDir = os.path.expanduser( os.path.expandvars(arg) )
        elif opt in ('-s', '--suppress-list'):
            exec( 'suppressList += %s' % arg )
            #suppressList = arg
        elif opt in ('-S', '--suppress-file'):
            suppressFileName = os.path.expanduser( os.path.expandvars(arg) )
            if os.path.exists( suppressFileName ):
                suppressFile = open( suppressFileName, 'r' )
                for line in suppressFile.readlines():
                    for l in line.splitlines():
                        suppressList.append( l.strip() )
                        pass
                    pass
                pass
            else:
                log.error("Could NOT access this file [%s]" % suppressFileName)
                pass
        elif opt in ('-w', '--work-area'):
            workAreaDirs = os.path.expanduser( os.path.expandvars(arg) )
            if workAreaDirs.count(os.pathsep) > 0:
               workAreaDirs = workAreaDirs.split(os.pathsep)
               pass
            for workAreaDir in workAreaDirs:
                if os.path.exists( workAreaDir ):
                    if os.access(workAreaDir, os.R_OK):
                        workAreas.append( os.path.abspath(workAreaDir) )
                        pass
                    else:
                        log.error( "Can't read from [%s] !!" % workAreaDir )
                        pass
                    pass
                else:
                    log.error("Directory does NOT exists [%s] !" % workAreaDir)
                    pass
                pass
        elif opt in ('-g', '--group-area'):
           if len(arg) == 0:
              arg = os.environ.get("GroupArea") or ""
              pass
           groupAreaDirs = os.path.expanduser( os.path.expandvars(arg) )
           if groupAreaDirs.count(os.pathsep) > 0:
              groupAreaDirs = groupAreaDirs.split(os.pathsep)
              pass
           for groupAreaDir in groupAreaDirs:
              if os.path.exists( groupAreaDir ):
                 if os.access(groupAreaDir, os.R_OK):
                    workAreas.append( groupAreaDir )
                    pass
                 else:
                    log.error( "Can't read from [%s] !!" % groupAreaDir )
                    pass
                 pass
              else:
                 log.error("Directory does NOT exists [%s] !" % groupAreaDir)
                 pass
              pass
        elif opt in ('-r', '--runtime'):
           if arg.lower() in runTimePkgAllowedValues:
              runTimePkg = arg
           else:
              log.error( "Unknown runtime package [%s]" % arg )
              log.error( "Must be one of: %s" % str(runTimePkgAllowedValues) )
              pass
        elif opt in ('-l', '--loglevel'):
            lvl = string.upper( arg )
            logLevel = getattr(logging, lvl)
            log.setLevel(logLevel)
            del lvl,logLevel
            pass
        else:
            pass
        pass

    if runTimePkg is None:
       # try to get it from .asetup.save
       if os.path.exists('.asetup.save'):
          import ConfigParser as _cp
          cfg = _cp.SafeConfigParser()
          try:
             cfg.read(['.asetup.save'])
          except _cp.ParsingError, err:
             # .asetup.save file does not, generally, conform to MS Windows INI files syntax
             log.debug('got these non-fatal parsing errors:\n%s' % err)
          else:
             if (cfg.has_section('summary') and
                 cfg.has_option('summary', 'AtlasProject')):
                try:
                   v = cfg.get('summary', 'AtlasProject')
                   v = v.lower()
                   if v.startswith('atlas'):
                      v = v[len('atlas'):]
                      runTimePkg = v
                      log.info('taking runtime package [%s] from .asetup.save',
                               runTimePkg)
                except Exception, err:
                   log.info('got this non-fatal parsing error:\n%s' % err)
                   log.info('taking runtime package [AtlasOffline] by default')
                   runTimePkg = None # offline

       # failing to determine runTimePkg,
       # take it from env-var AtlasProject,
       # or 'offline'

    return workAreas, installDir, runTimePkg, suppressList
    
if __name__ == "__main__":

    msg = logging.getLogger('WorkAreaMgr')
    msg.setLevel(logging.INFO)
    
    ## process user options
    workAreas,  installDir,  \
    runTimePkg, suppressList = _processOptions( _useropts, _userlongopts )

    createWorkArea( workAreas, installDir, runTimePkg, suppressList )
    pass
