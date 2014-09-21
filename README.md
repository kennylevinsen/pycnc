cnc
===

Shapeoko 2 CNC optimizer/sender

It ignores comments or what it considers illegal code for grbl, to spare the CNC controller some parsing.
For most of my tests, it effectively cuts the payload in half.

If interrupted by Ctrl-C, it will send Ctrl-X, which for grbl means "abort".That effectively makes it an emergency-stop.

Requires click and progressbar. use with:

    python cli.py
