#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import time
import paho.mqtt.client as paho
import optparse
from threading import Thread

__author__ = 'chevalir'

## https://realpython.com/
DPIN=14
APIN=6
CPIN=32
MAX_CPIN=128
digital_pins ={}
custom_pins ={}

## @RC
class mqtt_bridge:
  ## constructor
  def __init__(self, sbNode, source):
    self.client = paho.Client(bridgeID)
    self.broker="localhost"
    self.base_topic ="duitest/"+sbNode+"/"
    print("connecting to broker: ", self.broker)
    self.client.connect(self.broker) 
    self.pub_topic = self.base_topic+"to"+source
    self.sub_topic = self.base_topic+"from"+source
    print("subscribing: ", sub_topic)
    self.client.on_message=on_messageB
    self.client.subscribe(self.sub_topic)
    self.client.publish(self.pub_topic, "init")
    self.client.loop_start() #start loop to process received messages

def main():
  (options, args) = cli_parser(argv)
  python_json_file_to_dict("./defaultConf.json")
  options.comArduino = mqtt_bridge("abridge", "mqttArduino" )
  options.comJeedom = mqtt_bridge("abridge", "mqttArduino" )

  ## init thread to listen arduino
  init_Thread("fromArduino", arduinoListener, options)
  ## init thread to listen jeedom 


def init_Thread(threadName, theTarget, theOptions ):
  print("start Thread:", threadName)
  mqtt_thd_manager = Thread(target=theTarget, args=(theOptions,))
  mqtt_thd_manager.setDaemon(True)
  mqtt_thd_manager.start()


##-------------------------------
def arduino_listener(options):
  while True:
    ##print ( "COMServer send OFF" )
    ##options.mqttManager.publish("OFF") 
    ##@rc
    time.sleep(10)
    ##print ( "COMServer send ON" )
    ##options.mqttManager.publish("ON")
    time.sleep(10)

def jeedom_listener(options):
  while True:
    ##print ( "COMServer send OFF" )
    ##options.mqttManager.publish("OFF") 
    ##@rc
    time.sleep(10)
    ##print ( "COMServer send ON" )
    ##options.mqttManager.publish("ON")
    time.sleep(10)



def python_json_file_to_dict(file_path):
  global digital_pins, custom_pins
  try:
      # Get a file object with write permission.
      file_object = open(file_path, 'r')
      # Load JSON file data to a python dict object.
      decode = json.load(file_object)
##  DECODE Digitals
      dpins = decode['digitals']['dpins']
      for pinNum in range(len(dpins)):
        thepin = int(str(dpins[pinNum]['card_pin']).split(' ', 2)[1])
        mode = dpins[pinNum]['mode'].split(";",1)[0]
        topic = dpins[pinNum]['topic']
        digital_pins[thepin] = (mode, topic)
        ## print (str(thepin) +" % "+ mode +" % "+ topic )
##  DECODE Digitals
      cpins = decode['custom']['cpins']
      for pinNum in range(len(cpins)):
        thepin = int(cpins[pinNum]['custom_pin'])
        mode = cpins[pinNum]['mode'].split(";",1)[0]
        topic = cpins[pinNum]['topic']
        custom_pins[DPIN+APIN+thepin] = (mode, topic)
        ##print (str(DPIN+APIN+thepin) +" mode:"+ mode +" topic:"+ topic )

  except FileNotFoundError:
      print(file_path + " not found. ") 



def cli_parser(argv=None):
    parser = optparse.OptionParser("usage: %prog -h   pour l'aide")
    parser.add_option("-l", "--loglevel", dest="loglevel", default="INFO", type="string", help="Log Level (INFO, DEBUG, ERROR")
    parser.add_option("-n", "--nodaemon", dest="nodaemon", default="no", help="Mettre -nd pour lancer en DEBUG VERBOSE")
    return parser.parse_args(argv)


if __name__ == '__main__':
  main()
