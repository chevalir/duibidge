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
On_Off = ['0','1'] ## value used to transmit radio remote button status 
from_node = {'init': "HELLO" }
to_node   = {"config_pin" : 'CP', 'force_refresh':"RF", 'force_reload':"RE", "print_eeprom":"TS"}

##  DBG_todo:SP130001     SP130001_OK
##  DBG_todo:SP130001    'SP130001'   'SP{:02}{:04}'.format(13,1)

def format_chacon(t_pin, radiocode, group, action, device):
  ## example : SP03 H 12802190 0 100
  ## example : SP:3,H,12802190,0,100

  cmd = "SP{:0>2}H{}{}{}{:0>2}".format(t_pin, radiocode, group, action, device )
  return cmd 


def build_command(arduino_id, topic, value):
  pconfig = options.pin_config[arduino_id]
  try:
    pin_num = pconfig.all_topics[topic]
    if pin_num == pconfig.transmeter_pin:
      (device, radiocode) = pconfig.t_radio_vpins[topic]
      cmd = format_chacon( pconfig.transmeter_pin, radiocode, 0, value, device-1) ## "SP03H128021900100"
      ## "?>>RFD:"+radiocode+":A:"+value*100+device-1":P:4<<"
      request = Arduino_Request(cmd, cmd+"_OK", {"message":"RFD", "radiocode":radiocode, "action":int(value)==1, "device":(device)} )
      ##"?>>RFD:{}:A:{}:P:4<<".format(radiocode, int(value)*100+device-1))
    else:
      pin_info = pconfig.all_pins[pin_num]
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
    if topic in pconfig.all_topics.keys():
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
  def __init__(self, port, in_queue, arduino_id, out_queue, mqtt):
    self.usb_port=port
    self.request_queue=in_queue
    self.send_queue=out_queue
    self.ID = arduino_id
    self.baud=115200
    self.current_request=None
    self.mqtt=mqtt
    ''' Open tread to listen arduino serial port'''
    thread = threading.Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    '''Method that runs forever'''
    logger.debug( "Arduino_Node::RUN" )
    self.init_serial_com()
    '''start with an empty request in state: done'''
    self.current_request=Arduino_Request("","")
    self.current_request.received("")
    while True:
      time.sleep(0.1)
      ''' waitting the end of the current request'''
      if self.current_request.done(): 
        '''check if a cmd need to be sent to arduino'''
        if not self.request_queue.empty(): 
          self.read_queue()
      ''' check if the arduino have something for us.'''    
      line = self.read_serial() 
      if line != "" and not ( "DBG" in line ):
        if not self.current_request.done() and self.current_request.is_expected(line):
          self.current_request.received(line)
          if not (self.current_request.return_mess==None): 
            ''' automatic status sent to mqtt '''
            send_radio_to_topic(self.ID, self.mqtt, 
              self.current_request.return_mess["message"], 
              self.current_request.return_mess["radiocode"], 
              self.current_request.return_mess["device"], 
              self.current_request.return_mess["action"]) 
        else: 
          ''' No task in progress or not expected answer 
              so it's e new value of pin sent by the arduino 
          '''
          self.send_queue.put(line) 
          logger.debug( "sent to queue")
        
  def reset_with_DTR(self):
    self.SerialPort.flush()
    self.SerialPort.flushInput()
    ''' hardware reset using DTR line'''
    self.SerialPort.setDTR(True)
    time.sleep(0.030) 
    ''' Read somewhere that 22ms is what the UI does.'''
    self.SerialPort.setDTR(False)
    time.sleep(0.200)
    self.SerialPort.flush()
    self.SerialPort.flushInput()
  
  def init_arduidom_bridge(self):
    logger.debug("Arduino_Node::init_arduidom_bridge")

  def init_serial_com(self):
    logger.debug("Arduino {} waiting for HELLO".format(self.ID))
    self.SerialPort = serial.Serial(self.usb_port, self.baud, timeout=0.3, xonxoff=0, rtscts=0)
    self.reset_with_DTR()
    line = ""
    checktimer = 0
    while line.find(from_node['init']) < 0:
      time.sleep(2)
      checktimer += 1
      line = self.read_serial()
      line = line.replace('\n', '')
      line = line.replace('\r', '')
      logger.debug("received from Arduino " + str(self.ID) + " >> [" + line + "]")
      if checktimer in [3,6,9,12]:
        self.reset_with_DTR()
      if checktimer > 15:
        logger.error("TIMEOUT d'attente du HELLO de l'arduino " + str(self.ID))
        quit()
    self.SerialPort.flush()
    self.SerialPort.flushInput()
    logger.debug("Arduino " + str(self.ID) + " ready for action")
  
  def read_serial(self):
    line = self.SerialPort.readline()
    if line != '':
      line = line.replace('\n', '')
      line = line.replace('\r', '')
      logger.debug("read_serial:"+line)
    return line

  def read_queue(self):
    self.current_request = self.request_queue.get(False)
    logger.debug( "read_queue:"+str(self.current_request.request) )
    self.current_request.start()
    if self.current_request.request[0:2] in ['CP', 'SP']:
      self.write_serial(bytes(self.current_request.request))
    else :
      '''to force close the request'''
      self.current_request.received("") 
    self.request_queue.task_done()

  def write_serial(self, cmd): 
    while len(cmd) > 0:
      ''' send the first bloc 64 char    '''
      ''' and remove it from the request.'''
      self.SerialPort.write(cmd[:64]) 
      cmd = cmd[64:] 
      if len(cmd) > 0:
        ''' delay before next bloc (if any)'''
        time.sleep(0.1) 
      else :
        ''' all blocs sent, now send terminator'''
        self.SerialPort.write('\n') 
    logger.debug( "write_serial end")

''' -----------------------------------------
'''
class Arduidom_node(Arduino_Node):
  def __init__(self, port, in_queue, arduino_id, out_queue, jeedom_mqtt, arduidom_in_queue, arduidom_mqtt):
    self.arduidom_in_queue = arduidom_in_queue
    self.arduidom_mqtt = arduidom_mqtt
    Arduino_Node.__init__(self, port, in_queue, arduino_id, out_queue, jeedom_mqtt)

  def init_serial_com(self):
    self.SerialPort = None
    logger.debug( "Arduidom_node write_serial end")
    return None
  
  def write_serial(self, cmd):
    logger.debug( "Arduidom_node write_serial end:"+cmd)
    ''' in bridge mode the delay is longer than in direct mode so the timeout delay is increased ''' 
    self.current_request.timeout = self.current_request.timeout * 3 
    self.arduidom_mqtt.publish_to_arduidom(cmd)
    return None
  
  def read_serial(self):
    ##logger.debug( "Arduidom_node write_serial end")
    line =""
    if not self.arduidom_in_queue.empty():
      line = self.arduidom_in_queue.get(False)
    return line

''' -----------------------------------------
'''
class Arduino_Request:
  def __init__(self, request, expected_answer, return_value=None):
    self.request = request
    self.answer = ""
    '''status possible values: INIT|STARTED|OK|KO '''
    self.status = "INIT"  
    self.timeout = 10
    self.expected = expected_answer
    self.return_mess = return_value
    self.start_time = 0

  def start(self):
    self.start_time = int(time.time())
    self.status = "STARTED"
    return self.request

  def check_status(self):
    ##logger.debug("Arduino_Request start:{} timeout:{} time{}".format(self.start_time, self.timeout, time.time()))
    if (self.status == "STARTED") and (int(time.time()) - self.start_time) >= self.timeout:
      logger.debug("Arduino_Request:{} start:{} timeout:{} time:{}".format(self.request, self.start_time, self.timeout, time.time()))
      self.received("TIMEOUT")
    return self.status

  def done(self):
    return self.status == "OK" or self.check_status() == "KO"

  def is_expected(self, answer):
    if answer == self.expected:
      self.answer = answer
      self.status = "OK"
      return True
    else:
      return False
  
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
    #logger.debug("on_message topic:{} Qos:{} msg:{}".format( msg.topic, msg.qos, msg.payload))
    self.queue_out.put(build_command(self.arduino_id, msg.topic, msg.payload ))

  def on_publish(self, mqttc, obj, mid):
    ##print("on_publish mid: "+str(obj))
    return

  def on_subscribe(self, mqttc, obj, mid, granted_qos):
    ##print("on_subscribe: "+str(mid)+" "+str(granted_qos))
    return

  def on_log(self, mqttc, obj, level, string):
    ##print(string)
    return

  def publish_message(self, sub_topic , mess ):
    self.publish( sub_topic, mess )

  def subscribe_topics(self, list_of_topic):
    for topic in list_of_topic:
      self.subscribe(topic,0)
      logger.debug("MQTT_Client::subscribe_topic :"+str(topic))

  def run(self, arduino_id, broker, queue_out):
    self.arduino_id = arduino_id
    self.disable_logger()
    self.queue_out = queue_out
    self.connect(broker, 1883, 60)
    rc = 0
    while rc == 0:
      rc = self.loop_start()
    return rc

class MQTT_Arduidom(MQTT_Client):
  def on_message(self, mqttc, obj, msg):
    logger.debug("MQTT_Arduidom::on_message topic:{} Qos:{} msg:{}".format( msg.topic, msg.qos, msg.payload))
    self.queue_out.put(msg.payload)
  
  def set_topic(self, to_arduidom, from_arduidom):
    self.to_arduidom = to_arduidom
    self.subscribe(from_arduidom)
  
  def publish_to_arduidom(self, msg):
    self.publish_message(self.to_arduidom, msg)

''' -----------------------------------------
'''
class Pin_def:
  digital=1
  analog=2
  custom=3
  radio=4
  dht=5
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

  def __init__(self, ID, conf_pins_path, conf_ports_path, conf_save_path=None):
    self.id = ID
    self.conf_pins_path=conf_pins_path
    self.conf_ports_path=conf_ports_path
    self.conf_pins_modif_time=None
    if conf_save_path==None:
      self.conf_save_path=conf_pins_path
    else:
      self.conf_save_path=conf_save_path

    self.r_radio_vpins = {}
    self.t_radio_vpins = {}
    self.all_pins = {}
    self.all_topics = {}
    self.transmeter_pin = -1
    self.rootNode=''
    '''Default pin number of Arduino UNO'''
    self.DPIN=14
    self.APIN=6
    self.CPIN=32
    self.pins_decode=None
    ''' use to send CP command to arduino CPzzrtyiooizzzzbzzzazzcccczzccccccczzzzzzzczzzzccccccc'''
    self.cp_command = []  
    self.port=None

  def load_port_config(self, ports_decode=None):
    try:
      if ports_decode == None:
        logger.debug(self.conf_ports_path + " to load ")
        '''Get a file object with write permission.'''
        ## self.conf_pins_modif_time = os.path.getmtime(self.conf_ports_path)
        file_object = open(self.conf_ports_path, 'r')
        logger.debug(self.conf_ports_path + " loaded ") 
        '''Load JSON file data to a python dict object.'''
        ports_decode = json.load(file_object)
        file_object.close()
      self.port = ports_decode["{}_serial_port".format(self.id)]
    except Exception as e:
      print(e)
      return None
    return 

  def load_pin_config(self, all_pins_decode=None):
    try:
      if all_pins_decode == None:
        logger.debug(self.conf_pins_path + " to load ")
        '''Get a file object with write permission.'''
        file_object = open(self.conf_pins_path, 'r')
        logger.debug(self.conf_pins_path + " loaded ") 
        '''Load JSON file data to a python dict object.'''
        all_pins_decode = json.load(file_object)
        file_object.close()
    except Exception as e:
      print(e)
      return
    if type(all_pins_decode) == list:
      for i in range(len(all_pins_decode)):
        if all_pins_decode[i]['identifier'] == self.id:
          self.pins_decode = all_pins_decode[i]
    else :
      self.pins_decode = all_pins_decode
    if not self.pins_decode == None:
      self.rootNode = str(self.pins_decode['name'])
      cardType = self.pins_decode['card']
      if cardType.find('UNO'):
        self.DPIN=14
        self.APIN=6
        self.CPIN=32
      for dp in range(self.DPIN + self.APIN + self.CPIN):
        self.cp_command.append('z') 
      self.decode_digital()
      self.decode_ana()
      self.decode_custom()
      self.decode_radio()
      self.decode_dht()
    return all_pins_decode

  def reload_pin_config(self, all_pins_decode=None):
    self.r_radio_vpins = {}
    self.t_radio_vpins = {}
    self.all_pins = {}
    self.all_topics = {}
    self.transmeter_pin = -1
    self.rootNode=''
    self.cp_command = []
    self.load_pin_config(all_pins_decode)

  def decode_digital(self):
    try:
      pins = self.pins_decode['digitals']['dpins']
      pin_tag = 'card_pin'
      pin_offset = 0
      for pinNum in range(len(pins)):
        thepin = int(str(pins[pinNum][pin_tag]).split(' ', 2)[1])
        mode = pins[pinNum]['mode'].split(";",1)[0]
        topic = pins[pinNum]['topic']
        prefix = pins[pinNum]['prefix']
        if mode=='t':
          self.transmeter_pin = thepin
        full_topic = self.get_topic_prefix(mode, prefix)+topic
        pin_index = pin_offset + thepin
        self.all_pins[pin_index] = Pin_def(topic=full_topic, mode=mode, type=Pin_def.digital)
        self.all_topics[full_topic]=pin_index
        self.cp_command[pin_index]=mode
      pass
    except:
      logger.info("No digitals config")
      pass
 
  def decode_ana(self):
    try:
      pins = self.pins_decode['analog']['apins']
      pin_tag = 'card_pin'
      pin_offset = self.DPIN
      for pinNum in range(len(pins)):
        thepin = int(str(pins[pinNum][pin_tag]).split(' ', 2)[1])
        mode = pins[pinNum]['mode'].split(";",1)[0]
        topic = pins[pinNum]['topic']
        prefix = pins[pinNum]['prefix']
        full_topic = self.get_topic_prefix(mode, prefix)+topic
        pin_index = pin_offset + thepin
        self.all_pins[pin_index] = Pin_def(topic=full_topic, mode=mode, type=Pin_def.analog)
        self.all_topics[full_topic]=pin_index
        self.cp_command[pin_index]=mode
    ##logger.debug(self.custom_vpins)
      pass
    except:
      logger.info("No analog config")
      pass

  def decode_custom(self):
    try:
      pins = self.pins_decode['custom']['cpins']
      pin_tag = 'custom_pin'
      pin_offset = self.DPIN + self.APIN
      for pinNum in range(len(pins)):
        thepin = int(pins[pinNum][pin_tag])
        mode = pins[pinNum]['mode'].split(";",1)[0]
        topic = pins[pinNum]['topic']
        prefix = pins[pinNum]['prefix']
        full_topic = self.get_topic_prefix(mode, prefix)+topic
        pin_index = pin_offset + thepin
        self.all_pins[pin_index] = Pin_def(topic=full_topic, mode=mode, type=Pin_def.custom)
        self.all_topics[full_topic]=pin_index
        self.cp_command[pin_index]=mode
    ##logger.debug(self.custom_vpins)
      pass
    except:
      logger.info("No custom config")
      pass

  def decode_dht(self):
    logger.debug("decode_dht oups")
    try:
      pins = self.pins_decode['dht']['dhtpins']
      
      pin_tag = 'dht_pin'
      pin_offset = 500
      for pinNum in range(len(pins)):
        str_split = pins[pinNum][pin_tag].split(' ', 3)[1]
        thepin = int( str_split[:-1] )
        if str_split[-1:] == 'T':
          thepin += 1
        mode = pins[pinNum]['mode'].split(";",1)[0]
        topic = pins[pinNum]['topic']
        prefix = pins[pinNum]['prefix']
        full_topic = self.get_topic_prefix(mode, prefix)+topic
        pin_index = pin_offset + thepin
        self.all_pins[pin_index] = Pin_def(topic=full_topic, mode=mode, type=Pin_def.dht)
        self.all_topics[full_topic]=pin_index
      pass
    except:
      logger.info("No dht config")
      pass
      ##logger.debug(self.all_pins)

  def decode_radio(self):
    try:
      pins = self.pins_decode['radio']['cradio']
      for pinNum in range(len(pins)):
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
      pass
    except:
      logger.info("No radio config")
      pass


  def add_radio_conf(self, radiocode, device, radiocode_key):
    ''' This function is able to add radio configuration line in configuration file
        when it's done it's possible to change the default topic by the true one directly 
        in the configuration editor
    '''
    status_topic='radio/'+radiocode+"/"+str(device)
    self.pins_decode['radio']['cradio'].append({'typeradio': 'H; Chacon DIO', 'radiocode': radiocode, 'topic': status_topic
      , 'prefix': True, 'mode' : 'tr; Trans./Recep.', 'device': device})
    with open(self.conf_save_path, 'w') as outfile:
      json.dump(self.pins_decode, outfile, sort_keys = True, indent = 2)
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
    cp = 'CP' + ''.join(self.cp_command)
    return cp


'''-------------------------------'''                      
def send_to_topic(arduino_id, pin_num, value, lmqtt):
  global options

  pconfig = options.pin_config[arduino_id]
  logger.debug( str(arduino_id) + " "+str(pin_num) +" "+ str(value) )
  thePin = int(pin_num)
  try:
    if thePin in pconfig.all_pins.keys():
      pin_info = pconfig.all_pins[thePin]
      if pin_info.mode in Pin_def.mode_status :
        ''' check if the pin is the Radio receptor'''
        if pin_info.mode in ('r'): 
          send_radio_to_topic(arduino_id, lmqtt, value)
        else:     
          lmqtt.publish_message(pin_info.topic, value)    
      else:
        logger.error( 'unexpected mode:'+pin_info.mode )
    else :
      logger.info("arduino send value for Pin undefine in conf pin:{} value:{}".format(pin_num,value) )
  except KeyError:
    logger.error( "KeyError not found {} in {}".format(pin_num,  str(pconfig.all_pins.keys())))
  
'''-------------------------------'''                      
def send_radio_to_topic(arduino_id, mqtt, value, radiocode=None, device=None, device_on=None):
  global options

  pconfig = options.pin_config[arduino_id]
  logger.debug("send_radio_to_topic : {} {}".format(value, radiocode))
  if "RFD" in value:
    try:
      if radiocode==None or device==None or device_on==None:
        device_split = value.split(':')
        radiocode = device_split[1]
        device = int (device_split[3]) + 1
        device_on = device > 99
        if device_on :
          device = device - 100
      state = On_Off[int(device_on)]
      ''' search if a topic is define for this device'''
      radiocode_key = '{}#{:0>2}'.format(radiocode, device) 
      if radiocode_key not in pconfig.r_radio_vpins: 
        radiocode_key = '{}#{:0>2}'.format(radiocode, 0) 
        ''' search if a topic is define for all devices of this radiocode'''
        if radiocode_key not in pconfig.r_radio_vpins:
          logger.info("radio code={0} device ={1} not define in config ".format(radiocode, device) )
          ''' when the radiocode if not found in the config it is added in config file with default values '''
          pconfig.add_radio_conf(radiocode, device, radiocode_key)
          state = "{0}={1}".format(device, state)
      (device, topic) = pconfig.r_radio_vpins.get(radiocode_key)
      logger.info("radio code={0} device ={1} topic {2} value: {3} ".format(radiocode_key, device, topic, state) )
      mqtt.publish_message(topic, state)
    except Exception as e:
      logger.error( "send_radio_to_topic exception" )
      logger.error( e )
  return

class Arduidom_bridge():
  def __init__(self, bridgeID, sbNode, source, messageFunc):
    self.base_topic ="duitest/"+sbNode+"/" ##
    ##mqtt_bridge("abridgeID", "abridge", "arduino", on_arduino_message )
    self.pub_topic = self.base_topic+"to"+source
    self.sub_topic = self.base_topic+"from"+source


'''-------------------------------
///            MAIN            /// 
-------------------------------'''  
def main(argv=None):
  global stopMe, options
  myrootpath = os.path.dirname(os.path.realpath(__file__)) + "/"
  print ( "START DEAMON" )
  (options, args) = cli_parser(argv)
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

  sys.stderr = open(LOG_FILENAME + "_stderr", 'a', 1)

  options.loglevel.upper()
  logger.setLevel(logging.getLevelName(options.loglevel.upper()))

  logger.info("# duiBridged - duinode bridge for Jeedom # loglevel="+options.loglevel)
  
  options.pin_config={}
  all_pins_decode=None
  ##arduino_id="A1"
  conf_pins_modif_time = os.stat(options.config_pins_path).st_mtime

  logger.info("Config last modif time"+str(conf_pins_modif_time))
  for arduino_num in range (1,2):
    arduino_id = "A"+str(arduino_num)
    options.pin_config.update({arduino_id:Pin_Config(arduino_id, options.config_pins_path, options.config_ports_path)})
    pins_decode = options.pin_config[arduino_id].load_pin_config(all_pins_decode)
    if not pins_decode==None:
      ''' config found for this Arduino, json array saved for the next round '''
      all_pins_decode = pins_decode

      ''' hope that the port is also defined '''
      options.pin_config[arduino_id].load_port_config() 
      options.nodes={}
      ### rootNode = options.pin_config[arduino_id].rootNode ## TODO manage several arduino
      options.to_arduino_queues={arduino_id:Queue()}
      options.from_arduino_queues={arduino_id:Queue()}

      mqttc1 = MQTT_Client()
      mqttc1.run(arduino_id, "localhost", options.to_arduino_queues[arduino_id])
      
      if options.pin_config[arduino_id].port == "bridge":
        arduidom_mqtt = MQTT_Arduidom()
        arduidom_queue = Queue()
        arduidom_mqtt.run(arduino_id, "localhost", arduidom_queue)

        aNode = Arduidom_node(options.pin_config[arduino_id].port, options.to_arduino_queues[arduino_id], arduino_id, 
          options.from_arduino_queues[arduino_id], mqttc1, arduidom_queue, arduidom_mqtt)
        arduidom_mqtt.set_topic("duitest/abridge/toarduino", "duitest/abridge/fromarduino")
        cp_cmd=None
      else:
        aNode = Arduino_Node(options.pin_config[arduino_id].port, options.to_arduino_queues[arduino_id], 
          arduino_id, options.from_arduino_queues[arduino_id], mqttc1)
        cp_cmd =options.pin_config[arduino_id].get_pin_conf_cmd()

      options.nodes.update({arduino_id:aNode})
      if not cp_cmd == None:
        request = Arduino_Request(cp_cmd, "CP_OK")
        options.to_arduino_queues[arduino_id].put(request)
      ## subscribe to digital topics if any

      pin_list = options.pin_config[arduino_id].all_pins.values()
      for pin in pin_list:
        ##(mode, topic) = m_t
        if not ( pin.mode in Pin_def.mode_status ):
          mqttc1.subscribe(pin.topic)
          ##logger.debug('subscribe :'+pin.topic)
        ##else:
          ##logger.debug('not subscribe {} {}:'.format(pin.mode, pin.topic))
      ''' subscribe to radio topics '''
      topics = options.pin_config[arduino_id].t_radio_vpins.keys()
      mqttc1.subscribe_topics(topics)
    else :
      logger.info("config not found for "+arduino_id)
  count=0
  while True :
    time.sleep(0.1)
    count+=1
    if not options.from_arduino_queues[arduino_id].empty(): 
      mess = str(options.from_arduino_queues[arduino_id].get(False))
      logger.debug( "from_arduino_queues:"+mess )
      if '>>' in mess[:6]:
        (pin, value) = mess.split(">>")
        value = value.replace("<<", '')
        if value[-3:] == '.00':
          value = value[:(len(value)-3)]
        logger.debug(str(pin) +" "+ str(value))
        send_to_topic(arduino_id, pin, value, mqttc1)
      elif 'DHT' in mess[:6]:
        ''' Manage DHT Values '''
        line = mess[4:-1] ### remove DHT: in begining and the last ;
        dht_values = line.split(';')
        for pinnumber in range(0, len(dht_values)):
          if "na" not in dht_values[pinnumber]:
            logger.debug("DHT: {} = {}".format(501+pinnumber, dht_values[pinnumber]))
            send_to_topic(arduino_id, 501+pinnumber, dht_values[pinnumber], mqttc1)

      options.from_arduino_queues[arduino_id].task_done()
    else:
      if count > 20:
        count = 0
        new_conf_pins_modif_time = os.stat(options.config_pins_path).st_mtime
        if ( new_conf_pins_modif_time != conf_pins_modif_time):
          conf_pins_modif_time=new_conf_pins_modif_time
          logger.info(" Config pins changed")
          all_pins_decode=None
          for arduino_num in range (1,2):
            arduino_id = "A"+str(arduino_num)
            ##options.pin_config.update({arduino_id:Pin_Config(arduino_id, options.config_pins_path, options.config_ports_path)})
            pins_decode = options.pin_config[arduino_id].reload_pin_config(all_pins_decode)
            if not pins_decode==None:
              ''' config found for this Arduino, json array saved for the next round '''
              all_pins_decode = pins_decode
          logger.info(" Config pins reloaded ")

  logger.info("THE END")


'''-------------------------------'''
def write_pid(path):
	pid = str(os.getpid())
	logging.info("Writing PID " + pid + " to " + str(path))
	file(str(path), 'w').write("%s\n" % pid)

'''-------------------------------'''
def cli_parser(argv=None):
  parser = optparse.OptionParser("usage: %prog -h   pour l'aide")
  parser.add_option("-l", "--loglevel", dest="loglevel", default="INFO", type="string", help="Log Level (INFO, DEBUG, ERROR")
  ##parser.add_option("-p", "--usb_port", dest="usb_port", default="auto", type="string", help="USB Port (Auto, <Usb port> ")
  parser.add_option("-c", "--config_pins_path", dest="config_pins_path", default=".", type="string", help="config pin file path")
  parser.add_option("-p", "--config_ports_path", dest="config_ports_path", default=".", type="string", help="config ports file path")
  parser.add_option("-i", "--pid", dest="pid_path", default="./duibridge.pid", type="string", help="pid file path")
  return parser.parse_args(argv)

if __name__ == '__main__':
  main()
