#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import time # needed for sleep() and duration
import subprocess # needed by qx()
import configparser # needed by loadConfig
import logging	# used for logging
import datetime # needed for date calculations
import getopt

import re # regex

import pprint # needed sometimes during debugging 


class Mvst:
	"""
	Mvst is the core-class of the softwarecollection, it starts the sub-
	processes and loads the config.
	"""

	
	def __init__(self, argv):
		"""
		init function of the mvst-core
		"""
		# Variables
		self.__argv = ""
		
		# Loglevel variables
		self.LOGLEVEL = ('NONE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

		self.CRITICAL = 5
		self.ERROR = 4
		self.WARNING = 3
		self.INFO = 2
		self.DEBUG = 1

		# Check if valid arguments
		if len(argv) < 4:
			print("to few arguments")
			self.usage()

		# getopt
		try:
			opts, args = getopt.getopt(argv, "hc:", ["help"] )	# Option with ":" need an Argument
		except getopt.GetoptError:
			print("Unknown arguments.")
			self.usage()

		for opt, arg in opts:
			if opt in ("-h", "--help"):
				self.usage()
			elif opt in "-c": 
				self.__config = self.loadConfig(arg)
				if self.__config == None:
					print("Config file »%s« not found!" % argv[1])
					exit(1)
			else:
				print("unknown argument!")
				self.usage()

		self.__argv = argv[argv.index("--")+1:]
		
		# init log
		formatter = '%(asctime)s|%(name)s|%(levelname)s|%(message)s'
		_loglevel = int(self.get("core", "loglevel"))
		_logfile = self.getLogfile()
		logging.basicConfig(filename=_logfile,level=_loglevel,format=formatter)
		self.log = logging.getLogger('mvst')

		self.wrapper = WrapperCtl(self)
		self.irc = Irc(self)
		self.archive = Archive(self)


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
				self.usage()

			elif x == "start":
				self.wrapper.wrapperStart()
			elif x == "stop":
				self.wrapper.wrapperStop(args_str)
			elif x == "status":
				return self.wrapper.wrapperStatus()
			elif x == "restart":
				self.wrapper.wrapperRestart(args_str)
			elif x == "control":
				self.wrapper.control(args)
			elif x == "say":
				w = WrapperCtl(self)
				w.say(args_str)
			elif x == "shell":
				self.wrapper.shell(args)
			elif x == "force-kill":
				self.forceKill()
			elif x == "irc":
				return self.irc.do(args)
			elif x == "remote":
				remote = Remote(self, args[0])
				remote.start()

			elif x == "overviewer":
				self.overviewer()
			elif x == "whitelist":
				self.whitelist(args_str)
			elif x == "update":
				self.update(args_str)
				
			elif x == "backup":
				self.archive.backup(args_str)

			elif x == "tracer":
				self.tracerLog()
				
			elif x == "log":
				self.logViewer(args)

			elif x == "tracer-client":
				self.tracerClient(args_str)

			elif x == "crash-reports":
				self.crashReports(args_str)


			else:
				print("unknown command »%s«" % x)
				self.usage()
				
		except KeyboardInterrupt:
			pass



	def viewFile(self, filename, fromBottom=False):
		""" Views the given file with less """
		if os.path.isfile(filename):
			b = ""
			if fromBottom:
				b = " +G "
			cmd = "less %s \"%s\"" % (b, filename)
			#print(cmd)
			if self.startShell(cmd):
				self.log.critical("Can't execute the log view!")
		else:
			print("Can't view file »%s«!" % args)


	def getVersion(self):
		""" Returns the current version of the minecraft server if possible """
		cmd = "cat %sversion" % self.getServerDir()
		if not self.qx(cmd):
			return self.qx(cmd, returnoutput=True)
		else:
			return "No version available"





	### Crash Reports ###

	def crashReports(self, args):
		""" Shows a menu or the crash-reports with less """
		reportPath = "%scrash-reports/" % self.getServerDir()
		if os.path.isdir(reportPath): 
			if len(args) < 1:
				self.crashReportsList(reportPath)
			else:
				self.crashReportsView(args)
		else:
			print("No crash reports available")

	def crashReportsList(self, reportPath):
		""" List the available (max 10 newest) crash reports """
		limit = 3
		cmd = "ls -1 \"%s\" | head -n %s" % (reportPath, limit)
		out = self.qx(cmd, returnoutput=True)
		if len(out.strip()) == 0:
			print("No crash reports available")
		else:
			out = out[:-1].split("\n")

			itera = len(out)
			for i in out:
				print("(%s) %s" % (itera, i))
				itera -= 1

			x = input('View file: ')
			try:
				x = int(x)
				self.viewFile(reportPath+out[-x])
			except (ValueError, IndexError) :
				print("Wrong input.")


	### Log ###

	def logViewer(self, args):
		""" Views the current logfile with less """
		cmd = "less +G %s" % self.getLogfile()
		if self.startShell(cmd):
			self.log.critical("Can't execute the log view!")


	### Tracer ###

	def tracerLog(self):
		""" Prints the current positions from the playerfiles into the tracerdatabase """
		playerdataDir = "%s%s/playerdata/" % (self.getServerDir(), self.getMapName())
		tracerdb = self.getTracerDb()

		cmd = "%s %stracer.py \"%s\" \"%s\" " % (self.getPython2(), self.getBinDir(), playerdataDir, tracerdb)
		
		if self.qx(cmd):
			self.log.critical("Can't execute the tracer!")


	def tracerClient(self, args):
		""" Starts the Tracerclient """
		if len(args) < 1:
			enddate = datetime.date.today() - datetime.timedelta(days=7)
			args = "--since %s" % enddate
		
		tracerdb = self.getTracerDb()
		usercache = "%susercache.json" % self.getServerDir()
		cmd = "%s %stracer-client.py -c \"%s\" %s \"%s\"" % (self.getPython2(), self.getBinDir(), usercache, args, tracerdb)

		self.startShell(cmd)



	### Update ###

	def update(self, version):
		"""	Updates the minecraft jars the given version """
		
		if len(version) < 1:
			print("The update command needs a version!")
			return 1

		versionfile = '%sversion' % self.getServerDir()
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
		self.echo("Download server.jar ... ")
		cmd = "%s -q -O \"%sminecraft_server.jar\" \"http://s3.amazonaws.com/Minecraft.Download/versions/%s/minecraft_server.%s.jar\"" % (self.get("bins", "wget"), self.getTmpDir(), version, version)
		r1 = self.qx(cmd)
		if r1:
			print("fail!")
		else:
			print("done")

		self.echo("Download client.jar ... ")
		cmd = "%s -q -O \"%sminecraft_client.jar\" \"http://s3.amazonaws.com/Minecraft.Download/versions/%s/%s.jar\"" % (self.get("bins", "wget"), self.getTmpDir(), version, version)
		r2 = self.qx(cmd)
		if r2:
			print("fail!")
		else:
			print("done")

		# check if download was successfull
		if (r1 != "0") and (r2 != "0"):

			self.echo("Backup... ")
			if self.archive.backup("update_%s" % version):
				print("Failed")
				return 1
			else:
				print("Done")

			if self.wrapper.isWrapperRunning():
				startagain = True
				if self.wrapper.wrapperStop("Update to version %s: Server is going to restart!" % version):
					print("failed to shutdown")
					return 1
				
				
			# move jars to serverdir
			os.rename("%sminecraft_server.jar" % self.getTmpDir(), "%sminecraft_server.jar" % self.getServerDir())
			os.rename("%sminecraft_client.jar" % self.getTmpDir(), "%sminecraft_client.jar" % self.getServerDir())

			# changing ownership
			self.qx("chown %s:%s \"%sminecraft_server.jar\"" % (self.get("core","user"), self.get("core","group"), self.getServerDir()) )
			self.qx("chown %s:%s \"%sminecraft_client.jar\"" % (self.get("core","user"), self.get("core","group"), self.getServerDir()) )

			# write current version to file
			self.qx("echo %s > \"%sversion\"" % (version, self.getServerDir()) )

			self.log.info("Update to »%s« was successful" % version)
			print("Update to »%s« was successful" % version)

		else:
			# download failed
			print("Couldn't download the files. Maybe the version was wrong?")
			self.log.info("Unable to download version »%s«. Returncodes of wget were »%s« and »%s«." % (version, r1, r2) )
			return 1

		if startagain:
			self.wrapper.wrapperStart()



	### Overviewer ###

	def overviewer(self):
		""" Starts the overviewer """

		self.log.debug("Perform overviewer")

		lockname = "overviewer"
		if self.setLock(lockname):
			self.log.info("Can't perform rendering... lock is set.")
			return 1

		starttime = time.time()

		if self.wrapper.isWrapperRunning():
			self.wrapper.say("Start mapping...")

		if self.copyServer():
			self.log.error("Can't copy the server for mapping")
			return 1

		cmd = "%soverviewer.sh -n %s -c %s -l %s " % (self.getBinDir(), self.get("overviewer", "nice"), self.get("overviewer", "settings"), self.getLogfile() )
		self.qx(cmd)

		donetime = time.time()
		elapsed = "{0:.2f}".format( (donetime - starttime) / 60 )

		if self.wrapper.isWrapperRunning():
			self.wrapper.say("Finished mapping in %s minutes." % elapsed)

		self.log.info("Finished mapping in %s minutes." % elapsed)

		if self.releaseLock(lockname):
			self.log.info("overviewer: Can't release lock »%s«." % lockname)
			return 1
		return 0


	### Whitelist ###

	def whitelist(self, user=""):
		""" adds the given user to the whitelist """
		if len(user) < 1:
			print("Name of the user is not given.")
			return 1

		if self.wrapper.isWrapperRunning():
			user = user.lower()
			print("Add to whitelist: %s" % user)
			self.log.info("Add to whitelist: %s" % user)
			self.wrapper.say("Whitelist user »%s«" % user)

			print("Backup...")
			if self.archive.backup(user):
				print("Whitelist failed!")
				self.log.error("Whitelist failed!")
				self.wrapper.say("Whitelist failed!")
			else:
				print("Added »%s« to whitelist" % user)
				self.wrapper.control("whitelist add %s" % user)
				self.wrapper.say("Added »%s« to whitelist" % user)
		else:
			print("Could not connect to the server!")


	### Force kill ###

	def forceKill(self):
		""" Sends SIGTERM to the java process """
		self.echo("Kill the minecraft server... ");
		cmd = "kill $(ps -u %s -f | grep  \"%s\" | grep -v 'wrapper.py' | grep -v 'grep' | awk '{print $2}')" % ( self.get("core", "user"), self.wrapper.getJavaCommand() )

		if self.qx(cmd):
			print("ERROR: Cant force-kill the java process!")
			self.log.warning("Killing the process failed!")
		else:
			self.log.info("Killig the process was successful.")
			print("done")

			cmd = "rm -f %s" % self.getSocket()
			if self.qx(cmd):
				print("ERROR: Cant remove wrappers socket file")

			cmd = "rm -f %s" % self.wrapper.getDaemon().getPidFile()
			if self.qx(cmd):
				print("ERROR: Cant remove wrappers pidfile")



	### Server copy ###

	def copyServer(self):
		""" Copies the whole server directory to the share file """

		lockname = "servercopy"
		if self.setLock(lockname):
			self.log.info("Can't copy server. Lock is set.")
			print("Can't copy server. Lock is set.")
			return 1

		self.log.debug("Perform servercopy")

		if self.wrapper.isWrapperRunning():
			self.wrapper.control("save-off");
			self.wrapper.control("save-all");
			time.sleep(5)

		cmd = "rsync -a \""+self.getServerDir()+"\" \""+self.getShareDir()+"servercopy\""
		if self.qx(cmd):
			print("error occured!")

		if self.wrapper.isWrapperRunning():
			self.wrapper.control("save-on");

		if self.releaseLock(lockname):
			self.log.info("copyServer: Can't release lock »%s«." % lockname)
			print("copyServer: Can't release lock »%s«." % lockname)
			return 1
		return 0




	### Locking ###

	

	def setLock(self, name):
		""" Set a lockfile with a specific name
			returncodes:
			0 lockfile was created successfully
			1 lockfile already exists
			2 empty variable <name>
		"""
		if name != "":
			lockfile = "%s%s-%s.lock" % (self.getTmpDir(), self.getInstance(), name)
			if os.path.isfile(lockfile): 
				self.log.warning("Lockfile »%s« already exists!" % lockfile)
				return 1
			else:
				return self.qx("touch %s" % lockfile)
		else:
			self.log.error("None name set for lockfile!" % name)
			return 2



	def releaseLock(self, name):
		""" Release a lockfile with a specific name
			returncodes:
			0 lockfile was released successfully
			1 lockfile not found
			2 empty variable <name>
		"""
		if name != "":
			lockfile = "%s%s-%s.lock" % (self.getTmpDir(), self.getInstance(), name)
			if os.path.isfile(lockfile):
				return self.qx("rm %s" % lockfile)
			else:
				self.log.warning("Lockfile »%s« does not exist!" % lockfile)
				return 1
		else:
			self.log.error("None name set for lockfile!" % name)
			return 2



	### Config ###


	def loadConfig(self,filename):
		"""
		Loads the config file and returns a dict (always contains strings)

		get value by:
		CONFIG["core"].get("instance", "default")
		"""
		config = configparser.ConfigParser()
		try:
			config.read(filename)
		except:
			print("CRITICAL: can't parse ini-file »%s«!" % filename)
			return None
			# https://docs.python.org/3/library/configparser.html#exceptions
		return config


	def get(self, section, key):
		"""
		Gets the value from a key from the config or throws an error
		"""
		c = self.__config[section].get(key)
		if c == None:
			errmsg = "key »%s« inside the config section »%s« not found" % (key, section)
			self.log.critical(errmsg)
			print (errmsg)
			return ""
		return c


	def getConfigArray(self):
		""" Returns the whole config """
		return self.__config

	def getInstance(self):
		""" Return the current instance value from the config """
		return self.get("core","instance")

	def getSocket(self):
		""" Return the current wrapper socket from the config """
		return "%swrapper_%s.socket" % ( self.getTmpDir(), self.getInstance() ) 

	def getPython2(self):
		""" returns the path to the python2 bin """
		return self.get("bins", "python2")

	def getLogfile(self):
		""" Return the current logfile value from the config """
		return "%slogs/mvst_%s.log" % ( self.getHomeDir(), self.getInstance() )

	def getLoglevel(self):
		""" Returns the current loglevel """
		return self.get("core", "loglevel")

	def getHomeDir(self):
		""" Return the current homedir by the absolute path of __file__ and removes the 'bin' dir """
		homedir = os.path.abspath(os.path.join(os.path.abspath(__file__), "../.."))
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

	def getAutorunIrc(self):
		""" returns the bool of the autorun option """
		return self.__config.getboolean("irc", "autorun")

	def getMapName(self):
		""" Parses the mapname out of the current server.properties """
		cmd = "grep \"level-name\" \"%sserver.properties\" | cut -d \"=\" -f 2" % self.getServerDir()
		return self.qx(cmd, returnoutput=True)

	def getTracerDb(self):
		""" Returns the path to the database of the tracer """
		return "%stracer_data.sqlite" % self.getServerDir()


	### Common ###

	def echo(self, s):
		"""Do not output the trailing newline with print()"""
		print("%s " % s, end="", flush=True)
		#print('.',end="",flush=True)


	def startShell(self, cmd):
		"""
		Starts the command in the shell without returning or printing something
		https://docs.python.org/3/library/subprocess.html#replacing-os-system
		"""
		try:
			subprocess.call(cmd, shell=True)
		except OSError as e:
			self.log.error("Execution failed:", e, file=sys.stderr)


	def qx(self, cmd, returnoutput=False):
		"""
		Executes a command in the shell and returns the returncode or the output

		return values:
		0 - everything is alright
		1 - error occured

		TODO: http://xahlee.info/perl-python/system_calls.html
		"""
		self.log.debug("qx: %s" % cmd )
		try:
			output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).splitlines()
			returncode = 0
		except subprocess.CalledProcessError as e: # Do if returncode != 0
			output = e.output.splitlines()
			#self.log.debug("qx returns %s - %s" %(e.returncode, cmd))
			returncode = "%s" % e.returncode
			if returncode == None:
				returncode = "typeOfNone"

		out = ""
		for i in output:
			out = out+(i.decode('unicode_escape'))
			if len(output) > 1 and out[-1] != "\n":
				out = out+"\n"
		if returnoutput:
			return out

		return returncode


	def getCommandList(self):
		return """	help 			Print this message

	start			Starts the server
	stop			Stops the server
	status			Shows the status of the server
	restart			Restarts the Server

	log			Open the logfile with less
	shell			Show the tail of the logfile and starts the minecraft shell

	say <msg>		Say <msg> ingame
	control <cmd>		Sends a raw command to the server
	update <version>	Perform backup and change to <version> (eg. 1.5.6)
	whitelist <user> 	Perform backup and add <user> to whitelist

	backup <reason>		Backups the server
	(restore [backup]	Restore a specific backup)

	overviewer		Renders the overviewer map
	irc <start|stop|restart|status>	Controls the irc-bridge

	tracer			Logs the players positions
	tracer-client		View and filter the tracer positions

	crash-reports	Let you select and view the crash-reports
		"""


	def usage(self):
		"""
		Prints the manual and then exits.
		"""
		helpmsg = """Usage: %s -c /path/to/config.ini -- <command> [<arguments>]

Command:
%s
		""" % ( os.path.basename(__file__), self.getCommandList())
		print(helpmsg)
		exit(1)



########################################################





	### Backup / Restore ###



class Archive:
	"""
	The Archive class handles the backup and the restore of the server
	"""
	def __init__(self, mvst):
		if not isinstance(mvst, Mvst):
			print("CRITICAL: Backup.mvst ist not an instance of Mvst")
		self.mvst = mvst
		self.log = logging.getLogger('archive')



	def backup(self, reason=""):
		""" Backups the server """

		if len(reason) < 1:
			print("Too few arguments! (Backup needs a reason!)")
			return 1

		# sanitize the reason string
		reason = reason.lower()
		p = re.compile("[^a-z0-9_\-]+")
		reason = p.sub("", reason)

		timestamp = time.strftime("%Y-%m-%d-%H%M%S")
		backupfile = "%s_%s" % (timestamp, reason)

		if self.mvst.copyServer():
			print("Abort backup!")
			self.log.error("abort backup")
			return 1

		self.log.debug("Perform backup »%s«" % reason)
		
		if self.mvst.wrapper.isWrapperRunning():
			self.mvst.wrapper.say("Performing world backup »%s«" % reason)

		cmd = "tar -c -jh --exclude-vcs -C \"%sservercopy\" -f \"%s%s.tar.bz2\" ./" \
				% (self.mvst.getShareDir(), self.mvst.getBackupDir(), backupfile)

		if self.mvst.qx(cmd):
			self.log.error("Fail to create the tar.bz2 backup file!")
			return 1

		# generate md5sum
		if self.generateMd5(backupfile):
			self.log.error("Could not create the md5 sum!")

		# create the symlinks to the latest backup files
		self.createLatestLink(backupfile, ".tar.bz2")
		self.createLatestLink(backupfile, ".tar.bz2.md5")

		if self.mvst.wrapper.isWrapperRunning():
			self.mvst.wrapper.say("Backup complete")

		self.log.info("Backup saved as %s.tar.bz2" % backupfile)


	def createLatestLink(self, filename, extension):
		""" create the symlink that points to the latest backup """
		latest = "latest%s" % extension
		if os.path.exists("%s%s" %(self.mvst.getBackupDir(), latest)):
			os.remove("%s%s" %(self.mvst.getBackupDir(), latest))
		cmd = "cd %s && ln %s%s %s" % (self.mvst.getBackupDir(), filename, extension, latest)
		if self.mvst.qx(cmd):
			self.log.error("Failure during the creation of the %s link!" % latest)


	def generateMd5(self, filename):
		""" Generates the md5 checksum of the given filename
			(without file extension) and saves the result in
			a file next to it
		"""
		cmd = "cd %s && md5sum %s.tar.bz2 > %s.tar.bz2.md5" %(self.mvst.getBackupDir(), filename, filename)
		return self.mvst.qx(cmd)


	def checkMd5(self, filename):
		""" Checks the generated md5 checksum of the given
			filename (without file extension)
			return 0 if everything is OK and 1 if check failed
		"""
		cmd = "cd %s && md5sum -c %s.tar.bz2 --quiet" %(self.mvst.getBackupDir(), filename)
		return self.mvst.qx(cmd)


	def restore(self):
		""" Restores the map from a Backupfile """
		pass
#
# do_restore() {
# 	if [[ -z "$1" ]]; then
# 		echo "List the latest backups:"
# 		ls -1 ${_DIR_BACKUP}/*.tar.bz2 | xargs -n1 basename | tail -n 11 | head -n 10
# 		exit 0
# 	fi
#
# 	# validate backup file
# 	i=$(cd ${_DIR_BACKUP}/; md5sum --quiet -c ${1}.md5)
# 	ret=$?
# 	if [[ $ret -eq 0 ]]; then
# 		echo "md5 Check passed"
# 	else
# 		echo "Given file failed md5sum check!"
# 		exit 1
# 	fi
#
# 	log "restore" $_INFO "Perform restore of backup \"${1}\""
# 	echo "Backup before restore"
# 	do_backup "restore"
#
# 	echo -n "Restore backup \"$1\"..."
# 	tar --overwrite -xjf ${_DIR_BACKUP}/${1} -C ${_DIR_SERVER}
# 	ret=$?
# 	if [[ $ret -eq 0 ]]; then
# 		echo " successfull!"
# 		log "restore" $_INFO "Restoring of backup \"${1}\" successfull"
# 	else
# 		echo " failed!"
# 		log "restore" $_ERROR "Restoring of backup \"${1}\" failed!"
# 		exit 1
# 	fi
#
#
# }
#







########################################################



class WrapperCtl:
	"""
	The wrapper control class handles the functions of the wrapper
	"""
	def __init__(self, mvst):
		if not isinstance(mvst, Mvst):
			print("CRITICAL: Remote.mvst ist not an instance of Mvst")
		self.mvst = mvst
		self.name = "" # not more than 15 characters due to »comm«-name of kernel # TODO
		self.log = logging.getLogger('wrapperctl')

		self.daemon = Daemon(self.mvst, "wrapper") # TODO: write instance in daemon-name?


	def wrapperStart(self):
		"""
		Start the wrapper as a daemon
		Return 0 by success
		and 1 by failure
		"""
		self.mvst.echo("Start minecraft-server...")

		if self.isWrapperRunning():
			print("is already running.")
			return 1
		else:
			# build the command
			_wrapper = "%swrapper.py" % self.mvst.getBinDir()

			wrappercmd = "%s -- %s -s %s -v %s -l %s --- %s" % (self.mvst.getPython2(), _wrapper, self.mvst.getSocket(), self.mvst.getLoglevel(), self.mvst.getLogfile(), self.getJavaCommand() )
			r = self.daemon.start(wrappercmd, self.mvst.getServerDir()) 
			if r == 0:
				print("Done")
				if self.mvst.getAutorunIrc():
					self.mvst.irc.ircStart()
				return 0
			else:
				print("Fail")
				return 1


	def wrapperStop(self, reason):
		"""
		Stops the daemon wrapper
		"""
		self.mvst.echo("Stop minecraft server...")

		if self.isWrapperRunning():
			if reason != "":
				reason = "(Reason: %s)" % reason
			if reason == "restart":
				self.say("Server restarts in 3 seconds.")
			else:
				self.say("Server stops in 3 seconds. %s" % reason)

			if self.mvst.irc.isIrcRunning():
				self.mvst.irc.ircStop()
				
			time.sleep(3)
				
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


	def wrapperRestart(self, reason):
		"""
		Restarts the wrapper
		"""
		print("Restarting...")
		if reason == "":
			reason = "restart"
		r = self.wrapperStop(reason)
		if r == 0:
			time.sleep(3)
			self.wrapperStart()


	def wrapperStatus(self):
		"""
		Returns the current status of the server
		"""
		self.mvst.echo('Checking minecraft-server status...')
		if self.isWrapperRunning():
			print("Running.")
			return 0
		else:
			print("Stopped.")
			return 1


	def isWrapperRunning(self):
		"""
		Check if the wrapper is running. It tests the connection to the socket
		Return True for yes and False for no
		"""
		_socket = self.mvst.getSocket()
		cmd = "%s %scontrol.py -s %s --check" % (self.mvst.getPython2(), self.mvst.getBinDir(), _socket)
		r = "%s" % self.mvst.qx(cmd) # cast int to string

		if r == "0":
			return True
		elif r == "2":
			self.log.debug("Can't connect to socket (%s)!" % _socket)
			return False
		else:
			self.log.critical("Unknown error inside control.py")
			return False


	def control(self, message):
		"""
		Sends a message to the server
		"""
		_socket = self.mvst.getSocket()
		cmd = "echo '%s' | %s %scontrol.py -s %s 2>> %s > /dev/null" % (message, self.mvst.getPython2(), self.mvst.getBinDir(), _socket, self.mvst.getLogfile())
		r = self.mvst.qx(cmd)
		
		if r == "0":
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
		return self.control("say %s" % message)


	def shell(self, args):
		"""
		Starts a shell for the user
		"""
		cmd = "tail -n 25 %s" % self.mvst.getLogfile()
		print( self.mvst.qx(cmd, returnoutput=True) )
		shellcmd = "%s %scontrol.py -s %s" % (self.mvst.getPython2(), self.mvst.getBinDir(), self.mvst.getSocket())
		self.mvst.startShell(shellcmd)


	def getJavaCommand(self):
		""" Returns the command to start the java process """
		cmd = "java -jar %sminecraft_server.jar %s nogui" % (self.mvst.getServerDir(), self.mvst.get("wrapper", "javaopts"))
		return cmd.replace("  ", " ")


	def getDaemon(self):
		""" Returns the daemon """
		return self.daemon




########################################################



class Remote:
	"""
	The remote class handles the usermanagement for remote connected users
	"""
	def __init__(self, mvst, username):
		if not isinstance(mvst, Mvst):
			print("CRITICAL: Remote.mvst ist not an instance of Mvst")
		self.mvst = mvst
		self.log = logging.getLogger('remote')
		self.user = username


	def start(self):
		"""
		Starts a shell for a user with special rights
		"""
		remoteip = self.getSshIp()
		
		# check if user exists
		if not ("remote-%s" % self.user) in self.mvst.getConfigArray():
			print("You (%s) are not allowed to enter the remote shell!" % self.user)
			self.log.warning("User »%s« (%s) tried to login, but doesnt exist in the config ini!" % (self.user, remoteip))
			exit(1)
		# load configs for user
		self.conf = self.mvst.getConfigArray()["remote-%s" % self.user]

		# start the shell for the user
		print("You are now remote connected to mvst instance »%s« as %s" % (self.mvst.getInstance(), self.user) )
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
			home = self.mvst.getHomeDir()
			cmd = "python3 %smvst-core.py -c %smvst-%s.ini -- remote %s" % (home, home, instance, self.user)
			print("cmd=%s" % cmd)
		except:
			print("Error during change instance")


	def executeCommand(self, command):
		""" Executes the given command inside the mvst """
		self.log.info("Execute (%s): %s" % (self.user, " ".join(command)) )
		self.mvst.start(command)


	def isCommandAllowed(self, command):
		""" check if the given command can be executed by this user """
		command = command.strip().lower()
		isAllowed = self.mvst.getConfigArray().getboolean("remote-%s" % self.user, command )
		if isAllowed:
			return True
		else:
			return False


	def getListOfAllowedCommands(self):
		""" Get a list of commands which the user can execute """
		allowed = []
		c = self.mvst.getConfigArray()["remote-"+self.user]
		for i in c:
			if ( self.isCommandAllowed(i) ):
				allowed.append(i)
		return allowed


	def getSshIp(self):
		""" Return the IP of the SSH User (if available) """
		cmd = "echo ${SSH_CONNECTION%% *}"
		ip = self.mvst.qx(cmd, returnoutput=True)
		if ip == "":
			return "local"
		return ip


	def printWelcome(self):
		""" Prints the welcome message """
		print("Version: %s" % self.mvst.getVersion() )
		print("Type »help« to see all available commands")


	def printHelp(self):
		"""
		Prints the help for the remote plugin
		"""
		print("List of commands:")
		print( self.mvst.getCommandList() )
		print("You are allowed to use:")
		print( ", ".join(self.getListOfAllowedCommands()) ) 



########################################################


class Daemon:
	"""
	The daemon class start and stop a daemon with start-stop-daemon and give back a status
	"""

	def __init__(self, mvst, name):
		if not isinstance(mvst, Mvst):
			print("CRITICAL: Daemon's mvst ist not an instance of Mvst")
		self.mvst = mvst
		self.log = logging.getLogger('daemon')
		self.name = name


	def start(self, cmd, chdir):
		"""
		Starts a command as a daemon
		Return 0 by success
		and 1 by failure
		"""
		# build the command
		_group = self.mvst.get("core", "group")
		_user = self.mvst.get("core", "user")
		
		daemoncmd = "%s -n %s --start --background --chuid %s:%s --user %s --group %s --pidfile %s --make-pidfile --chdir %s --exec %s" %(self.getDaemonBin(), self.name, _user, _group, _user, _group, self.getPidFile(), chdir, cmd)
		return self.mvst.qx(daemoncmd)

	def stop(self):
		"""
		Stops the daemon
		"""
		cmd = "%s --pidfile %s --stop --signal INT --retry 10" % (self.mvst.get("bins","start-stop-daemon"), self.getPidFile() )
		return self.mvst.qx(cmd)

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
		return self.mvst.qx(cmd)

	def getDaemonBin(self):
		""" returns the path to the start-stop-daemon binary """
		return self.mvst.get("bins","start-stop-daemon")

	def getPidFile(self):
		""" return the path of the given pidfile """
		return "%s%s_%s.pid" % (self.mvst.getTmpDir(), self.name, self.mvst.getInstance())


########################################################



class Irc:
	"""
	The Irc class implements the functions that are needed for the irc bridge
	"""

	def __init__(self, mvst):
		if not isinstance(mvst, Mvst):
			print("CRITICAL: Irc.mvst (%s) ist not an instance of Mvst" % type(mvst))
		self.mvst = mvst
		self.log = logging.getLogger('irc')

		self.daemon = Daemon(self.mvst, "irc")


	def do(self, command):
		""" Starts a function with the correct commands """
		x = command[0]
			
		if x == "start":
			self.ircStart()
		elif x == "stop":
			self.ircStop( " ".join(command[1:]) )
		elif x == "status":
			return self.ircStatus()
		elif x == "restart":
			self.ircRestart( " ".join(command[1:]) )
			
		else:
			print("irc: unknown command »%s«" % x)


	def ircStart(self):
		"""
		Start the irc-bridge as a daemon
		Return 0 by success
		and 1 by failure
		"""
		self.mvst.echo("Start irc-bridge...")

		time.sleep(5)
		if not self.mvst.wrapper.isWrapperRunning():
			print("Fail. (wrapper is not running)")
			return 1

		if self.isIrcRunning():
			print("is already running.")
			return 1
		else:
			_instance = self.mvst.getInstance()

			irccmd = "%s -- %sirc.py -l %s -r %s -n %s %s %s %s" \
						%(self.mvst.getPython2(), self.mvst.getBinDir(), self.mvst.getLogfile(), \
						self.mvst.get("irc","realname"), self.mvst.get("irc","nick"), \
						self.mvst.getSocket(), self.mvst.get("irc","host"), self.mvst.get("irc","channel"))

			r = self.daemon.start(irccmd, self.mvst.getServerDir())

			if r == 0:
				print("Done")
				self.log.info("Started irc-bridge")
				self.mvst.wrapper.say("irc-bridge is back online...")
				return 0
			else:
				print("Fail")
				return 1



	def ircStop(self, reason=""):
		"""
		Stops the irc-bridge
		"""
		self.mvst.echo("Stop irc-bridge...")

		if self.isIrcRunning():

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

	def ircRestart(self, reason=""):
		"""
		Restarts the irc-bridge
		"""
		print("Restarting...")
		r = self.ircStop(reason)
		if r == 0:
			time.sleep(3)
			self.ircStart()

	def ircStatus(self):
		"""
		Returns the current status of the irc bridge
		"""
		self.mvst.echo('Checking irc-bridge status...')
		if self.isIrcRunning():
			print("Running.")
			return 0
		else:
			print("Stopped.")
			return 1

	def isIrcRunning(self):
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


	def getDaemon(self):
		""" Returns the daemon """
		return self.daemon

########################################################





if __name__ == "__main__":
	m = Mvst(sys.argv[1:])
	exit(m.start())



