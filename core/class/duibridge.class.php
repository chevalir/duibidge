<?php

/* This file is part of Jeedom.
 *
 * Jeedom is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Jeedom is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Jeedom. If not, see <http://www.gnu.org/licenses/>.
 */

/* * ***************************Includes********************************* */
require_once dirname(__FILE__) . '/../../../../core/php/core.inc.php';







class duibridge extends eqLogic {
    /*     * *************************Attributs****************************** */



    /*     * ***********************Methode static*************************** */

    /*
     * Fonction exécutée automatiquement toutes les minutes par Jeedom
      public static function cron() {

      }
     */


    /*
     * Fonction exécutée automatiquement toutes les heures par Jeedom
      public static function cronHourly() {

      }
     */

    /*
     * Fonction exécutée automatiquement tous les jours par Jeedom
      public static function cronDayly() {

      }
     */



    /*     * *********************Méthodes d'instance************************* */

    public function preInsert() {
        
    }

    public function postInsert() {
        
    }

    public function preSave() {
        
    }

    public function postSave() {
        
    }

    public function preUpdate() {
        
    }

    public function postUpdate() {
        
    }

    public function preRemove() {
        
    }

    public function postRemove() {
        
    }

    /*
     * Non obligatoire mais permet de modifier l'affichage du widget si vous en avez besoin
      public function toHtml($_version = 'dashboard') {

      }
     */

	public static function deamon_info() {
		$return = array();
		$return['state'] = 'nok';
		$pid_file = jeedom::getTmpFolder('duibridge') . '/deamon.pid';
		if (file_exists($pid_file)) {
			if (posix_getsid(trim(file_get_contents($pid_file)))) {
				$return['state'] = 'ok';
			} else {
				shell_exec(system::getCmdSudo() . 'rm -rf ' . $pid_file . ' 2>&1 > /dev/null');
			}
		}
		$return['launchable'] = 'ok';
		$port = config::byKey('port', 'duibridge');
		if ($port != 'auto') {
			$port = jeedom::getUsbMapping($port);
			if (@!file_exists($port)) {
				$return['launchable'] = 'nok';
				$return['launchable_message'] = __('Le port USB n\'est pas configuré', __FILE__);
			} else {
				exec(system::getCmdSudo() . 'chmod 777 ' . $port . ' > /dev/null 2>&1');
			}
		}
		return $return;
	}

	public static function deamon_start($_debug = false) {
		self::deamon_stop();
		$deamon_info = self::deamon_info();
		if ($deamon_info['launchable'] != 'ok') {
			throw new Exception(__('Veuillez vérifier la configuration', __FILE__));
		}
		$port = config::byKey('port', 'duibridge');
		if ($port != 'auto') {
			$port = jeedom::getUsbMapping($port);
		}
    $ressource_path = realpath(dirname(__FILE__) . '/../../ressources');

		$duibridge_path = dirname(__FILE__) . '/../../resources';
		$config_path = dirname(__FILE__) . '/../../pinconf/pinConf.json';
		$data_path = dirname(__FILE__) . '/../../resources/data';
		if (!file_exists($data_path)) {
			exec('mkdir ' . $data_path . ' && chmod 775 -R ' . $data_path . ' && chown -R www-data:www-data ' . $data_path);
		}

		$suppressRefresh = 0;
		if (config::byKey('suppress_refresh', 'duibridge') == 1) {
			$suppressRefresh = 1;
		}
/*
		$disabledNodes = '';
		foreach (self::byType('duibridge') as $eqLogic) {
			if (!$eqLogic->getIsEnable()) {
				$disabledNodes .= $eqLogic->getLogicalId() . ',';
			}
		}
		$disabledNodes = trim($disabledNodes, ',');
*/
    $cmd = '/usr/bin/python ' . $duibridge_path . '/deamon/duiBridgeD.py';
		$cmd .= ' --usb_port ' . $port;
		$cmd .= ' --loglevel ' . log::convertLogLevel(log::getLogLevel('duibridge'));
    // $cmd .= ' --loglevel INFO';
		$cmd .= ' --config_folder ' . $config_path;
		$cmd .= ' --pid ' . jeedom::getTmpFolder('duibridge') . '/deamon.pid';

		log::add('duibridge', 'info', 'Lancement démon duibridge : ' . $cmd);
		exec($cmd . ' >> ' . log::getPathToLog('duibridge') . ' 2>&1 &');
		$i = 0;
		while ($i < 30) {
			$deamon_info = self::deamon_info();
			if ($deamon_info['state'] == 'ok') {
				break;
			}
			sleep(1);
			$i++;
		}
		if ($i >= 30) {
			log::add('duibridge', 'error', 'Impossible de lancer le démon duibridge, relancer le démon en debug et vérifiez la log', 'unableStartDeamon');
			return false;
		}
		message::removeAll('duibridge', 'unableStartDeamon');
		log::add('duibridge', 'info', 'Démon duibridge lancé');
	}

	public static function deamon_stop() {
		$deamon_info = self::deamon_info();
		$pid_file = jeedom::getTmpFolder('duibridge') . '/deamon.pid';
		if (file_exists($pid_file)) {
			$pid = intval(trim(file_get_contents($pid_file)));
			system::kill($pid);
		}
		system::kill('duibridged.py');
		$port = config::byKey('port', 'duibridge');
		if ($port != 'auto') {
			system::fuserk(jeedom::getUsbMapping($port));
		}
		sleep(1);
	}




    /*     * **********************Getteur Setteur*************************** */
}

class duibridgeCmd extends cmd {
    /*     * *************************Attributs****************************** */


    /*     * ***********************Methode static*************************** */


    /*     * *********************Methode d'instance************************* */

    /*
     * Non obligatoire permet de demander de ne pas supprimer les commandes même si elles ne sont pas dans la nouvelle configuration de l'équipement envoyé en JS
      public function dontRemoveCmd() {
      return true;
      }
     */

    public function execute($_options = array()) {
        
    }

    /*     * **********************Getteur Setteur*************************** */
}

?>
