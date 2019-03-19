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
$ArduinoQty = config::byKey('ArduinoQty', 'duibridge', 1);
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
    Actualiser la page après la page apres tout changement et sauvegarde.
</div>


<ul class="nav nav-pills nav-justified" id="tab_arid">
    <?php for ($i=1; $i <= $ArduinoQty; $i++) {
        if ($i == 1) {
            echo '<li class="active">';
        } else {
            echo '<li>';
        }
        $daemonstate = 1;
        echo '<a data-toggle="tab" href="#tab_' . $i . '">{{Arduino A' . $i . '}}</a></li>';
    } ?>
</ul>

<div class="tab-content" id="arduinotabs">
    <?php for ($i=1; $i <= 8; $i++) { ?>
        <div class="tab-pane<?php if ($i == 1) echo " active" ?>" id="tab_<?php echo $i ?>">
            <hr>
            <form class="form-horizontal">
                <fieldset>
                    <div class="form-group">
                        <label class="col-lg-3 control-label">Port de l'Arduino A<?php echo $i ?></label>
                        <div class="col-lg-9">
                            <select class="configKey form-control" data-l1key="A<?php echo $i ?>_port">
                                <option value="none">{{NULL}}</option>
                                <option value="auto">{{Auto}}</option>
                                <?php
                                            foreach (jeedom::getUsbMapping('', true) as $name => $value) {
                                            echo '<option value="' . $name . '">' . $name . ' (' . $value . ')</option>';
                                            }
                                ?>
                                <option value="/dev/ttyUSB0">{{Arduino sur USB /dev/ttyUSB0}}</option>
                                <option value="/dev/ttyUSB1">{{Arduino sur USB /dev/ttyUSB1}}</option>
                                <option value="/dev/ttyUSB2">{{Arduino sur USB /dev/ttyUSB2}}</option>
                                <option value="/dev/ttyACM0">{{Arduino sur USB /dev/ttyACM0}}</option>
                                <option value="/dev/ttyACM1">{{Arduino sur USB /dev/ttyACM1}}</option>
                                <option value="/dev/ttyACM2">{{Arduino sur USB /dev/ttyACM2}}</option>
                                <option value="/dev/ttyS0">{{Arduino sur USB /dev/ttyS0}}</option>
                                ?>
                            </select>
                        </div>
                    </div>
                </fieldset>
            </form>
            <form>
                <fieldset>
                    <legend><i class="fa fa-list-alt"></i> {{Général}}</legend>
                    <div class="form-group">
                        <label class="col-sm-4 control-label">{{Mode bridge (utilisation avec le plugins Arduidom)}}</label>
                        <div class="col-sm-2">
                            <input type="checkbox" class="configKey" data-l1key="bridgemode"/>
                        </div>
                    </div>
                </fieldset>
            </form>
        </div>

    <?php } ?>  <!-- FIN DU For PHP -->
</div>
<script>
    var jsinitok = false;
    $('#bt_savePluginConfig').on('click', function () {
        console.log("bt_savePluginConfig");

        $.ajax({// fonction permettant de faire de l'ajax
            type: "POST", // methode de transmission des données au fichier php
            url: "plugins/duibridge/core/ajax/duibridge.ajax.php", // url du fichier php
            data: {
                action: "SaveConfToJson"
            },
            dataType: 'json',
            error: function (request, status, error) {
                handleAjaxError(request, status, error);
            },
            success: function (data) { // si l'appel a bien fonctionné
                if (data.state != 'ok') {
                    $('#div_alert').showAlert({message: data.result, level: 'danger'});
                    return;
                }
                $('#div_alert').showAlert({message: 'La Migration a été correctement effectuée.', level: 'success'});
            }
        });

        //history.go(0);
    });



        $('#Arduinoqty').change(function() {
            if (jsinitok) {
                console.log("Qty Changed ! Saving...");
                document.getElementById("bt_savePluginConfig").click();
                location.reload();
                $('#ul_plugin .li_plugin[data-plugin_id=duibridge]').click();
            }
        });

    //$(document).ready(function(){
        setTimeout(function() {
        jsinitok = true;
        console.log("initOK");
    }, 3000);

</script>
