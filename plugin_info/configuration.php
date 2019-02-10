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

require_once dirname(__FILE__) . '/../../../core/php/core.inc.php';
include_file('core', 'authentification', 'php');
if (!isConnect()) {
    include_file('desktop', '404', 'php');
    die();
}
?>
<div class="row">
    <label class="col-xs-2 control-label">Nombre d'arduino(s) utilisés</label>
    <div class="col-xs-2">
        <select id="Arduinoqty" class="configKey form-control" data-l1key="ArduinoQty">
            <option value="1" id="ArduinoQty">1</option>
            <option value="2" id="ArduinoQty">2</option>
            <option value="3" id="ArduinoQty">3</option>
            <option value="4" id="ArduinoQty">4</option>
            <option value="5" id="ArduinoQty">5</option>
            <option value="6" id="ArduinoQty">6</option>
            <option value="7" id="ArduinoQty">7</option>
            <option value="8" id="ArduinoQty">8</option>
        </select>
    </div>
    Actualiser la page après la Sauvegarde d'un changement.
</div>

<form class="form-horizontal">
    <fieldset>
        <legend><i class="fa fa-list-alt"></i> {{Général}}</legend>
        <div class="form-group">
          <label class="col-sm-4 control-label">{{Mode bridge (utilisation avec Arduidom)}}</label>
          <div class="col-sm-2">
            <input type="checkbox" class="configKey" data-l1key="bridgemode"/>
          </div>
        </div>

        <div class="form-group">
            <label class="col-lg-4 control-label">{{Port USB}}</label>
            <div class="col-lg-2">
                <select class="configKey form-control" data-l1key="port">
                	<option value="none">{{Aucun}}</option>
                	<option value="auto">{{Auto}}</option>
                	<?php
                				foreach (jeedom::getUsbMapping('', true) as $name => $value) {
                				echo '<option value="' . $name . '">' . $name . ' (' . $value . ')</option>';
                				}
                	?>
                </select>
            </div>
        </div>
  </fieldset>
</form>

