#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import logging	# used for logging

from .core_functions import CoreFunctions as Core
from .config import Config

class DaemonHandler:
	"""
	The daemonhandler class start and stop a daemon with start-stop-daemon and give back a status
	"""

	def __init__(self, config, name):
		if not isinstance(config, Config):
			print("CRITICAL: DaemonHandler.config ist not an instance of mvst.Config")
		self.config = config

		if name == "":
			print("CRITICAL: DaemonHandler init has no name")
			exit(2)
		self.name = name

		self.log = logging.getLogger('DaemonHandler')
		self.log.setLevel( 10*int(self.config.getLoglevel("daemon")) )


	def start(self, cmd, chdir):
		"""
		Starts a command as a daemon
		Return 0 by success
		and 1 by failure
		"""
		# build the command
		_group = self.config.get("core", "group")
		_user = self.config.get("core", "user")
		
		#daemoncmd = "%s -n %s --start --background --chuid %s:%s --user %s --group %s --pidfile %s --make-pidfile --chdir %s --exec %s" %(self.getDaemonBin(), self.name, _user, _group, _user, _group, self.getPidFile(), chdir, cmd)
		daemoncmd = "{0} -n {1} --start --background --chuid {2}:{3} --user {2} --group {3} --pidfile {4} --make-pidfile --chdir {5} --exec {6}".format(self.getDaemonBin(), self.name, _user, _group, self.getPidFile(), chdir, cmd)
		return Core.qx(daemoncmd, Core.QX_RETURNCODE)


	def stop(self):
		"""
		Stops the daemon
		"""
		cmd = "%s --pidfile %s --stop --signal INT --retry 10" % (self.config.get("bins","start-stop-daemon"), self.getPidFile() )
		return Core.qx(cmd, Core.QX_RETURNCODE)


	def status(self):
		"""
		Checks if a daemon is running
		Return Codes:
			0 Program is running.
			1 Program is not running and the pid file exists.
			3 Program is not running.
			4 Unable to determine program status.
		"""
		cmd = "%s --pidfile %s --status" % (self.getDaemonBin(), self.getPidFile() )
		return Core.qx(cmd, Core.QX_RETURNCODE)


	def getDaemonBin(self):
		""" returns the path to the start-stop-daemon binary """
		return self.config.get("bins","start-stop-daemon")


	def getPidFile(self):
		""" return the path of the given pidfile """
		return "%s%s_%s.pid" % (self.config.getTmpDir(), self.name, self.config.getInstance())
