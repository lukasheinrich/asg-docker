# File: pyshell/vt100.py

"""vt100 decoder"""

## removal of escape sequences and the like

def filter(line_p):
    """
    remove non-printable characters from line <line_p>
    return a printable string.
    """
    line, i, imax = '', 0, len(line_p)
    while i<imax:
        ac = ord(line_p[i])
        if (32<=ac<127) or ac in (9,10): # printable, \t, \n
            line += line_p[i]
        elif ac == 27:                   # remove coded sequences
            i += 1
            while i<imax and line_p[i].lower() not in 'abcdhsujkm':
                i += 1
        elif ac == 8 or (ac==13 and
                         line and line[-1] == ' '): # backspace or EOL spacing
            if line:
                line = line[:-1]
        i += 1
    return line
