#!/usr/bin/python
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

tty = False
if sys.stdin.isatty():
	tty = True


# getopts
try:
	# Option with ":" need an Argument
	opts, args = getopt.getopt(sys.argv[1:], "hs:", ["socket=", "help"] )
except getopt.GetoptError:
	print( traceback.print_exc() )
	help()
for opt, arg in opts:
	if opt in ("-h", "--help"):
		help()
	elif opt in ("-s", "--socket"):
		socketfile = arg


client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.settimeout(2)
try :
	client.connect(socketfile)
	connected = True
except :
	print("Can't connect to socket: %s" % socketfile)
	sys.exit(1)


# Check if TTY
if not tty:
	try:
		for line in sys.stdin:
			client.send(line)
	except:
		print("failed to send the commands")
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
						sys.stdout.write(data)
						prompt()
				else :
					msg = sys.stdin.readline()
					client.send(msg)
					prompt()

	except KeyboardInterrupt:
		print("\n")
	except:	
		print( traceback.print_exc() )
