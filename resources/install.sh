#!/bin/sh

touch /tmp/dependancy_duibridge_in_progress
echo 0 > /tmp/dependancy_duibridge_in_progress
echo "Launch install of duibridge dependancy"
echo "-------------------------------------"
echo ">>> Apt Clean"
#sudo apt-get clean
echo 20 > /tmp/dependancy_duibridge_in_progress
echo ">>> Apt Update"
#sudo apt-get update
echo 40 > /tmp/dependancy_duibridge_in_progress
echo ">>> Install Arduino"
#sudo apt-get install -y arduino
echo 50 > /tmp/dependancy_duibridge_in_progress
echo ">>> Install Python PIP"
#sudo apt-get install -y python-pip
echo 60 > /tmp/dependancy_duibridge_in_progress
echo ">>> Install INOTOOLS"
#sudo pip install ino
echo ">>> Install PAHO MQTT"
sudo pip install paho-mqtt
echo 70 > /tmp/dependancy_duibridge_in_progress
echo ">>> Install INOTOOLS"
#sudo easy_install ino
echo 80 > /tmp/dependancy_duibridge_in_progress
echo ">>> Install AVRDUDE"
#sudo apt-get install -y avrdude
echo 90 > /tmp/dependancy_duibridge_in_progress
#sudo usermod -G dialout www-data
echo 100 > /tmp/dependancy_duibridge_in_progress
echo " ---------------------------- "
echo "|  Everything is installed!  |"
echo " ---------------------------- "
rm /tmp/dependancy_duibridge_in_progress

