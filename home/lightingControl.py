import RPi.GPIO as GPIO
import ephem
import logging
import datetime as dt

logging.basicConfig()

#Simple class for sun data
class sunData():
    def __init__(self,
                 lat=34.213869,
                 lon =-118.161517,
                 elev = 480,
                 twilight = "sensible",
                 horizon = None):

        self.logger = logging.getLogger("SunData")
        self.logger.setLevel(logging.DEBUG)

        self.twilight_def = {"sensible" : -3,
                             "civil" : -6,
                             "nautical" : -12,
                             "astronomical" : -18}

        self.meadows = ephem.Observer()
        self.meadows.lat = str(lat)
        self.meadows.lon = str(lon)
        self.meadows.elev = elev

        # No custom horizon so use standard definitaion
        if horizon is None:
            self.twilight = twilight
            self.meadows.horizon = str(self.twilight_def[twilight])
        else:
            self.twilight = "custom"
            self.meadows.horizon = str(horizon)

    def get_sunrise(self):
        self.meadows.date = ephem.now()
        if self.sunup() is True:
            sunrise = self.meadows.previous_rising(ephem.Sun(), use_center=True)
        else:
            sunrise = self.meadoews.next_rising(ephem.Sun(), use_center=True)
        return ephem.localtime(sunrise)

    def get_sunset(self):
        self.meadows.date = ephem.now()
        if self.sunup() is True:
            sunset = self.meadows.next_setting(ephem.Sun(), use_center=True)
        else:
            sunset = self.meadows.previous_setting(ephem.Sun(), use_center=True)
        return ephem.localtime(sunset)

    def sunup(self):
        # This calculates if the sun as above virtual horizon
        # useful as we need to know if it's day or night
        self.meadows.date = ephem.now()
        sun = ephem.Sun(self.meadows)
        sun.compute(self.meadows)
        sunup = (sun.alt > self.meadows.horizon)
        return sunup


class lightingZone():
    def __init__(self, name, pin):
        self.logger = logging.getLogger('LightingZone')
        self.logger.setLevel(logging.DEBUG)

        self.sundata = sunData()

        self.name = name
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)

        # Inputs are inverted as sinks current
        self.OFF = True
        self.ON = False

        self.modes = {"Auto" : 0,
                      "Timed" : 1,
                      "Manual" : 3,
                      "On" : 4,
                      "Off" : 5}

        self.start_mode = self.modes["Auto"] #sunset
        self.stop_mode = self.modes["Manual"] # 11pm
        self.start_time = None
        self.stop_time = None
        self.start_duration = None
        self.stop_duration = dt.timedelta(hours=2)

        self.manual_on = dt.time(19,30,00)
        self.manual_off = dt.time(23,00,00)

        self.lights_on = False
        self.update_times()

    def set_timer(self,
                  start = None,
                  stop = None):
        # Let's try a single function here
        # It either are None or gibberish then ignore
        # Do modes

        if start == "Auto":
            self.start_mode = self.modes["Auto"]
        elif start == "On":
            self.start_mode = self.modes["On"]
        elif start == "Off":
            self.start_mode = self.modes["Off"]
        elif isinstance(start, dt.time):
            self.start_mode = self.modes["Manual"]
            self.manual_on = start
        elif isinstance(start, float):
            self.start_mode = self.modes["Timed"]
            self.start_duration = dt.timedelta(hours=start)

        if stop == "Auto":
            self.stop_mode = self.modes["Auto"]
        elif isinstance(stop, dt.time):
            self.stop_mode = self.modes["Manual"]
            self.manual_off = stop
        elif isinstance(stop, float):
            self.stop_mode = self.modes["Timed"]
            self.stop_duration = dt.timedelta(hours=stop)

        self.update_times()

    def update_times(self):
        # This actually sets the times for running the lights
        # Should be called periodically
        # note the on and off cases do not use any times

        if self.start_mode is self.modes["Auto"]:
            self.start_time = self.sundata.get_sunset()
        elif self.start_mode is self.modes["Manual"]:
            self.start_time = dt.datetime.combine(dt.date.today(),
                                                  self.manual_on)
        elif self.start_mode is self.modes["Timed"]:
            self.start_time = dt.datetime.now() + self.start_duration

        if self.stop_mode is self.modes["Auto"]:
            self.stop_time = self.sundata.get_sunrise()
        elif self.stop_mode is self.modes["Manual"]:
            self.stop_time = dt.datetime.combine(dt.date.today(),
                                                 self.manual_off)
        elif self.stop_mode is self.modes["Timed"]:
            self.stop_time = self.start_time + self.stop_duration

        # We need to do the sanity check and make sure the stop_time
        # is after the start_time - should only be an issue when
        # using manual mode

        t_delta = self.stop_time - self.start_time
        if t_delta.total_seconds() < 0:
            self.stop_time = self.stop_time + dt.timedelta(days=1)

        self.set_lights()

    def set_lights(self):
        current_time = dt.datetime.now()
        print(current_time)
        print(self.start_time)
        print(self.stop_time)
        if self.start_mode is self.modes["On"]:
            GPIO.output(self.pin, self.ON)
            self.lights_on = True
        elif self.start_mode is self.modes["Off"]:
            GPIO.output(self.pin, self.OFF)
            self.lights_on = False

        elif (current_time > self.start_time) and (current_time < self.stop_time):
            GPIO.output(self.pin,self.ON)
            print("TURNING ON")
        else:
            GPIO.output(self.pin,self.OFF)
            print("TURNING OFF")


class lightingControl():
    def __init__(self,zones=None):
        self.logger = logging.getLogger('LightingControl')
        self.logger.setLevel(logging.DEBUG)

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # We could load infor from file etc but just setup
        # A default zone and pin list here that can be added
        # Upon at a later date if required

        if zones is None:
            # Dictionary is NAME: pin
            zones = {"PATH" : 2,
                     "FRONT" : 3,
                     "SPARE" : 4,
                     "ALLEY" : 7}

        self.setup_zones(zones)
        self.local_settings()
        self.set_lights()

    def setup_zones(self, zones):
        self.zones = {}
        for name, pin in zones.items():
            self.zones[name] = lightingZone(name, pin)

    def set_lights(self):
        for name,zone in self.zones.items():
            self.logger.debug(name)
            zone.update_times()

    def local_settings(self):
        # This is to setup the local profile
        # It should really be a config file but seen
        # as it's just me I'll put them in here
        # Path comes on at civil twilight, turns off at 11pm
        # All other zones are off

        self.zones["PATH"].set_timer("Auto", dt.time(23,00,00))
        #self.zones["PATH"].set_timer("Auto", "Auto")
        self.zones["FRONT"].set_timer("Off")
        self.zones["SPARE"].set_timer("Off")
        self.zones["ALLEY"].set_timer("Off")
