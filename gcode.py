class GManager(object):
	def __init__(self, *args):
		self.args = args

	def iter_codes(self):
		for statement in self.args:
			for code in statement:
				yield code
		return

	def limit_feedrate(self, max_feed):
		for code in self.iter_codes():
			if code.type != 'code':
				continue
			if code.address == 'F':
				rate = code.command
				if rate > max_feed:
					code.command = max_feed

	def detect_feedrates(self):
		rates = set()
		min_f, max_f = None, None
		for code in self.iter_codes():
			if code.type != 'code':
				continue
			if code.address == 'F':
				rate = code.command
				rates.add(rate)
		rates = list(rates)
		rates.sort()
		return rates

	def detect_metric(self):
		metric = None
		movement = False
		for code in self.iter_codes():
			if code.type != 'code':
				continue
			if code.address == 'G':
				if code.command in (20, 21) and movement:
					raise RuntimeError('Unable to detect unit: Change of units after first move (%s)' % str(code))

				if code.command == 20:
					metric = False
				elif code.command == 21:
					metric = True
			elif code.address in ('X', 'Y', 'Z', 'A', 'B', 'C', 'I', 'J', 'K', 'R'):
				movement = True

		return metric

	def detect_workarea(self):
		absolute = False
		movement = False
		axes = ('X', 'Y', 'Z', 'A', 'B', 'C')
		max_axes, min_axes = {}, {}
		for i in axes:
			max_axes[i] = 0
			min_axes[i] = 0
		for code in self.iter_codes():
			if code.type != 'code':
				continue
			if code.address == 'G':
				if code.command == 90:
					absolute = True
				elif code.command == 91:
					absolute = False
				elif code.command in (20, 21) and movement:
					raise RuntimeError('Unable to detect workarea: Change of units after first move (%s)' % str(code))
			if code.address in axes:
				if not absolute:
					raise RuntimeError('Unable to detect workarea: Relative movements detected (%s)' % str(code))

				movement = True
				if code.command < min_axes[code.address]:
					min_axes[code.address] = code.command
				elif code.command > max_axes[code.address]:
					max_axes[code.address] = code.command


		return {axis:(min_axes[axis], max_axes[axis]) for axis in axes if min_axes[axis] != 0 or max_axes[axis] != 0}


class GStatement(object):
	type = 'statement'
	def __init__(self, *args):
		self.codes = list(args)

	def append(self, code):
		self.codes.append(code)

	def stringify(self, max_len, spaces=False):
		cmd = []
		m = 0
		for i in self.codes:
			s = str(i)
			cmd.append(s)
			m = max(len(s), m)

		joiner = ' ' if spaces else ''

		while len(joiner.join(cmd)) >= max_len:
			m -= 1
			for i in range(len(cmd)):
				cmd[i] = cmd[i][:m]

		return joiner.join(cmd)

	def __iter__(self):
		return self.codes.__iter__()

	def __str__(self):
		return self.stringify(70)


class GCode(object):
	type = 'code'
	def __init__(self, address, command, precision=4):
		self.address = address
		self.command = command
		self.precision = precision

	def __eq__(self, other):
		try:
			return self.type == other.type and self.address == other.address and self.command == other.command
		except:
			return False

	def __str__(self):
		if type(self.command) == float:
			return ("{}{:.%df}" % self.precision).format(self.address, self.command)
		return "%s%d" % (self.address, self.command)


class GComment(object):
	type = 'comment'
	def __init__(self, content):
		self.content = content

	def __eq__(self, other):
		try:
			return self.type == other.type and self.content == other.content
		except:
			return False

	def __str__(self):
		return '(%s)' % self.content


class GFileMarker(object):
	type = 'filemark'
	def __str__(self):
		return '%'

	def __eq__(self, other):
		try:
			return self.type == other.type
		except:
			return False


class GCodeParserError(RuntimeError):
	pass


class GCodeParser(object):
	def __init__(self):
		self.parser = None
		self.statements = None
		self.statement = None
		self.buffer = None

	def detected(self, code=None, end=False):
		if end or self.statement is None:
			self.statement = GStatement()
			self.statements.append(self.statement)

		if code is not None:
			self.statement.append(code)

	def change_parser(self, parser, retry=False):
		self.parser = parser
		if retry:
			self.parser(retry)

	def comment_parser(self, c):
		if c == '(':
			self.buffer = ''
		elif c == ')':
			self.detected(GComment(self.buffer))
			self.buffer = None
			self.change_parser(self.address_parser)
		else:
			self.buffer += c

	def argument_parser(self, c):
		if c in ('.', '-', '+') or c.isdigit():
			self.buffer[1] = self.buffer[1] + c
		else:
			address = self.buffer[0]
			try:
				arg = int(self.buffer[1])
			except:
				arg = float(self.buffer[1])
			self.detected(GCode(address, arg))
			self.buffer = None
			self.change_parser(self.address_parser, c)

	def address_parser(self, c):
		if c == '%':
			self.detected(GFileMarker())
		elif c == '(':
			self.change_parser(self.comment_parser, c)
		elif c == '\r' or c == '\n':
			self.detected(end=True)
		elif c == ' ':
			pass
		else:
			if not c.isalpha():
				raise GCodeParserError('Unknown symbol: [%s]' % ord(c))
			self.buffer = [c.upper(), '']
			self.change_parser(self.argument_parser)

	def parse(self, string):
		# Resetting...
		self.parser = self.address_parser
		self.statements = []
		self.statement = None
		self.buffer = None

		# Ready!
		for c in string:
			try:
				self.parser(c)
			except GCodeParserError:
				raise
			except:
				raise GCodeParserError('Unknown symbol: [%s]' % ord(c))

		return self.statements
