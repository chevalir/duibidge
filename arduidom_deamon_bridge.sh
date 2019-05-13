#!/bin/bash
Backup="../arduidom/ressources/arduidomx.py.original"
Orginal="../arduidom/ressources/arduidomx.py"
Bridge="resources/bridge/arduidomx.py.bridge"
if [ -f $Backup ]
then
    echo "$Backup found backup, install only"
    sudo cp $Bridge $Original
else
	echo "$file not found backup to arduidomx.py.original"
    sudo cp $Orginal $Backup
    sudo chown www-data:www-data $Backup
fi