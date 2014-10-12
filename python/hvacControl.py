import threading
from time import sleep
import RPi.GPIO as GPIO
import logging

logging.basicConfig()

class hvacControl(threading.Thread):
    def __init__(self, temperature,
                 update_rate = 10,
                 hysterisis = 0.5):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('HVACControl')
        self.logger.setLevel(logging.DEBUG)
        
        self.temps = temperature
        self.update_rate = update_rate
        self.hysterisis = hysterisis
        #Set stupid setpoints 
        self.heater_setpoint = -1e9
        self.cooling_setpoint = 1e9

        self.heat_max = 27
        self.cool_min = 10

        self.ATTIC_FAN = 22
        self.VENT_FAN = 18
        self.AC_UNIT = 23
        self.HEATER_UNIT = 24       

        self.stop_event = threading.Event()
        self.mutex = threading.Lock()
        
        self.setup_pins()
        self.start_safety_timer()

    def __del__(self):
        self.logger.info("Deleting Myself")
        self.stop_event.set()
    
    def setup_pins(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.ATTIC_FAN, GPIO.OUT)
        GPIO.setup(self.VENT_FAN, GPIO.OUT)
        GPIO.setup(self.AC_UNIT, GPIO.OUT)
        GPIO.setup(self.HEATER_UNIT, GPIO.OUT)  

        #And make sure they are all false
        GPIO.output(self.ATTIC_FAN, True) #wired up wrong
        GPIO.output(self.VENT_FAN, False)
        GPIO.output(self.AC_UNIT, False)
        GPIO.output(self.HEATER_UNIT, False)
    
    def start_safety_timer(self):
        self.logger.debug("Starting safety timer")
        self.s_thread = threading.Thread(target=self.safety_timer)
        self.s_thread.deamon = True
        self.s_thread.start()
    
    def safety_timer(self):
        # Hard coded timer for compressor safety
        # No varibles here for time do not change
        self.ok_to_start = False
        for i in xrange(5):
            t_time = 5-i
            str = "Time remaining to start %i" % t_time
            self.logger.debug(str)
            sleep(60) 
        self.ok_to_start = True
        self.logger.debug("OK TO START")

    def start_fan_timer(self):
        self.logger.debug("Starting Fan timer")
        self.f_thread = threading.Thread(target=self.fan_timer)
        self.f_thread.deamon = True
        self.f_thread.start()

    def fan_timer(self):
        #Time to wait before turning fan off
        #Hard coded to 90 seconds but not a safety isse
        sleep(60):
        GPIO.output(self.VENT_FAN, False)

    def set_heater_setpoint(self, temp):
        if temp > self.heat_max:
            self.logger.warn("Setting to max temp")
        self.heater_setpoint = temp
        self.heater_on = self.heater_setpoint
        self.heater_off = self.heater_setpoint + self.hysterisis

    def set_cooling_setpoint(self, temp):
        if temp < self.cool_min:
            self.logger.warn("Setting to min temp")
        self.cooling_setpoint = temp
        self.cooling_on = self.cooling_setpoint
        self.cooling_off = self.cooling_setpoing - self.hysterisis

    def set_state(self, state):
        if state == "Cool":
            self.state = state
        elif state == "Heat":
            self.state = state
        elif state == "Fan":
            self.state = state
        else:
            state = "Off"

    def AC_Switch(self, state):
        if state is True:
            GPIO.output(self.VENT_FAN, True)
            GPIO.output(self.AC_UNIT, True)
        else:
            GPIO.output(self.AC_UNIT, False)
            self.start_fan_timer()
            self.start_safety_timer()

    def heater_Switch(self, state):
        if state is True:
            GPIO.output(self.VENT_FAN, True)
            GPIO.output(self.HEATER_UNIT, True)
        else:
            GPIO.output(self.HEATER_UNIT, False)
            self.start_fan_timer()
            self.start_safety_timer()

    def vent_fan_Switch(self, state):
        if state is True:
            GPIO.output(self.VENT_FAN, True):
        else:
            GPIO.output(self.VENT_FAN, False):


    def state_machine(self):
        room_temp = self.temps.get_room_t()
        if self.state == "Cool":
            if room_temp > self.cooling_on:
                self.AC_Switch(True):
            elif  room_temp < self.cooling_off:
                self.AC_Switch(False):

        elif self.state == "Heat":
            if room_temp < self.heating_on:
                self.heater_Switch(True):
            elif room_temp > self.heating_off:
                self.heater_Switch(False):

        elif self.state == "Fan":
            self.vent_fan_Switch(True)

        else:
            self.AC_Switch(False):
            self.heater_Switch(False):

    def run(self):
        self.stop_event.clear()
        while not self.stop_event.isSet():
            #Only run if we are not in a safety state
            if self.ok_to_start is True:
                self.state_machine()
            sleep(self.read_rate)

        self.mutex.release()
