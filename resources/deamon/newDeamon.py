#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import serial
import time
import subprocess
import os
import optparse
import sys
import signal
import logging
import re
import xml.dom.minidom as minidom
from Queue import Queue
import threading

__author__ = 'chevalir'
logger = logging.getLogger("duibridge")
options={}


''' -----------------------------------------
'''
class Arduino_Node(object):
  def __init__(self, port, queue, arduino_id):
    self.usb_port=port
    self.request_queue=queue
    self.ID = arduino_id
    self.baud=115200
    thread = threading.Thread(target=self.run, args=())
    thread.daemon = True                            # Daemonize thread
    thread.start()                                  # Start the execution
    print( "__init__" )

  def run(self):
    '''Method that runs forever'''
    print( "RUN" )
    self.init_serial_com()
    while True:
      # Do something
      print('Doing something imporant in the background')
      time.sleep(1)
      if not self.request_queue.empty(): 
        self.read_queue()      
      self.read_serial()

  def init_serial_com(self):
    SerialPort = serial.Serial(self.usb_port, self.baud, timeout=0.3, xonxoff=0, rtscts=0)
    SerialPort.flush()
    SerialPort.flushInput()
    SerialPort.setDTR(True)
    time.sleep(0.030) # Read somewhere that 22ms is what the UI does.
    SerialPort.setDTR(False)
    time.sleep(0.200)
    SerialPort.flush()
    SerialPort.flushInput()
    logger.debug("Arduino {} wainting for HELLO".format(self.ID))
    line = ""
    checktimer = 0
    while not re.search("^HELLO", line):
      time.sleep(1)
      checktimer += 1
      line = SerialPort.readline()
      line = line.replace('\n', '')
      line = line.replace('\r', '')
      logger.debug("0_Arduino " + str(self.ID) + " >> [" + line + "]")
      if checktimer > 15:
        logger.error("TIMEOUT d'attente du HELLO de l'arduino " + str(arduID))
        quit()
    SerialPort.flush()
    SerialPort.flushInput()
    logger.debug("Arduino " + str(self.ID) + " ready for action")
    ##open serial port @@TODO
  
  def read_serial(self):
    print( "@@TODO read_serial" )

  def read_queue(self):
    print( "@@TODO read_queue" )





''' -----------------------------------------
'''
class Arduino_Config:

  ''' ...............................................'''
  def __init__(self, conf_file_path):
    self.conf_file_path=conf_file_path
    self.ArduinoStekchVersion = "0.0.0"
    self.ArduinoQty = 0
    self.Arduino_ports = {}
    self.pid_file =""

  ''' ...............................................'''
  def load_config(self):
    if os.path.exists( self.conf_file_path ):
      #open the xml file for reading:
      f = open( self.conf_file_path ,'r')
      data = f.read()
      f.close()
  
      try:
        xmlDom = minidom.parseString(data)
      except:
        print "Error: problem in the config_arduidom.xml file, cannot process it"
        logger.debug('Error to read file : '+self.conf_file_path)
  
      # ----------------------
      # Serial device
      self.ArduinoStekchVersion = self.read_config_item( xmlDom, "ArduinoVersion")
      self.ArduinoQty = int(self.read_config_item( xmlDom, "ArduinoQty"))
      logger.debug("Arduino Version:{} Qty:{}".format( self.ArduinoStekchVersion, self.ArduinoQty))
    
      # ----------------------
      # SERIALS
      for n_node in range(1, 1+self.ArduinoQty):
        port = self.read_config_item( xmlDom, "A{}_serial_port".format(n_node))
        self.Arduino_ports.update({n_node : port })
      logger.debug( self.Arduino_ports )
      # -----------------------
      # DAEMON
      self.pid_file = self.read_config_item( xmlDom, "daemon_pidfile")
      logger.debug("Daemon_pidfile: " + self.pid_file)
    
    else:
      # config file not found, set default values
      print "Error: Configuration file not found (" + configFile + ")"
      logger.error("Error: Configuration file not found (" + configFile + ") Line: ")
  
  ''' ...............................................'''
  def read_config_item(self, xmlDom, configItem):
    # Get config item
    xmlData = ""
    try:
      xmlTag = xmlDom.getElementsByTagName( configItem )
      xmlData = xmlTag[0].firstChild.data
      logger.debug(configItem + " : " +xmlTag[0].firstChild.data)
    except:
      logger.debug('The item tag not found in the config file')
      xmlData = ""
    return xmlData


''' -----------------------------------------
'''
class pin_Config:

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
  formatter = logging.Formatter('%(threadName)s-%(asctime)s| %(levelname)s | %(lineno)d | %(message)s')
  filehandler = logging.FileHandler(LOG_FILENAME)
  filehandler.setFormatter(formatter)
  console = logging.StreamHandler()
  console.setFormatter(formatter)
  ##sys.stderr = open(LOG_FILENAME + "_stderr", 'a', 1)

  # options.loglevel.upper()
  logger.setLevel(logging.getLevelName(options.loglevel.upper()))
  logger.addHandler(console)
  ##logger.addHandler(filehandler)
  logger.info("# duiBridged - duinode bridge for Jeedom # loglevel="+options.loglevel)
  
  configFile = os.path.join(myrootpath, "config_duibridge_nodes.xml")
  logger.debug("Config file: " + configFile)
  logger.debug("Read jeedom configuration file")
  options.Ardno_conf = Arduino_Config(configFile)
  options.Ardno_conf.load_config()
  options.nodes={}
  arduino_id = 1
  options.arduino_queues={arduino_id:Queue()}
  aNode = Arduino_Node(options.Ardno_conf.Arduino_ports[arduino_id], options.arduino_queues[arduino_id], arduino_id)
  options.nodes.update({arduino_id:aNode})

  count = 0
  while count in range(10000):
    time.sleep(1)
    count +=1
  print("THE END")


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
  parser.add_option("-i", "--pid", dest="pid_path", default="./duibridge.pid", type="string", help="pid file folder folder path")

  return parser.parse_args(argv)

if __name__ == '__main__':
  main()
