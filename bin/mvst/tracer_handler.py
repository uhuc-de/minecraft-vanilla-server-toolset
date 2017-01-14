#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import datetime
import logging	# used for logging

from .core_functions import CoreFunctions as Core



class TracerHandler:
	"""
	This class handles everything regarding the tracer
	"""

	def __init__(self, config):
		self.config = config
		self.log = logging.getLogger('TracerHandler')
		self.log.setLevel( 10*int(self.config.getLoglevel("tracer")) )


	def record(self):
		""" Prints the current positions from the playerfiles into the tracerdatabase """
		playerdataDir = "%s%s/playerdata/" % (self.config.getServerDir(), self.config.getMapName())
		tracerdb = self.getTracerDb()

		cmd = "%s %stracer.py \"%s\" \"%s\" " % (self.config.getPython2(), self.config.getBinDir(), playerdataDir, tracerdb)
		
		if Core.qx(cmd, Core.QX_RETURNCODE):
			self.log.critical("Can't execute the tracer!")


	def client(self, args):
		""" Starts the Tracerclient """
		if len(args) < 1:
			enddate = datetime.date.today() - datetime.timedelta(days=7)
			args = "--since %s" % enddate
		
		tracerdb = self.getTracerDb()
		usercache = "%susercache.json" % self.config.getServerDir()
		cmd = "%s %stracer-client.py -c \"%s\" %s \"%s\"" % (self.config.getPython2(), self.config.getBinDir(), usercache, args, tracerdb)

		Core.qx(cmd, Core.QX_SHELL)


	def getTracerDb(self):
		""" Returns the path to the database of the tracer """
		#FIXME: now = datetime.datetime.now().strftime("%Y-%m")
		#return "%stracer_data_%s.sqlite" % (self.config.getServerDir(), now)
		return "%stracer_data.sqlite" % (self.config.getServerDir())


