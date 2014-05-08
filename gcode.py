class GStatement(object):
	def __init__(self, *args):
		self.args = args

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
	def __init__(self, command=None):
		self.command = command

	def __str__(self):
		return self.command


class GCodeParser(object):
	def __init__(self):
		pass

	def parse_command(self, cmd):
		components = cmd.split(' ')
		args = []
		for i, component in enumerate(components):
			if not component[0].isalpha():
				continue
			allowed = ['.', '-', '+']
			for c in component[1:]:
				if c in allowed:
					allowed.remove(c)
				elif not c.isdigit():
					break
			else:
				args.append(GCode(component.upper()))

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
			else:
				print(' -- Ignoring GCode line: %s' % line)
		return codes
