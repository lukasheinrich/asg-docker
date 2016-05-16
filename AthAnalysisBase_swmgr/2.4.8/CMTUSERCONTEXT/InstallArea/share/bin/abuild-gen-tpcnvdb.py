#!/usr/bin/env python

__doc__ = """a simple python script to extract informations relative to T/P converter libraries"""

import os
import subprocess

try:
    from PyUtils.Decorators import forking
except ImportError:
    def forking(fct):
        return fct

_exclude_list = [
    'libpyquen.so',
    'libhydjet.so',
    'libjetset73hydjet.so',
    'libpythia6.so',
    'libpythia6_dummy.so',
    'libpythia6_pdfdummy.so',
    'MEee2gZ2qq.so',
    ## libAhadicFormation.so,
    ## libExoGraviton_i.so,
    ## libToolsMath.so,
    ## GRVBase.so,
    ## libSherpaMain.so,
    ## libPythia8_i.so,
    ## libCascade_iLib.so,
    
    ]
"""list of libraries to exclude from massaging
"""

def import_root(batch=True):
    import PyCintex
    PyCintex.Cintex.Enable()
    import sys
    sys.argv.insert(1, '-b')
    import ROOT
    ROOT.gROOT.SetBatch(batch)
    ROOT.gErrorIgnoreLevel = ROOT.kError
    del sys.argv[1]
    return ROOT

def import_pyathena(batch=True):
    import AthenaPython.PyAthena as PyAthena
    import_root(batch)
    return PyAthena

def _get_mbr_factories():
    pyathena = import_pyathena()
    rflx_scope = getattr(pyathena, 'Reflex::Scope')
    factories = rflx_scope.ByName('__pf__')
    members = [factories.FunctionMemberAt(i)
               for i in xrange(factories.FunctionMemberSize())]
    return members

def _get_props(mbr):
    _props = mbr.Properties()
    props = {}
    for i in xrange(_props.KeySize()):
        k = _props.KeyAt(i)
        v = _props.PropertyAsString(i)
        props[k] = v
    return props

def _get_id(fct):
    props = _get_props(fct)
    if 'id' in props and props['id']:
        return props['id']
    return props['name']

@forking
def inspect_library(libname):
    tpcnv_db = {}
    print "::: inspecting [%s]..." % (libname,)
    pyathena = import_pyathena()
    pyathena.load_library('AthenaKernelDict')
    is_in_dso = pyathena.Athena.DsoUtils.inDso

    members = _get_mbr_factories()
    
    #print "-->",len(members)
    bkg = set()
    for i,fct in enumerate(members):
        ident = _get_id(fct)
        #print "==",ident
        bkg.add(ident)
    #bkg = list(bkg)

    # load the component library
    print "::: loading [%s]..." % (libname,)
    dso = pyathena.load_library(libname)

    lib_dsoname = os.path.basename(pyathena.find_library(libname))
    
    members = _get_mbr_factories()
    #print "-->",len(members)
   
    for mbr in members:
        props = _get_props(mbr)
        ident = _get_id(mbr)
        #print " ~~~>",ident
        if ident in bkg:
            print "\t==> skipping [%s]..." % (ident,)
            continue
        if not is_in_dso(mbr, lib_dsoname):
            print "\t==> skipping [%s]... (not a local symbol)" % (ident,)
            continue
            
        ret_type = mbr.TypeOf().ReturnType()
        ret_type = ret_type.Name()
        component_type = {
            'IInterface*' : 'IInterface',
            'IAlgorithm*' : 'Algorithm',
            'IService*':    'Service',
            'IAlgTool*':    'AlgTool',
            'IAuditor*':    'Auditor',
            'IConverter*':  'Converter',
            'DataObject*':  'DataObject',
            'ITPCnvBase*':  'TPCnv',
            }.get(ret_type, 'Unknown')
        if ident == 'ApplicationMgr':
            component_type = 'ApplicationMgr'
        if component_type != 'TPCnv':
            continue
        name = ident.strip()
        props['latest_vers'] = '1' if props['latest_vers'] == '1' else '0'
        props['is_ara_cnv'] = props.get('is_ara_cnv', '0')
        props['is_ara_cnv'] = '0' if props['is_ara_cnv'] in ('','0') else '1'
        print " - tpcnv:",name,props
        tpcnv_db[name] = {'tpcnv': name,
                          'pers_type': props['pers_type'],
                          'trans_type': props['trans_type'],
                          'latest_vers': props['latest_vers'],
                          'is_ara_cnv': props['is_ara_cnv'],
                          'libname': lib_dsoname}
        
    return tpcnv_db

def inspect_installarea(topdir=None):
    if topdir is None:
        cmtpath = os.environ['CMTPATH']
        topdir = os.path.join(cmtpath.split(os.pathsep)[0],
                              'InstallArea')
    if os.path.exists(os.path.join(topdir, 'InstallArea')):
        topdir = os.path.join(topdir, 'InstallArea')
    topdir = os.path.expandvars(topdir)
    topdir = os.path.expanduser(topdir)
    topdir = os.path.join(topdir,os.environ['CMTCONFIG'],'lib')

    if not os.path.exists(topdir):
        print "**error** no such directory [%s]" % (topdir,)
        return {}
    
    # load some needed libraries and tools
    pyathena = import_pyathena()
    pyathena.load_library('AthenaKernelDict')
    is_in_dso = pyathena.Athena.DsoUtils.inDso

    tpcnv_db = {}
    from glob import glob
    dso_files = glob(os.path.join(topdir,'*TPCnv.so'))
    for dso in dso_files:
        libname = os.path.basename(dso)
        if libname in _exclude_list:
            print "::: skipping:",dso
            continue
        try:
            db = inspect_library(libname)
            tpcnv_db.update(db)
        except Exception,err:
            pass

    return tpcnv_db

def save_tpcnv_db(tpcnv_db, fname):
    """save the registry of T/P converter into file `fname`
    
    Arguments:
    - `tpcnv_db`: a dict of 'tpcnv name' -> {'trans','pers','version'}
    - `fname`: the file name where to save the db
    """

    fname = os.path.expandvars(fname)
    fname = os.path.expanduser(fname)

    if os.path.exists(fname):
        os.remove(fname)

    with open(fname, 'w+') as fd:
        print >> fd, "# automatically produced"
        print >> fd, "# a db of T/P converters"
        fmt = "%(libname)s;%(tpcnv)s;" + \
              "%(trans_type)s;%(pers_type)s;%(latest_vers)s;%(is_ara_cnv)s"
        for k,v in tpcnv_db.iteritems():
            print >> fd, fmt % v
        fd.flush()

    return

def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog='abuild-gen-tpcnvdb',
        description="""\
        inspect a (set of) InstallArea(s) and extract the informations related
        to T/P converters"""
        )

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
    
    parser.add_argument(
        'install-area',
        default=_install_area(),
        #dest='install_area',
        nargs='*',
        help='the path to the install area to inspect'
        )

    def _outfname():
        cmtpath = _get_currentpath()
        cmtconf = os.environ['CMTCONFIG']
        install_area = os.path.join(cmtpath, 'InstallArea')
        outdir = os.path.join(install_area, cmtconf, 'lib')
        outfname = os.path.join(outdir, 'tpcnv.db')
        return outfname
    
    parser.add_argument(
        '-o','--output-file',
        default=_outfname(),
        help='the path to the file where T/P cnv infos will be saved [default=%(default)s]')

    parser.add_argument(
        '-v','--verbose',
        action='store_true',
        default=False,
        help='enable verbose output')

    args = parser.parse_args()

    outdir = os.path.dirname(args.output_file)
    if not os.path.exists(outdir):
        try:
            os.makedirs(outdir)
        except OSError, err:
            import errno
            # "handle" race condition
            if err.errno == errno.EEXIST:
                pass
            else:
                raise

    install_area = []
    _install_area = getattr(args, 'install-area')
    if isinstance(_install_area, basestring):
        _install_area = _install_area.split(os.pathsep)
    else:
        _install_area = list(_install_area)

    for i,d in enumerate(_install_area[:]):
        _install_area[i] = os.path.expanduser(os.path.expandvars(d))

    for d in _install_area:
        install_area.extend(d.split(os.pathsep))

    print ":"*80
    print ":::",parser.prog

    #############################
    # silence root error-printout
    # it tries to feed a foo/path:bar/path:baz/path to a TUrl
    # (and complains it isn't a valid URL. d'oh!)
    sys.argv = sys.argv[:1]
    #############################
    
    db = {}
    for topdir in install_area:
        print "::  install-area [%s]..." % (topdir,)
        db.update(inspect_installarea(topdir=topdir))
    save_tpcnv_db(db, args.output_file)

    print "::: bye."
    print ":"*80
    return 0

if __name__ == "__main__":
    try:
        import argparse
    except ImportError:
        print ""
        print "*** could not import 'argparse'. not enough project-karma ?"
        main = lambda : 0
    
    import sys
    sys.exit(main())
    
    

