from __future__ import print_function

from gcode import GCode, GStatement, GCodeParser, GManager
from cnc import CNC
from optimizer import * # Optimizer, CommentRemover, FileMarkRemover, CodeSaver, EmptyStatementRemover

from progressbar import ProgressBar, ETA, Percentage, Bar
import click

import sys

@click.group()
def main():
	pass

def make_progressbar(length, prefix=''):
	progressbar = ProgressBar(maxval=length,
		                       widgets=[prefix, Percentage(), ' ', Bar(), ' ', ETA()]).start()
	def update(i):
		progressbar.update(i)

	def complete():
		progressbar.finish()
	return (update, complete)

def parse_and_optimize(code, noopt):
	parser = GCodeParser()
	code = parser.parse(code)
	if noopt:
		return code
	opt = Optimizer(CommentRemover(),
	                FileMarkRemover(),
	                CodeSaver(),
	                GrblCleaner(),
	                FeedratePatcher(),
	                MPatcher(),
	                EmptyStatementRemover())
	return opt.optimize(code)

def generate_stats(codes):
	output = '''
Job information:
-----------------------
  %d codes
''' % len(codes)

	manager = GManager(*codes)
	try:
		is_metric = manager.detect_metric()
		if is_metric == True:
			output += '  Metric units\n'
		elif is_metric == False:
			output += '  Imperial units\n'
		else:
			output += '  No units\n'
	except Exception, e:
		output += '  Unable to detect units (%s)\n' % str(e)

	try:
		workarea = manager.detect_workarea()

		output += '  Required workarea (without arcs):\n'
		for axis in workarea:
			output += '     %s: %f, %f\n' % (axis, workarea[axis][0], workarea[axis][1])

	except Exception, e:
		output += '  Unable to detect workarea (%s)\n' % str(e)

	try:
		rates = manager.detect_feedrates()
		if len(rates):
			output += '  Feedrates:\n'
			output += '    %s\n' % ', '.join([str(i) for i in rates])
	except RuntimeError:
		output += '  Unable to detect feedrates\n'

	return output

@main.command()
@click.option('-c', '--code', 'code', metavar='CODE', type=str, help='inline gcode')
@click.option('-f', '--file', 'ifile', metavar='INPUT', type=click.File('rb'), help='gcode file')
@click.option('-d', '--dump', 'dump', is_flag=True, help='dump code to stdout')
@click.option('-o', '--output', 'ofile', metavar='OUTPUT', type=click.File('wb'), help='output')
@click.option('-s', '--stats', 'stats', is_flag=True, help='print stats to stderr')
@click.option('-n', '--no-opt', 'noopt', is_flag=True, help='disable optimizations')
def parse(code, ifile, dump, ofile, stats, noopt):
	if not ifile and not code:
		print("Need either file or code")
		return -1

	if ifile:
		code = ifile.read()
	else:
		code = '\n'.join(code.split(';'))

	codes = parse_and_optimize(code, noopt)
	if stats:
		print(generate_stats(codes), file=sys.stderr)

	s = []
	for statement in codes:
		s.append(str(statement))

	if ofile:
		ofile.write('\n'.join(s))
	if dump:
		print('\n'.join(s),)


@main.command()
@click.version_option('0.1')
@click.argument('device', help='serial device')
@click.option('-c', '--code', 'code', metavar='CODE', type=str, help='inline gcode')
@click.option('-f', '--file', 'ifile', metavar='INPUT', type=click.File('rb'), help='gcode file')
@click.option('-b', '--baudrate', default=115200, help='baudrate')
@click.option('-m', '--metric', 'measure', flag_value='metric', default=True, help='start in metric mode')
@click.option('-i', '--imperial', 'measure', flag_value='imperial', help='start in imperial mode')
@click.option('-y', '--yes', 'yes', is_flag=True, help='do not ask questions')
@click.option('-q', '--quiet', 'quiet', is_flag=True, help='quiet output')
@click.option('-s', '--stats', 'stats', is_flag=True, help='print stats to stderr')
@click.option('-n', '--no-opt', 'noopt', is_flag=True, help='disable optimizations')
def send(code, ifile, device, baudrate, measure, yes, noopt, stats):
	if not f and not c:
		print("Need either file or code")
		return -1

	if ifile:
		code = ifile.read()
	else:
		code = '\n'.join(code.split(';'))

	codes = parse_and_optimize(code, noopt)

	if measure == 'metric':
		adjust = GCode('G', 21)
	else:
		adjust = GCode('G', 20)

	codes.insert(0, GStatement(adjust))

	if stats:
		print(generate_stats(codes), file=sys.stderr)

	if not yes:
		print()
		x = None
		while x != 'y':
			x = raw_input('Start? (y/n) ')
			if x == 'n':
				print('Aborting')
				return -1

	cnc = CNC(device, baudrate)
	cnc.add_codes(*codes)

	cnc.onprogress, cnc.oncomplete = make_progressbar(len(cnc), 'Buffer: ')
	cnc.onalarm = lambda x: print('\nalarm: %s, %s' % (x, cnc.cur))
	cnc.onerror = lambda x: print('\nerror: %s, %s' % (x, cnc.cur))

	try:
		cnc.connect()
		cnc.send_queue()
	except KeyboardInterrupt:
		print()
		print('Interrupted')
		print('Raising position alarm')
		cnc.halt()
		return -1

	if alarm:
		print('Raising position alarm')
		cnc.halt()
	return 0

if __name__ == '__main__':
	main()
