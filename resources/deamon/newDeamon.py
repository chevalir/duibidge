#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import serial
import time
import os
import optparse
import sys
import logging
import xml.dom.minidom as minidom
from Queue import Queue
import threading
import paho.mqtt.client as paho
import json



__author__ = 'chevalir'
logger = logging.getLogger("duibridge")
options={}

from_node = {'init': "HELLO" }
to_node   = {"config_pin" : 'CP', 'force_refresh':"RF", 'force_reload':"RE", "print_eeprom":"TS"}

cmd_cp_default = "CPzzrtyiooizzzzbzzzzzzcccccccccccccccccccccccccccccccczzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzcccccccccccccccc"

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
      time.sleep(1)
      if not self.request_queue.empty(): 
        self.read_queue()      
      self.read_serial()

  def init_serial_com(self):
    self.SerialPort = serial.Serial(self.usb_port, self.baud, timeout=0.3, xonxoff=0, rtscts=0)
    self.SerialPort.flush()
    self.SerialPort.flushInput()
    ## hardware reset using DTR line
    self.SerialPort.setDTR(True)
    time.sleep(0.030) # Read somewhere that 22ms is what the UI does.
    self.SerialPort.setDTR(False)
    time.sleep(0.200)
    
    self.SerialPort.flush()
    self.SerialPort.flushInput()
    logger.debug("Arduino {} wainting for HELLO".format(self.ID))
    line = ""
    checktimer = 0
    while line.find(from_node['init']) < 0:
      time.sleep(1)
      checktimer += 1
      line = self.read_serial()
      
      line = line.replace('\n', '')
      line = line.replace('\r', '')
      logger.debug("0_Arduino " + str(self.ID) + " >> [" + line + "]")
      if checktimer > 15:
        logger.error("TIMEOUT d'attente du HELLO de l'arduino " + str(arduID))
        quit()
    self.SerialPort.flush()
    self.SerialPort.flushInput()
    logger.debug("Arduino " + str(self.ID) + " ready for action")
    ##open serial port @@TODO
  
  def read_serial(self):
    line = self.SerialPort.readline()
    if line != '':
      line = line.replace('\n', '')
      line = line.replace('\r', '')
      print("read_serial :"+line)
    return line
    ##print( "@@TODO read_serial"+line )

  def read_queue(self):
    task = self.request_queue.get(False)
    print( "@@TODO read_queue:"+str(task) )
    if 'CP' in task[0:2]:
      self.write_serial(bytes(task))
    self.request_queue.task_done()

  def write_serial(self, request):
    while len(request) > 0:
      self.SerialPort.write(request[:64]) ## send the first bloc 64 char    
      request = request[64:] ## remove the first bloc from the request.
      if len(request) > 0:
        time.sleep(0.1) ## delay before next bloc (if any)
      else :
        self.SerialPort.write('\n') ## all blocs sent, now send terminator
    print( "write_serial end")


''' -----------------------------------------
'''
class MQTT_Client(paho.Client):
    
  def on_connect(self, mqttc, obj, flags, rc):
    print("on_connect rc: "+str(rc))

  def on_message(self, mqttc, obj, msg):
    print("on_message topic:{} Qos:{} msg:{}".format( msg.topic, msg.qos, msg.payload))
    self.queue.put(str(msg.payload))

  def on_publish(self, mqttc, obj, mid):
    print("on_publish mid: "+str(mid))

  def on_subscribe(self, mqttc, obj, mid, granted_qos):
    print("on_subscribe: "+str(mid)+" "+str(granted_qos))

  def on_log(self, mqttc, obj, level, string):
    ##print(string)
    return

  def run(self, broker, sub_topic, qq):
    self.disable_logger()
    self.queue = qq
    self.connect(broker, 1883, 60)
    self.subscribe( sub_topic+"/#", 0)
    rc = 0
    while rc == 0:
      rc = self.loop_start()
    return rc



''' -----------------------------------------
'''
class Arduino_Config(object):

  ''' ...............................................'''
  def __init__(self, conf_file_path):
    self.conf_file_path=conf_file_path
    self.ArduinoStekchVersion = "0.0.0"
    self.ArduinoQty = 0
    self.Arduino_ports = {}
    self.pid_file =""

  ''' ...............................................'''
  def load_node_config(self):
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
class Pin_Config(object):

  def __init__(self, conf_file_path, conf_save_path=None):
    self.conf_file_path=conf_file_path
    if conf_save_path==None:
      self.conf_save_path=conf_file_path
    else:
      self.conf_save_path=conf_save_path

    self.digital_pins = {}
    self.analog_pins = {}
    self.custom_vpins = {}
    self.r_radio_vpins = {}
    self.t_radio_vpins = {}
    self.transmeter_pin = -1
    self.rootNode=''
    self.DPIN=14  #default value
    self.APIN=6   #default value
    self.CPIN=32  #default value
    self.decode={}
    self.cp_list = []

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
    for dp in range(self.DPIN + self.APIN + self.CPIN):
      self.cp_list.append('z') 
    self.decode_digital()
    self.decode_ana()
    self.decode_custom()
    self.decode_radio()

  ''' --------------------- '''
  def decode_digital(self):
    pins = self.decode['digitals']['dpins']
    pin_tag = 'card_pin'
    for pinNum in range(len(pins)):
      thepin = int(str(pins[pinNum][pin_tag]).split(' ', 2)[1])
      mode = pins[pinNum]['mode'].split(";",1)[0]
      topic = pins[pinNum]['topic']
      prefix = pins[pinNum]['prefix']
      if mode=='t':
        self.transmeter_pin = thepin
      full_topic = self.get_topic_prefix(mode, prefix)+topic
      self.digital_pins[thepin] = (mode, full_topic)
      self.cp_list[thepin]=mode
      # @TODO manage output pin ( subscrib to topic )
  
  def decode_custom(self):
    pins = self.decode['custom']['cpins']
    pin_tag = 'custom_pin'
    for pinNum in range(len(pins)):
      thepin = int(pins[pinNum][pin_tag])
      mode = pins[pinNum]['mode'].split(";",1)[0]
      topic = pins[pinNum]['topic']
      prefix = pins[pinNum]['prefix']
      full_topic = self.get_topic_prefix(mode, prefix)+topic
      self.custom_vpins[self.DPIN + self.APIN + thepin] = (mode, full_topic)
      self.cp_list[self.DPIN + self.APIN + thepin]=mode
    logger.debug(self.custom_vpins)

  def decode_ana(self):
    pins = self.decode['analog']['apins']
    pin_tag = 'card_pin'
    for pinNum in range(len(pins)):
      thepin = int(str(pins[pinNum][pin_tag]).split(' ', 2)[1])
      mode = pins[pinNum]['mode'].split(";",1)[0]
      topic = pins[pinNum]['topic']
      prefix = pins[pinNum]['prefix']
      full_topic = self.get_topic_prefix(mode, prefix)+topic
      self.analog_pins[self.DPIN + thepin] = (mode, full_topic)
      self.cp_list[self.DPIN + thepin]=mode
      # @TODO manage output pin ( subscrib to topic )

  def decode_radio(self):
    pins = self.decode['radio']['cradio']
    pin_tag = 'typeradio'
    for pinNum in range(len(pins)):
      prefix_topic=''
      typeradio = pins[pinNum][pin_tag].split(";",1)[0]
      mode = pins[pinNum]['mode'].split(";",1)[0]
      topic = pins[pinNum]['topic']
      device = pins[pinNum]['device']
      prefix = pins[pinNum]['prefix']
      '''if len(device) < 2:
        device = "0"+device '''
      # @TODO change device format
      radiocode = pins[pinNum]['radiocode']
  
      if mode in ['r', 'tr']: 
        status_topic = self.get_topic_prefix('r', prefix)+topic
        radiocode_key = '{}#{:0>2}'.format(pins[pinNum]['radiocode'], device)
        self.r_radio_vpins.update({radiocode_key:(device, status_topic)})
  
      if mode in ['t', 'tr']:
        action_topic = self.get_topic_prefix('t', prefix)+topic
        self.t_radio_vpins.update({action_topic:(device, radiocode)})
        ## @TODO ???  options.comJeedom.subscribe_topic( action_topic )
    #logger.debug(self.r_radio_vpins)
    #logger.debug(self.t_radio_vpins)

  def add_radio_conf(self, radiocode, device, radiocode_key):
    status_topic='radio/'+radiocode+"/"+str(device)
    self.decode['radio']['cradio'].append({'typeradio': 'H; Chacon DIO', 'radiocode': radiocode, 'topic': status_topic
      , 'prefix': True, 'mode' : 'tr; Trans./Recep.', 'device': device})
    with open(self.conf_save_path, 'w') as outfile:
      json.dump(self.decode, outfile, sort_keys = True, indent = 2)
    status_topic=self.get_topic_prefix('r', True)+status_topic
    logger.info(" new topic added " + status_topic)
    self.r_radio_vpins.update({radiocode_key:(device, status_topic)})

  def get_topic_prefix(self, mode, enable):
    global options
    if enable:
      if mode in ['r', 'c', 'a', 'y','i','j', range(1,8)]: 
        return(self.rootNode+"/"+'status/') 
      else:
        return(self.rootNode+"/"+'action/')
    else:
       return(self.rootNode+"/")

  def get_pin_conf_cmd(self):
    cp = 'CP' + ''.join(self.cp_list)
    return cp



'''
2019-02-27 07:10:39,851 | DEBUG | Thread-2 - arduidomx:248 - p1_Arduino 1 >> [DBG_todo:
CPzzrtyiooizzzzbzzzazzcccccccccccccccccccccccccccccccczzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzcccccccccccccccc]
CPzzrtyiooizzzzbzzzazzcccczzccccccczzzzzzzczzzzccccccc

[
CPzzrtyiooizzzzb
A:
zzzzzz
C:
cccccccccccccccccccccccccccccccc
O:
zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
DTH:
cccccccccccccccc]
'''






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
  options.Ardno_conf.load_node_config()

  options.pin_config = Pin_Config(options.config_folder)
  options.pin_config.load_config()
  
  options.nodes={}
  arduino_id = options.pin_config.rootNode ## TODO manage several arduino
  options.arduino_queues={arduino_id:Queue()}
  aNode = Arduino_Node(options.Ardno_conf.Arduino_ports[1], options.arduino_queues[arduino_id], arduino_id)
  options.nodes.update({arduino_id:aNode})
  mqttc1 = MQTT_Client()
  rc = mqttc1.run("localhost", arduino_id, options.arduino_queues[arduino_id])
  cp_cmd =options.pin_config.get_pin_conf_cmd()
  ## print ( cp_cmd )
  options.arduino_queues[arduino_id].put(cp_cmd)
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
