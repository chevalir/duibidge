# duibridge

![configuration-deamon](doc/images/duibridge_icon.png)
duibidge jeedom plugins

Ce plugins est fait d’abord fait pour ceux qui cherche à remplacer le plugins *[Arduidom](https://github.com/bobox59/arduidom)* sous [Jeedom](https://www.jeedom.com/site/fr/). Depuis que le plugins *Arduidom* qui a disparu du market Jeedom je cherchais une solution pour le remplacer sans trop casser mon installation.

Plus globalement il permet la communication entre un Arduino USB et Jeedom via protocol de messaging MQTT

[Arduidom](https://github.com/bobox59/arduidom) me permettais de communiquer entre Jeedom et un Arduino USB ( Nano ). Après qq recherche je me suis orienté vers une solution MQTT. Il y plusieurs plugins MQTT pour Jeedom. MQTT permet simplement d’envoyer ou de recevoir des informations. Toutes les informations sur MQTT sont disponibles sur le web [voir mqtt.fr](http://mqtt.fr).
Pour les Arduinos avec Ethernet ou Wifi ou les ESP il est possible de faire directement du MQTT sur l’Arduino mais dans le cas des Arduinos connectés en *serial* (USB) ce n'est pas possible. Je suis donc reparti du Plugins Arduidom, j’ai gardé le Sketch pour la compatibilité mais j’ai transformé le *deamon* pour qu’il communique avec Jeedom via MQTT. Finalement j’ai refait un Plugins Jeedom qui ne fait que gérer le deamon. 

Schéma de connexion :
---------------------

Arduino <---USB----> RPI (deamon) <- MQTT-> Jeedom 

Pour mes tests, coté Jeedom j'ai utilisé le plugins [jMQTT](https://github.com/domotruc/jMQTT). 
Coté Arduino on peut garder le sketch Arduidom pas de changement ou bien installer celui que je fourni.

Mode bridge
===========

Pour ceux qui aurons besoin de faire une migration depuis *Arduidom*, un mode mixte est possible. Ce mmode permet de garder de plugins *Arduidom* en place mais de pouvoir communiqué en même temps avec l'Arduino via MQTT. Cela permet d'avoir un mode de transition, de créé tous vos equipements via MQTT tout en concervant les equipements Arduidom operationel. Cela peut vuos permetre de faire des tests sans cassé votre installation.

> Attension dans ce mode **Bridge** les performanaces sont un peu moins bonnes mais reste tres correctes.

> Pour le mode bridge vous devez patcher le deamon python d'Arduidom aduidomx.py pour cela vous trouverez un shell à la racine du projet: plugins/duibridge/arduidom_deamon_bridge.sh


Limitation de la version actuelle (testeur vous êtes les bienvenus):
====================================================================
 - Testée avec un seul Arduino. 
 - Support uniquement du protocol radio Chacon ê - Support des sonde DHT fonctionel mais pas encore testé 

 - Pas de configuration possible du host et port MQTT ( uniquement via changement dans le deamon en python) 
 - 


