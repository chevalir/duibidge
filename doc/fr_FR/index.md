
Description
===========
Ce plugins permet de réaliser un pont entre Jeedom et un Arduino connecté en serie (USB). La communication vers Jeedom est réalisée via [MQTT](https://mqtt.org/). Ce plugins nécessite donc l'utilisation d'un plugins MQTT pour Jeedom. Plusieurs plugins MQTT sont disponible sur le [market](https://www.jeedom.com/market/index.php?v=d&p=market&type=plugin&&name=mqtt)


Introduction
============

Configuration du plugin
=======================

Après le téléchargement du plugin, il vous suffit de l’activer et de le configurer.

![configuration-deamon](../images/configuration-deamon.png)

Une fois activé, le démon devrait se lancer. Le plugin est préconfiguré avec des valeurs par défaut. Vous aurez plusieurs chose à changer:
* definir le nombre d'arduinos connectés
* pour chaque arduino definir le port USB utilisé
* pour chaque arduino la configuration des pins, c'est la partie la plus longue mais la plus importante.

Dépendances
-----------

> **Tip**
>
> La mise à jour des dépendances peut prendre plus de 10 minutes selon
> votre matériel. La progression est affichée en temps réel.

Démon
-----

Cette partie permet de valider l’état actuel du démon et de
configurer la gestion automatique de celui-ci.
![configuration04](../images/configuration04.png)

* Le **Statut** indique que le démon est actuellement en fonction.

* La **Configuration** indique si la configuration du démon
    est valide.

* Le bouton **(Re)Démarrer** permet de forcer le redémarrage du
    plugin, en mode normal ou de le lancer une première fois.

* Le bouton **Arrête**, visible seulement si la gestion automatique
    est désactivée, force l’arrêt du démon.

* La **Gestion automatique** permet à Jeedom de lancer automatiquement
    le démon au démarrage de Jeedom, ainsi que de le relancer en cas
    de problème.

* Le **Dernier lancement** est comme son nom l’indique la date du
    dernier lancement connue du demon.

Log
---

Cette partie permet de choisir le niveau de log ainsi que d’en consulter le contenu.

[configuration05](../images/configuration05.png)


Sélectionner le niveau puis sauvegarder, le démon sera alors relancé
avec les instructions et traces sélectionnées.

Le niveau **Debug** ou **Info** peuvent être utiles pour comprendre
pourquoi le démon plante ou ne remonte pas une valeur.

> **Important**
>
> En mode **Debug** le démon est très verbeux, il est recommandé
> d’utiliser ce mode seulement si vous devez diagnostiquer un problème
> particulier. Il n’est pas recommandé de laisser tourner le démon en
> **Debug** en permanence, surtout si on utilise une **SD-Card**. 
> Une fois le debug terminé, il ne faut pas oublier de retourner sur un 
> niveau moins élevé comme le niveau **Error** qui ne remonte que 
> d’éventuelles erreurs.

Configuration
-------------

Cette partie permet de configurer les paramètres généraux du plugin

![configuration-deamon](../images/configuration-deamon.png)

**Général** :

   * Le paramètre  **Nombre d'Arduinos connectés** vous permet d'indiquer au demon le nombre d'Arduino qu'il devra gérer
   * Les onglets **"Arduino A1"** à **"Arduino A8"** apparaissent en fonction nombre d'Arduino indiqué dans le paramètre  précedent.
   * Le paramètre  **Port de l'Arduino Ax** est accessible dans l'onglet correspondant, il permet d'indiquer le port USB utilisé pour connecter l'Arduino. 
       * une valeur particulier est disponible pour indiquer que l'Arduino est connecté via le plugins Arduidom  **Bridge Arduidom**.

> **Important**
> le mode **"Bridge Arduidom"** ne marche qu'avec le premier Arduino **"Arduino A1"** voir chapitre **Mode Bridge Arduidom**

Gestion des équipements
=======================
Il n'y pas d'équipement dans ce plugins. Le plugins a pour objectif de faire l'interface entre un Arduino série (USB) et le protocole MQTT. La configuration des équipements ce fait dans l’un des plugins MQTT disponible sous Jeedom.

Configuration des pins des Arduinos
-----------------------------------

C'est la partie la plus importante et la plus compliquée.
C'est à partir de cette configuration que le demon Duibridge fera le lien entre un **"topic MQTT"** et une **"pin"** de l'un des Arduinos.
Pour simplifier l'utlisation des topic MQTT il est recommander de bien séparer le topics de commande des topics de status ( retours ). Par example si vous avez une lampe pilotée via une pin et qui remonte son status sur une autre pin de l'Arduino. Dans Jeedom il faut deux commandes de type Action et une commande de type Info. Sur l'arduino il faudra deux pins, une **Digital out** pour piloté la lampe, une en **Digital In** pour remonté son status. Il faudra egalement deux topics un pour la pin qui pilote la lampe un pour remonté le status à Jeedom. L'un des avantage de MQTT est de pouvoir s'abonner facilement à une liste de topic et de sous topic.

Donc cela donne (mauvais choix):
| Pin N° | Pin Type  | Topic |
|---|:-------------:|---------:|
| 4 | Digital OUT | maison/salon/lampe/status |
| 5 | Digital IN | maison/salon/lampe/action |

c'est configuartion fonctionne mais cela n'est tres pratique si vous avez deux lampes dans votre salon. cela donnerai :

Donc cela donne (tuojours pas bon ):
| Pin N° | Pin Type  | Topic |
|---|:-------------:|---------:|
| 4 | Digital OUT | maison/salon/lampe1/status |
| 5 | Digital IN | maison/salon/lampe1/action |
| 6 | Digital OUT | maison/salon/lampe2/status |
| 7 | Digital IN | maison/salon/lampe2/action |

si vous vouler vous abonner a tous les topics de status vous ne pouvez pas utliser les carateres générique proposer par MQTT. Si vous vous abonner à 
maison/salon/# par exemple vous serez abonné aussi au topic action.

la bonne solution est de séparer les topics action et status comme ceci:
| Pin N° | Pin Type  | Topic |
|---|-------------:|---------:|
| 4 | Digital OUT | maison/status/salon/lampe1 |
| 5 | Digital IN | maison/action/salon/lampe1 |
| 6 | Digital OUT | maison/status/salon/lampe2 |
| 7 | Digital IN | maison/action/salon/lampe2 |

De cette facon vous pouvez vous abonner à tous les topics status :
maison/status/#
ou à tous les status des equipements du salon :
maison/action/#








Exemple d'utilation avec jMQTT
------------------------------

Mode bridge Arduidom, migration Arduidom vers MQTT
--------------------------------------------------


