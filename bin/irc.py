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



""" main method """
def main(argv):
	# default values	
	IDENT="mvstMcBridge"
	REALNAME="MvstBot"
	NICK="mvstMcBridge"
	PORT=6667
	HOST="irc.host.net"
	CHANNEL="#mychannel"
	SOCKETFILE="../tmp/wrapper_default.socket"

	argv=sys.argv[1:]
	try:
		# Option with ":" need an Argument
		opts, args = getopt.getopt(argv, "hi:r:n:p:", ["help"] )
	except getopt.GetoptError:
		usage()

	# check if enough arguments were given
	if len(argv) < 3:
		print("To few arguments!")
		usage()

	# set arguments to values
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

	# change values with fixed arguments
	SOCKETFILE=argv[-3]
	HOST=argv[-2]
	CHANNEL=argv[-1]

	if not os.path.exists(SOCKETFILE): 
		print ("ERROR: socketfile not found: %s" % SOCKETFILE)
		usage()
	try:

		# connect to IRC
		s=socket.socket( )
		s.connect((HOST, PORT))
		s.send("NICK %s\r\n" % NICK)
		s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))

		# connect to the minecraft socket
		client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		client.connect(SOCKETFILE)

		print("connected %s@%s:%s/#%s with %s" % (NICK, HOST, PORT, CHANNEL, SOCKETFILE) )

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
				## process the minecraft socket
				if sock == client: 
				
					data = sock.recv(1024) 
					text = data.strip().decode("UTF-8", errors='replace')

					# check if "not-whitelisted"-message an send it to ingame and irc
					if "): You are not white-listed on this server!" in text:
						name=text.split(",name=")[1].split(",")[0]
						s = "Trying to connect but not white-listed: %s" % name 
						msg = "/say "+s
						client.send( msg.encode("utf-8", errors='replace') )
						text = s

					# filter a normal chat message
					try: 
						text = "<"+text.split("]: <")[1].strip()
						msg = "PRIVMSG #%s :%s%s" % (CHANNEL, text, "\r\n")
						s.send( msg.encode("utf-8", errors='replace')  )
					except: 
						pass

					# filter a action message
					try:
						text = "*"+text.split("]: *")[1].strip()
						msg = "PRIVMSG #%s :%s%s" % (CHANNEL, text, "\r\n")
						s.send( msg.encode("utf-8", errors='replace')  )
					except: # not a /me neither... drop it
						pass


				## process the IRC socket
				elif sock == s: 
				
					readbuffer=readbuffer+sock.recv(1024).decode("UTF-8", errors='replace')
					temp=string.split(readbuffer, "\n")
					readbuffer=temp.pop( )

					# process line by line
					for line in temp:

						line=string.rstrip(line)
						line=string.split(line)

						if(line[0]=="PING"): # simple ping → pong back
							s.send("PONG %s\r\n" % line[1])

						elif (line[1]=="001"):
							print("sucessfully connected")
							s.send("JOIN #%s\r\n" % CHANNEL)

						elif (line[1]=="433"): # nick already in use
							print("Nickname \"%s\"is already in use. Exit." % NICK)
							sys.exit(3)

						elif (line[1]=="372"): # motd
							pass 

						elif (line[1]=="PRIVMSG"): # message -> send it to the mc socket
							bang = line[0].rfind('!')# index of !
							nick = line[0][1:bang]
							msg = " ".join(line[3:])[1:]
							isAction = msg.rfind("\001ACTION")

							if isAction != -1: # check if its an action
								t = "/say *%s %s" % (nick, msg[8:-1])
							else:
								t = "/say <%s> %s" % (nick, msg)
							client.send( t.encode("utf-8", errors='replace') )

				else:
					print("unknown Socket - should not happen 0_o")

	except:
		traceback.print_exc(file=sys.stdout)
		sys.exit(3)


if __name__ == "__main__":
	main(sys.argv[1:])
