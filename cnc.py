from serial import Serial, SerialException
from time import sleep

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
				self.callback('error', s[5:])
			elif s[:5] == b'ALARM':
				self.callback('alarm', s[6:])
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

	def __len__(self):
		return len(self.queue)

	def onprogress(self, i):
		pass

	def oncomplete(self):
		pass

	def onerror(self, msg):
		pass

	def onalarm(self, msg):
		pass

	def connect(self):
		if self.serial is not None:
			self.serial.close()
		self.serial = Serial(self.devpath, self.baudrate)
		if not self.await_connect():
			sleep(1)
			self.connect()

	def rescb(self, val, arg=None):
		if val == 'ok':
			return
		elif val == 'alarm':
			self.onalarm(arg)
		elif val == 'error':
			self.onerror(arg)
		else:
			self.onerror(arg)
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

	def hold(self):
		self.serial.write('!\n')
		self.monitor()

	def send_queue(self):
		for i, cmd in enumerate(self.queue):
			self.cur = cmd
			self.serial.write(str(cmd)+'\n')
			self.monitor()
			self.onprogress(i)

		self.oncomplete()

	def monitor(self):
		while True:
			try:
				s = self.serial.read(1)
			except SerialException:
				pass

			if self.result_parser.feed(s):
				break
