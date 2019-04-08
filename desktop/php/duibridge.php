<?php
if (!isConnect('admin')) {
	throw new Exception('{{401 - Accès non autorisé}}');
}
sendVarToJS('eqType', 'duibridge');
$eqLogics = eqLogic::byType('duibridge');
?>

<div class="row row-overflow">

    <div class="col-lg-10 col-md-9 col-sm-8 eqLogicThumbnailDisplay"
        style="border-left: solid 1px #EEE; padding-left: 25px;">
        <legend>{{Duibridge plugins}}</legend>
        <legend><i class="fa fa-cog"></i> {{Gestion}}</legend>
        <div class="eqLogicThumbnailContainer">
            <div class="cursor" id="bt_configurePin"
                style="background-color : #ffffff; height : 140px;margin-bottom : 10px;padding : 5px;border-radius: 2px;width : 160px;margin-left : 10px;">
                <center>
                    <i class="fa fa-cogs" style="font-size : 5em;color:#767676;"></i>
                </center>
                <span
                    style="font-size : 1.1em;position:relative; top : 23px;word-break: break-all;white-space: pre-wrap;word-wrap: break-word;color:#767676">
                    <center>{{Configuration des Pins}}</center>
                </span>
            </div>
            <div class="cursor eqLogicAction" data-action="gotoPluginConf"
                style="background-color : #ffffff; height : 120px;margin-bottom : 10px;padding : 5px;border-radius: 2px;width : 160px;margin-left : 10px;">
                <center>
                    <i class="fa fa-wrench" style="font-size : 6em;color:#767676;"></i>
                </center>
                <span
                    style="font-size : 1.1em;position:relative; top : 15px;word-break: break-all;white-space: pre-wrap;word-wrap: break-word;color:#767676">
                    <center>{{Configuration du plugin}}</center>
                </span>
            </div>
        </div>
        <div>
        <br/>
        <br/>
        <br/>

        <br/>
        <center>Pas d'equipement dans ce plugins, les equipements seront configurés dans l'un des plugins MQTT de votre choix.</center>
        <center>Vous pouvez utiliser le bouton <b>Configuration des Pins</b> pour definir la correspondance entre les pins des Arduinos et les topics MQTT</center>
        
        </div>
    </div>
</div>

<?php include_file('desktop', 'duibridge', 'js', 'duibridge');?>
<?php include_file('core', 'plugin.template', 'js');?>