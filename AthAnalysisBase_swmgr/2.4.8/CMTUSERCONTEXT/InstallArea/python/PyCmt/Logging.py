## @author: Sebastien Binet
## @file :  Logging.py
## @purpose: try to import Logging from AthenaCommon.
##           falls back on stdlib's one

__version__ = "$Revision$"
__author__  = "Sebastien Binet"

__all__ = ['msg', 'logging']

try:
    import AthenaCommon.Logging as L
    msg = L.log
    logging = L.logging
except ImportError:
    import logging
    logging.VERBOSE = logging.DEBUG - 1
    logging.ALL     = logging.DEBUG - 2
    logging.addLevelName( logging.VERBOSE, 'VERBOSE' )
    logging.addLevelName( logging.ALL, 'ALL' )
    logging.basicConfig(level=logging.INFO,
                        format="Py:%(name)-14s%(levelname)8s %(message)s")
    cls = logging.getLoggerClass()
    def verbose(self, msg, *args, **kwargs):
        if self.manager.disable >= logging.VERBOSE:
            return
        if logging.VERBOSE >= self.getEffectiveLevel():
            apply(self._log, (logging.VERBOSE, msg, args), kwargs)
    cls.verbose = verbose
    del verbose
    
    log = msg = logging.getLogger("Athena")
    
            
