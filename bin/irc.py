#!/bin/env python2
# -*- coding: utf-8 -*-

import sys
import socket
import string
import signal
import os
import getopt
import logging
import sys
import socket
import string
import select
import traceback


def usage():
	print("""irc.py [optional args] <socket> <host> <channel>

	socket		unix socket that should be bridged into IRC
	host		hostname or ip adress of the irc server
	channel		channel in which should be joined (without starting '#')

optional arguments:

	-i <ident>	Ident-Name of the bot
	-r <realname>	Realname of the bot
	-n <nick>	Nickname of the bot
	-p <port>	Port of the irc server
	-h	--help	Shows this message
""")	
	sys.exit(2)




def main(argv):
	""" main method """

	# default values	
	IDENT="mcbridge"
	REALNAME="MvstBot"
	NICK="mcBridge"
	PORT=6667

	HOST="irc.jdqirc.net"
	CHANNEL="#mcbridge"
	SOCKETFILE="../tmp/wrapper_default.socket"

	try:
		# Option with ":" need an Argument
		opts, args = getopt.getopt(argv, "hi:r:n:p:", ["help"] )
	except getopt.GetoptError:
		usage()


	for opt, arg in opts:

		if opt in ("-h", "--help"):
			usage()
			
		elif opt in "-i": 
			IDENT=arg	
		elif opt in "-r": 
			REALNAME=arg
		elif opt in "-n":
			NICK=arg
		elif opt in "-p":
			try: 
				PORT=int(arg)
			except ValueError:
				print("ERROR: port need to be an integer!")
				usage()
		else:
			print("unknown argument!")
			usage()

	SOCKETFILE=argv[-3]
	HOST=argv[-2]
	CHANNEL=argv[-1]

	if not os.path.exists(SOCKETFILE): 
		print ("ERROR: socketfile not found: %s" % SOCKETFILE)
		usage()

	try:

		print("connect to %s:%s" % (HOST, PORT) )
		s=socket.socket( )
		s.connect((HOST, PORT))
		s.send("NICK %s\r\n" % NICK)
		s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))

		client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		client.connect(SOCKETFILE)

		readbuffer = ""



		while 1:
			# Get the list sockets which are ready to be read through select
			try:
				read_sockets,write_sockets,error_sockets = select.select([s, client],[],[],1)
			except select.error as e:
				break
			except socket.error as e:
				break

			for sock in read_sockets:

				if sock == client:
					data = sock.recv(1024) 
					text = data.strip().decode("UTF-8", errors='replace')
					text = filterMc(text)
					if len(text) > 0:
						toIrc("PRIVMSG %s :%s" % (CHANNEL, text) )	

				elif sock == s:

					readbuffer=readbuffer+s.recv(1024).decode("UTF-8", errors='replace')
					temp=string.split(readbuffer, "\n")
					readbuffer=temp.pop( )

					for line in temp:
						line=string.rstrip(line)
						line=string.split(line)

						if(line[0]=="PING"):
							s.send("PONG %s\r\n" % line[1])
						elif (line[1]=="001"):
							print("sucessfully connected")
							s.send("JOIN %s\r\n" % CHANNEL)
						elif (line[1]=="PRIVMSG"):
							ausrufezeichen = line[0].rfind('!')# index des ausrufezeichens
							nick = line[0][1:ausrufezeichen]
							msg = " ".join(line[3:])[1:]
							isAction = msg.rfind("\001ACTION")
							if isAction != -1:
								t = "*%s %s" % (nick, msg[8:-1])
							else:
								t = "<%s> %s" % (nick, msg)
							toMc(t)


				else:
					print("unknown Socket")

	except:
		traceback.print_exc(file=sys.stdout)




def filterMc(t):
#	print("filter: %s" % t)
	try:
		if "): You are not white-listed on this server!" in t:
			name=t.split(",name=")[1].split(",")[0]
			s = "Trying to connect but not white-listed: %s" % name 
			toMc(s)
			return s

		#print("FILTER: %s"  % t)
		msg = "<"+t.split("]: <")[1].strip()
		if msg.startswith("/"):
			return ""
		else:
			return msg
	except:
		return ""

def toIrc(msg):
#	print("toIRC: %s" % msg)
	msg = msg+"\r\n"
	s.send( msg.encode("utf-8", errors='replace')  )

def toMc(msg):
#	print("toMc: %s" % msg)
	msg = "/say "+msg
	client.send( msg.encode("utf-8", errors='replace') )




if __name__ == "__main__":
	main(sys.argv[1:])

