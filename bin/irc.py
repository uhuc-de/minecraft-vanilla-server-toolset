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


class IrcBridge(object):

	def __init__(self, argv):
		"""
		init function of the mvst-core
		"""
		self.socketTimeout = 1
		self.running = True
		
		# Loglevel variables
		self.LOGLEVEL = ('NONE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

		self.CRITICAL = 5
		self.ERROR = 4
		self.WARNING = 3
		self.INFO = 2
		self.DEBUG = 1

		# default values
		self.ircSocket = None
		self.mvstSocket = None
		
		self.ident = "mvstMcBridge"
		self.realname = "MvstBot"
		self.nick = "mvstMcBridge"

		self.host = "irc.host.net"
		self.port = 6667
		self.channel = "mychannel"

		self.socketfile = "../tmp/wrapper_default.socket"
		self.logfile = ""
		self.verbose = 20

		# check if enough arguments were given
		if len(argv) < 3:
			print("To few arguments!")
			self.usage()

		try:
			# Option with ":" need an Argument
			opts, args = getopt.getopt(argv, "hl:i:r:n:p:v:", ["help"] )
		except getopt.GetoptError:
			print("Wrong arguments!")
			self.usage()

		# set arguments to values
		for opt, arg in opts:
			if opt in ("-h", "--help"):
				self.usage()
			elif opt in "-i": 
				self.ident = arg
			elif opt in "-r": 
				self.realname = arg
			elif opt in "-n":
				self.nick = arg
			elif opt in "-l":
				self.logfile = arg
			elif opt in "-v":
				try: 
					self.verbose=int(arg)*10
				except ValueError:
					print("ERROR: verbose need to be an integer!")
					self.usage()
			elif opt in "-p":
				try: 
					self.port=int(arg)
				except ValueError:
					print("ERROR: port need to be an integer!")
					self.usage()
			else:
				print("unknown argument!")
				usage()

		# init logging
		formatter = '%(asctime)s|%(name)s|%(levelname)s|%(message)s'
		if self.logfile == "":
			logging.basicConfig(level=self.verbose,format=formatter)
		else:
			logging.basicConfig(filename=self.logfile,level=self.verbose,format=formatter)
		self.log = logging.getLogger('irc')



		# change values with fixed arguments
		self.socketfile = argv[-3]
		self.host = argv[-2]
		self.channel = argv[-1]



	def connectIrc(self):
		""" connect the irc socket to the irc """
		try:
			# connect to IRC
			self.ircSocket = socket.socket()
			self.ircSocket.connect((self.host, self.port))
			self.ircSocket.send("NICK %s\r\n" % self.nick)
			self.ircSocket.send("USER %s %s bla :%s\r\n" % (self.ident, self.host, self.realname) )
			return True
		except:
			if traceback.print_exc():
				self.log.critical(traceback.print_exc())
				sys.exit(2)
			else:
				sys.exit(0)


	def connectMcSocket(self):
		""" connects to the mvst wrapper socket """
		try:
			if not os.path.exists(self.socketfile): 
				logging.critical("CRITICAL: socketfile not found: %s" % self.socketfile)
				sys.exit(2)

			self.mvstSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			self.mvstSocket.connect(self.socketfile)
		except:
			if traceback.print_exc():
				self.log.critical(traceback.print_exc())
				sys.exit(2)
			else:
				sys.exit(0)


	def processIrcInput(self, inSock):
		""" process the input from the irc """
		readbuffer = ""
		lastline = ""
		try:
			readbuffer=readbuffer+inSock.recv(1024).decode("UTF-8", errors='replace')
			temp=string.split(readbuffer, "\n")
			readbuffer=temp.pop( )

			# process line by line
			for line in temp:
				lastline = line
				line=string.rstrip(line)
				line=string.split(line)
				
				try:

					if(line[0]=="PING"): # simple ping → pong back
						self.ircSocket.send("PONG %s\r\n" % line[1])

					elif (line[1]=="001"):
						self.ircSocket.send("JOIN #%s\r\n" % self.channel)

					elif (line[1]=="433"): # nick already in use
						self.log.critical("Nickname \"%s\"is already in use. Exit." % self.nick)
						sys.exit(3)

					elif (line[1]=="372"): # motd
						pass 

					elif (line[1]=="PRIVMSG"): # message -> send it to the mc socket
						bang = line[0].rfind('!')# index of !
						nick = line[0][1:bang]
						msg = " ".join(line[3:])[1:]
						isAction = msg.rfind("\001ACTION")

						if isAction != -1: # check if its an action
							t = "*%s %s" % (nick, msg[8:-1])
						else:
							t = "<%s> %s" % (nick, msg)
						self.sendToMc(t)
						
				except IndexError:
					self.log.debug("IndexError with: %s" % line)

		except:
			self.log.critical("error in processIrcInput() - last input:")
			self.log.critical(lastline)
			if traceback.format_exc():
				self.log.critical(traceback.format_exc())
				sys.exit(3)


	def processMcInput(self, inSock):
		""" process the input from the irc """
		lastline = ""
		try:
			data = inSock.recv(1024)
			lastline = data
			if len(data) == 0:
				self.log.critical("minecraft socket closed -> exit")
				sys.exit(3)

			text = data.strip().decode("UTF-8", errors='replace')

			# check if "not-whitelisted"-message an send it to ingame and irc
			if "): You are not white-listed on this server!" in text:
				
				self.log.debug("parse whitelist message")
				name = text.split(",name=")[1].split(",")[0]
				s = "Trying to connect but not white-listed: %s" % name 
				self.sendToMc(s)
				self.sendToIrc(s)
			
			else:
				
				# filter a normal chat message
				try: 
					text = "<"+text.split("]: <")[1].strip()
					self.sendToIrc(text)
				except: 
					pass

				# filter a action message
				try:
					text = "*"+text.split("]: *")[1].strip()
					self.sendToIrc(text)
				except: # not a /me neither... drop it
					pass

		except:
			self.log.error("error in processMcInput() - last input: %s" % lastline)
			if traceback.format_exc():
				self.log.critical(traceback.format_exc())
				sys.exit(3)


	def sendToIrc(self, msg):
		""" Sends the text to the irc server """
		# split text, max irc msg length is 512
		for text in self.chunkstring(msg, 400):
			msg = "PRIVMSG #%s :%s%s" % (self.channel, text, "\r\n")
			self.log.debug("to irc: %s" % msg)
			self.ircSocket.send( msg.encode("utf-8", errors='replace')  )


	def sendToMc(self, msg):
		""" Sends the text to the mc wrapper socket """
		# in MC v1.11: Messages can now be 256 characters long instead of 100
		for text in self.chunkstring(msg, 240):
			text = "/say "+text
			self.log.debug("to mc: %s" % text)
			self.mvstSocket.send( text.encode("utf-8", errors='replace') )


	def chunkstring(self, string, length):
		"""
		The generator returns the string sliced, from 0 + a multiple of
		the length of the chunks, to the length of the chunks + a
		multiple of the length of the chunks.
		Source: http://stackoverflow.com/a/18854817
		"""
		return (string[0+i:length+i] for i in range(0, len(string), length))

    
	def start(self):
		""" main method """

		try:
			# connecting
			self.connectIrc()
			self.connectMcSocket()
			self.log.info("connected %s@%s:%s/#%s with %s" % (self.nick, self.host, self.port, self.channel, self.socketfile) )


			readbuffer = ""
			while self.running:
				# Get the list of sockets which are ready to be read through select
				socketlist = [self.mvstSocket, self.ircSocket]
				try:
					read_sockets,write_sockets,error_sockets = select.select(socketlist, [], [], self.socketTimeout)
				except select.error as e:
					self.log.error("select error")
					break
				except socket.error as e:
					self.log.info("socket error")
					break

				for inSock in read_sockets:

					if inSock == self.mvstSocket: 
						self.processMcInput(inSock)
					elif inSock == self.ircSocket: 
						self.processIrcInput(inSock)

					else:
						self.log.warning("unknown Socket - should not happen 0_o")

		except KeyboardInterrupt:
			self.log.info("Keyboard interrupt: quitting")
			sys.exit(1)

		except:
			if traceback.format_exc():
				self.log.critical(traceback.format_exc())
				sys.exit(3)
			else:
				sys.exit(0)




	def usage(self):
		print("""irc.py [optional args] <socket> <host> <channel>

socket		unix socket that should be bridged into IRC
host		hostname or ip adress of the irc server
channel		channel in which should be joined (without starting '#')

optional arguments:

	-i <ident>	Ident-Name of the bot
	-r <realname>	Realname of the bot
	-n <nick>	Nickname of the bot
	-p <port>	Port of the irc server
	-l <file>	Logfile
	-v <level>	Verbosity (1 to 5)
	-h	--help	Shows this message

Verbosity level:
	CRITICAL = 5
	ERROR    = 4
	WARNING  = 3
	INFO     = 2
	DEBUG    = 1

	""")	
		sys.exit(2)


if __name__ == "__main__":
	c = IrcBridge(sys.argv[1:])
	exit(c.start())
