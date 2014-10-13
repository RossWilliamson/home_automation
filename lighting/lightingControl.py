import RPi.GPIO as GPIO
import ephem
import logging

logging.basicConfig()

#!!! Insert CLASS for each zone


class lightingControl():
    def __init__(self):
        self.logger = logging.getLogger('LightingControl')
        self.logger.setLevel(logging.DEBUG)

        self.LIGHTS_ONE = 7
        self.LIGHTS_TWO = 8
        self.LIGHTS_THREE = 9
        self.LIGHTS_FOUR = 11

        #Relays sink current and we'll keep them
        #+ve when out to reduce current draw
        self.OFF = True
        self.ON = False

        self.setup_pins()

        #setup location for the meadows
        self.meadows = ephem.Observer()
        self.meadows.lat = str(34.213869)
        self.meadows.lon = str(-118.161517)
        self.meadows.elev = 480 # height in meters
        self.meadows.horizon = '-6' #-6=civil twilight


    def setup_pins(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(self.LIGHTS_ONE, GPIO.OUT)
        GPIO.setup(self.LIGHTS_TWO, GPIO.OUT)
        GPIO.setup(self.LIGHTS_THREE, GPIO.OUT)
        GPIO.setup(self.LIGHTS_FOUR, GPIO.OUT)
        
        #Make sure they are all off
        #note that
        GPIO.output(self.LIGHTS_ONE, self.OFF)
        GPIO.output(self.LIGHTS_TWO, self.OFF)
        GPIO.output(self.LIGHTS_THREE, self.OFF)
        GPIO.output(self.LIGHTS_FOUR, self.OFF)

    def get_sunrise(self):
        print ephem.localtime(ephem.now())
        xx = self.meadows.previous_rising(ephem.Sun(), use_center=True)
        print ephem.localtime(xx)

    def get_sunset(self):
        xx = self.meadows.next_setting(ephem.Sun(), use_center=True)
        print ephem.localtime(xx)
        
        
