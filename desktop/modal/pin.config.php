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

if (!isConnect('admin')) {
    throw new Exception('{{401 - Accès non autorisé}}');
}

?>
<script src="./plugins/duibridge/pinconf/jsoneditor.js"></script>
    
    <button id='submit'>View JSON</button>
    <button id='save'>Save Config</button>
    <button id='restore'>Load Config</button>
    <span id='valid_indicator'></span>
    <div id='editor_holder'></div>


    
    <script>
      // This is the starting value for the editor
      // We will use this to seed the initial editor 
      // and to provide a "Restore to Default" button.
     var starting_value = [
        {
        "name": "Arduino1",
        "card": "UNO, duemilanove328, leo, nano168, nano328, mega2560",
        "port": "USB1",
        "digitals": {
          "dpins": [
            {"card_pin": "PD5; DIGITAL 5 (PWM)","mode": "out; Sortie Digitale"}
          ]
        },
        "analog": {
          "apins": [
            {"card_pin": "A1; ANALOG IN A1","mode": "ain; Entrée analogique"}
          ]
        },
        "custom": {
          "cpin": [
            {
              "custom_pin": 0,
              "mode": "custout; Sortie Customisée"
            }
          ]
        }
      }
     ];



      var jURL = './plugins/duibridge/pinconf/pinConf.json';

    //console.log("start", JSON.stringify(starting_value, null, 2));
      
      // Initialize the editor
      var editor = new JSONEditor(document.getElementById('editor_holder'),{
        // Enable fetching schemas via ajax

        ajax: true,
        
        // The schema for the editor
        schema: {
          type: "array",
          title: "Pins Configuration",
          format: "tabs",
          items: {
            title: "Configuration",
            headerTemplate: "{{i}} - {{self.name}}",
            $ref: "plugins/duibridge/pinconf/schema-duinodeConf.json"
          }
        },
        
        // Seed the form with a starting value
        startval: starting_value,
        disable_edit_json: true,
        disable_properties: true,
        theme: 'bootstrap2',
        iconlib: 'bootstrap2',
        // Disable additional properties
        no_additional_properties: true,
        
        // Require all properties by default
        required_by_default: true
      });
      
    var ttjson ="";
    fetch(jURL, {cache: "reload", mode: 'cors'})
      .then(function(response) {
        return response.text();
      })
      .then(function(json) {
        ttjson = json;
        console.log('Request successful', ttjson);
        editor.setValue(JSON.parse(ttjson));
        return ttjson;
      })
      .catch(function(error) {
        log('Request failed', error)
      });
      // Hook up the submit button to log to the console
      document.getElementById('submit').addEventListener('click',function() {
        // Get the value from the editor
        console.log(editor.getValue());
        window.alert('Form submitted. Values object:\n' +
          JSON.stringify(editor.getValue(), null, 2));
      });
      
      // Hook up the Restore to Default button
      document.getElementById('restore').addEventListener('click',function() {
            fetch(jURL, {mode: 'cors'})
      .then(function(response) {
        return response.text();
      })
      .then(function(json) {
        ttjson = json;
        console.log('Request successful', ttjson);
        editor.setValue(JSON.parse(ttjson));
        return ttjson;
      })
      .catch(function(error) {
        log('Request failed', error)
      });

        console.log('Editor successful', ttjson);
          
        //editor.setValue(JSON.parse(ttjson));
      });

      document.getElementById('save').addEventListener('click',function() {
        console.log(editor.getValue());
        window.alert('Form submitted. Values object:\n' +
          JSON.stringify(editor.getValue(), null, 2));

        var response=document.getElementById("editor_holder");
        var value = editor.getValue();
        var data = 'data='+ JSON.stringify(value[0], null, 2);
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.onreadystatechange=function(){
          if (xmlhttp.readyState==4 && xmlhttp.status==200){
            //response.innerHTML='<a href="/'+xmlhttp.responseText+'">'+'open config file'+'</a>';
          }
        }
        xmlhttp.open("POST","./plugins/duibridge/pinconf/save.php",true);
              //Must add this request header to XMLHttpRequest request for POST
              xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xmlhttp.send(data);
      });


      
      // Hook up the enable/disable button
      document.getElementById('enable_disable').addEventListener('click',function() {
        // Enable form
        if(!editor.isEnabled()) {
          editor.enable();
        }
        // Disable form
        else {
          editor.disable();
        }
      });
      
      // Hook up the validation indicator to update its 
      // status whenever the editor changes
      editor.on('change',function() {
        // Get an array of errors from the validator
        var errors = editor.validate();
        
        var indicator = document.getElementById('valid_indicator');
        
        // Not valid
        if(errors.length) {
          indicator.style.color = 'red';
          indicator.textContent = "not valid";
        }
        // Valid
        else {
          indicator.style.color = 'green';
          indicator.textContent = "valid";
        }
      });
      
</script>
