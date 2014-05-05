from serial import Serial
from pprint import pprint
from time import sleep
from collections import deque
from progressbar import ProgressBar, ETA, Percentage, Bar
import click
import sys


class GCode(object):
	def __init__(self, command=None, *args):
		self.command = command
		self.args = args

	def __str__(self):
		return '%s %s' % (self.command, ' '.join(self.args))


class GCodeParser(object):
	def __init__(self):
		pass

	def parse_command(self, cmd):
		components = cmd.split(' ')
		args = []
		for i, component in enumerate(components):
			if not component[0].isalpha():
				continue
			allowed = ['.', '-']
			for c in component[1:]:
				if c in allowed:
					allowed.remove(c)
				elif not c.isdigit():
					break
			else:
				args.append(component.upper())

		return args

	def parse(self, string):
		lines = string.split('\n')
		codes = []
		for line in lines:
			if len(line) == 0:
				continue

			res = self.parse_command(line)
			if len(res):
				codes.append(GCode(*res))
			else:
				print(' -- Ignoring GCode line: %s' % line)
		return codes


class ResultParser(object):
	def __init__(self, callback):
		self.buffer = b''
		self.callback = callback

	def feed(self, c):
		if c == b'\r': # Ignore
			return False
		elif c == b'\n':
			s = self.buffer
			self.buffer = b''
			if s == b'ok':
				self.callback('ok')
			elif s[:5] == b'error':
				self.callback('error')
			else:
				self.callback('info', s)
			return True
		else:
			self.buffer += c
			return False


class CNC(object):
	def __init__(self, devpath, baudrate):
		self.devpath = devpath
		self.baudrate = baudrate
		self.serial = None
		self.queue = []
		self.result_parser = ResultParser(self.rescb)
		self.cur = None

	def connect(self):
		if self.serial is not None:
			self.serial.close()
		self.serial = Serial(self.devpath, self.baudrate)
		if not self.await_connect():
			sleep(1)
			self.connect()

	def rescb(self, val, arg=None):
		if val == 'ok':
			pass
		elif val == 'error':
			print('COMMAND ERROR AT: %s' % self.cur)
			self.queue = []
		else:
			print('RETURN ERROR AT: %s' % arg)
			self.queue = []

	def await_connect(self):
		a = self.serial.read(2)
		if a != b'\r\n':
			return False
		while a != b'\n':
			a = self.serial.read(1)
		return True

	def add_codes(self, *codes):
		self.queue.extend(codes)

	def halt(self):
		self.serial.write('\x18\n')
		self.monitor()

	def send_queue(self):
		progressbar = ProgressBar(maxval=len(self.queue),
		                          widgets=['Buffer:', Percentage(), ' ', Bar(), ' ', ETA()]).start()
		for i, cmd in enumerate(self.queue):
			self.cur = cmd
			self.serial.write(str(cmd)+'\n')
			progressbar.update(i)
			self.monitor()
		progressbar.finish()

	def monitor(self):
		while True:
			if self.result_parser.feed(self.serial.read(1)):
				break


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
	try:
		cnc.send_queue()
	except KeyboardInterrupt:
		print('\nHALTING!')
		cnc.halt()
		raise

if __name__ == '__main__':
	main()
