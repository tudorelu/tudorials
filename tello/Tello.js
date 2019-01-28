class Tello {

	constructor(){
		this.tello_address = '192.168.10.1';
		this.command_port = 8889;

		const dgram = require('dgram');
		this.command_socket = dgram.createSocket('udp4');
		this.initCommandSocket();
	}

	// function for handling incoming messages & errors from tello
	initCommandSocket(){
		this.command_socket.on('message', (msg, rinfo) => {
			console.log(`got ${msg}`)
		});
		this.command_socket.on('error', (err) => {
				console.log(`error: ${err}\n closing socket`);
				this.command_socket.close();
		});
		this.command_socket.on('listening', () => {
			let address = this.command_socket.address();
			console.log(`established connection with ${address.address}:${address.port}`)
		});
		this.command_socket.bind(this.command_port);
	}

	// function for sending commands to tello
	sendCommand(message){
		var command = new Buffer(message);
		this.command_socket.send(command, 0, command.length, this.command_port, this.tello_address, (err, bytes) =>{
			if(err)
				console.log(err);
		})
	}

	// function to command the drone through command line
	startCLI(){
		// first enter SDK mode:
		this.sendCommand('command');
		// create CLInterface
		const readline = require('readline');
		const rl = readline.createInterface({
		  input: process.stdin,
		  output: process.stdout
		});

		let that = this;
		rl.on('line', (line) => {
			// if we type in close, close interface
			if(line === 'close'){
				rl.close();
			}
			// send command receive from CL to tello
			that.sendCommand(line);
		}).on('close', () => {
			// upon closing interface, terminate program
			that.command_socket.close();
			process.exit(0);
		})
	}
}

// init drone and start
let drone = new Tello();
drone.startCLI();

// IMPORTANT close socket connection upon exception
process.on('uncaughtException', () => {
	drone.command_socket.close();
});

// ENJOY!