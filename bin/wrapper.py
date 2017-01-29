#!/usr/bin/python3
# -*- coding: utf-8 -*-


from subprocess import *
import os
import sys
import time

from time import sleep
from threading import Thread
import socket
import select
import string
import signal
import traceback

import getopt
import logging



"""
Show the usage
"""
def help():
	print("""wrapper.py [args] --- {command}

	command			Command to start the minecraft jar

Arguments:
	-h --help		Shows this output
	-s {socketfile}		Change the socketfile 
				(default: /tmp/mcwrapper.socket)
	-l {logfile}		Set the logfile (default: stdout)
	-v {loglevel}		Change the loglevel (5-1) (Default: 2)

Loglevels:
	CRITICAL	5
	ERROR		4
	WARNING		3
	INFO		2
	DEBUG		1

Returncodes:
	0 	everything is alright
	1 	wrong parameter
	2 	unable to access jar file
""")	
	sys.exit(1)


"""
Main method
"""
def main(argv):
	## default values
	mccommand = "" 
	socket = "/tmp/mcwrapper.socket"
	linebreak = "\n"
	loglevel = 10
	logfile = ""

	if len(argv) < 1:
		help()

	## getopt
	try:
		# Option with ":" need an Argument
		opts, args = getopt.getopt(argv, "hs:v:l:", ["help", "socket=", "log=", "-"] )
	except getopt.GetoptError:
		print( traceback.print_exc() )
		help()

	for opt, arg in opts:
		
		if opt in ("-h", "--help"):
			help()
		elif opt in ("-s", "--socket"):
			socket = arg
		elif opt in ("-v"):
			loglevel = int(arg) * 10
		elif opt in ("-l", "--log"):
			logfile = arg
		elif opt in ("---"):
			mccommand = " ".join( argv[argv.index('---')+1:] )

	if mccommand == "":
		print("No command found!")
		help()

	formatter = '%(asctime)s|%(name)s|%(levelname)s|%(message)s'
	if logfile == "":
		logging.basicConfig(level=loglevel,format=formatter)
	else:
		logging.basicConfig(filename=logfile,level=loglevel,format=formatter)

	# check if *.jar exists
	for i in mccommand.split(" "):
		if ".jar" in i:
			if not os.path.isfile(i):
				print("ERROR: no valid JAR-File given!")
				exit(2)


	wrapper = Wrapper(mccommand, socket, linebreak)
	wrapper.start()

"""
Provides a unix socket to communicate with clients and exchance messages between 
them and the wrapper
"""
class Broadcaster(object):

	def __init__(self, wrapper, socketaddr, linebreak):
		self.log = logging.getLogger('broadcast')
		self.wrapper = wrapper
		self.socketaddr = socketaddr
		self.linebreak = linebreak

		self.buffersize = 1024
		self.running = True	

		self.connections=[]
		self.server_socket = 0

	def close(self):
		# Close the server
		self.log.debug('Shutdown ...' )
		self.running = False

		for o in self.connections:
			o.close()
		self.server_socket.close()
		self.log.debug('Shutdown ... done' )


	def do(self):
		self.log.debug( "Start ..." )
		self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			os.remove(self.socketaddr)
		except OSError:
			pass

		self.server_socket.bind(self.socketaddr)
		self.server_socket.listen(5)

		# Add server socket to the list of readable connections
		self.connections.append(self.server_socket)
		self.log.debug( "Start ... done" )

		while self.running:
			# Get the list sockets which are ready to be read through select
			try:
				read_sockets,write_sockets,error_sockets = select.select(self.connections,[],[],1)
			except select.error as e:
				break
			except socket.error as e:
				break

			for sock in read_sockets:

				if sock == self.server_socket:
					# Handle the case in which there is a new connection recieved through server_socket
					sockfd, addr = self.server_socket.accept()
					self.connections.append(sockfd)
					#self.log.debug("client connected")
				else:
					# Data recieved from client
					try:
						text = self.receive(sock)

						if len(text) > 0:
							self.log.debug("input=%s" % text)
							self.wrapper.write(text)


					except:
						self.log.debug("client disconnected [read]")
						self.log.debug( traceback.print_exc(file=sys.stdout) )
						sock.close()
						self.connections.remove(sock)
						continue

					data = text
					if data:
						self.broadcast_data(data) 
					else:
						self.log.debug("client disconnected [no data]")
						sock.close()
						self.connections.remove(sock)   


	def broadcast_data (self, message):
		for socket in self.connections:
			if socket != self.server_socket:
				try:
					socket.send( message.encode("utf-8")  ) #.encode("utf-8")
				except:
					pass

	def read(self, text):
		""" Text received from a client """
		text = text.strip()
		if len(text) > 0:
			self.log.debug("input=%s" % text)
			self.wrapper.write(text)

	def receive(self, socket):
		""" receives the data from a socket """
		data = socket.recv(self.buffersize)
		text = data.strip().decode("UTF-8")
		return text


class Wrapper(object):

	def __init__(self, mccommand, socket, linebreak):
		self.log = logging.getLogger('wrapper')

		self.mccommand = mccommand
		self.socketaddr = socket
		self.linebreak = linebreak

		self.sout=PIPE
		self.serr=PIPE
		self.sin=PIPE 
		self.process = 0
		self.broadcaster = 0

		# Minecraft process runs?
		self.mcrunning = False
		
		self.log.debug("..:: Start ::..")

		# For ^C
		signal.signal(signal.SIGINT, self.sighandler)

	# ^C Handling
	def sighandler(self, signum, frame):
		self.log.info("Received SIGINT: Shutdown.")
		self.write("stop")

	"""
	Starts the minecraft server and the broadcast for potential clients.
	"""
	def start(self):
		self.broadcaster = Broadcaster(self, self.socketaddr, self.linebreak)
		broadcasterThread = Thread(target=self.broadcaster.do)
		broadcasterThread.start()

		""" starts the wrapper """
		self.log.debug("Starting Wrapper... (%s)" % self.mccommand)

		# XXX: DEBUG:Wrapper:ERROR: parsing Error: Unable to access jarfile minecraft_server.jar.1.7.9
		self.process = Popen(\
				self.mccommand, \
				stdin=self.sin, stdout=self.sout, stderr=self.serr, \
				cwd=os.getcwd(), shell=True,
				universal_newlines=True \
				)

		self.mcrunning = True
		self.log.debug("Starting Wrapper... done")

		## main loop
		while self.mcrunning:
			try:
				output = self.read(self.process.stdout)
				
				if output == "": 
					self.log.debug("wrapper readline is empty")
					self.mcrunning = False
				else:

					o = "]:".join(output.split("]:")[1:]).strip()
					if len(o.strip()) == 0:
						self.log.info( "Server-RAW: %s" % output )
					else:
						self.log.info( "Server: %s" % o )

					try:
						self.broadcaster.broadcast_data(output)
					except:
						self.log.error("parsing %s" % output )
						self.log.debug( traceback.print_exc() )	
						pass

			except IOError:
				self.log.error("IOError.. shutdown")
				self.running = False

		## Shutdown the wrapper
		self.log.debug("Server stoped")
		self.broadcaster.close()
		self.log.info("..:: Goodbye ::..")


	def read(self, stdout):
		""" Read from the given stdin """
		try:
			line = stdout.readline()
			if not isinstance(line, str):
				line = line.decode("utf-8")
			line = line.strip()
			return line
		except:
			self.log.error("Error in Wrapper.read()")
			return ""


	def write(self, msg):
		""" Sends msg to the server """
		try:
			self.process.stdin.write("{0}{1}".format(msg, self.linebreak))
			self.process.stdin.flush()
		except:
			print(traceback.print_exc())
			print("exception write(). msg=%s" % msg)


if __name__ == '__main__':
	main(sys.argv[1:])






