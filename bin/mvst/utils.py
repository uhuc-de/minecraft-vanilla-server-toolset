#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import time
import logging	# used for logging


from .core_functions import CoreFunctions as Core
from .config import Config

from .wrapper_handler import WrapperHandler
from .archive import Archive


class Utils:
	"""
	The Utils class contains all non-core functions which are
	not static and not big enough to be in a standalone class
	"""

	def __init__(self, config):
		if not isinstance(config, Config):
			print("CRITICAL: Utils.config ist not an instance of mvst.Config")
		self.config = config

		self.log = logging.getLogger('Utils')
		self.log.setLevel( 10*int(self.config.getLoglevel("utils")) )


	### Force kill ###

	def forceKill(self):
		""" Sends SIGTERM to the java process """
		wrapper = WrapperHandler(self.config)

		Core.echo("Kill the minecraft server... ");
		cmd = "kill $(ps -u %s -f | grep  \"%s\" | grep -v 'wrapper.py' | grep -v 'grep' | awk '{print $2}')" % ( self.get("core", "user"), wrapper.getJavaCommand() )

		if Core.qx(cmd, Core.QX_RETURNCODE):
			print("ERROR: Cant force-kill the java process!")
			self.log.warning("Killing the process failed!")
		else:
			self.log.info("Killig the process was successful.")
			print("done")

			cmd = "rm -f %s" % self.config.getSocket()
			if Core.qx(cmd, Core.QX_RETURNCODE):
				print("ERROR: Cant remove wrappers socket file")

			cmd = "rm -f %s" % wrapper.getDaemon().getPidFile()
			if Core.qx(cmd, Core.QX_RETURNCODE):
				print("ERROR: Cant remove wrappers pidfile")


	### Whitelist ###

	def whitelist(self, user=""):
		""" adds the given user to the whitelist """
		if len(user) < 1:
			print("Name of the user is not given.")
			return 1

		wrapper = WrapperHandler(self.config)
		archive = Archive(self.config)

		if wrapper.isRunning():
			user = user.lower()
			print("Add to whitelist: %s" % user)
			self.log.info("Add to whitelist: %s" % user)
			wrapper.say("Whitelist user »%s«" % user)

			print("Backup...")
			if archive.backup(user):
				print("Whitelist failed!")
				self.log.error("Whitelist failed!")
				wrapper.say("Whitelist failed!")
			else:
				print("Added »%s« to whitelist" % user)
				wrapper.sendToSocket("whitelist add %s" % user)
				wrapper.say("Added »%s« to whitelist" % user)
		else:
			print("Could not connect to the server!")


	### Update ###

	def update(self, version):
		"""	Updates the minecraft jars the given version """

		wrapper = WrapperHandler(self.config)
		archive = Archive(self.config)

		if len(version) < 1:
			print("The update command needs a version!")
			return 1

		versionfile = '%sversion' % self.config.getServerDir()
		if os.path.isfile(versionfile):
			oldversion = ""
			with open(versionfile, 'r') as versionfile:
				oldversion = versionfile.read().replace('\n', '')
				if oldversion == version:
					print("No update necessary. Server is already on version %s." % version)
					return 0
			print("Update from %s to %s..." % (oldversion, version) )
		else:
			print("Update to %s..." % version)


		startagain=False

		# Download the jars
		Core.echo("Download server.jar and client.jar ... ")

		if self.downloadJars(version):
			print("Done") 

			Core.echo("Backup... ")
			if archive.backup("update_%s" % version):
				print("Failed")
				return 1
			else:
				print("Done")

			if wrapper.isRunning():
				startagain = True
				if wrapper.stop("Update to version %s: Server is going to restart!" % version):
					print("failed to shutdown")
					return 1

			self.installJars(version)

			self.log.info("Update to »%s« was successful" % version)
			print("Update to »%s« was successful" % version)

		else:
			# download failed
			print("Couldn't download the files. Maybe the version was wrong?")
			self.log.info("Unable to download version »%s«." % (version) )
			return 1

		if startagain:
			wrapper.start()


	def downloadJars(self, version):
		""" Downloads the minecraft jars into the tmp directory """
		noerror = True
		
		link = "http://s3.amazonaws.com/Minecraft.Download/versions/{0}/minecraft_server.{0}.jar".format(version)
		cmd = "%s -q -O \"%sminecraft_server.jar\" \"%s\"" % (self.config.get("bins", "wget"), self.config.getTmpDir(), link)
		r1 = Core.qx(cmd, Core.QX_RETURNCODE)
		if r1:
			print("Cant download %s" % link)
			noerror = False

		link = "http://s3.amazonaws.com/Minecraft.Download/versions/{0}/{0}.jar".format(version)
		cmd = "%s -q -O \"%sminecraft_client.jar\" \"%s\"" % (self.config.get("bins", "wget"), self.config.getTmpDir(), link)
		r2 = Core.qx(cmd, Core.QX_RETURNCODE)
		if r2:
			print("Cant download %s" % link)
			noerror = False

		return noerror


	def installJars(self, version):
		""" move the minecraft jars in tmp to their destination and chown them """

		for jar in ['minecraft_server.jar', 'minecraft_client.jar']:
			# move jars to serverdir
			oldfile = "{0}{1}".format( self.config.getTmpDir(), jar )
			newfile = "{0}{1}".format( self.config.getServerDir(), jar )
			os.rename(oldfile, newfile)

			# changing ownership
			cmd = "chown {0}:{1} \"{2}{3}\"".format(self.config.get("core","user"), self.config.get("core","group"), self.config.getServerDir(), jar)
			Core.qx(cmd, Core.QX_RETURNCODE)

		# write current version to file
		cmd = "echo %s > \"%sversion\"" % (version, self.config.getServerDir())
		print (cmd)
		print( Core.qx(cmd, Core.QX_RETURNCODE ) )


	### Overviewer ###

	def overviewer(self):
		""" Starts the overviewer """

		wrapper = WrapperHandler(self.config)
		archive = Archive(self.config)



		# check variables from config
		try:
			_nice = int( self.config.get("overviewer", "nice") )
		except:
			self.log.critical("Overviewer: nice is not an integer!")
			exit(1)

		if _nice < -20 and _nice > 19:
			self.log.critical("Overviewer: nice is not an integer between -20 and 19: %s" % _nice)
			exit(1)

		_settings = os.path.realpath( self.config.get("overviewer", "settings") )
		if not os.path.isfile(_settings):
			self.log.critical("Overviewer: Not a settings file: %s" % _settings)
			exit(1)


		self.log.debug("Perform overviewer")

		lockname = "overviewer"
		if archive.setLock(lockname):
			self.log.error("Can't perform rendering... lock is set.")
			return 1

		starttime = time.time()

		if wrapper.isRunning():
			wrapper.say("Start mapping...")

		if archive.copyServer():
			self.log.error("Can't copy the server for mapping")
			return 1

		cmd = "nice -n {0} overviewer.py --quiet -c {1} 1>>{2} 2>&1".format( _nice, _settings, self.config.getLogfile() )
		if Core.qx(cmd, Core.QX_RETURNCODE):
			self.log.critical("Failed execution of: %s" % cmd)

		if self.isGenpoi():
			cmd = "nice -n {0} overviewer.py --quiet -c {1} --genpoi 1>>{2} 2>&1".format( _nice, _settings, self.config.getLogfile() )
			if Core.qx(cmd, Core.QX_RETURNCODE):
				self.log.critical("Failed execution of: %s" % cmd)

		donetime = time.time()
		elapsed = "{0:.2f}".format( (donetime - starttime) / 60 )

		if wrapper.isRunning():
			wrapper.say("Finished mapping in %s minutes." % elapsed)

		self.log.info("Finished mapping in %s minutes." % elapsed)

		if archive.releaseLock(lockname):
			self.log.error("overviewer: Can't release lock »%s«." % lockname)
			return 1
		return 0


	def isGenpoi(self):
		""" Return the config value of overviewer/genpoi in boolean """
		return self.config.getConfigArray().getboolean("overviewer", "genpoi")



	### Install ###

	def install(self, version):
		""" Creates the directories for a new instance and downloads the jars """
		if len(version) < 3:
			print("CRITICAL: the install command needs a version argument!")
			Core.usage()


		print("Create new instance of mvst named »%s« with minecraft version %s" % (self.config.getInstance(), version) )

		# create directories
		Core.echo("(1/3) make directories... ")
		try:
			os.makedirs( self.config.getServerDir() )
		except OSError:
			pass
		try:
			os.makedirs( self.config.getBackupDir() )
		except OSError:
			pass
		try:
			os.makedirs( "%slogs" % self.config.getHomeDir() )
		except OSError:
			pass
		try:
			os.makedirs( "%stmp" % self.config.getHomeDir() )
		except OSError:
			pass
		try:
			os.makedirs( "%sservercopy" % self.config.getShareDir() )
		except OSError:
			pass
		print("done")

		# download minecraft jars
		Core.echo("(2/3) download jars... ")
		if self.downloadJars(version):
			self.installJars(version)
			print("done")

			# create the shortcut shell script
			Core.echo("(3/3) create shortcut shell... ")
			filename = self.getNewShortcutSkriptFilename( self.config.getInstance() )
			fo = open(filename, "w")
			raw="""#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from mvst.Mvst import Mvst

if __name__ == "__main__":
	m = Mvst(sys.argv[1:])
	exit(m.start())
"""
			fo.write( "#!/bin/bash\n\npython3 mvst-core.py -c mvst-dev.ini -- $@\n" )
			fo.close()
			Core.qx("chmod +x %s" % filename, Core.QX_RETURNCODE)
			print("done")

			print("Now execute »%s start« to start the server." % filename)

		else:
			print("Error")


	def getNewShortcutSkriptFilename(self, name = ""):
		""" generates the filename and checks if the file already exists """
		filename = "%smvst-%s.sh" % (self.getBinDir(), name)
		if os.path.exists(filename):
			filename = self.getNewShortcutSkriptFilename(name+"_")
		return filename






