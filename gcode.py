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
			if code.address == 'F':
				rate = code.command
				if rate > max_feed:
					code.command = max_feed

	def detect_feedrates(self):
		rates = set()
		min_f, max_f = None, None
		for code in self.iter_codes():
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
			if code.address == 'G':
				if code.command in (20, 21) and movement:
					raise RuntimeError('Unable to detect unit: Change of units after first move (%s)' % str(code))

				if code.command == 20:
					metric = False
				elif code.command == 21:
					metric = True
			elif code.address in ('X', 'Y', 'Z', 'A', 'B', 'C'):
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
	def __init__(self, *args):
		self.args = args

	def __iter__(self):
		return self.args.__iter__()

	def __str__(self):
		cmd = []
		m = 0
		for i in self.args:
			cmd.append(str(i))
			m = max(len(str(i)), m)

		while len(' '.join(cmd)) >= 70:
			m -= 1
			for i in range(len(cmd)):
				cmd[i] = cmd[i][:m]

		return ' '.join(cmd)


class GCode(object):
	def __init__(self, address, command):
		self.address = address
		self.command = command

	def __str__(self):
		return self.address + str(self.command)


class GCodeParser(object):
	def __init__(self):
		pass

	def comment_stripper(self, line):
		newcmd = []
		comment = False
		for i in line:
			if i == '(':
				comment = True
			elif i == ')':
				comment = False
			elif not comment:
				newcmd.append(i)
		return ''.join(newcmd)

	def parse_command(self, cmd):
		cmd = self.comment_stripper(cmd)
		components = cmd.split(' ')
		args = []
		for i, component in enumerate(components):
			if not len(component):
				continue

			if not component[0].isalpha():
				print('WARNING: Ignoring code: %s' % component)
				continue

			address = component[0].upper()

			command = component[1:]

			if '.' in command:
				command = float(command)
			else:
				try:
					command = int(command)
				except:
					print(command)

			args.append(GCode(address, command))

		return args

	def parse(self, string):
		lines = string.replace('\r', '').split('\n')

		codes = []
		for line in lines:
			if len(line) == 0:
				continue

			res = self.parse_command(line)
			if len(res):
				codes.append(GStatement(*res))
		return codes
