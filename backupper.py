# TODO
# - Check free space 
# - Error Codes

import commands, subprocess, time, traceback
import RPi.GPIO as GPIO

OUT1_PIN = 18
OUT2_PIN = 12
OUT3_PIN = 13

def getTime():
	return str(list(time.localtime())[0]) + '_' + str(list(time.localtime())[1]) + '_' + str(list(time.localtime())[2]) + '___' + str(list(time.localtime())[3]) + '_' + str(list(time.localtime())[4]) + '_' + str(list(time.localtime())[5])

def writeToLog(text):
	print text
	with open('/home/pi/Documents/CopyToSafety/log', 'a') as f:
		f.write(getTime() + '	' + text + '\n')
		f.close()

def executeCommand(command):
	writeToLog('executing: ' + command)
	res = commands.getstatusoutput(command)
	if res[0] == 0 or res[0] == 256:
		return res[1]
	else:
		writeToLog(res[1])
		raise Exception("Error when executing command")

def copyFromTo(device1, device2):
	writeToLog('Attempting to copy..')

	writeToLog('device1 contains: ' + executeCommand('ls ' + device1.path ))
	numOfFiles_device1 = int(executeCommand('find '  + device1.path  +  ' -type f | wc -l'))
	writeToLog('device1 numOfFiles: ' + str(numOfFiles_device1))

	writeToLog('device2 contains: ' + executeCommand('ls '  + device2.path ))
	#numOfFiles_device2 = int(executeCommand('find '  + device2.path  + ' -type f | wc -l'))
	#writeToLog('device2 numOfFiles: ' + str(numOfFiles_device2))

	#if(device1.totalSpace >= device2.totalSpace):
	#	blinkError(OUT1_PIN)
	#	writeToLog('device1 has more capacity than device2. Exiting.')
	#	exit()

	writeToLog('Getting file list from source device')
	files = executeCommand('cd '  + device1.path  + ' ; find . -type f').split('\n')

	writeToLog('Creating directory on target device')
	dirName = getTime()
	executeCommand('cd '  + device2.path  + ' ; mkdir ' + dirName)
	device2.curPath = device2.path + '/' + dirName
	writeToLog('Saving files to ' + device2.curPath + ' on target device')

	for f in files:
		GPIO.output(OUT1_PIN,1)
		process = subprocess.Popen('cd '  + device1.path  + ' ;  cp --parents '  + f  + ' '  + device2.curPath , shell=True, stdout=subprocess.PIPE)
		process.wait()
		GPIO.output(OUT1_PIN,0)
		time.sleep(0.2)

	GPIO.output(OUT2_PIN,1)
	writeToLog("Copying succsesful")
	writeToLog("Exiting. Goodbye")
	exit()

def blinkOnce(pin):
	GPIO.output(pin, 1)
	time.sleep(1)
	GPIO.output(pin, 0)

def blinkTwice(pin):
	blinkOnce(pin)
	time.sleep(0.5)
	blinkOnce(pin)

def blinkError(pin):
	for i in range(10):
		GPIO.output(pin, 1)
		time.sleep(0.2)
		GPIO.output(pin, 0)
		time.sleep(0.2)

class device:
	
	def __init__(self, line):
		self.line = line
		self.list = self.getList()
		self.path = self.getPath()
		self.curPath = None
		self.freeSpace = self.getFreeSpace()
		self.usedSpace = self.getUsedSpace()
		self.totalSpace = self.freeSpace + self.usedSpace
	
	def getList(self): 
		list = self.line.split(' ')
		list = filter(lambda a: a != '', list)
		return list

	def getPath(self):
		return self.line[self.line.index('%')+2:].replace(" ","\\ ")

	def getUsedSpace(self):
		print(self.list[2])
		return int(self.list[2])

	def getFreeSpace(self):
		return int(self.list[3])

	def __str__(self):
		return ('\nList: ' + str(self.list) + '\n' +
			'Path: ' + self.path + '\n' +
			'Used space: ' + str(self.usedSpace) + '\n' +
			'Free space: ' + str(self.freeSpace) + '\n')

prev_outputs = []
device1 = None
device2 = None
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(OUT1_PIN, GPIO.OUT)
GPIO.setup(OUT2_PIN, GPIO.OUT)
GPIO.setup(OUT3_PIN, GPIO.OUT)
GPIO.output(OUT1_PIN, 0)
GPIO.output(OUT2_PIN, 0)
GPIO.output(OUT3_PIN, 0)

try:
	writeToLog("################## STARTING UP ####################")

	while(1):	
		if device1 == None:
			new_output = executeCommand('df --sync | grep media/pi')
		else:
			new_output = executeCommand('df --sync | grep media/pi | grep -v '  + device1.path )

		if prev_outputs == []:
			prev_outputs.append(new_output)
		
		if new_output not in prev_outputs and new_output != '':
			writeToLog('new device connected: ' + new_output)
			if device1 == None:
				device1 = device(new_output)
				writeToLog('Device 1: ' + str(device1))
				blinkOnce(OUT1_PIN)
			elif device2 == None:
				device2 = device(new_output)
				writeToLog('Device 2: ' + str(device2))
				blinkTwice(OUT1_PIN)
				copyFromTo(device1, device2)

		prev_outputs.append(new_output)
		time.sleep(5)

except Exception, err:
	writeToLog(traceback.format_exc())
	exit()
