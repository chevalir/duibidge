
Description
===========
Ce plugins permet de réaliser un pont entre Jeedom et un Arduino connecté en serie (USB). La communication vers Jeedom est réalisé via [MQTT](https://mqtt.org/). Ce plugins nécessite donc l'utilisation d'un plugins MQTT pour Jeedom. Plusieurs plugins gratuits sont disponible sur le [market](https://www.jeedom.com/market/index.php?v=d&p=market&type=plugin&&name=mqtt)

Introduction
============

Configuration du plugin
=======================

Après le téléchargement du plugin, il vous suffit de l’activer et de le
configurer.

![configuration01](../images/configuration01.png)

Une fois activé, le démon devrait se lancer. Le plugin est préconfiguré
avec des valeurs par défaut. Vous aurez plusieurs chose à configurer:

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

Cette partie permet de choisir le niveau de log ainsi que d’en consulter
le contenu.

![configuration05](../images/configuration05.png)

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
![configuration06](../images/configuration06.png)

**Général** :

    * Le paramètre  **Nombre d'arduinos connectés** vous permet d'indiqué au demon le nombre d'arduino qu'il devra gérer
    * Les onglets **"Arduino A1"** à **"Arduino A8"** apparaissent en fonction nombre d'arduino indiqué dans le paramètre  précedent.
    * Les paramètre  **Port de l'Arduino A1** sont accéssible dans l'onglet correspondant, il permet d'indiqué le port USB utilisé pour connecter l'arduino. 
        * une valeur particulier est disponible pour indiqué que l'arduino est connecté via Arduidom **Bridge Arduidom**.

> **Important**
> le mode **"Bridge Arduidom"** ne marche qu'avec le premier arduino **"Arduino A1"**
