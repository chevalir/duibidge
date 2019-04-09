#!/bin/bash
Backup="../arduidom/ressources/arduidomx.py.original"
Orginal="../arduidom/ressources/arduidomx.py"
Bridge="ressources/arduidomx.py.bridge"
if [ -f $Backup ]
then
    echo "$Backup found backup to arduidomx.py.original"
else
	echo "$file not found backup to arduidomx.py.original"
    sudo cp $Orginal $Backup
 #   sudo cp $Bridge $Original
fi