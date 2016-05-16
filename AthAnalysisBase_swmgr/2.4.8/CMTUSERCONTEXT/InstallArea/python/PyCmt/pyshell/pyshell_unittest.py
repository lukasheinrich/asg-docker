# @file: pyshell_unittest.py

"""unit tests for pyshell"""

import logging, os, unittest

import utils
import localshell

### data ----------------------------------------------------------------------
msg = logging.getLogger ('pyshell-test')
if len(msg.handlers)==0:
    logging.basicConfig()

### registration --------------------------------------------------------------
class ShellUtilsTestCase (unittest.TestCase):
    def setUp (self):
        pass

    def tearDown (self):
        pass

    def test1_shell_family (self):
        """retrieving shell family"""
        sf = utils.shell_family (os)
        self.assert_ (sf==utils.BASH or sf==utils.CSH)

class LocalShellTestCase (unittest.TestCase):
    def setUp (self):
        self.sh = localshell.LocalShell()

    def tearDown (self):
        pass

    def test1_navigation (self):
        """directory navigation in local shell"""
        self.sh.chdir ("/tmp")
        self.assertEqual (self.sh.getcwd(), "/tmp")

    def test2_command (self):
        """programmatic access to a local shell"""
        stat, out = self.sh.getstatusoutput ("/bin/ls")
        self.assert_ (stat==0)
        msg.debug ('shell output of ls in %s:\n%s',
                   self.sh.getcwd(), out[:-1])

## run test in standalone mode
if __name__ == '__main__':
    unittest.main()
    
