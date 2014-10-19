cnc
===

Shapeoko 2 CNC optimizer/sender

It ignores comments or what it considers illegal code for grbl, to spare the CNC controller some parsing.
For most of my tests, it effectively cuts the payload in half. For Easel payloads, I have seen 90% reductions.

It performs the following processes:
* Removes comments
* Removes file-marks
* Removes bonus G codes (they're stateful)
* Removes noop move codes
* Removes linear incremental move commands
* Removes commands not understood by GRBL
* Move feedrate setting to its own statement, and removes noop feedrate codes
* Puts M codes on their own line
* Removes empty lines

If interrupted by Ctrl-C, it will send Ctrl-X, which for grbl means "abort".That effectively makes it an emergency-stop.

Requires click and progressbar. use with:

    python cli.py
