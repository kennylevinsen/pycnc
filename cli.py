from gcode import GCode, GCodeParser
from cnc import CNC
import click
from progressbar import ProgressBar, ETA, Percentage, Bar

def make_progressbar(length, prefix=''):
	progressbar = ProgressBar(maxval=len(self.queue),
		                       widgets=[prefix, Percentage(), ' ', Bar(), ' ', ETA()]).start()
	def update(i):
		progressbar.update(i)
		if i == length:
			progressbar.finish()
	return update

@click.command()
@click.help_option('-h')
@click.version_option('0.1')
@click.argument('f', metavar='FILE', type=click.File('rb'), help='gcode file')
@click.argument('device', help='serial device')
@click.option('-b', '--baudrate', default=115200, help='baudrate')
def main(f, device, baudrate):
	print('Parsing gcode')
	parser = GCodeParser()
	codes = parser.parse(f.read())
	print('Found %d codes' % len(codes))
	cnc = CNC(device, baudrate)
	cnc.connect()
	cnc.add_codes(GCode('G21'))
	cnc.add_codes(*codes)

	cnc.onprogress = make_progressbar(len(cnc), 'Buffer:')

	try:
		cnc.send_queue()
	except KeyboardInterrupt:
		print('\nABORT!')
		cnc.halt()

if __name__ == '__main__':
	main()
