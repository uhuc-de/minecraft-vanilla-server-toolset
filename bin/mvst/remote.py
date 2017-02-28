#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import logging	# used for logging
import time # needed for sleep() and duration
import sys

from .core_functions import CoreFunctions as Core
from .config import Config

from .daemon_handler import DaemonHandler
from .wrapper_handler import WrapperHandler
from .archive import Archive


class Remote:
	"""
	The remote class handles the usermanagement for remote connected users
	"""
	def __init__(self, config, username):
		if not isinstance(config, Config):
			print("CRITICAL: Remote.config ist not an instance of mvst.Config")
		self.config = config

		self.log = logging.getLogger('Remote')
		self.log.setLevel( 10*int(self.config.getLoglevel("remote")) )
		
		self.user = username


	def start(self):
		"""
		Starts a shell for a user with special rights
		"""
		remoteip = self.getSshIp()
		
		# check if user exists
		if not ("remote-%s" % self.user) in self.config.getConfigArray():
			print("You (%s) are not allowed to enter the remote shell of instance »%s«!" % (self.user, self.config.getInstance()) )
			self.log.warning("User »%s« (%s) tried to login, but doesnt exist in the config ini!" % (self.user, remoteip))
			exit(1)
		# load configs for user
		self.conf = self.config.getConfigArray()["remote-%s" % self.user]

		# start the shell for the user
		print("You are now remote connected to mvst instance »%s« as %s" % (self.config.getInstance(), self.user) )
		self.log.info("Connected: %s (%s)" % (self.user, remoteip))
		self.menu()


	def menu(self):
		run=1
		self.printWelcome()

		while run:
			i = input("\n> ")

			# primitive commands
			if i.lower() in ["q", "quit", "exit"]: # Quits
				run = 0
				break
			if i.lower() in ["help", "?", "h"]: # Help
				self.printHelp()
				continue
			if i.split(" ")[0].lower() in ["change"]: # Change instance
				self.changeInstance(i.split(" ")[1])
				continue
			
			try:
				command = i.split(' ')[0]
				
				if self.isCommandAllowed(command):
					self.executeCommand( i.split(' ') )
				else:
					print("You are not allowed to execute this command! Abusive behaviour will be reported.")
					self.log.warning("ExecutionWarning (%s): %s" % (self.user, i) )
			except configparser.NoOptionError:
				print("This is not a valid command or you are not allowed to execute it.")

		print("Quitting remote connection")


	def changeInstance(self, instance):
		""" Change from the current remote session to another instance """
		try:
			print("change instance to %s" % instance)
			binDir = self.config.getBinDir()
			cmd = "python3 {0}mvst-core.py -c {0}mvst-{1}.ini -- remote {2}".format(binDir, instance, self.user)
			self.config.startShell(cmd)
		except:
			print("Error during change instance")
			import traceback
			traceback.print_exc(file=sys.stdout)


	def executeCommand(self, command_arr):
		""" Executes the given command inside the mvst """
		self.log.info("Execute (%s): %s" % (self.user, " ".join(command_arr)) )
		cmd = "python3 {0} {1}".format(sys.argv[0], " ".join(command_arr))
		Core.qx(cmd, Core.QX_SHELL)


	def isCommandAllowed(self, command):
		""" check if the given command can be executed by this user """
		command = command.strip().lower()
		try:
			isAllowed = self.config.getConfigArray().getboolean("remote-%s" % self.user, command )
			if isAllowed:
				return True
			else:
				return False
		except:
			return False


	def getListOfAllowedCommands(self):
		""" Get a list of commands which the user can execute """
		allowed = []
		c = self.config.getConfigArray()["remote-"+self.user]
		for i in c:
			if ( self.isCommandAllowed(i) ):
				allowed.append(i)
		return allowed


	def getSshIp(self):
		""" Return the IP of the SSH User (if available) """
		cmd = "echo ${SSH_CONNECTION%% *}"
		ip = Core.qx(cmd, Core.QX_OUTPUT)
		if ip == "":
			return "local"
		return ip


	def printWelcome(self):
		""" Prints the welcome message """
		archive = Archive(self.config)
		print("Version: %s" % archive.getVersion() )
		print("Type »help« to see all available commands")


	def printHelp(self):
		"""
		Prints the help for the remote plugin
		"""
		print("List of commands:")
		print( Core.getCommandList() )
		print("You are allowed to use:")
		print( ", ".join(self.getListOfAllowedCommands()) ) 

