import sys
from io import StringIO
import re
import fileinput
import os

base_path = ''
cur_dir = os.getcwd().split('\\')[-1]
if cur_dir == 'crazyflie-firmware':
	base_path = '../'
elif cur_dir == 'testing':
	base_path = './'
elif cur_dir == 'crazyflie-swarm-python':
	base_path = '../'
else:
	base_path = './'

# setup the environment
backup = sys.stdout

bs_position_path = base_path + "crazyflie-firmware/tools/lighthouse/get_bs_position.py"

# ####
sys.stdout = StringIO()     # capture output
exec(open(bs_position_path).read())
out = sys.stdout.getvalue() # release output
# ####

sys.stdout.close()  # close the stream 
sys.stdout = backup # restore original stdout

print('Positions:')
print(out)

regex2line = r'\{.*\, \}\, \}\}\,.*\s.*\, \}\, \}\}\,'
regex= r'\{.*\, \}\, \}\}\,'

pos_new = re.findall(regex2line, out)

lighthouse_path = base_path + 'crazyflie-firmware/src/deck/drivers/src/lighthouse.c'

print('Writing position from')
print(bs_position_path)
print('to')
print(lighthouse_path)

filedata = ""
with open(lighthouse_path, 'r') as file:
	filedata = file.read()

filedata = re.sub(regex2line, pos_new[0], filedata)

with open(lighthouse_path, 'w') as file:
	file.write(filedata)
