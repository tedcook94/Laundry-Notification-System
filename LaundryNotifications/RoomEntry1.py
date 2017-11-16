########## KEYPAD & TEXTING SETUP ##########

from time import sleep				# imports necessary APIs
from time import strftime
import RPi.GPIO as GPIO
from twilio.rest import Client

from PhoneNumbers import Room0			# imports phone numbers from central file
from PhoneNumbers import Room1
from PhoneNumbers import Room2
from PhoneNumbers import Room3
from PhoneNumbers import Room4
from PhoneNumbers import Room5
from PhoneNumbers import Room6
from PhoneNumbers import Room7
from PhoneNumbers import Room8

GPIO.setmode(GPIO.BOARD)			# sets GPIO mode
GPIO.setwarnings(False)

MATRIX = [ [1,2,3,'A'],				# sets key layout
	   [4,5,6,'B'],
	   [7,8,9,'C'],
	   ['*',0,'#','D'] ]

ROW = [19,21,23,29]				# pinout for RPi 2
COL = [18,22,24,26]

def confirmtext(roomNumber):						# sets confirmation text function for all numbers
	account_sid = "Insert Account ID here"
	auth_token = "Insert authentication token here"
	client = Client(account_sid, auth_token)

	client.api.account.messages.create(
		to=roomNumber,
		from_="+1**********",
		body="You successfully entered your room number into the washer. You will be notified when your clothes are done washing.")

def alerttext(roomNumber):						# sets notification text function for all numbers
	account_sid = "Insert Account ID here"
	auth_token = "Insert authentication token here"
	client = Client(account_sid, auth_token)

	client.api.account.messages.create(
		to=roomNumber,
		from_="+1**********",
		body="Your clothes in the washer are now done.")

########## ACCELEROMETER SETUP ##########

import smbus

revision = ([l[12:-1] for l in open('/proc/cpuinfo','r').readlines() if l[:8]=="Revision"]+['0000'])[0]		# select the correct i2c bus
bus = smbus.SMBus(1 if int(revision, 16) >= 4 else 0)

EARTH_GRAVITY_MS2   = 9.80665			#ADXL345 constants
SCALE_MULTIPLIER    = 0.004

DATA_FORMAT         = 0x31
BW_RATE             = 0x2C
POWER_CTL           = 0x2D

BW_RATE_1600HZ      = 0x0F
BW_RATE_800HZ       = 0x0E
BW_RATE_400HZ       = 0x0D
BW_RATE_200HZ       = 0x0C
BW_RATE_100HZ       = 0x0B
BW_RATE_50HZ        = 0x0A
BW_RATE_25HZ        = 0x09

RANGE_2G            = 0x00
RANGE_4G            = 0x01
RANGE_8G            = 0x02
RANGE_16G           = 0x03

MEASURE             = 0x08
AXES_DATA           = 0x32

class ADXL345:

    address = None

    def __init__(self, address = 0x53):        
        self.address = address
        self.setBandwidthRate(BW_RATE_100HZ)
        self.setRange(RANGE_2G)
        self.enableMeasurement()

    def enableMeasurement(self):
        bus.write_byte_data(self.address, POWER_CTL, MEASURE)

    def setBandwidthRate(self, rate_flag):
        bus.write_byte_data(self.address, BW_RATE, rate_flag)

    # set the measurement range for 10-bit readings
    def setRange(self, range_flag):
        value = bus.read_byte_data(self.address, DATA_FORMAT)

        value &= ~0x0F;
        value |= range_flag;  
        value |= 0x08;

        bus.write_byte_data(self.address, DATA_FORMAT, value)
    
    # returns the current reading from the sensor for each axis
    #
    # parameter gforce:
    #    False (default): result is returned in m/s^2
    #    True           : result is returned in gs
    def getAxes(self, gforce = False):
        bytes = bus.read_i2c_block_data(self.address, AXES_DATA, 6)
        
        x = bytes[0] | (bytes[1] << 8)
        if(x & (1 << 16 - 1)):
            x = x - (1<<16)

        y = bytes[2] | (bytes[3] << 8)
        if(y & (1 << 16 - 1)):
            y = y - (1<<16)

        z = bytes[4] | (bytes[5] << 8)
        if(z & (1 << 16 - 1)):
            z = z - (1<<16)

        x = x * SCALE_MULTIPLIER 
        y = y * SCALE_MULTIPLIER
        z = z * SCALE_MULTIPLIER

        if gforce == False:
            x = x * EARTH_GRAVITY_MS2
            y = y * EARTH_GRAVITY_MS2
            z = z * EARTH_GRAVITY_MS2

        x = round(x, 4)
        y = round(y, 4)
        z = round(z, 4)

        return {"x": x, "y": y, "z": z}
       
########## BEGIN AUTOCALIBRATE LOOP ##########		#automatically calibrates accelerometers on script start

adxl345 = ADXL345()

f = open("/home/pi/LaundryNotifications/WasherValues.py", "w")   

washerXvalues = []
washerYvalues = []
washerZvalues = []

print "********** WASHER **********"
print " "

for i in range(0,31):
	axes = adxl345.getAxes(True)
	washerXvalues.append(axes['x'])
	washerYvalues.append(axes['y'])
	washerZvalues.append(axes['z'])
	i += 1
	sleep(10)
	
print "X values for autocalibration: " + str(washerXvalues)
print "Y values for autocalibration: " + str(washerYvalues)
print "Z values for autocalibration: " + str(washerZvalues)
print " "

xmin = min(washerXvalues)
xmax = max(washerXvalues)
ymin = min(washerYvalues)
ymax = max(washerYvalues)
zmin = min(washerZvalues)
zmax = max(washerZvalues)

print "X calibrated for values between " + str(xmin) + " and " + str(xmax) + "."
print "Y calibrated for values between " + str(ymin) + " and " + str(ymax) + "."
print "Z calibrated for values between " + str(zmin) + " and " + str(zmax) + "."
print " "

f.write("xmin = " + str(xmin) + "\n")
f.write("xmax = " + str(xmax) + "\n")
f.write("ymin = " + str(ymin) + "\n")
f.write("ymax = " + str(ymax) + "\n")
f.write("zmin = " + str(zmin) + "\n")
f.write("zmax = " + str(zmax))

f.close()

########## BEGIN CONFIRMENTRY LOOP ##########		# confirms input from main loop


def confirmentry():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)

	MATRIX = [ [1,2,3,'A'],
	   	[4,5,6,'B'],
	   	[7,8,9,'C'],
	   	['*',0,'#','D'] ]

	ROW = [19,21,23,29]
	COL = [18,22,24,26]

	for j in range(4):
		GPIO.setup(COL[j], GPIO.OUT)
		GPIO.output(COL[j], 1)

	for i in range(4):
		GPIO.setup(ROW[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

	try:
		while(True):
			for j in range(4):
				GPIO.output(COL[j],0)

				for i in range(4):
					if GPIO.input(ROW[i]) == 0:
						if MATRIX[i][j] == '#':
							return 1

						elif MATRIX[i][j] == '*':
							return 0
						else:
							return 2
			
				GPIO.output(COL[j],1)
				
	except KeyboardInterrupt:
		GPIO.cleanup()


########## BEGIN ACCELEROMETER LOOP ##########

def accelerometer():
	adxl345 = ADXL345()
	
	from WasherValues import xmin
	from WasherValues import xmax
	from WasherValues import ymin
	from WasherValues import ymax
	from WasherValues import zmin
	from WasherValues import zmax

	sleep(300)
	
	try:
		while(True):
			sleep(300)
			axes = adxl345.getAxes(True)
			if xmin <= axes['x'] <= xmax  and  ymin <= axes['y'] <= ymax  and  zmin <= axes['z'] <= zmax:
				return 1

	except KeyboardInterrupt:
		GPIO.cleanup()
		exit()

########## BEGIN MAIN LOOP ##########

for j in range(4):				# sets all column pins as high outputs
	GPIO.setup(COL[j], GPIO.OUT)
	GPIO.output(COL[j], 1)

for i in range(4):							# sets all row pins as inputs
	GPIO.setup(ROW[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

try:
	while(True):
		for j in range(4):
			GPIO.output(COL[j],0)			# sets one column pin at a time as a low output

			for i in range(4):
				if GPIO.input(ROW[i]) == 0:		# polls for a low output on any row
		# Room 0	
					if MATRIX[i][j] == 0:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 0. (" + strftime("%H:%M") + ")"
							confirmtext(Room0)
							if accelerometer() == 1:
								print "Washer notification sent to room 0. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room0)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 1
					elif MATRIX[i][j] == 1:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 1. (" + strftime("%H:%M") + ")"
							confirmtext(Room1)
							if accelerometer() == 1:
								print "Washer notification sent to room 1. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room1)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 2	
					elif MATRIX[i][j] == 2:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 2. (" + strftime("%H:%M") + ")"
							confirmtext(Room2)
							if accelerometer() == 1:
								print "Washer notification sent to room 2. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room2)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 3	
					elif MATRIX[i][j] == 3:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 3. (" + strftime("%H:%M") + ")"
							confirmtext(Room3)
							if accelerometer() == 1:
								print "Washer notification sent to room 3. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room3)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 4	
					elif MATRIX[i][j] == 4:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 4. (" + strftime("%H:%M") + ")"
							confirmtext(Room4)
							if accelerometer() == 1:
								print "Washer notification sent to room 4. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room4)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 5	
					elif MATRIX[i][j] == 5:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 5. (" + strftime("%H:%M") + ")"
							confirmtext(Room5)
							if accelerometer() == 1:
								print "Washer notification sent to room 5. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room5)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 6	
					elif MATRIX[i][j] == 6:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 6. (" + strftime("%H:%M") + ")"
							confirmtext(Room6)
							if accelerometer() == 1:
								print "Washer notification sent to room 6. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room6)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 7	
					elif MATRIX[i][j] == 7:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 7. (" + strftime("%H:%M") + ")"
							confirmtext(Room7)
							if accelerometer() == 1:
								print "Washer notification sent to room 7. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room7)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"
		# Room 8	
					elif MATRIX[i][j] == 8:
						print str(MATRIX[i][j]) + " (" + strftime("%H:%M") + ")"
						sleep(0.5)
						if confirmentry() == 1:
							print "Confirmation message sent to room 8. (" + strftime("%H:%M") + ")"
							confirmtext(Room8)
							if accelerometer() == 1:
								print "Washer notification sent to room 8. (" + strftime("%H:%M") + ") [" + str(axes['x']) + ", " + str(axes['y']) + ", " + str(axes['z']) + "]"
								alerttext(Room8)
						elif confirmentry() == 0:
							print "Entry cancelled. (" + strftime("%H:%M") + ")"
						else:
							print "Improper entry. (" + strftime("%H:%M") + ")"

					else:
						print "That input is not a recognized room number. (" + strftime("%H:%M") + ")"
					
					while(GPIO.input(ROW[i]) == 0):			# stops other input while button pressed
						pass
					sleep(0.5)					# adds temporary pause between inputs

			GPIO.output(COL[j],1)						# raises each column pin back to high after polling it

except KeyboardInterrupt:					# allows for Ctrl-C to end the script
	GPIO.cleanup()


