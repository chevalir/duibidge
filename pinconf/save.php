<?php
//error_reporting(E_ALL);
//var_dump($_SERVER);
$post_data = $_POST['data'];
if (!empty($post_data)) {
    $data_path = dirname(__FILE__);
    $dir = 'plugins/duibridge/pinconf';
    $file = uniqid().getmypid();
    $filename = $data_path.'/pinConf.json';
    $handle = fopen($filename, "w");
    fwrite($handle, $post_data);
    fclose($handle);
    echo $dir.'/pinConf.json';
}
?>
