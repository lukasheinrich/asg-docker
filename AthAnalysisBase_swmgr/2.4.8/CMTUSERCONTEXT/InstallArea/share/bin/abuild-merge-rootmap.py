#!/usr/bin/env python

__doc__ = """a simple script to merge all .dsomap files into a project-wide .rootmap file"""

### imports --------------------------------------------------------------------
import os
import sys
from fnmatch import fnmatch as _fnmatch
import shutil
import getopt
import subprocess

### globals --------------------------------------------------------------------
_dsomap_exclude_list = [
    "TestRootConversions1Dict.dsomap",
    "TestRootConversions2Dict.dsomap",
    "DataModelTestDataRead.rootmap",
    "DataModelTestDataWriteCnvPoolCnv.rootmap",
    "DataModelTestDataReadCnvPoolCnv.rootmap",
    "DataModelTestDataReadDict.dsomap",
    "DataModelTestDataWriteDict.dsomap",
    # from APR
    "test_PersistencySvc_CustomReferenceAndStreamerDict.dsomap",
    "test_PersistencySvc_CustomReferenceDict.dsomap",
    "test_PersistencySvc_CustomStreamersDict.dsomap",
    "test_PersistencySvc_NoClassIDDict.dsomap",
    "test_StorageSvc_TransientMembersDict.dsomap",
    "test_TestDictionaryDict.dsomap",
    ]
"""list of dsomap files to ignore from the merge"""

_useropts = "i:o:vh"
_userlongopts = [
    "install-area=",
    "output-file=",
    "verbose",
    "help"
    ]
_error_msg = """\
inspect a (set of) InstallArea(s), collect all .dsomap files and merge them into one single project-wide .rootmap file.

Accepted command line options:
 -i, --install-area=<path or env.var> ...  path to the InstallArea to inspect
 -o, --output-file                    ...  name of the merged output file
 -v, --verbose                        ...  enable verbose mode
 -h, --help                           ...  print this help message
"""

### functions ------------------------------------------------------------------

def fnmatch(path, pattern):
    """helper function to test multiple patterns
    """
    patterns = pattern
    if isinstance(patterns, basestring):
        patterns = [patterns]
    for pattern in patterns:
        if _fnmatch(path, pattern):
            return True
    return False

def _is_in_ignore_list(fname):
    """ helper method to test if `fname` is in any of the ignore list
    """
    bfname = os.path.basename(fname)
    return bfname in _dsomap_exclude_list

def collect_dsomap_fnames(topdir, pattern=['*.dsomap','*.rootmap']):
    """ recursively inspect the `topdir` directory for files named '*.dsomap'
        returns a list of unique real paths
    """
    print "::: collecting dsomap files..."
    all_files = []
    # we need the 'followlinks' argument
    if sys.version_info[:2] < (2,6): os_walk = _walk
    else:                            os_walk = os.walk

    if isinstance(pattern, basestring):
        pattern = [pattern]

    # opt hack
    _install_area_cmtcfg = os.path.join('InstallArea', os.environ['CMTCONFIG'])
    
    for root, dirs, files in os_walk(topdir, followlinks=True):
        for f in files:
            if fnmatch(f, pattern):
                full_name = os.path.join(root, f)
                full_name = os.path.realpath(full_name)
                if (os.environ['CMTCONFIG'] in full_name and
                    not _is_in_ignore_list(full_name) and
                    # FIXME: we can't rely on *ALL* files being under the
                    # install-area b/c of component libs!
                    #not _install_area_cmtcfg in full_name and
                    1):
                    all_files.append(full_name)
                    print " - [%s]" % (full_name,)
                
    all_files = list(set(all_files))
    print "::: collecting dsomap files... [done] (nbr=%i)" % (len(all_files),)
    return all_files
    
def merge_files(fnames, ofname):
    """merge the content of all files `fnames` into the file `ofname`
    """
    print "::: merging files into [%s]..." % (ofname,)
    _copy = shutil.copyfileobj
    ofile = open(ofname, 'w')
    for fname in fnames:
        print "::: processing [%s]..." % (fname,)
        _copy(fsrc=open(fname, 'r'), fdst=ofile)
        ofile.flush()
    ofile.close()
    
    print "::: merging files into [%s]... [done]" % (ofname,)
    return 0

def do_merge_files(topdir, ofname, pattern=['*.dsomap','*.rootmap']):

    if isinstance(topdir, basestring):
        topdir = topdir.split(os.pathsep)
        
    dsomap_fnames = []
    for d in topdir:
        dsomap_fnames.extend(collect_dsomap_fnames(d, pattern))
    return merge_files(dsomap_fnames, ofname)

def main():
    """the main entry point of this script
    """

    class Options(object):
        """place holder for command line options values"""
        pass
    
    def _help_and_exit():
        print _error_msg
        sys.exit(1)

    def _get_currentpath():
        current = []
        for m in ('CMTINSTALLAREA', 'cmt_installarea_prefix'):
            cmd = 'cmt show macro_value %s' % m
            p = subprocess.Popen(cmd, shell = True,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.STDOUT)
            out = p.communicate()[0]
            if p.returncode != 0:
                raise OSError(out)
            current.append(out)
        return current[0].rstrip(current[1]).rstrip(os.sep)

    def _install_area():
        cmtpath = _get_currentpath()
        install_area = os.path.join(cmtpath, 'InstallArea')
        #return install_area
        # FIXME: we should only return the install-area, but some needed
        # rootmap files (for component libs) are installed under the pkg
        # $CMTCONFIG directory and not installed under the install-area
        return cmtpath
    
    def _outfname():
        cmtpath = _get_currentpath()
        proj_name = os.path.basename(cmtpath)
        try:
            proj_name = cmtpath.split(os.sep)[-2]
        except Exception:
            pass
        cmtconf = os.environ['CMTCONFIG']
        install_area = os.path.join(cmtpath, 'InstallArea')
        outdir = os.path.join(install_area, cmtconf, 'lib')
        outfname = os.path.join(outdir, '%s.rootmap' % proj_name)
        return outfname

    opts = Options()
    opts.install_area = _install_area()
    opts.output_file = _outfname()
    opts.verbose = False

    # process user options
    try:
        optlist, args = getopt.getopt(sys.argv[1:], _useropts, _userlongopts)
    except getopt.error:
        print "-->",_useropts
        print sys.exc_value
        _help_and_exit()
        pass

    if args:
        print "Unhandled arguments:", args
        _help_and_exit()
        pass

    for opt, arg in optlist:
        if opt in ("-i", "--install-area",):
            opts.install_area = arg
            pass
        elif opt in ("-o", "--output-file",):
            opts.output_file = arg
            pass
        elif opt in ("-v", "--verbose"):
            opts.verbose = True
            pass
        elif opt in ("-h", "--help"):
            _help_and_exit()
            pass
        else:
            print "Unknown option:", opt
            _help_and_exit()
            pass
        
    #print args

    install_area = []
    _install_area = opts.install_area[:]
    if isinstance(_install_area, basestring):
        _install_area =[_install_area]
    else:
        _install_area = list(_install_area)

    for i,d in enumerate(_install_area[:]):
        _install_area[i] = os.path.expanduser(os.path.expandvars(d))

    for d in _install_area:
        install_area.extend(d.split(os.pathsep))
        
    
    
    outdir = os.path.dirname(opts.output_file)
    if not os.path.exists(outdir):
        if outdir:
            try:
                os.makedirs(outdir)
            except OSError, err:
                import errno
                # "handle" race condition
                if err.errno == errno.EEXIST:
                    pass
                else:
                    raise

    if os.path.exists(opts.output_file):
        os.remove(opts.output_file)
        
    print ":"*80
    print "::: abuild-merge-rootmap"
    rc = do_merge_files(topdir=install_area,
                        ofname=opts.output_file)
    print "::: bye."
    print ":"*80
    return rc

# copied verbatim from py-2.6
def _walk(top, topdown=True, onerror=None, followlinks=False):
    """Directory tree generator.
 
    For each directory in the directory tree rooted at top (including top
    itself, but excluding '.' and '..'), yields a 3-tuple
 
        dirpath, dirnames, filenames
 
    dirpath is a string, the path to the directory.  dirnames is a list of
    the names of the subdirectories in dirpath (excluding '.' and '..').
    filenames is a list of the names of the non-directory files in dirpath.
    Note that the names in the lists are just names, with no path components.
    To get a full path (which begins with top) to a file or directory in
    dirpath, do os.path.join(dirpath, name).
 
    If optional arg 'topdown' is true or not specified, the triple for a
    directory is generated before the triples for any of its subdirectories
    (directories are generated top down).  If topdown is false, the triple
    for a directory is generated after the triples for all of its
    subdirectories (directories are generated bottom up).
 
    When topdown is true, the caller can modify the dirnames list in-place
    (e.g., via del or slice assignment), and walk will only recurse into the
    subdirectories whose names remain in dirnames; this can be used to prune
    the search, or to impose a specific order of visiting.  Modifying
    dirnames when topdown is false is ineffective, since the directories in
    dirnames have already been generated by the time dirnames itself is
    generated.
 
    By default errors from the os.listdir() call are ignored.  If
    optional arg 'onerror' is specified, it should be a function; it
    will be called with one argument, an os.error instance.  It can
    report the error to continue with the walk, or raise the exception
    to abort the walk.  Note that the filename is available as the
    filename attribute of the exception object.
 
    By default, os.walk does not follow symbolic links to subdirectories on
    systems that support them.  In order to get this functionality, set the
    optional argument 'followlinks' to true.
 
    Caution:  if you pass a relative pathname for top, don't change the
    current working directory between resumptions of walk.  walk never
    changes the current directory, and assumes that the client doesn't
    either.
 
    Example:
 
    import os
    from os.path import join, getsize
    for root, dirs, files in os.walk('python/Lib/email'):
        print root, "consumes",
        print sum([getsize(join(root, name)) for name in files]),
        print "bytes in", len(files), "non-directory files"
        if 'CVS' in dirs:
            dirs.remove('CVS')  # don't visit CVS directories
    """
 
    from os.path import join, isdir, islink
 
    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.path.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        # Note that listdir and error are globals in this module due
        # to earlier import-*.
        names = os.listdir(top)
    except os.error, err:
        if onerror is not None:
            onerror(err)
        return
 
    dirs, nondirs = [], []
    for name in names:
        if isdir(join(top, name)):
            dirs.append(name)
        else:
            nondirs.append(name)
 
    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        path = join(top, name)
        if followlinks or not islink(path):
            for x in _walk(path, topdown, onerror, followlinks):
                yield x
    if not topdown:
        yield top, dirs, nondirs

if __name__ == "__main__":
    import sys
    sys.exit(main())
