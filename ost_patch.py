import os

# This is a complete and utter hack. Auto inputs path to SNAP gpt.exe into ost package WHICH WILL ALWAYS ASK FOR USER INPUT.
if os.name == "nt":
    import sys
    from io import StringIO, BytesIO
    import shutil

    snap_gpt_string = shutil.which("gpt.exe")
    
    # save default implementation of stdin
    default_stdin = sys.stdin

    # use prepared input
    sys.stdin = StringIO(snap_gpt_string)

    # import
    import ost

    # restore default implementation
    sys.stdin = default_stdin
else:
    import ost