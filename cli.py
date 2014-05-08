from __future__ import print_function

from gcode import GCode, GStatement, GCodeParser
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
def main(f, c, device, baudrate, measure, parse):
	if not f and not c:
		print("Need either file or code")
		return -1

	sys.stdout.write('Parsing gcode')
	sys.stdout.flush()

	parser = GCodeParser()
	if f:
		codes = parser.parse(f.read())
	else:
		c = '\n'.join(c.split(';'))
		codes = parser.parse(c)

	sys.stdout.write(': %d codes found\n' % len(codes))
	sys.stdout.flush()

	cnc = CNC(device, baudrate)

	if measure == 'metric':
		adjust = GCode('G21')
	else:
		adjust = GCode('G20')

	cnc.add_codes(GStatement(adjust))

	cnc.add_codes(*codes)

	cnc.onprogress, cnc.oncomplete = make_progressbar(len(cnc), 'Buffer: ')
	cnc.onalarm = lambda x: print('\nalarm: %s, %s' % (x, cnc.cur))
	cnc.onerror = lambda x: print('\nerror: %s, %s' % (x, cnc.cur))

	if parse:
		return 0

	try:
		cnc.connect()
		cnc.send_queue()
	except KeyboardInterrupt:
		print('\nInterrupted')
		cnc.halt()
	return 0

if __name__ == '__main__':
	main()
