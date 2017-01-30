#!/usr/bin/python2
# -*- coding: utf-8 -*-


import os
import configparser # needed to load the Config
import logging	# used for logging

from .core_functions import CoreFunctions as Core


class Config:
	"""
	The Config class loads the config and provide it to the other mvst classes
	"""

	def __init__(self, configfile):

		# Load Config
		self.__config = self.loadConfig(configfile)
		if self.__config == None:
			print("Config file »%s« not found!" % configfile)
			exit(1)

		self.log = logging.getLogger('config')

		# Load Mapname
		self.mapname = self.loadMapName(retry=True)
		if self.mapname == "":
			print("Can't load the mapname from {0}server.properties!".format(self.getServerDir()))
			exit(1)



	def loadConfig(self,filename):
		"""
		Loads the config file and returns a dict (always contains strings)

		get value by eg:
		CONFIG["core"].get("instance", "default")
		"""
		config = configparser.ConfigParser()
		try:
			config.read(filename)
		except:
			print("CRITICAL: can't parse ini-file »%s«!" % filename)
			return None
			# TODO: handle exceptions https://docs.python.org/3/library/configparser.html#exceptions
		return config


	def get(self, section, key, print_error=True):
		"""
		Gets the value from a key from the config or throws an error
		"""
		c = self.__config[section].get(key)
		if c == None:
			if (print_error):
				errmsg = "key »%s« inside the config section »%s« not found" % (key, section)
				self.log.warning(errmsg)
				print (errmsg)
			return ""
		return c


	def getConfigArray(self):
		""" Returns the whole config """
		return self.__config




	def getInstance(self):
		""" Return the current instance value from the config """
		instance = self.get("core","instance")
		if len(instance) < 1:
			print("CRITICAL ERROR: No »instance« value found in ini-file!")
		return instance
		
	def getSocket(self):
		""" Return the current wrapper socket from the config """
		return "%swrapper_%s.socket" % ( self.getTmpDir(), self.getInstance() ) 

	def getPython2(self):
		""" returns the path to the python2 bin """
		return self.get("bins", "python2")

	def getPython3(self):
		""" returns the path to the python3 bin """
		return self.get("bins", "python3")

	def getLogfile(self):
		""" Return the current logfile value from the config """
		return "%smvst_%s.log" % ( self.getLogDir(), self.getInstance() )

	def getLoglevel(self):
		""" Returns the current loglevel """
		return self.get("core", "loglevel")


	def getLoglevel(self, submodule = "core"):
		""" Returns the current loglevel of the given submodule """
		try:
			loglevel = self.get(submodule, "loglevel", False)
		except:
			loglevel = ""
		if len(loglevel) < 1:
			return self.getLoglevel()
		else:
			return loglevel

	### Directory getters ###


	def getHomeDir(self):
		""" Return the current homedir by the absolute path of __file__ and removes the 'bin' dir """
		homedir = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../.."))
		return homedir+"/"

	def getTmpDir(self):
		""" Return the current tmp dir """
		return "%stmp/" % self.getHomeDir()

	def getBinDir(self):
		""" Return the current bin dir """
		return "%sbin/" % self.getHomeDir()

	def getServerDir(self):
		""" Return the current server dir """
		return "%sserver/%s/" % ( self.getHomeDir(), self.getInstance() )

	def getShareDir(self):
		""" Return the current share dir """
		return "%sshare/%s/" % ( self.getHomeDir(), self.getInstance() )

	def getBackupDir(self):
		""" Return the current backup dir """
		return "%sbackups/%s/" % ( self.getHomeDir(), self.getInstance() )

	def getLogDir(self):
		""" Return the current log dir """
		return "%slogs/" % self.getHomeDir()

	def loadMapName(self, retry=False):
		""" Parses the mapname out of the current server.properties """
		propfile = "{0}server.properties".format(self.getServerDir())
		cmd = "grep \"level-name\" \"{0}\" | cut -d \"=\" -f 2".format(propfile)
		level_name = Core.qx(cmd, Core.QX_OUTPUT)
		if level_name == "" and retry == True:
			cmd = "echo \"level-name=world\" >> {0}".format(propfile)
			Core.qx(cmd, Core.QX_RETURNCODE)
			level_name = self.loadMapName()
		return level_name

	def getMapName(self):
		""" Returns the name of the map """
		return self.mapname





