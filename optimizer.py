from gcode import GStatement, GCode
class Optimizer(object):
	def __init__(self, *args):
		self.optimizers = args

	def optimize(self, statements):
		for optimizer in self.optimizers:
			statements = optimizer.optimize(statements)
		return statements

class FileMarkRemover(object):
	'Removes file markers'
	def optimize(self, statements):
		for statement in statements:
			codes = []
			for code in statement:
				if code.type != 'filemark':
					codes.append(code)

			statement.codes = codes
		return statements

class FeedratePatcher(object):
	'Ensures that F-codes are alone to help grbl'
	def optimize(self, statements):
		cur_statement = GStatement()
		nstatements = [cur_statement]
                last_val = None
                for statement in statements:
			for code in statement:
				if code.address == 'F':
				        if code.command != last_val:
					    s = GStatement(code)
					    nstatements.insert(-1, s)
					    last_val = code.command
				else:
					cur_statement.append(code)

			cur_statement = GStatement()
			nstatements.append(cur_statement)
		return nstatements

class MPatcher(object):
	'Ensures that there is only one M-code per statement'
	def optimize(self, statements):
		cur_statement = GStatement()
		nstatements = [cur_statement]
		for statement in statements:
			for code in statement:
				if code.address == 'M':
					cur_statement = GStatement()
					nstatements.append(cur_statement)
				cur_statement.append(code)

			cur_statement = GStatement()
			nstatements.append(cur_statement)
		return nstatements

class CodeSaver(object):
	'Ensures that no unnecessary G-codes are issued'
	move_desc = ('X', 'Y', 'Z', 'A', 'B', 'C', 'I', 'J', 'K', 'R', 'F', 'S')
	def optimize(self, statements):
		cur_statement = GStatement()
		nstatements = [cur_statement]
		cur_code = None
		for statement in statements:
			for code in statement:
				if code.address in self.move_desc:
					cur_statement.append(code)
				elif code == cur_code:
					pass
				elif code.address == 'G' and code.command >= 0 and code.command <= 3:
					cur_code = code
					cur_statement.append(code)
				else:
					cur_code = None
					cur_statement.append(code)

			cur_statement = GStatement()
			nstatements.append(cur_statement)
		return nstatements

class GrblCleaner(object):
	'Removes codes that are not supported by grbl'
	supported_g = (0, 1, 2, 3, 4, 10, 17, 18, 19, 20, 21, 28, 28.1, 30, 30.1, 53, 54, 55, 56, 57, 58, 59, 80, 90, 91, 92, 92.1, 93, 94)
	supported_m = (0, 2, 3, 4, 5, 8, 9, 30)
	move_desc = ('X', 'Y', 'Z', 'A', 'B', 'C', 'I', 'J', 'K', 'R', 'F', 'S')
	def optimize(self, statements):
		for statement in statements:
			codes = []
			for code in statement:
				if code.address == 'M':
					if code.command in self.supported_m:
						codes.append(code)
				elif code.address == 'G':
					if code.command in self.supported_g:
						codes.append(code)
				elif code.address in self.move_desc:
					codes.append(code)
			statement.codes = codes

		return statements

class CommentRemover(object):
	'Removes comments'
	def optimize(self, statements):
		for statement in statements:
			codes = []
			for code in statement:
				if code.type != 'comment':
					codes.append(code)

			statement.codes = codes
		return statements

class EmptyStatementRemover(object):
	'Removes empty statements'
	def optimize(self, statements):
		nstatements = []
		for statement in statements:
			if len(statement.codes):
				nstatements.append(statement)
		return nstatements
