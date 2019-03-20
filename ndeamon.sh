#!/usr/bin/env bash
cd /var/www/html/plugins/duibridge
sudo cp -r /home/pi/pidomo/jeedom/duibridge/resources/deamon/* resources/deamon/.
sudo rm /var/www/html/log/duibridge_daemon
sudo python resources/deamon/nduideamon.py $* --config_pins_path /var/www/html/plugins/duibridge/pinconf/pinConf.json --config_ports_path /var/www/html/plugins/duibridge/resources/deamon/duibridge_ports.json --loglevel DEBUG
