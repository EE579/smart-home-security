/*
var python = require('child_process').spawn('python', ["motionDetection.py"]);

python.stdout.on('data', function (data){
	console.log(data.toString());
});
*/
var fs = require('fs');
var foscam = require('foscam-client');
var net = require('net');


var cam = new foscam({
	username: '',
	password: '',
	host: '',
	port: 88,
	protocol: 'http',
	rejectUnauthorizedCerts: true
});


var python = require('child_process').spawn('python', ["../control/final.py"])

python.stdout.on('data', function(data){
	
	if (!data.toString().includes("None")) {
		console.log(data.toString());
		var client = new net.Socket();
		client.connect(, '', function() {
		console.log('Connected');		
		});
		client.on('data', function(data) {
			console.log('Received: ' + data);
			client.destroy(); // kill client after server's response
		});
		client.on('close', function() {
			console.log('Connection closed');
		});
	}
	
});
	
