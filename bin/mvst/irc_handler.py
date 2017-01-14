#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import logging	# used for logging
import time # needed for sleep() and duration


from .core_functions import CoreFunctions as Core
from .config import Config
from .daemon_handler import DaemonHandler
from .wrapper_handler import WrapperHandler


class IrcHandler:
	"""
	The Irc class implements the functions that are needed for the irc bridge
	"""

	def __init__(self, config):
		if not isinstance(config, Config):
			print("CRITICAL: IrcHandler.config ist not an instance of mvst.Config")
			exit(1)
		self.config = config
		self.log = logging.getLogger('IrcHandler')
		self.log.setLevel( 10*int(self.config.getLoglevel("irc")) )

		self.daemon = DaemonHandler(self.config, "irc")
		self.wrapper = WrapperHandler(self.config)


	def do(self, command):
		""" Starts a function with the correct commands """
		x = command[0]
			
		if x == "start":
			self.start()
		elif x == "stop":
			self.stop( " ".join(command[1:]) )
		elif x == "status":
			return self.status()
		elif x == "restart":
			self.restart( " ".join(command[1:]) )
			
		else:
			print("irc: unknown command »%s«" % x)


	def start(self):
		"""
		Start the irc-bridge as a daemon
		Return 0 by success
		and 1 by failure
		"""
		Core.echo("Start irc-bridge...")

		time.sleep(5)
		if not self.wrapper.isRunning():
			print("Fail. (wrapper is not running)")
			return 1

		if self.isRunning():
			print("is already running.")
			return 1
		else:
			_instance = self.config.getInstance()

			irccmd = "%s -- %sirc.py -l %s -v %s -r %s -n %s %s %s %s" \
						%(self.config.getPython2(), self.config.getBinDir(), \
						self.config.getLogfile(), self.config.getLoglevel("irc"),
						self.config.get("irc","realname"), self.config.get("irc","nick"), \
						self.config.getSocket(), self.config.get("irc","host"), self.config.get("irc","channel"))

			r = self.daemon.start(irccmd, self.config.getServerDir())

			if r == 0:
				print("Done")
				self.log.info("Started irc-bridge")
				self.wrapper.say("irc-bridge is back online...")
				return 0
			else:
				print("Fail")
				return 1


	def stop(self, reason=""):
		"""
		Stops the irc-bridge
		"""
		Core.echo("Stop irc-bridge...")
		if self.isRunning():

			# TODO: reason mitgeben
			r = self.daemon.stop()

			if r == 0:
				print("Done")
				return 0
			else:
				print("Fail")
				return 1
		else:
			print("bridge is not running.")
			return 2


	def restart(self, reason=""):
		"""
		Restarts the irc-bridge
		"""
		print("Restarting...")
		r = self.stop(reason)
		if r == 0:
			time.sleep(3)
			self.start()


	def status(self):
		"""
		Returns the current status of the irc bridge
		"""
		Core.echo('Checking irc-bridge status...')
		if self.isRunning():
			print("Running.")
			return 0
		else:
			print("Stopped.")
			return 1


	def isRunning(self):
		"""
		Check if the irc-bridge is running as a daemon
		Return 1 for yes and 0 for no
		"""
		r = self.daemon.status()
		if r == 0:
			return 1
		elif r == 3:
			return 0
		else:
			self.log.error("Unknown error inside isIrcRunning() (returncode=%s)" % r)
			return 0


	def getAutorunIrc(self):
		""" returns the bool of the autorun option """
		return self.config.getConfigArray().getboolean("irc", "autorun")


	def getDaemon(self):
		""" Returns the daemon """
		return self.daemon
