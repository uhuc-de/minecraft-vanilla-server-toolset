#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import datetime
import logging	# used for logging
import time # needed for sleep() and duration


from .core_functions import CoreFunctions as Core
from .config import Config
from .daemon_handler import DaemonHandler


class WrapperHandler:
	"""
	This class handles everything regarding the wrapper
	"""

	def __init__(self, config):
		if not isinstance(config, Config):
			print("CRITICAL: WrapperHandler.config ist not an instance of mvst.Config")
		self.config = config
		self.log = logging.getLogger('WrapperHandler')
		self.log.setLevel( 10*int(self.config.getLoglevel("wrapper")) )

		self.daemon = DaemonHandler(self.config, "wrapper")


	def start(self):
		"""
		Start the wrapper as a daemon
		Return 0 by success
		and 1 by failure
		"""
		Core.echo("Start minecraft-server...")

		if self.isRunning():
			print("is already running.")
			return 1
		else:
			# build the command
			_wrapper = "%swrapper.py" % self.config.getBinDir()

			wrappercmd = "%s -- %s -s %s -v %s -l %s --- %s" % (self.config.getPython2(), _wrapper, self.config.getSocket(), self.config.getLoglevel("wrapper"), self.config.getLogfile(), self.getJavaCommand() )
			print(wrappercmd)
			r = self.daemon.start(wrappercmd, self.config.getServerDir()) 
			if r == 0:
				print("Done")
				return 0
			else:
				print("Fail")
				return 1


	def stop(self, reason=""):
		"""
		Stops the daemon wrapper
		"""
		Core.echo("Stop minecraft server...")

		if self.isRunning():
			if reason != "":
				reason = "(Reason: %s)" % reason
			if reason == "restart":
				self.say("Server restarts in 3 seconds.")
			else:
				self.say("Server stops in 3 seconds. %s" % reason)

			r = self.daemon.stop()

			if r == 0:
				print("Done")
				return 0
			else:
				print("Fail")
				return 2
		else:
			print("server is not running.")
			return 1


	def restart(self, reason=""):
		"""
		Restarts the wrapper
		"""
		print("Restarting...")
		if reason == "":
			reason = "restart"
		r = self.stop(reason)
		if r == 0:
			time.sleep(3)
			self.start()


	def status(self):
		"""
		Returns the current status of the server
		"""
		Core.echo('Checking minecraft-server status...')
		if self.isRunning():
			print("Running.")
			return 0
		else:
			print("Stopped.")
			return 1


	def isRunning(self):
		"""
		Check if the wrapper is running. It tests the connection to the socket
		Return True for yes and False for no
		"""
		_socket = self.config.getSocket()
		cmd = "%s %scontrol.py -s %s --check" % (self.config.getPython2(), self.config.getBinDir(), _socket)
		r = "%s" % Core.qx(cmd) # cast int to string
		if r == "0":
			return True
		elif r == "2":
			self.log.debug("Can't connect to socket (%s)!" % _socket)
			return False
		else:
			self.log.critical("Unknown error inside control.py")
			return False


	def sendToSocket(self, message):
		"""
		Sends a message to the server
		"""
		_socket = self.config.getSocket()
		cmd = "echo '%s' | %s %scontrol.py -s %s 2>> %s > /dev/null" % (message, self.config.getPython2(), self.config.getBinDir(), _socket, self.config.getLogfile())
		r = Core.qx(cmd, Core.QX_RETURNCODE)
		
		if (r == "0") or (r == 0):
			return 0
		elif r == "2":
			self.log.debug("Can't connect to socket (%s)" % _socket)
			return 1
		else:
			self.log.error("Unknown error inside control.py (returncode=%s)" % r)
			return 0


	def control(self, message):
		"""
		DEPRECATED
		Sends a message to the server
		"""
		_socket = self.config.getSocket()
		cmd = "echo '%s' | %s %scontrol.py -s %s 2>> %s > /dev/null" % (message, self.config.getPython2(), self.config.getBinDir(), _socket, self.config.getLogfile())
		r = Core.qx(cmd)
		
		if (r == "0") or (r == 0):
			return 0
		elif r == "2":
			self.log.debug("Can't connect to socket (%s)" % _socket)
			return 1
		else:
			self.log.error("Unknown error inside control.py (returncode=%s)" % r)
			return 0


	def say(self, message):
		"""
		Sends a say message to the server
		"""
		return self.sendToSocket("say %s" % message)


	def shell(self, args):
		"""
		Starts a shell for the user
		"""
		cmd = "tail -n 25 %s" % self.config.getLogfile()
		print( Core.qx(cmd, Core.QX_OUTPUT) )
		shellcmd = "%s %scontrol.py -s %s" % (self.config.getPython2(), self.config.getBinDir(), self.config.getSocket())
		Core.qx(shellcmd, Core.QX_SHELL)


	def getJavaCommand(self):
		""" Returns the command to start the java process """
		cmd = "java -jar %sminecraft_server.jar %s nogui" % (self.config.getServerDir(), self.config.get("wrapper", "javaopts"))
		return cmd.replace("  ", " ")


	def getDaemon(self):
		""" Returns the daemon """
		return self.daemon

