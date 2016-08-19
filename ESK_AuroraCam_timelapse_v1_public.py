# Code to run a time-lapse Aurora camera at Eskdalemuir obsveratory
# The code uses picamera module to control the camera in the Raspberry Pi
# The code runs in the background and is triggered by a high Kp index 
# and it being dark enough for full 6 second exposure

# Author: Ciaran Beggan
# Date: 11-Jan-2016
# v1: initial code to check HSD and is_dark
#	code also catches an error if unable to access network or Kp file
#   	set to run on re-boot if there is a power failure via /etc/rc.local
# public: 19-Aug-2016
#       : a version that uses Kp rather than HSD index. Kp goes from 0-9. Values
#	  above 5 are active or stormy. Values over 8 are very stormy.

import time 
import picamera
import datetime as dt
from datetime import timedelta
from fractions import Fraction
import logging


def is_dark():
	import datetime as dt
	import ephem as ep
	import math

	my_location = ep.Observer()
	lat, lon = [55.3, -3]	# Approximate location of Eskdalemuir camera
	my_location.lat = lat*math.pi/180	# Convert to radians
	my_location.lon = lon*math.pi/180

	# Find today's sunrise and sunset times
	today_date = dt.datetime.utcnow().strftime("%Y/%m/%d 00:00:00")
	
	my_location.date = today_date
	today_sunrise = my_location.next_rising(ep.Sun())
	today_sunset = my_location.next_setting(ep.Sun())
	
	# Now convert the time at this moment to the ephem date format (i.e. number of days since 1889 A.D.  [why 1889? I don't know])
	now_date = dt.datetime.utcnow().strftime("%Y/%m/%d %H:%M:00")
	my_location.date = now_date
	
	# Check if it's day or night
	if  (my_location.date > today_sunrise) and  (my_location.date < today_sunset):
	    logging.info("is day")
	    is_dark = False
	else:
	    logging.info("is dark")
	    is_dark = True

        return is_dark

def Kp_high():
        import urllib2

	# Code to look at the BGS three hourly Kp prediction to see if
	# the variation is high (over Kp > 5)
	# There are other indexes or predictions that can be used. This is just an example.


	theurl = 'http://www.geomag.bgs.ac.uk/data_service/space_weather/current/3hrKuk.json'

	# This is a json file, so there are better ways to read it in and parse. This
	# is a really simple and crude way to check if the period is active.
	try:
		pagehandle = urllib2.urlopen(theurl)

		#Grab the data
		unparsed_values = pagehandle.read()
		lines = unparsed_values.split('\n')
		# As we've split at the \n character the very last line is blank, so choose the
		# second to last line. These files are standard, so choose the last value in the line
		kp_data = float(lines[-3][57:60])
	except:
		logging.info("Failed to reach website ... waiting")	
		kp_data = 0   # Set expected values to zero

	# if the Kp value is high, start snapping images
	if (kp_data > 5 ) 
	    logging.info("Kp High")
	    Kp_high = True
	else:
	    #logging.info( "Kp low")
	    Kp_high = False

	return Kp_high
	
def wait():
	  # Calculate the delay to the start of the next five minute block 
	  next_5min = (dt.datetime.now() + timedelta(minutes=5)) .replace(second=0, microsecond=0)
	  delay = (next_5min - dt.datetime.now()).seconds
	  #logging.info(delay)
	  time.sleep(delay)


 
# Set up a logging file
logging.basicConfig(filename='ESK_AuroraCam.log',level=logging.INFO, format='%(asctime)s %(message)s',  datefmt='%Y-%d-%m %H:%M:%S')
logging.info('Logging file beginning: ' +  dt.datetime.utcnow().strftime("%Y/%m/%d %H:%M:00"))
    

while 1:
	# If it is dark and the Kp is high start snapping images
        if is_dark() and Kp_high():
		# Start the camera each time through the if statement
		with picamera.PiCamera() as camera:
			camera.resolution = (1280, 720)
			# Set a framerate of 1/6fps, then set shutter
			# speed to 6s and ISO to 800
			camera.framerate = Fraction(1, 6)
			camera.shutter_speed = 6000000
			camera.exposure_mode = 'off'
			camera.iso = 800

			# Give the camera a good long time to measure AWB
			# (or you may wish to use fixed AWB instead)
			time.sleep(10)
			
			# Prepare the annoation 
			camera.annotate_foreground = picamera.Color('yellow')
		   	camera.annotate_text_size = 12
			camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			filename = 'ESKAuroraCam' + dt.datetime.now().strftime('%Y-%m-%-d%-H-%M-%S') + '.jpg'
			camera.capture(filename)    # Take the photo

			logging.info('Captured %s' % filename)
			camera.close()
			wait()
	else:
		wait()
        
