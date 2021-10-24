import serial
import sys
import codecs
import yaml
import signal
import logging
import os
import RPi.GPIO as GPIO
from time import sleep, strftime
from datetime import datetime
import numpy as np
import time
import Freenove_DHT as DHT
import bmp180

#fname = 'throwaway.csv'#
fname = 'AQMOct_23_2021.csv'# csv output filename
file1 = open(fname, "a")

valvePin = 21    # define buzzerPin
def valve(switch):
    GPIO.setmode(GPIO.BCM)        # use PHYSICAL GPIO Numbering
    GPIO.setup(valvePin, GPIO.OUT)   # set buzzerPin to OUTPUT mode
    if switch == 0:
        GPIO.output(valvePin,GPIO.HIGH)
    if switch == 1:
        GPIO.output(valvePin,GPIO.LOW)

def valve_reset():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.OUT) 
    GPIO.output(21,GPIO.HIGH)

def get_cpu_temp():     # get CPU temperature and store it into file "/sys/class/thermal/thermal_zone0/temp"
    tmp = open('/sys/class/thermal/thermal_zone0/temp')
    cpu = tmp.read()
    tmp.close()
    return '{:.2f}'.format( float(cpu)/1000 ) + ' C'
 
def get_time_now():     # get system time
    return datetime.now().strftime('%D %H:%M:%S')

DHTPin = 17     #define the pin of DHT11
def temp_hum():
    dht = DHT.DHT(DHTPin)   #create a DHT class object
    while(True):
        for i in range(0,15):            
            chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                break
            time.sleep(0.1)
        #print("Humidity : %.2f, \t Temperature : %.2f \n"%(dht.humidity,dht.temperature))
        return[str(dht.humidity), str(dht.temperature)]     
'''        
if __name__ == '__main__':
    print ('Program is starting ... ')
    try:
        loop()
    except KeyboardInterrupt:
        GPIO.cleanup()
        exit()  

'''


# https://kookye.com/2017/06/01/design-a-lel-gas-detector-through-a-raspberry-pi-board-and-mq-5-sensor/
# http://osoyoo.com/driver/mq-5.py
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
smokesensor_dpin = 26
smokesensor_apin = 0


def get_time_now():     # get system time
    return datetime.now().strftime('%D %H:%M:%S')

#port init
def init():
         GPIO.setwarnings(False)
         #GPIO.cleanup()			#clean up at the end of your script
         GPIO.setmode(GPIO.BCM)		#to specify whilch pin numbering system
         # set up the SPI interface pins
         GPIO.setup(SPIMOSI, GPIO.OUT)
         GPIO.setup(SPIMISO, GPIO.IN)
         GPIO.setup(SPICLK, GPIO.OUT)
         GPIO.setup(SPICS, GPIO.OUT)
         GPIO.setup(smokesensor_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)


#read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)	

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

def MQ2():
    init()
    lastmeasurement = 440
    
    while True:
        smokelevel=readadc(smokesensor_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
        return smokelevel
    
logger = logging.getLogger(__name__)

# PMS5003 transport protocol-Active Mode
# Each field has a list indicating the field position
# in the frame. (e.g., [start_byte, num_bytes])
frame_info = { 'frame_size': 32, 'data_size': 30, 
               'fields':{'start_char': [0,2],
                         'frame_length': [2,2],
                         'PM1_std': [4,2],
                         'PM25_std': [6,2],
                         'PM10_std': [8,2],
                         'PM1_env': [10,2],
                         'PM25_env': [12,2],
                         'PM10_env': [14,2],
                         'P03': [16,2],
                         'P05': [18,2],
                         'P1': [20,2],
                         'P25': [22,2],
                         'P5': [24,2],
                         'P10': [26,2],
                         'reserved': [28,2],
                         'checksum': [30,2],
                         }
               }


class Timeout(Exception):
    """ Timeout decorator obtained from 
        https://www.saltycrane.com/blog/
    """
    def __init__(self, value = "Timed Out"):
        self.value = value
    def __str__(self):
        return repr(self.value)


class ChecksumError(Exception):
    def __init__(self, value = "Checksum failed"):
        self.value = value
    def __str__(self):
        return repr(self.value)


def timeout(seconds_before_timeout):
    """ Timeout decorator obtained from 
        https://www.saltycrane.com/blog
    """
    def decorate(f):
        def handler(signum, frame):
            raise Timeout()
        def new_f(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds_before_timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, old)
                signal.alarm(0)
            return result
        new_f.__name__ = f.__name__
        return new_f
    return decorate


class pms5003():
    """This class handles the serial connection between the PMS5003 and 
       a Raspberry PI
    """
    
    def __init__(self, baudrate=9600, device='/dev/ttyS0', timeout=20):
        self.endian = sys.byteorder
        self.baudrate = baudrate
        self.device = device
        self.timeout = timeout
        self.start_char = b'424d'
        self.data = dict()
        self.frame = frame_info
        self.temp_hum = temp_hum
        self.get_time_now = get_time_now
        self.MQ2 = MQ2
        self.iter = 0
        self.switch = [1,0]
        self.conditioning_sampling = 0
        self.indoor_outdoor = 0
        self.currenttime_sample = time.time()
        #self.currenttime_door = time.time()
        self.count = 0
        self.interval = 5*60
    
    def conn_serial_port(self):
        """Define the connection with the serial port"""
        self.serial = serial.Serial(self.device, baudrate=self.baudrate)
        
    @timeout(20)
    def find_start_chars(self):
        while True:
            buff = self.serial.read(self.frame['fields']['start_char'][1])
            buff_hex = codecs.encode(buff, 'hex_codec')
            if buff_hex == self.start_char:
                return True
            
            
    def read_frame(self, data_size=30):
        try:
            self.conn_serial_port()
            if self.find_start_chars():# and ((self.iter%10!=0) or (self.iter==0)):#artificial errors for testing
                buff = self.serial.read(data_size)
                buff_hex = self.start_char + codecs.encode(buff, 'hex_codec')
                try:
                    self.verify_checksum(buff_hex)
                    if os.stat(fname).st_size == 0: self.cols(buff_hex) # alex added            
                    self.get_data(buff_hex)
                except ChecksumError:
                    logger.error("Checksum does not match", exc_info=True)
        except Timeout:
            logger.error("Timeout! No data collected in %s seconds",
                          self.timeout, exc_info=True)
            GPIO.cleanup()
            #GPIO.cleanup(21)
            raise Timeout()
            
        
        self.iter+=1
                
    def verify_checksum(self, buff_hex):
        """According to the specs, the checksum is stored in the last 4 bytes
        """
        checksum = 0
        checksum_size_nibble = 2*self.frame['fields']['checksum'][1]
        data = buff_hex[:-checksum_size_nibble]
        for x in range(0, len(data), 2):
            checksum += int(data[x:x+2], 16)
        if checksum != int(buff_hex[-checksum_size_nibble:], 16):
            raise ChecksumError() 


    def cols(self, buff_hex):      
        no_data = ['start_char', 'frame_length', 'reserved', 'checksum']
        file1 = open(fname, "a")
        for k,v in self.frame['fields'].items():
            if k not in no_data:
                # Start and end points need to be in nibbles
                st = 2*v[0]
                nd = st + 2*v[1]
                self.data[k] = int(buff_hex[st:nd], 16) 
                file1.write(str(k)+ ",")
        file1.write('MQ2_VCs,Humidity,Temperature,Pressure,Timestamp,Sample_Conditioning,Indoor_Outdoor,\n')
        file1.close()

    def get_data(self, buff_hex):      
        no_data = ['start_char', 'frame_length', 'reserved', 'checksum']
        file1 = open(fname, "a")

        if (time.time() >= (self.currenttime_sample + self.interval)) and (self.count == 0):
            self.conditioning_sampling = 1
            self.indoor_outdoor = 0#self.switch[self.conditioning_sampling]
            self.currenttime_sample = time.time()
            self.count = 1
        elif (time.time() >= (self.currenttime_sample + self.interval)) and (self.count == 1):
            self.conditioning_sampling = 0
            self.indoor_outdoor = 1#self.switch[self.conditioning_sampling]
            valve(self.indoor_outdoor)
            self.currenttime_sample = time.time()
            self.count = 2
        elif (time.time() >= (self.currenttime_sample + self.interval)) and (self.count == 2):
            self.conditioning_sampling = 1
            self.indoor_outdoor = 1#self.switch[self.conditioning_sampling]
            self.currenttime_sample = time.time()
            self.count = 3
        elif (time.time() >= (self.currenttime_sample + self.interval)) and (self.count == 3):
            self.conditioning_sampling = 0
            self.indoor_outdoor = 0#self.switch[self.conditioning_sampling]
            valve(self.indoor_outdoor)
            self.currenttime_sample = time.time()
            self.count = 0  
            """
        if time.time() >= (self.currenttime_door + 10*60):
            self.indoor_outdoor = self.switch[self.indoor_outdoor]
            valve(self.indoor_outdoor)
            self.currenttime_door = time.time()
            """
        for k,v in self.frame['fields'].items():
            if k not in no_data:
                # Start and end points need to be in nibbles
                st = 2*v[0]
                nd = st + 2*v[1]
                self.data[k] = int(buff_hex[st:nd], 16)
                #file1 = open("myfile" + str(k) + ".csv", "a")
                file1.write(str(self.data[k]) + ",")
        temphum = self.temp_hum()# function outputs two items
        bmp = bmp180.bmp180(0x77)
        mystr = ','.join([str(i) for i in [self.MQ2(), temphum[0], temphum[1], bmp.get_pressure(), self.get_time_now(),self.conditioning_sampling,self.indoor_outdoor]])
        print(mystr)
        print(str(np.round((self.currenttime_sample + self.interval) - time.time(), 0)) + " seconds until next phase")
        file1.write(mystr+'\n')
        file1.close()
        #GPIO.cleanup([11,17,23])
        
            

        

#GPIO.cleanup()
