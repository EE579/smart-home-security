var net = require('net');

var server = net.createServer(function(socket){
	socket.write('Welcome');
	dev$.selectByID('WDFL00001B').call('on');
	setTimeout(function dark(){
		dev$.selectByID('WDFL00001B').call('off')
	},5000);
});



console.log("Starting server at port 2333...");
server.listen(2333, '0.0.0.0');