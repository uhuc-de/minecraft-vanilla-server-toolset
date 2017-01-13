#!/usr/bin/python2
# -*- coding: utf-8 -*-


import os

from .core_functions import CoreFunctions as Core
from .config import Config


class Reports(object):

	def __init__(self, config):
		if not isinstance(config, Config):
			print("CRITICAL: WrapperHandler.config ist not an instance of mvst.Config")
		self.config = config


	def start(self):
		""" Start the submenus to select a logfile """
		lines = ["mvst logs", "server logs", "crash reports"]
		submenu = self.viewList(lines, "Select a directory")

		if submenu == 0:
			directory = self.config.getLogDir()
			self.chooseAndStart(directory, True)
		elif submenu == 1:
			directory = "{0}logs/".format(self.config.getServerDir())
			self.chooseAndStart(directory, True)
		elif submenu == 2:
			directory = "{0}crash-reports/".format(self.config.getServerDir())
			self.chooseAndStart(directory, False)


	def logFile(self, args = []):
		""" Shows the current logfile with less and filters it """
		if len(args) == 0:
			cmd = "less +G %s" % self.config.getLogfile()
		else:
			a = "cat {0} | grep -e \"".format(self.config.getLogfile())
			b = "\" | egrep -e \"".join(args)
			c = "\" | less"
			cmd = "{0}{1}{2}".format(a,b,c)

		if Core.qx(cmd, Core.QX_SHELL):
			#TODO self.log.critical("Can't execute the log view!")
			print("error")


	def chooseAndStart(self, directory, fromBottom=False):
		""" Lists an option of files in the directory and opens them in less """
		filelist = self.getFilelistOfDirectory(directory)
		selected = self.viewList(filelist)
		if selected != None:
			self.viewFile(directory+filelist[selected], fromBottom)


	def getFilelistOfDirectory(self, directory):
		""" Returns a list of files inside given directory """
		cmd = "ls -1 %s" % directory
		filelist = Core.qx(cmd, 3).split("\n")
		filelist = list(filter(None, filelist)) 
		return filelist


	def viewList(self, lines="", selectline="View file"):
		""" Lists the lines and let the user choose one """

		if len(lines) == 0:
			print("No content inside.")
		else:
			out = lines

			#itera = len(out)
			itera = 1
			print("")
			for i in out:
				print("(%s) %s" % (itera, i))
				#itera -= 1
				itera += 1
				
			x = input('%s: ' % selectline)
			try:
				x = int(x)
				if (x >= 1 and x <= len(lines) ):
					return x-1
				else:
					raise IndexError
			except (ValueError, IndexError) :
				return None


	def viewFile(self, filename, fromBottom=False):
		""" Views the given file with less """
		if os.path.isfile(filename):
			b = ""
			less = "less"
			if fromBottom:
				b = " +G "
			if filename.endswith(".gz"):
				less = "zless"
			cmd = "%s %s \"%s\"" % (less, b, filename)
			#print(cmd)
			if Core.qx(cmd, Core.QX_SHELL):
				pass
				#TODO self.log.critical("Can't execute the log view!")
		else:
			print("Can't view file »%s«!" % filename)


