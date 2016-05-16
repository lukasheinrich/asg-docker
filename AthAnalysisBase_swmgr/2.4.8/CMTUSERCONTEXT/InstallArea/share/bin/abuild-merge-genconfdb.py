#!/usr/bin/env python

__doc__ = """asimple script to merge all _confDb files into a project-wide _merged_confDb file"""

### imports --------------------------------------------------------------------
import os
import sys
from fnmatch import fnmatch
import shutil
import getopt
import subprocess

_useropts = "o:vh"
_userlongopts = [
    "install-area=",
    "output-file=",
    "verbose",
    "help"
    ]
_error_msg = """\
inspect a (set of) InstallArea(s), collect all confDb files and merge them into one single project-wide merged_confDb file.

Accepted command line options:
     --install-area=<path or env.var> ...  path to the InstallArea to inspect
 -o, --output-file                    ...  name of the merged output file
 -v, --verbose                        ...  enable verbose mode
 -h, --help                           ...  print this help message
"""

### functions ------------------------------------------------------------------

def collect_genconfdb_fnames(topdir,
                             pattern='*confDb.py',
                             exclude_pattern='*_merged_confDb.py'):
                          
    """ recursively inspect the `topdir` directory for files named '*confDb.py'
        but exclude the files named '*_merged_confDb.py'
        returns a list of unique real paths
    """
    print "::: collecting genconfdb files..."
    all_files = []
    # we need the 'followlinks' argument
    if sys.version_info[:2] < (2,6): os_walk = _walk
    else:                            os_walk = os.walk

    for root, dirs, files in os_walk(topdir, followlinks=True):
        for f in files:
            if fnmatch(f, pattern) and not fnmatch(f, exclude_pattern):
                full_name = os.path.join(root, f)
                full_name = os.path.realpath(full_name)
                all_files.append(full_name)
                print " - [%s]" % (full_name,)
                
    all_files = list(set(all_files))
    print "::: collecting genconfdb files... [done] (nbr=%i)" % (len(all_files),)
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

def do_merge_files(topdir, ofname,
                   pattern='*_confDb.py',
                   exclude_pattern='*_merged_confDb.py'):

    if isinstance(topdir, basestring):
        topdir = topdir.split(os.pathsep)
        
    confdb_fnames = []
    for d in topdir:
        confdb_fnames.extend(collect_genconfdb_fnames(d, pattern,
                                                      exclude_pattern))

    return merge_files(confdb_fnames, ofname)

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
        return install_area
    
    def _outfname():
        cmtpath = _get_currentpath()
        proj_name = os.path.basename(cmtpath)
        try:
            proj_name = cmtpath.split(os.sep)[-2]
        except Exception:
            pass
        cmtconf = os.environ['CMTCONFIG']
        install_area = os.path.join(cmtpath, 'InstallArea')
        pyvers = 'python%s.%s' % sys.version_info[:2]
        outdir = os.path.join(install_area, cmtconf, 'lib', pyvers)
        outfname = os.path.join(outdir, '%s_merged_confDb.py' % proj_name)
        return outfname

    opts = Options()
    opts.install_area = _install_area()
    opts.output_file = _outfname()
    opts.verbose = False

    # process user options
    try:
        optlist, args = getopt.getopt(sys.argv[1:], _useropts, _userlongopts)
    except getopt.error:
        print sys.exc_value
        _help_and_exit()
        pass

    if args:
        print "Unhandled arguments:", args
        _help_and_exit()
        pass

    for opt, arg in optlist:
        if opt in ("--install-area",):
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
    print "::: abuild-merge-genconfdb"
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
