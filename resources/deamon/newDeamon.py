#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import serial
from socket import *
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
from threading import Thread

__author__ = 'chevalir'
logger = logging.getLogger("duibridge")



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
  sys.stderr = open(LOG_FILENAME + "_stderr", 'a', 1)
  # options.loglevel.upper()
  logger.setLevel(logging.getLevelName(options.loglevel.upper()))
  logger.addHandler(console)
  ##logger.addHandler(filehandler)
  logger.info("# duiBridged - duinode bridge for Jeedom # loglevel="+options.loglevel)
  
  configFile = os.path.join(myrootpath, "config_arduidom.xml")
  logger.debug("Configfile: " + configFile)
  logger.debug("Read configuration file")
  read_configFile(options, configFile)
  ##print(options)


def read_configFile(options, configFile):
  global trigger_nice
  if os.path.exists( configFile ):
    #open the xml file for reading:
    f = open( configFile,'r')
    data = f.read()
    f.close()

    try:
      xmlDom = minidom.parseString(data)
    except:
      print "Error: problem in the config_arduidom.xml file, cannot process it"
      logger.debug('Error in config_arduidom.xml file')

    # ----------------------
    # Serial device
    options.ArduinoVersion = read_config( xmlDom, "ArduinoVersion")
    options.ArduinoQty = int(read_config( xmlDom, "ArduinoQty"))
    logger.debug("ArduinoQty: " + str(options.ArduinoQty))

    # ----------------------
    # SOCKET SERVER
    options.sockethost = read_config( xmlDom, "sockethost")
    options.socketport = read_config( xmlDom, "socketport")
    logger.debug("Socket Host: " + str(options.sockethost))
    logger.debug("Socket Port: " + str(options.socketport))

    # ----------------------
    # SERIALS
    options.A_ports={}
    for n_node in range(1, 1+options.ArduinoQty):
      opt = read_config( xmlDom, "A{}_serial_port".format(n_node))
      options.A_ports.update({n_node : opt })
    print ( options.A_ports )

    # -----------------------
    # DAEMON
    options.daemon_pidfile = read_config( xmlDom, "daemon_pidfile")
    logger.debug("Daemon_pidfile: " + str(options.daemon_pidfile))

    # TRIGGER
    trigger_nice = read_config( xmlDom, "trigger_nice")
    options.trigger_nice = read_config( xmlDom, "trigger_nice")
    logger.debug("trigger_nice: " + str(options.trigger_nice))
    options.trigger_url = read_config( xmlDom, "trigger_url")
    logger.debug("trigger_url: " + str(options.trigger_url))
    options.apikey = read_config( xmlDom, "apikey")
    logger.debug("apikey: " + str(options.apikey))

  else:
    # config file not found, set default values
    print "Error: Configuration file not found (" + configFile + ")"
    logger.error("Error: Configuration file not found (" + configFile + ") Line: ")

# ----------------------------------------------------------------------------
def read_config( xmlDom, configItem):
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
