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
			allowed = ['.', '-', '+']
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
