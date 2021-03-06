from idautils import *
from idc import *
import re

class Register():
	TYPE8 = 0
	TYPE16 = 1
	TYPE32 = 2
	TYPE64 = 3
	TYPEA = 4

	GREG64 = ['eax','ebx','ecx','edx','esi','edi']
	AREG64 = GREG64 + ['ebp','esp']
	
	GREG32 = ['eax','ebx','ecx','edx','esi','edi']
	AREG32 = GREG32 + ['ebp','esp']

	GREG16 = ['ax','bx','cx','dx','si','di']
	AREG16 = GREG16 + ['bp','sp']

	GREG8 = ['al','bl','cl' , 'ah', 'bh', 'ch']
	AREG8 = GREG8
	"""A simple attempt to model a car."""
	def __init__(self, str):
		"""Initialize car attributes."""
		self.type = 0
		self.name = ""
		self.replacement = ""
		self.group = []
		m = re.match('(.)REG([0-9](?:[0-9])?)(.*)',str)
		if m != None:
			if m.group(1) == 'A':
				self.type = self.type | TYPEA
			if m.group(2) == "8":
				self.type = self.type | TYPE8
				if self.type & TYPEA:
					self.group = AREG8
				else:
					self.group = GREG8
			if m.group(2) == "16":
				self.type = self.type | TYPE16
				if self.type & TYPEA:
					self.group = AREG16
				else:
					self.group = GREG16
			if m.group(2) == "32":
				self.type = self.type | TYPE32
				if self.type & TYPEA:
					self.group = AREG32
				else:
					self.group = GREG32
			if m.group(2) == "64":
				self.type = self.type | TYPE64
				if self.type & TYPEA:
					self.group = AREG64
				else:
					self.group = GREG64
			if m.group(3) != None:
				self.name = m.group(3)
	
	def toString(self):
		if self.replacement == "":
			return '(' + '|'.join(self.group) + ')'
		else:
			return '(' + self.replacement + ')'
	
	
def findCodeSeqInFunction(ea):
	func_start_ea = get_func_attr(ea, FUNCATTR_START)
	func_end_ea = get_func_attr(ea, FUNCATTR_END)
	
	instructions_set = [x for x in Heads(func_start_ea,func_end_ea)]
	instructions_count = len(instructions_set)
	
	code_seq = str_find.split(";")
	
	result = []
	for i, head in enumerate(instructions_set):
		if i < instructions_count-len(code_seq):
			# clearing known_regs
			known_regs.clear()
			found = True;
			for j, code in enumerate(code_seq):
				if codeMatches(instructions_set[i+j], code) == False:
					found = False
					break
			if found:
				result.append(head)
	return result

def codeMatches(ea, code):
	dis_asm = idc.generate_disasm_line(ea,GENDSM_FORCE_CODE)
	regex_code,rep = replaceRegisters(code)
	regex_code = re.sub('\s+', '\\s*', regex_code)

	m = re.match(regex_code,dis_asm)
	if m != None:
		# we need to double check if two registers with same names are replaced with same registers
		if len(rep) == 2:
			if rep[0] == rep[1] and m.group(1) != m.group(2):
				return False
		if len(rep) > 2:
			for i in range (0,len(rep)-2):
				for j in range (i,len(rep)-1):
					if rep[i] == rep[j] and m.group(i+1) != m.group(j+1):
						return False
		
		# every thing is ok, let's update.
		for i,r in rep.items():
			known_regs[r].replacement = m.group(i+1)
		return True
	return False

def replaceRegisters(code):
	result = code
	matchs = re.finditer('%([^,]+?)%', code)
	replacements = {}
	for i, m in enumerate(matchs):
		reg = Register(m.group(1))
		kr = known_regs.get(reg.name)
		if kr != None:
			result = result.replace(m.group(0),kr.toString(),1)
			replacements[i] = reg.name
		else:
			if reg.name != "":
				known_regs[reg.name]=reg
				replacements[i] = reg.name
			result = result.replace(m.group(0),reg.toString(),1)
	return result,replacements

str_find = AskStr('lea %GREG32X%,.*%AREG32Y%.*',"enter a regex")

known_regs = {}
for addr in findCodeSeqInFunction(here()):
	print "0x%X " % addr