from __future__ import print_function

from gcode import GCode, GCodeParser
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
def main(f, c, device, baudrate, measure):
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
	cnc.connect()

	if measure == 'metric':
		cnc.add_codes(GCode('G21'))
	else:
		cnc.add_codes(GCode('G20'))

	cnc.add_codes(*codes)

	cnc.onprogress, cnc.oncomplete = make_progressbar(len(cnc), 'Buffer: ')
	cnc.onalarm = lambda x: print('\nalarm: %s' % x)
	cnc.onerror = lambda x: print('\nerror: %s' % x)

	try:
		cnc.send_queue()
	except KeyboardInterrupt:
		print('\nInterrupted')
		cnc.halt()
	return 0

if __name__ == '__main__':
	main()
