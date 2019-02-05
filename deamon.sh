#!/usr/bin/env bash
cd /var/www/html/plugins/duibridge ; sudo cp -r /home/pi/pidomo/jeedom/duibridge/* .;
sudo rm /var/www/html/log/duibridge_daemon
sudo python resources/deamon/duiBridgeD.py $* --config_folder /var/www/html/plugins/duibridge/pinconf/pinConf.json
