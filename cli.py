from __future__ import print_function

from gcode import GCode, GStatement, GCodeParser, GManager
from cnc import CNC

from progressbar import ProgressBar, ETA, Percentage, Bar
import click

import sys

def make_progressbar(length, prefix=''):
	progressbar = ProgressBar(maxval=length,
		                       widgets=[prefix, Percentage(), ' ', Bar(), ' ', ETA()]).start()
	def update(i):
		progressbar.update(i)

	def complete():
		progressbar.finish()
	return (update, complete)

@click.command()
@click.help_option('-h')
@click.version_option('0.1')
@click.option('-f', metavar='FILE', type=click.File('rb'), help='gcode file')
@click.option('-c', metavar='CODE', type=str, help='inline gcode')
@click.argument('device', help='serial device')
@click.option('-b', '--baudrate', default=115200, help='baudrate')
@click.option('-m', '--metric', 'measure', flag_value='metric', default=True)
@click.option('-i', '--imperial', 'measure', flag_value='imperial')
@click.option('-p', '--parse', 'parse', is_flag=True, help='parse only')
@click.option('-d', '--dump', 'dump', is_flag=True, help='dump parsed gcodes')
@click.option('-y', '--yes', 'yes', is_flag=True, help='do not ask questions')
def main(f, c, device, baudrate, measure, parse, dump, yes):
	if not f and not c:
		print("Need either file or code")
		return -1
	parser = GCodeParser()
	if f:
		codes = parser.parse(f.read())
	else:
		c = '\n'.join(c.split(';'))
		codes = parser.parse(c)


	if not dump:
		print('Job information:')
		print('-----------------------')
		print('  %d codes' % len(codes))

		manager = GManager(*codes)
		try:
			is_metric = manager.detect_metric()
			if is_metric == True:
				print('  Metric units')
			elif is_metric == False:
				print('  Imperial units')
			else:
				print('  No units')
		except:
			print('  Unable to detect units')

		try:
			workarea = manager.detect_workarea()

			print('  Required workarea (without arcs):')
			for axis in workarea:
				print('     %s: %f, %f' % (axis, workarea[axis][0], workarea[axis][1]))

		except RuntimeError:
			print('  Unable to detect workarea')

		try:
			rates = manager.detect_feedrates()
			if len(rates):
				print('  Feedrates:')
				print('    %s' % ', '.join([str(i) for i in rates]))
		except RuntimeError:
			print('  Unable to detect feedrates')

	if dump:
		for i in codes:
			print(i)

	if parse:
		return 0

	if measure == 'metric':
		adjust = GCode('G', 21)
	else:
		adjust = GCode('G', 20)

	if not yes:
		print()
		x = None
		while x != 'y':
			x = raw_input('Start? (y/n)')
			if x == 'n':
				print('Aborting')
				return -1

	cnc = CNC(device, baudrate)
	cnc.add_codes(GStatement(adjust))
	cnc.add_codes(*codes)

	cnc.onprogress, cnc.oncomplete = make_progressbar(len(cnc), 'Buffer: ')
	cnc.onalarm = lambda x: print('\nalarm: %s, %s' % (x, cnc.cur))
	cnc.onerror = lambda x: print('\nerror: %s, %s' % (x, cnc.cur))

	try:
		cnc.connect()
		cnc.send_queue()
	except KeyboardInterrupt:
		print('\nInterrupted')
		cnc.halt()
	return 0

if __name__ == '__main__':
	main()
