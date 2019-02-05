#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import time
import paho.mqtt.client as paho
import optparse
from threading import Thread
import logging
import os
import sys

__author__ = 'chevalir'

## https://realpython.com/
dio_button_section = ['a','b','c','d']
On_Off = ['Off','On']
logger = logging.getLogger("duibridge")
prefix_dio=""
stopMe = False
options = {}


'''-------------------------------
'''
class config_manager:

  def __init__(self, conf_file_path, conf_save_path):
    self.conf_file_path=conf_file_path
    self.conf_save_path=conf_save_path
    self.digital_pins = {}
    self.custom_vpins = {}
    self.r_radio_vpins = {}
    self.t_radio_vpins = {}
    self.transmeter_pin = -1
    self.rootNode=''
    self.DPIN=14  #default value
    self.APIN=6   #default value
    self.CPIN=32  #default value
    self.decode={}

  def load_config(self):
    try:
      logger.debug(self.conf_file_path + " to load ")
      # Get a file object with write permission.
      file_object = open(self.conf_file_path, 'r')
      logger.debug(self.conf_file_path + " loaded ") 
      # Load JSON file data to a python dict object.
      self.decode = json.load(file_object)
    except Exception as e:
      print(e)
      return
    self.rootNode = str(self.decode['nodeName'])
    cardType = self.decode['card']
    if cardType.find('UNO'):
      self.DPIN=14
      self.APIN=6
      self.CPIN=32
    self.decode_digital()
    self.decode_custom()
    self.decode_radio()

  ''' --------------------- '''
  def decode_digital(self):
    dpins = self.decode['digitals']['dpins']
    for pinNum in range(len(dpins)):
      thepin = int(str(dpins[pinNum]['card_pin']).split(' ', 2)[1])
      mode = dpins[pinNum]['mode'].split(";",1)[0]
      topic = dpins[pinNum]['topic']
      prefix = dpins[pinNum]['prefix']
      if mode=='t':
        self.transmeter_pin = thepin
      full_topic = get_topic_prefix(mode, prefix)+topic
      self.digital_pins[thepin] = (mode, full_topic)
      # @TODO manage output pin ( subscrib to topic )
  
  def decode_custom(self):
    cpins = self.decode['custom']['cpins']
    for pinNum in range(len(cpins)):
      thepin = int(cpins[pinNum]['custom_pin'])
      mode = cpins[pinNum]['mode'].split(";",1)[0]
      topic = cpins[pinNum]['topic']
      prefix = cpins[pinNum]['prefix']
      full_topic = get_topic_prefix(mode, prefix)+topic
      self.custom_vpins[self.DPIN+self.APIN+thepin] = (mode, full_topic)
    logger.debug(self.custom_vpins)

  def decode_radio(self):
    rpins = self.decode['radio']['cradio']
    for pinNum in range(len(rpins)):
      prefix_topic=''
      typeradio = rpins[pinNum]['typeradio'].split(";",1)[0]
      mode = rpins[pinNum]['mode'].split(";",1)[0]
      topic = rpins[pinNum]['topic']
      device = rpins[pinNum]['device']
      prefix = rpins[pinNum]['prefix']
      '''if len(device) < 2:
        device = "0"+device '''
      # @TODO change device format
      radiocode = rpins[pinNum]['radiocode']
  
      if mode in ['r', 'tr']: 
        status_topic = get_topic_prefix('r', prefix)+topic
        radiocode_key = '{}#{:0>2}'.format(rpins[pinNum]['radiocode'], device)
        self.r_radio_vpins.update({radiocode_key:(device, status_topic)})
  
      if mode in ['t', 'tr']:
        action_topic = get_topic_prefix('t', prefix)+topic
        self.t_radio_vpins.update({action_topic:(device, radiocode)})
        options.comJeedom.subscribe_topic( action_topic )
    #logger.debug(self.r_radio_vpins)
    #logger.debug(self.t_radio_vpins)

  def add_radio_conf(self, radiocode, device, radiocode_key):
    status_topic='radio/'+radiocode+"/"+str(device)
    self.decode['radio']['cradio'].append({'typeradio': 'H; Chacon DIO', 'radiocode': radiocode, 'topic': status_topic
      , 'prefix': True, 'mode' : 'tr; Trans./Recep.', 'device': device})
    with open(self.conf_save_path, 'w') as outfile:
      json.dump(self.decode, outfile, sort_keys = True, indent = 2)
    status_topic=get_topic_prefix('r', True)+status_topic
    logger.info(" new topic added " + status_topic)
    self.r_radio_vpins.update({radiocode_key:(device, status_topic)})


## @RC
class mqtt_bridge:
  ## constructor
  def __init__(self, bridgeID, sbNode, source, messageFunc):
    self.client = paho.Client(bridgeID)
    self.broker="localhost"
    self.base_topic ="duitest/"+sbNode+"/"
    logger.debug("connecting to broker: " + self.broker)
    self.client.connect(self.broker) 
    self.pub_topic = self.base_topic+"to"+source
    self.sub_topic = self.base_topic+"from"+source
    logger.info("subscribing: "+ self.sub_topic)
    self.client.on_message=messageFunc
    self.client.subscribe(self.sub_topic)
    self.client.publish(self.pub_topic, "init")
    self.client.loop_start() #start loop to process received messages

  def publish_message(self, topic, mess ):
    logger.info('publish on '+topic+ " = "+mess)
    self.client.publish(topic, mess) 

  def send(self,  mess ):
    self.publish_message(self.pub_topic, mess) 

  def subscribe_topic(self, topic):
    logger.info("subscribing: "+ topic)
    self.client.subscribe(topic)   


'''-------------------------------
///            MAIN            /// 
-------------------------------'''  
def main(argv=None):
  global stopMe, options
  myrootpath = os.path.dirname(os.path.realpath(__file__)) + "/"
  print ( "START DEAMON " )
  (options, args) = cli_parser(argv)
  print(options)
  write_pid(options.pid_path)
  LOG_FILENAME = myrootpath + '../../../../log/duibridge_daemon'
  ## formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(threadName)s - %(module)s:%(lineno)d - %(message)s')
  formatter = logging.Formatter('%(asctime)s| %(levelname)s | %(lineno)d | %(message)s')
  #loglevel  = "DEBUG"
  filehandler = logging.FileHandler(LOG_FILENAME)
  filehandler.setFormatter(formatter)
  console = logging.StreamHandler()
  console.setFormatter(formatter)
  sys.stderr = open(LOG_FILENAME + "_stderr", 'a', 1)
  logger.setLevel(logging.getLevelName(options.loglevel.upper()))
  ##logger.addHandler(console)
  ##logger.addHandler(filehandler)
  logger.info("# duiBridged - duinode bridge for Jeedom # loglevel="+options.loglevel)

  options.comArduino = mqtt_bridge("abridgeID", "abridge", "arduino", on_arduino_message )
  options.comJeedom = mqtt_bridge( "jbridgeID", "jbridge", "jeedom", on_jeedom_message )
  options.config = config_manager(options.config_folder, options.config_folder ) 
  # "/home/pi/pidomo/jeedom/template/pinconf/pinConfSave.json")
  options.config.load_config()
  logger.debug(options.config.rootNode)


  ## init thread to listen arduino
  ## init_Thread("fromArduino", arduino_listener, options)
  ## init thread to listen jeedom 
  ## init_Thread("fromJeedom", jeedom_listener, options)
  #parse_arduino_message("43>>0<<")
  ##send_to_arduino("cabradom/node1/salon/bureau/lampe", "OFF")

  while not stopMe:
    time.sleep(0.5)
  logger.info("after stop...")

#===========================================================

'''-------------------------------
'''
def init_Thread(threadName, theTarget, theOptions ):
  logger.debug("start Thread: " + threadName)
  mqtt_thd_manager = Thread(target=theTarget, args=(theOptions,))
  mqtt_thd_manager.setDaemon(True)
  mqtt_thd_manager.start()

'''-------------------------------
'''
def on_arduino_message(client, userdata, message):
  global stopMe, options
  line = str(message.payload.decode("utf-8"))
  # logger.debug("on_arduino_message message =" + line)
  parse_arduino_message(line)

'''-------------------------------
'''
def parse_arduino_message(duiMessage):
  if duiMessage.find(">>"):
    (pin, value) = duiMessage.split(">>")
    value = value.replace("<<", '')
    logger.debug(str(pin) +" "+ str(value))
    send_to_jeedom(pin, value)


'''-------------------------------
'''
def send_to_jeedom(pin, value):
  global options
  logger.debug(str(pin) +" "+ str(value)+" "+ str(options.config.DPIN))
  thePin = int(pin)
  try:
    if thePin in range(1, options.config.DPIN):
      (mode, topic) = options.config.digital_pins[thePin]
    elif thePin in range(options.config.DPIN+options.config.APIN , options.config.DPIN + options.config.APIN+options.config.CPIN):
      (mode, topic) = options.config.custom_vpins[thePin]
    else :
      logger.info("Others pins" )

    logger.debug(mode+" "+topic)

    if mode in ('c', 'i', 'j', 'y', 'a' ) :
      options.comJeedom.publish_message(topic, value)
    elif mode in ('r'):
      send_radio_to_jeedom(topic, value)
    else:
      logger.error( 'unexpected result' )
  except KeyError:
    logger.error( "KeyError "+ str(options.config.custom_vpins))

'''-------------------------------
'''                      
def send_radio_to_jeedom(topic, value):
  global options

  if "RFD" in value:
    try:
      device_on = False
      device_split = value.split(':')
      radiocode = device_split[1]
      device = int (device_split[3]) + 1
      device_on = device > 99
      if device_on :
        device = device - 100
      value = On_Off[int(device_on)]
      radiocode_key = '{}#{:0>2}'.format(radiocode, device)
      if radiocode_key not in options.config.r_radio_vpins:
        radiocode_key = '{}#{:0>2}'.format(radiocode, 0)
        if radiocode_key not in options.config.r_radio_vpins:
          logger.info("radio code={0} device ={1} not define in config ".format(radiocode, device) )
          options.config.add_radio_conf(radiocode, device, radiocode_key_gl)
          value = "{0}={1}".format(device, value)      
      (device, topic) = options.config.r_radio_vpins.get(radiocode_key)
      logger.info("radio code={0} device ={1} topic {2} ".format(radiocode_key, device, topic) )
      options.comJeedom.publish_message(topic, value)

    except Exception as e:
      logger.error( "send_radio_to_jeedom exception" )
      logger.error( e )
  return

'''-------------------------------
'''                        
def send_to_arduino(topic, raw_message):
  global options
  logger.info("send_to_arduino topic: "+topic)
  if topic in options.config.t_radio_vpins:
    (device, radiocode) =  options.config.t_radio_vpins.get(topic)
    if str(raw_message).upper() in ["1","ON"]:
      cmd="1"
    elif str(raw_message).upper() in ["0","OFF"]:
      cmd="0"
    else:
      logger.error("send_to_arduino command unk :"+str(raw_message))
      return
    options.comArduino.send("SP{:0>2}H{}0{}{:0>2}".format(options.config.transmeter_pin, radiocode, cmd, device ))


'''-------------------------------
'''                        
def on_jeedom_message(client, userdata, message):
  global stopMe
  line = str(message.payload.decode("utf-8"))
  # logger.debug("on_jeedom_message ="+ line)
  send_to_arduino(str(message.topic), line)  
'''
  if line.find("stopMe"):
    stopMe=True
    logger.info("Bye")
'''



'''-------------------------------
'''
def get_topic_prefix(mode, enable):
  global options
  if enable:
    if mode in ['r', 'c', 'a', 'y','i','j', range(1,8)]: 
      return(options.config.rootNode+"/"+'status/') 
    else:
      return(options.config.rootNode+"/"+'action/')
  else:
     return(options.config.rootNode+"/")



'''-------------------------------
'''
def write_pid(path):
	pid = str(os.getpid())
	logging.info("Writing PID " + pid + " to " + str(path))
	file(str(path), 'w').write("%s\n" % pid)

'''-------------------------------
'''
def cli_parser(argv=None):
  parser = optparse.OptionParser("usage: %prog -h   pour l'aide")
  parser.add_option("-l", "--loglevel", dest="loglevel", default="INFO", type="string", help="Log Level (INFO, DEBUG, ERROR")
  parser.add_option("-p", "--usb_port", dest="usb_port", default="auto", type="string", help="USB Port (Auto, <Usb port> ")
  parser.add_option("-c", "--config_folder", dest="config_folder", default=".", type="string", help="config folder path")
  parser.add_option("-i", "--pid", dest="pid_path", default="./tmp", type="string", help="pid file folder folder path")

  return parser.parse_args(argv)


if __name__ == '__main__':
  main()
