# @file: pyshell/shellcmd.py

import getpass, os, sys
import pyshell.localshell as localshell

class ShellCMD (localshell.LocalShell):
    def ask_user (self, question):
        return raw_input (question)

    def password (self):
        return getpass.getpass()

    def command (self, text):
        pass

    def prompt (self):
        pass

    def write (self, text):
        sys.stdout.write (text)
        
