#!/usr/bin/env python3

#from pms5003py import pms5003
from Alex_AQ_Draft1 import pms5003
import logging.config
import logging
import os
import yaml
import RPi.GPIO as GPIO

def valve_reset():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.OUT) 
    GPIO.output(21,GPIO.HIGH)

def setup_logging(default_path='logging.yml', default_level=logging.INFO, env_key='LOG_CFG'):
    """Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

        
def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    sensor = pms5003()
    valve_reset()
    #GPIO.cleanup()
    #GPIO.cleanup(21)
    while True:
        try: 
            sensor.read_frame()
            print(sensor.data)
        except KeyboardInterrupt:
            print("\nTerminating data collection")
            GPIO.cleanup()
            break
        except:
            logger.debug('Error:', exc_info=True)
            #GPIO.cleanup(21)
            GPIO.cleanup()# put this in the function file instead
            main()


if __name__ == '__main__':
    main()
