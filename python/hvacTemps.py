import MySQLdb
import threading
from datetime import datetime
from numpy import mean
from time import sleep
from wunderground import collect_pws
from collections import deque
import logging

logging.basicConfig()

class get_temps(threading.Thread):
    def __init__(self, read_rate = 10,
                 sample_average = 6,
                 sample_max = 100):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('GetTemps')
        self.logger.setLevel(logging.DEBUG)
        
        self.read_rate = read_rate
        self.sample_max = sample_max
        self.sample_average = sample_average

        self.attic_t_dev = "28-000004a82b4a"
        self.room_t_dev = "28-000004a82a59"
        self.attic_t = 0
        self.room_t = 0

        self.stop_event = threading.Event()
        self.mutex = threading.Lock()
        
        self.attic_t_buffer = deque(maxlen=self.sample_max)
        self.room_t_buffer = deque(maxlen=self.sample_max)

        self.init_temps()

    def __del__(self):
        self.logger.info("Deleting Myself")
        self.stop_event.set()
    
    def run(self):
        self.stop_event.clear()
        while not self.stop_event.isSet():
            self.collect_temps()
            sleep(self.read_rate)

    def read_temp(self, id, celcius=True):
        tmp_str = "/sys/bus/w1/devices/" + id + "/w1_slave"
        tfile = open(tmp_str)
        tmp_txt = tfile.read()
        tfile.close()

        lines = tmp_txt.split("\n")
        print lines
        if lines[0].find("YES") > 0:
            tt = float((lines[1].split(" ")[9])[2:])
            tt /= 1000
            if celcius is False:
                return ctof(tt)
            else:
                return tt
        else:
            return False

    def collect_temps(self):
        self.mutex.acquire()
        attic_t = self.read_temp(self.attic_t_dev)
        room_t = self.read_temp(self.room_t_dev)

        if attic_t is not False:
            self.attic_t = attic_t
            self.attic_t_buffer.append(attic_t)
        if room_t is not False:
            self.room_t = room_t
            self.room_t_buffer.append(room_t)
    
        self.mutex.release()

    def get_room_t(self, sample_count=None):
        if sample_count is None:
            sample_count = self.sample_average
        elif len(self.room_t_buffer) <= sample_count:
            sample_count = len(self.room_t_buffer)
        return mean(list(self.room_t_buffer)[-sample_count:])

    def get_attic_t(self, sample_count=None):
        if sample_count is None:
            sample_count = self.sample_average
        elif len(self.attic_t_buffer) <= sample_count:
            sample_count = len(self.attic_t_buffer)
        return mean(list(self.attic_t_buffer)[-sample_count:])

    def init_temps(self):
        attic_t = self.read_temp(self.attic_t_dev)
        room_t = self.read_temp(self.room_t_dev)
        while attic_t is False:
            attic_t = self.read_temp(self.attic_t_dev)
        while room_t is False:
            room_t = self.read_temp(self.room_t_dev)

        self.attic_t = attic_t
        self.room_t = room_t

    def ctof(self,c):
        return c*9/5 + 32

    def ftoc(self,f):
        return (f-32)*5/9.0


class collect_data(threading.Thread):
    def __init__(self, lograte = 5):
        threading.Thread.__init__(self)
        self.daemon = True
        self.lograte = lograte*60.0
        self.sample_count = int(self.lograte/10)
        self.conn = MySQLdb.connect(host = "192.168.1.2", 
                                    user = "hvac_master",
                                    passwd = "hvac69",
                                    db = "hvac")
        self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
        self.temp_collector = get_temps()
        self.ac_on = False
        self.attic_fan_on = False

        self.command_buffer = []
        
        self.stop_event = threading.Event()
        self.mutex = threading.Lock()
        self.temp_collector.daemon = True
        self.temp_collector.start()

    def run(self):
        self.stop_event.clear()
        #self.temp_collector.start()
        while not self.stop_event.isSet():
            self.attic_t = self.temp_collector.get_attic_t(self.sample_count)
            self.room_t = self.temp_collector.get_room_t(self.sample_count)
            try:
                self.outside_data = collect_pws()
            except:
                print "outside temp failed"
            print self.attic_t, self.room_t, self.outside_data["temperature"]
            self.populate_db()
            sleep(self.lograte)

    def populate_db(self):
        now = datetime.now()
        tmp_str = """INSERT INTO data_logs (timestamp, attic_fan1_on, attic_fan2_on, central_fan_on, heating_on, ac_on, attic_temp, inside_temp, outside_temp, outside_humidity, outside_pressure, wind_dir, wind_speed, precip_hour, precip_day) VALUES ('%s',%i,0,0,0,%i,%f,%f,%f, %f, %f, %f, %f, %f, %f)"""  % (now,self.attic_fan_on,self.ac_on,self.attic_t,self.room_t, self.outside_data["temperature"], self.outside_data["humidity"], self.outside_data["pressure"], self.outside_data["wind_dir"], self.outside_data["wind_mph"], self.outside_data["precip_hour"], self.outside_data["precip_day"])
        self.cursor.execute(tmp_str)
        self.conn.commit()

    def __del__(self):
        self.stop_event.set()
