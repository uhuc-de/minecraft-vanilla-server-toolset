#!/usr/bin/python2
# -*- coding: utf-8 -*-

import socket, select, string, sys, getopt, traceback


"""
Show the usage
"""
def help(self):
	print("""control.py [<options> ...] 

Options:
-h|--help			Shows this output
-s|--socket {socketfile}	Change the socketfile (def: /tmp/mcwrapper.socket)
-c|--check		Return exit code 1 if the server is not running

Pipe example: 
echo "/say something" | control.py -s /tmp/mcwrapper.socket 

Shell example:
control.py -s /tmp/mcwrapper.socket 
""")	
	sys.exit(2)


def prompt() :
	sys.stdout.write('> ')
	sys.stdout.flush()


## default values
socketfile = "/tmp/mcwrapper.socket"
linebreak = "\n"
client = None # socket
buffersize = 1024
connected = False
check = False

lastsend = ""

tty = False
if sys.stdin.isatty():
	tty = True


# getopts
try:
	# Option with ":" need an Argument
	opts, args = getopt.getopt(sys.argv[1:], "hs:c", ["socket=", "help", "check"] )
except getopt.GetoptError:
	print( traceback.print_exc() )
	help()
for opt, arg in opts:
	if opt in ("-h", "--help"):
		help()
	elif opt in ("-s", "--socket"):
		socketfile = arg
	elif opt in ("-c", "--check"):
		check = True


client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.settimeout(2)
try :
	client.connect(socketfile)
	connected = True
except :
	sys.stderr.write("can't connect to socket: %s\n" % socketfile)
	sys.exit(-1)

if check:
	sys.exit(0)


# Check if TTY
if not tty:
	try:
		for line in sys.stdin:
			client.send(line)
	except:
		sys.stderr.write("failed to send the commands\n")
		sys.exit(1)

# Start TTY mode
else: 

	try:
		print ('Connected to server. Quit with ^C.')
		prompt()

		while connected:
			socket_list = [sys.stdin, client]
			read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])

			for sock in read_sockets:
				if sock == client:
					data = sock.recv(buffersize)
					if not data :
						print('\nDisconnected from socket')
						connected = False
					else :
						#print data
						if data != "" and data.strip() != lastsend.strip():
							sys.stdout.write(data.decode("UTF-8").strip()+"\n")
							prompt()
						
				else :
					msg = sys.stdin.readline()
					lastsend = msg
					client.send(msg)
					prompt()

	except KeyboardInterrupt:
		print("\n")
	except:	
		print( "\nConnection closed by remote host" )
