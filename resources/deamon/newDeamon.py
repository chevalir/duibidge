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
On_Off = ['Off','On']
from_node = {'init': "HELLO" }
to_node   = {"config_pin" : 'CP', 'force_refresh':"RF", 'force_reload':"RE", "print_eeprom":"TS"}
cmd_cp_default = "CPzzrtyiooizzzozzzzzzzcccccccccccccccccccccccccccccccczzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzcccccccccccccccc"

##  DBG_todo:SP130001     SP130001_OK
##  DBG_todo:SP130001    'SP130001'   'SP{:02}{:04}'.format(13,1)

def format_chacon(t_pin, radiocode, group, action, device):
  ## example : SP03 H 12802190 0 100
  cmd = "SP{:0>2}H{}{}{}{:0>2}".format(t_pin, radiocode, group, action, device )
  return cmd 

## @TODO  manage SP03H128021900000_OK to post status to topic 
def decode_chacon(radio_message): ## TODO to return directly the satus to Jeedom
  return


def build_command(topic, value):
  try:
    pin_num = options.pin_config.all_topics[topic]
    if pin_num == options.pin_config.transmeter_pin:
      (device, radiocode) = options.pin_config.t_radio_vpins[topic]
      cmd = format_chacon( options.pin_config.transmeter_pin, radiocode, 0, value, device-1) ## "SP03H128021900100"
      ## @TODO send "?>>RFD:"+radiocode+":A:"+value*100+device-1":P:4<<"
      request = Arduino_Request(cmd, cmd+"_OK", "?>>RFD:{}:A:{}:P:4<<".format(radiocode, int(value)*100+device-1))
    else:
      pin_info = options.pin_config.all_pins[pin_num]
      if pin_info.mode in Pin_def.mode_out_time:
        cmd = "SP{:0>2}{:0>4}".format(pin_num,value)
      if pin_info.mode in Pin_def.mode_out:
        cmd = "SP{:0>2}{}".format(pin_num,value)
      if pin_info.mode in Pin_def.mode_pwm:
        cmd = "SP{:0>2}{:0>3}".format(pin_num,value)
      if pin_info.mode in Pin_def.mode_custom_out:
        cmd = "SP{:0>2}{:0>10}".format(pin_num,value)
      request = Arduino_Request(cmd, cmd+"_OK")
    pass
  except:
    if topic in options.pin_config.all_topics.keys():
      logger.debug("topic  found "+topic)
    else:
      logger.debug("topic not found "+topic)
    request = Arduino_Request(str(value), str(value)+"_OK")    
    pass
  finally:
    logger.debug("build_command cmd="+request.request)
    pass

  logger.debug("build_command topic: {} value: {} cmd: {}".format(topic, value, request.request))
  return request ## replace by { command:cmd, answer:cmd+"_OK"}

''' -----------------------------------------
'''
class Arduino_Node(object):
  def __init__(self, port, in_queue, arduino_id, out_queue):
    self.usb_port=port
    self.request_queue=in_queue
    self.send_queue=out_queue
    self.ID = arduino_id
    self.baud=115200
    self.last_request=None
    ## Open tread to listen arduino serial port
    thread = threading.Thread(target=self.run, args=())
    thread.daemon = True    # Daemonize thread
    thread.start()          # Start the execution

  def run(self):
    '''Method that runs forever'''
    logger.debug( "Arduino_Node::RUN" )
    self.init_serial_com()
    while True:
      time.sleep(1)
      if self.last_request==None or self.last_request.done():
        if not self.request_queue.empty(): ## check if a cmd need to be sent to arduino
          self.read_queue()
      line = self.read_serial() ## check if the arduino have sothing for us.
      if line != "" and not ( "DBG" in line ):
        self.send_queue.put(line) ## sent to the main thread
      ## @TODO Manage expected answer
        
  def reset_with_DTR(self):
    self.SerialPort.flush()
    self.SerialPort.flushInput()
    ## hardware reset using DTR line
    self.SerialPort.setDTR(True)
    time.sleep(0.030) # Read somewhere that 22ms is what the UI does.
    self.SerialPort.setDTR(False)
    time.sleep(0.200)
    self.SerialPort.flush()
    self.SerialPort.flushInput()

  def init_serial_com(self):
    self.SerialPort = serial.Serial(self.usb_port, self.baud, timeout=0.3, xonxoff=0, rtscts=0)
    logger.debug("Arduino {} wainting for HELLO".format(self.ID))
    self.reset_with_DTR()
    line = ""
    checktimer = 0
    while line.find(from_node['init']) < 0:
      time.sleep(1)
      checktimer += 1
      line = self.read_serial()
      line = line.replace('\n', '')
      line = line.replace('\r', '')
      logger.debug("0_Arduino " + str(self.ID) + " >> [" + line + "]")
      if checktimer in [3,6,9,12]:
        self.reset_with_DTR()
      if checktimer > 15:
        logger.error("TIMEOUT d'attente du HELLO de l'arduino " + str(self.ID))
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
      logger.debug("read_serial :"+line)
    return line

  def read_queue(self):
    arduino_request = self.request_queue.get(False)
    logger.debug( "read_queue:"+str(arduino_request.request) )
    arduino_request.start()
    if arduino_request.request[0:2] in ['CP', 'SP']:
      self.write_serial(bytes(arduino_request.request))
    else :
      arduino_request.received("")
    self.request_queue.task_done()

  def write_serial(self, cmd): ## @TODO MANAGE expected answer  
    while len(cmd) > 0:
      self.SerialPort.write(cmd[:64]) ## send the first bloc 64 char    
      cmd = cmd[64:] ## remove the first bloc from the request.
      if len(cmd) > 0:
        time.sleep(0.1) ## delay before next bloc (if any)
      else :
        self.SerialPort.write('\n') ## all blocs sent, now send terminator
    logger.debug( "write_serial end")



class Arduino_Request:
  def __init__(self, request, expected_answer, return_value=None):
    self.request = request
    self.answer = ""
    self.status = "INIT"  # INIT|STARTED|OK|KO
    self.timeout = 10
    self.expected = expected_answer
    self.return_mess = return_value

  def start(self):
    self.start_time = int(time.time())
    self.status = "STARTED"
    return self.request

  def check_status(self):
    # logger.debug("IN CLASS " + str(self.start_time) + " " + str(self.timeout) + " " + str(time.time()))
    if (self.status == "STARTED") and (int(time.time()) - self.start_time) >= self.timeout:
      self.received("TIMEOUT")
    return self.status

  def done(self):
    return self.check_status() == "OK" or self.check_status() == "KO"

  def received(self, answer):
    if answer == self.expected:
      self.status = "OK"
    else:
      self.status = "KO"
    self.answer = answer




''' -----------------------------------------
'''
class MQTT_Client(paho.Client):
    
  def on_connect(self, mqttc, obj, flags, rc):
    logger.debug("on_connect rc: "+str(rc))

  def on_message(self, mqttc, obj, msg):
    self.queue.put(build_command( msg.topic, msg.payload ))
    logger.debug("on_message topic:{} Qos:{} msg:{}".format( msg.topic, msg.qos, msg.payload))

  def on_publish(self, mqttc, obj, mid):
    ##print("on_publish mid: "+str(obj))
    return

  def on_subscribe(self, mqttc, obj, mid, granted_qos):
    ###print("on_subscribe: "+str(mid)+" "+str(granted_qos))
    return

  def on_log(self, mqttc, obj, level, string):
    ##print(string)
    return

  def publish_message(self, sub_topic , mess ):
    self.publish( sub_topic, mess )

  def subscribe_topics(self, list_of_topic):
    ##logger.debug(list_of_topic)
    for topic in list_of_topic:
      self.subscribe(topic)

  def run(self, broker, sub_topic, qq):
    self.disable_logger()
    self.queue = qq
    self.connect(broker, 1883, 60)
    ##self.subscribe( sub_topic+"/#", 0)
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
      print "Error: Configuration file not found (" + self.conf_file_path  + ")"
      logger.error("Error: Configuration file not found (" + self.conf_file_path  + ") Line: ")
  
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
class Pin_def:
  digital=1
  analog=2
  custom=3
  mode_status=['r', 'c', 'a', 'y','i','j', range(1,8)]
  mode_out=['o', 'i', 'y' 'e'] 
  mode_out_time=[ 'x', 'v', 'u', 'b' ]
  mode_pwm=[ 'p' ]
  mode_custom_out=['d']

  def __init__(self, **kwds):
    self.__dict__.update(kwds)
  def __repr__(self):
    return str(self.__dict__)

''' -----------------------------------------
'''
class Pin_Config(object):

  def __init__(self, conf_file_path, conf_save_path=None):
    self.conf_file_path=conf_file_path
    if conf_save_path==None:
      self.conf_save_path=conf_file_path
    else:
      self.conf_save_path=conf_save_path

    self.r_radio_vpins = {}
    self.t_radio_vpins = {}
    self.all_pins = {}
    self.all_topics = {}
    self.transmeter_pin = -1
    self.rootNode=''
    self.DPIN=14  #default Digital Pin number
    self.APIN=6   #default Alalog pin number 
    self.CPIN=32  #default Custom pin number
    self.decode={}
    self.cp_list = []  # use to send CP command to arduino CPzzrtyiooizzzzbzzzazzcccczzccccccczzzzzzzczzzzccccccc

  def load_config(self, ID, alldecode=None):
    try:
      if not alldecode == None:
        self.alldecode = alldecode
      else :   
        logger.debug(self.conf_file_path + " to load ")
        # Get a file object with write permission.
        file_object = open(self.conf_file_path, 'r')
        logger.debug(self.conf_file_path + " loaded ") 
        # Load JSON file data to a python dict object.
        self.alldecode = json.load(file_object)
        file_object.close()
    except Exception as e:
      print(e)
      return
    if type(self.alldecode) == list:
      for i in range(len(self.alldecode)):
        if self.alldecode[i]['identifier'] == ID: ## seach A1, or A2, ...
          self.decode = self.alldecode[i]
    if not self.decode == None:
      self.ID = str(self.decode['identifier'])
      print(self.ID)
      self.rootNode = str(self.decode['name'])
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
      self.all_pins[thepin] = Pin_def(topic=full_topic, mode=mode, type=Pin_def.digital)
      self.all_topics[full_topic]=thepin
      self.cp_list[thepin]=mode
  
  def decode_ana(self):
    pins = self.decode['analog']['apins']
    pin_tag = 'card_pin'
    for pinNum in range(len(pins)):
      thepin = int(str(pins[pinNum][pin_tag]).split(' ', 2)[1])
      mode = pins[pinNum]['mode'].split(";",1)[0]
      topic = pins[pinNum]['topic']
      prefix = pins[pinNum]['prefix']
      full_topic = self.get_topic_prefix(mode, prefix)+topic
      self.all_pins[self.DPIN + thepin] = Pin_def(topic=full_topic, mode=mode, type=Pin_def.digital)
      self.all_topics[full_topic]=self.DPIN + thepin
      self.cp_list[self.DPIN + thepin]=mode

  def decode_custom(self):
    pins = self.decode['custom']['cpins']
    pin_tag = 'custom_pin'
    for pinNum in range(len(pins)):
      thepin = int(pins[pinNum][pin_tag])
      mode = pins[pinNum]['mode'].split(";",1)[0]
      topic = pins[pinNum]['topic']
      prefix = pins[pinNum]['prefix']
      full_topic = self.get_topic_prefix(mode, prefix)+topic
      self.all_pins[self.DPIN + self.APIN + thepin] = Pin_def(topic=full_topic, mode=mode, type=Pin_def.custom)
      self.all_topics[full_topic]=self.DPIN + self.APIN + thepin
      ### self.custom_vpins[self.DPIN + self.APIN + thepin] = (mode, full_topic)
      self.cp_list[self.DPIN + self.APIN + thepin]=mode
    ##logger.debug(self.custom_vpins)

  def decode_radio(self):
    pins = self.decode['radio']['cradio']
    ## @TODO del  pin_tag = 'typeradio'
    for pinNum in range(len(pins)):
      ## @TODO del   prefix_topic=''
      ## @TODO del   typeradio = pins[pinNum][pin_tag].split(";",1)[0]
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
        self.all_topics[action_topic]=self.transmeter_pin
        self.t_radio_vpins.update({action_topic:(device, radiocode)})

  def add_radio_conf(self, radiocode, device, radiocode_key):
    ''' This function is able to add radio configuration line in configuration file
        when it's done it's possible to change the default topic by the true one directly 
        in the configuration editor
    '''
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
      if mode in Pin_def.mode_status: 
        return(self.rootNode+"/"+'status/') 
      else:
        return(self.rootNode+"/"+'action/')
    else:
       return(self.rootNode+"/")

  def get_pin_conf_cmd(self):
    cp = 'CP' + ''.join(self.cp_list)
    return cp


'''-------------------------------'''                      
def send_to_topic(pin_num, value, lmqtt):
  global options
  logger.debug(str(pin_num) +" "+ str(value)+" "+ str(options.pin_config.DPIN))
  thePin = int(pin_num)
  try:
    if thePin in options.pin_config.all_pins.keys():
      pin_info = options.pin_config.all_pins[thePin]
      if pin_info.mode in Pin_def.mode_status :
        if pin_info.mode in ('r'): ## Radio receptor
          send_radio_to_topic(pin_info.topic, value, lmqtt)
        else:      
          lmqtt.publish_message(pin_info.topic, value)    
      else:
        logger.error( 'unexpected mode:'+pin_info.mode )
    else :
      logger.info("arduino send value for Pin undefine in conf pin:{} value:{}".format(pin_num,value) )
  except KeyError:
    logger.error( "KeyError not found {} in {}".format(pin_num,  str(options.pin_config.all_pins.keys())))
  

'''-------------------------------'''                      
def send_radio_to_topic(topic, value, mqtt):
  global options
  logger.debug("send_radio_to_topic : {} {}".format(topic, value))
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
      if radiocode_key not in options.pin_config.r_radio_vpins:
        radiocode_key = '{}#{:0>2}'.format(radiocode, 0)
        if radiocode_key not in options.pin_config.r_radio_vpins:
          logger.info("radio code={0} device ={1} not define in config ".format(radiocode, device) )
          options.pin_config.add_radio_conf(radiocode, device, radiocode_key)
          value = "{0}={1}".format(device, value)      
      (device, topic) = options.pin_config.r_radio_vpins.get(radiocode_key)
      logger.info("radio code={0} device ={1} topic {2} ".format(radiocode_key, device, topic) )
      mqtt.publish_message(topic, value)
    except Exception as e:
      logger.error( "send_radio_to_topic exception" )
      logger.error( e )
  return



'''-------------------------------
///            MAIN            /// 
-------------------------------'''  
def main(argv=None):
  global stopMe, options
  myrootpath = os.path.dirname(os.path.realpath(__file__)) + "/"
  print ( "START DEAMON " )
  (options, args) = cli_parser(argv)
  ##print(options)
  write_pid(options.pid_path)
  LOG_FILENAME = myrootpath + '../../../../log/duibridge_daemon'
  formatter = logging.Formatter('%(threadName)s-%(asctime)s| %(levelname)s | %(lineno)d | %(message)s')
  '''filehandler = logging.FileHandler(LOG_FILENAME)
  filehandler.setFormatter(formatter)
  logger.addHandler(filehandler)
  '''

  console = logging.StreamHandler()
  console.setFormatter(formatter)
  logger.addHandler(console)
  logger.setLevel(logging.DEBUG)

  ##sys.stderr = open(LOG_FILENAME + "_stderr", 'a', 1)

  # options.loglevel.upper()
  ##logger.setLevel(logging.getLevelName(options.loglevel.upper()))
  ##
  logger.info("# duiBridged - duinode bridge for Jeedom # loglevel="+options.loglevel)
  
  configFile = os.path.join(myrootpath, "config_duibridge_nodes.xml")
  logger.debug("Config file: " + configFile)
  logger.debug("Read jeedom configuration file")
  options.Ardno_conf = Arduino_Config(configFile)
  options.Ardno_conf.load_node_config()

  options.pin_config = Pin_Config(options.config_folder)
  options.pin_config.load_config("A1")
  
  options.nodes={}
  arduino_id = options.pin_config.rootNode ## TODO manage several arduino
  options.to_arduino_queues={arduino_id:Queue()}
  options.from_arduino_queues={arduino_id:Queue()}

  aNode = Arduino_Node(options.Ardno_conf.Arduino_ports[1], options.to_arduino_queues[arduino_id], arduino_id, options.from_arduino_queues[arduino_id])
  options.nodes.update({arduino_id:aNode})
  mqttc1 = MQTT_Client()
  rc = mqttc1.run("localhost", arduino_id, options.to_arduino_queues[arduino_id])
  cp_cmd =options.pin_config.get_pin_conf_cmd()
  request = Arduino_Request(cp_cmd, "CP_OK")
  options.to_arduino_queues[arduino_id].put(request)
  ## subscribe to digital topics if any
  print("----\n\n")
  pin_list = options.pin_config.all_pins.values()
  for pin in pin_list:
    ##(mode, topic) = m_t
    if not ( pin.mode in Pin_def.mode_status ):
      mqttc1.subscribe(pin.topic)
      logger.debug('subscribe :'+pin.topic)
    else:
      logger.debug('not subscribe {} {}:'.format(pin.mode, pin.topic))
  ## subscribe to radio topics
  topics = options.pin_config.t_radio_vpins.keys()
  mqttc1.subscribe_topics(topics)


  while True :
    time.sleep(0.1)
    if not options.from_arduino_queues[arduino_id].empty(): 
      mess = str(options.from_arduino_queues[arduino_id].get(False))
      logger.debug( "from_arduino_queues:"+mess )
      if '>>' in mess[:6]:
        (pin, value) = mess.split(">>")
        value = value.replace("<<", '')
        logger.debug(str(pin) +" "+ str(value))
        send_to_topic(pin, value, mqttc1)
      options.from_arduino_queues[arduino_id].task_done()

    
  logger.debug("THE END")


'''-------------------------------'''
def write_pid(path):
	pid = str(os.getpid())
	logging.info("Writing PID " + pid + " to " + str(path))
	file(str(path), 'w').write("%s\n" % pid)

'''-------------------------------'''
def cli_parser(argv=None):
  parser = optparse.OptionParser("usage: %prog -h   pour l'aide")
  parser.add_option("-l", "--loglevel", dest="loglevel", default="INFO", type="string", help="Log Level (INFO, DEBUG, ERROR")
  parser.add_option("-p", "--usb_port", dest="usb_port", default="auto", type="string", help="USB Port (Auto, <Usb port> ")
  parser.add_option("-c", "--config_folder", dest="config_folder", default=".", type="string", help="config folder path")
  parser.add_option("-i", "--pid", dest="pid_path", default="./duibridge.pid", type="string", help="pid file folder folder path")

  return parser.parse_args(argv)

if __name__ == '__main__':
  main()
