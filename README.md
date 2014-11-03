cnc
===

Shapeoko 2 CNC optimizer/sender

It ignores comments or what it considers illegal code for grbl, to spare the CNC controller some parsing.
For most of my tests, it effectively cuts the payload in half. For Easel payloads, I have seen 90% reductions.

It performs the following processes:
* Removes comments
* Removes file-marks
* Removes bonus G codes (they're modal)
* Removes noop move codes
* Removes commands not understood by GRBL
* Move feedrate setting to its own statement, and removes noop feedrate codes
* Puts M codes on their own line
* Removes empty lines

If interrupted by Ctrl-C, it will send Ctrl-X, which for grbl means "abort".That effectively makes it an emergency-stop.

Requires click and progressbar. use with:

    python cli.py

Notes
===

After seeing some performance issues and complexities in performing optimizations in this tool, I decided to try my luck with a go variant: https://github.com/joushou/gocnc
I find the new tool to be successful, and intend to place my effort there, rather than in maintaining this prototypal tool. I will fix bugs if noticed, but I am unlikely to do large features or rewrites unless my interest is for some reason restored, or someone begs me hard enough.

Apart from that, the tool have worked fine, and prior to my gocnc tool, it has been my only tool for sending gcode to my Shapeoko 2.
