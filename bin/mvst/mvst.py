#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import time # needed for sleep() and duration
import configparser # needed by loadConfig
import logging	# used for logging
import stat # used for chmod


from .reports import Reports
from .config import Config
from .core_functions import CoreFunctions as Core
from .tracer_handler import TracerHandler
from .wrapper_handler import WrapperHandler
from .irc_handler import IrcHandler
from .archive import Archive
from .remote import Remote
from .utils import Utils


class Mvst:
	"""
	Mvst is the core-class of the softwarecollection, it starts the sub-
	processes and loads the config.
	"""

	def __init__(self, argv, configfile):
		"""
		init function of the mvst-core
		"""
		# Variables
		self.__argv = argv

		self.configObj = Config(configfile)
		if self.configObj == None:
			print("Config file »%s« not found!" % argv[1])
			exit(1)


		# init log
		formatter = '%(asctime)s|%(name)s|%(levelname)s|%(message)s'
		_loglevel = int(self.configObj.get("core", "loglevel"))
		_logfile = self.configObj.getLogfile()
		logging.basicConfig(filename=_logfile,level=_loglevel,format=formatter)
		self.log = logging.getLogger('mvst')


	def start(self, args=None):
		"""
		starts the mvst and selects the command
		"""
		if not args:
			args = self.__argv

		try:
			x = args[0]
			args = args[1:]
			args_str = " ".join(args)
				
			if x == "help":
				Core.usage()

			# WrapperHandler

			elif x == "start":
				wrapperHandler = WrapperHandler(self.configObj)
				if not wrapperHandler.start():
					# Wrapper successfully started
					
					ircHandler = IrcHandler(self.configObj)
					if ircHandler.getAutorunIrc():
						ircHandler.start()

			elif x == "stop":
				ircHandler = IrcHandler(self.configObj)
				if ircHandler.isRunning():
					ircHandler.stop()
					time.sleep(3)
				wrapperHandler = WrapperHandler(self.configObj)
				wrapperHandler.stop(args_str)

			elif x == "status":
				wrapperHandler = WrapperHandler(self.configObj)
				wrapperHandler.status()

			elif x == "restart":
				wrapperHandler = WrapperHandler(self.configObj)
				wrapperHandler.restart()

			elif x == "control":
				wrapperHandler = WrapperHandler(self.configObj)
				wrapperHandler.sendToSocket(args)

			elif x == "say":
				wrapperHandler = WrapperHandler(self.configObj)
				wrapperHandler.say(args_str)

			elif x == "shell":
				wrapperHandler = WrapperHandler(self.configObj)
				wrapperHandler.shell(args)

			# IrcHandler

			elif x == "irc":
				ircHandler = IrcHandler(self.configObj)
				return ircHandler.do(args)

			# TracerHandler

			elif x == "tracer":
				tracer = TracerHandler(self.configObj)
				tracer.record()

			elif x == "tracer-client":
				tracer = TracerHandler(self.configObj)
				tracer.client(args_str)

			# Reports

			elif x == "log":
				reports = Reports(self.configObj)
				reports.logFile(args)

			elif x == "reports":
				reports = Reports(self.configObj)
				reports.start()

			# Remote

			elif x == "remote":
				remote = Remote(self.configObj, args[0])
				return remote.start()

			# Archive

			elif x == "backup":
				archive = Archive(self.configObj)
				return archive.backup(args_str)

			elif x == "restore":
				archive = Archive(self.configObj)
				if len(args_str) > 0:
					return archive.restore(args_str)
				else:
					return archive.restoreList()

			# Utils

			elif x == "force-kill":
				utils = Utils(self.configObj)
				return utils.forceKill()

			elif x == "whitelist":
				utils = Utils(self.configObj)
				return utils.whitelist(args_str)

			elif x == "overviewer":
				utils = Utils(self.configObj)
				return utils.overviewer()

			elif x == "update":
				utils = Utils(self.configObj)
				return utils.update(args_str)

			elif x == "install":
				utils = Utils(self.configObj)
				return utils.install(args_str)


			else:
				print("unknown command »%s«" % x)
				Core.usage()
				
		except KeyboardInterrupt:
			pass

if __name__ == "__main__":
	m = Mvst(sys.argv[1], sys.argv[2:])
	exit(m.start())

