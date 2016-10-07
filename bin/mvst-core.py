#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import time # needed for sleep() and duration
import subprocess # needed by qx()
import configparser # needed by loadConfig
import logging	# used for logging
import getopt

import re # regex



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
		self.currentUser = None
		
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
			opts, args = getopt.getopt(argv, "hc:u:", ["help"] )	# Option with ":" need an Argument
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
			elif opt in "-u": 
				self.currentUser = arg
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
			x = self.__argv[0]
		else:
			x = args
			
		if x == "help":
			self.releaseLock("blubb")
			#self.usage()

		elif x == "start":
			self.wrapper.wrapperStart()
		elif x == "stop":
			self.wrapper.wrapperStop(args)
		elif x == "status":
			self.wrapper.wrapperStatus()
		elif x == "restart":
			self.wrapper.wrapperRestart(args)
		elif x == "control":
			self.wrapper.control(args)
		elif x == "say":
			w = WrapperCtl(self)
			w.say(args)
		elif x == "shell":
			print("TODO")
			#self.wrapper.shell(args)
			
		elif x == "irc":
			self.irc.do(self.__argv[1:])
			pass
		elif x == "remote":
			remote = Remote(self)
			remote.start()

		elif x == "overviewer":
			self.overviewer()
		elif x == "whitelist":
			self.whitelist(" ".join(self.__argv[1:]))
		elif x == "update":
			self.whitelist(" ".join(self.__argv[1:]))
			
		elif x == "backup":
			self.archive.backup(" ".join(self.__argv[1:]))

			
		else:
			print("unknown command »%s«" % x)
			self.usage()



	### Tracer ###

	def tracerLog(self):
		""" Prints the current positions from the playerfiles into the tracerdatabase """
		playerdataDir = ""
		tracerdb = self.get("tracer", "tracerdb")
		"${_DIR_SERVER}/${_MAPNAME}/tracer_data.sqlite"

		cmd = "%s %stracer.py \"%s\" \"%s\" " % (self.getPython2(), self.getBinDir(), playerdataDir, tracerdb)
		
		if self.qx(cmd):
			self.log.critical("Can't execute the tracer!")


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
		echo("Download server.jar ... ")
		cmd = "%s -q -O \"%sminecraft_server.jar\" \"http://s3.amazonaws.com/Minecraft.Download/versions/%s/minecraft_server.%s.jar\"" % (self.get("bins", "wget"), self.getTmpDir(), version, version)
		r1 = self.qx(cmd)
		if r1:
			print("fail!")
		else:
			print("done")

		echo("Download client.jar ... ")
		cmd = "%s -q -O \"%sminecraft_client.jar\" \"http://s3.amazonaws.com/Minecraft.Download/versions/%s/%s.jar\"" % (self.get("bins", "wget"), self.getTmpDir(), version, version)
		r2 = self.qx(cmd)
		if r2:
			print("fail!")
		else:
			print("done")

		# check if download was successfull
		if (r1 != 0) and (r2 != 0):

			echo("Backup... ")
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

		if self.mvst.wrapper.isWrapperRunning():
			user = user.lower()
			self.log.info("Add to whitelist: %s" % user)
			self.mvst.wrapper.say("Whitelist user »%s«" % user)

			if self.archive.backup(user):
				print("Whitelist failed!")
				self.log.error("Whitelist failed!")
				self.mvst.wrapper.say("Whitelist failed!")
			else:
				self.mvst.wrapper.control("whitelist add %s" % user)
				self.mvst.wrapper.say("Added »%s« to whitelist" % user)
		else:
			print("Could not connect to the server!")



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
			#raise Exception("key »%s« inside the config section »%s« not found" % (key, section))
			errmsg = "key »%s« inside the config section »%s« not found" % (key, section)
			self.log.warning(errmsg)
			print (errmsg) # FIXME: warnmeldung wirklich notwendig?
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

	def getPidFileWrapper(self): # TODO: should be function of daemon class
		""" returns the pidfile of the wrapper """
		return "%s%s_%s.pid" % (self.getTmpDir(), name, _instance)

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
		return os.path.dirname(os.path.abspath(__file__))[:-3]

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


	### Common ###

	def echo(self, s):
		"""Do not output the trailing newline with print()"""
		print("%s " % s, end="",flush=True)
		#print('.',end="",flush=True)



	def qx(self, cmd, interactive=False):
		"""
		Executes a command in the shell and returns the returncode or the output

		return values:
		0 - everything is alright
		1 - error occured

		TODO: http://xahlee.info/perl-python/system_calls.html
		"""

		if interactive: # XXX: maybe delete it again
			print("TODO: interactive=true")
			sout=subprocess.PIPE
			process = subprocess.Popen(cmd,stdout=sout, cwd=os.getcwd(), shell=True)
			while True:
				try:
					output = process.stdout.readline().decode("utf-8")
					output = output.strip()
					if output == "": 
						print("process line is empty")
						break
					else:
						print("-- %s" % output)
				except IOError:
					print("ioerror")
					break
			return process.returncode
			
		else:
			try:
				output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).splitlines()
				returncode = 0
			except subprocess.CalledProcessError as e: # Do if returncode != 0
				output = e.output.splitlines()
				self.log.debug("qx returns %s - %s" %(e.returncode, cmd))
				returncode = "%s" % e.returncode
				if returncode == None:
					returncode = "typeOfNone"
			for i in output:
				print(i.decode('unicode_escape'))
			return returncode

	def usage(self):
		"""
		Prints the manual and then exits.
		"""
		helpmsg = """Usage: %s -c /path/to/config.ini -- <command> [<arguments>]

Command:
	help 			Print this message

	start			Starts the server
	stop			Stops the server
	status			Shows the status of the server
	restart			Restarts the Server

	say <msg>		Say <msg> ingame
	control <cmd>		Sends a raw command to the server
	-update <version>	Perform backup and change to <version> (eg. 1.5.6)
	-whitelist <user> 	Perform backup and add <user> to whitelist
	-tracer			Logs the players positions
	-backup <reason>		Backups the server
	-restore [backup]	Restore a specific backup
	-overviewer		Renders the overviewer map
	-irc <start|stop|restart|status>	Controls the irc-bridge

	-log			Open the logfile with less
	-shell			Show the tail of the logfile and starts the minecraft shell
		""" % os.path.basename(__file__)
		helpmsg="%%HELPTEXT%%"
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
		print (cmd)
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
			_java = "java -jar %sminecraft_server.jar %s nogui" % (self.mvst.getServerDir(), self.mvst.get("wrapper", "javaopts"))

			wrappercmd = "%s -- %s -s %s -v %s -l %s --- %s" % (self.mvst.getPython2(), _wrapper, self.mvst.getSocket(), self.mvst.getLoglevel(), self.mvst.getLogfile(), _java)
			daemon = Daemon(self.mvst)
			r = daemon.start(wrappercmd, "wrapper", self.mvst.getServerDir()) # TODO: write instance in name
			if r == 0:
				print("Done")
				if self.mvst.getAutorunIrc():
					#print("TODO: start irc-bridge")
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
			self.say("Server stops in 3 seconds. %s" % reason)

			if self.mvst.irc.isIrcRunning():
				self.mvst.irc.ircStop()
				
			time.sleep(3)
				
			daemon = Daemon(self.mvst)
			r = daemon.stop("wrapper")

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
			exit(0)
		else:
			print("Stopped.")
			exit(1)


	def isWrapperRunning(self):
		"""
		Check if the wrapper is running. It tests the connection to the socket
		Return True for yes and False for no
		"""
		_instance = self.mvst.getInstance()
		_socket = self.mvst.getSocket()
		cmd = "%s %scontrol.py -s %s --check" % (self.mvst.getPython2(), self.mvst.getBinDir(), _socket)
		r = self.mvst.qx(cmd) # TODO: use daemon.status
		
		if r == 0:
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
		if r == 0:
			return 0
		elif r == 2:
			self.log.debug("Can't connect to socket (%s)!" % _socket)
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
		self.mvst.qx("tail -n 25 %s" % self.mvst.getLogfile(), interactive=True)
		print("")
		shellcmd = "%s %scontrol.py -s %s" % (self.mvst.getPython2(), self.mvst.getBinDir(), self.mvst.getSocket())
		self.mvst.qx(shellcmd)







########################################################



class Remote:
	"""
	The remote class handles the usermanagement for remote connected users
	"""
	def __init__(self, mvst):
		if not isinstance(mvst, Mvst):
			print("CRITICAL: Remote.mvst ist not an instance of Mvst")
		self.mvst = mvst
		self.log = logging.getLogger('remote')
		self.user = mvst.currentUser
		self.conf = []


	def start(self):
		"""
		Starts a shell for a user with special rights
		"""
		# check if user exists
		if not ("remote-%s" % self.user) in self.mvst.getConfigArray():
			print("You (%s) are not allowed to enter the remote shell!" % self.user)
			# XXX uncomment: self.warning("User »%s« tried to login, but doesnt exist in the config ini!" % self.user)
			exit(1)
		# load configs for user
		self.conf = self.mvst.getConfigArray()["remote-%s" % self.user]
		for i in self.conf:
			print("config[%s]=%s" %(i, self.mvst.getConfigArray()["remote-max"][i]))
		# start the shell for the user
		print("start for user %s" % self.user)
		pass#TODO: usermanagement, logging, 


	def help(self):
		"""
		Prints the help for the remote plugin
		"""
		print("TODO: Remote.help()")



########################################################


class Daemon:
	"""
	The daemon class start and stop a daemon with start-stop-daemon and give back a status
	"""

	def __init__(self, mvst):
		if not isinstance(mvst, Mvst):
			print("CRITICAL: Daemon's mvst ist not an instance of Mvst")
		self.mvst = mvst
		self.log = logging.getLogger('daemon')


	def start(self, cmd, name, chdir):
		"""
		Starts a command as a daemon
		Return 0 by success
		and 1 by failure
		"""
		# build the command
		_pidfile = "%s%s_%s.pid" % (self.mvst.getTmpDir(), name, self.mvst.getInstance())
		daemoncmd = "%s -n %s --start --background --user %s --group %s --pidfile %s --make-pidfile --chdir %s --exec %s" %(self.getDaemonBin(), name, self.mvst.get("core", "user"), self.mvst.get("core", "group"), _pidfile, chdir, cmd)
		return self.mvst.qx(daemoncmd)

	def stop(self, name):
		"""
		Stops the daemon with the specific name
		"""
		cmd = "%s --pidfile %stmp/%s_%s.pid --stop --signal INT --retry 10" % (self.mvst.get("bins","start-stop-daemon"), self.mvst.getHomeDir(), name, self.mvst.getInstance())
		return self.mvst.qx(cmd)

	def status(self, name):
		"""
		Checks if a daemon is running
		Return Codes:
			0 Program is running.
			1 Program is not running and the pid file exists.
			3 Program is not running.
			4 Unable to determine program status.
		"""
		cmd = "%s --pidfile %s --status" % (self.getDaemonBin(), self.getPidFile(name))
		return self.mvst.qx(cmd)
		pass

	def getDaemonBin(self):
		""" returns the path to the start-stop-daemon binary """
		return self.mvst.get("bins","start-stop-daemon")

	def getPidFile(self, name):
		""" return the path of the given pidfile """
		return "%s%s_%s.pid" % (self.mvst.getTmpDir(), name, self.mvst.getInstance())


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
		

	def do(self, command):
		""" Starts a function with the correct commands """
		x = command[0]
			
		if x == "start":
			self.ircStart()
		elif x == "stop":
			self.ircStop( " ".join(command[1:]) )
		elif x == "status":
			self.ircStatus()
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
						%(self.mvst.getPython2(), self.mvst.getBinDir(), self.mvst.getLogfile(), self.mvst.get("irc","realname"), self.mvst.get("irc","nick"), self.mvst.getSocket(), self.mvst.get("irc","host"), self.mvst.get("irc","channel"))

			daemon = Daemon(self.mvst)
			r = daemon.start(irccmd, "irc", self.mvst.getServerDir())

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

			daemon = Daemon(self.mvst)
			r = daemon.stop("irc")

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
			exit(0)
		else:
			print("Stopped.")
			exit(1)

	def isIrcRunning(self):
		"""
		Check if the irc-bridge is running as a daemon
		Return 1 for yes and 0 for no
		"""

		daemon = Daemon(self.mvst)
		r = daemon.status("irc")

		if r == 0:
			return 1
		elif r == 3:
			return 0
		else:
			self.log.error("Unknown error inside isIrcRunning() (returncode=%s)" % r)
			return 0


########################################################





if __name__ == "__main__":
	m = Mvst(sys.argv[1:])
	m.start()




########################################################











# https://wiki.python.org/moin/ConfigParserExamples
# modularisation via "import mvst-irc"
# cat: http://stackoverflow.com/questions/11532980/reproduce-the-unix-cat-command-in-python
# http://stackoverflow.com/questions/5631624/how-to-get-exit-code-when-using-python-subprocess-communicate-method

# Zu implementierenden funktionen:
# - hauptfunktion: parameter aufbau bestimmen
# - hauptfunktion: switch schreiben
# Schritt 1
# - start
# - stop
# - status
# Schritt 2
# - Config-Loader
# - mc server reload argument
# Schritt 3
# - Shell
# - Remote-shell
# - Berechtigungen für Shell
#
# - grep (greps the log)
# - log <loglevel> (filtert nach loglevel)
#
#
# Backup redention / delete old backups but keep weeklys
# hat irc kein loglevel?
#
# locks setzen für mapcopy
#	backup
# 	overviewer


# irc trigger für den pingback in den chats in die config einbauen





#
# _DIR_SERVER="${MAINDIR}/server/${_INSTANCE}"
# _DIR_BACKUP="${MAINDIR}/backups/${_INSTANCE}"
# _DIR_MVSTBIN="${MAINDIR}/bin"
# _DIR_TMP="${MAINDIR}/tmp"
# _DIR_SHARE="${MAINDIR}/share/${_INSTANCE}"
#
#
# _BIN_PYTHON2=`which python2`
# _BIN_DAEMON=`which start-stop-daemon`
# _BIN_OVERVIEWER=`which overviewer.py`
# _BIN_WGET=`which wget`
#
# # Get name of the world
# grep -q "level-name" "${_DIR_SERVER}/server.properties" 2> /dev/null
# if [[ $? == 2 ]] # grep file not found
# then
# 	_MAPNAME=world
# else
# 	_MAPNAME=$(grep "level-name" "${_DIR_SERVER}/server.properties" | cut -d "=" -f 2)
# fi
#
#
# _WRAPPER_SOCKET="${_DIR_TMP}/wrapper_${_INSTANCE}.socket"
# _WRAPPER_PID="${_DIR_TMP}/wrapper_${_INSTANCE}.pid"
# _WRAPPER_CMD="${_DIR_MVSTBIN}/wrapper.py -s $_WRAPPER_SOCKET -v ${_LOGLEVEL} -l $_LOGFILE --- java -jar minecraft_server.jar nogui"
#
# _TRACER_DATABASE="${_DIR_SERVER}/${_MAPNAME}/tracer_data.sqlite"
#
#
#


#
#
# usage() {
# 	echo """
# Usage: $0 {command}
#
# Command:
# 	start			Starts the server
# 	stop			Stops the server
# 	status			Shows the status of the server
# 	restart			Restarts the Server
#
# 	say <msg>		Say <msg> ingame
# 	control <cmd>		Sends a raw command to the server
# 	update <version>	Perform backup and change to <version> (eg. 1.5.6)
# 	whitelist <user> 	Perform backup and add <user> to whitelist
# 	tracer			Logs the players positions
# 	backup <reason>		Backups the server
# 	restore [backup]	Restore a specific backup
# 	overviewer		Renders the overviewer map
# 	irc <start|stop|restart|status>	Controls the irc-bridge
#
# 	log			Open the logfile with less
# 	shell			Show the tail of the logfile and starts the minecraft shell
#
# """
# 	exit 1
# }
#
#
#
#
# #### LOAD MODULES ####
#
# source "${MAINDIR}/bin/mvst-irc.sh"
#
#
#
# ## MAIN
#
# case "$1" in
#
# 	start)
# 		do_start
# 		;;
# 	stop)
# 		do_stop
# 		;;
# 	restart)
# 		do_restart
# 		;;
#  	status)
# 		do_status
# 		;;
# 	update)
# 		do_update $2
# 		;;
# 	overviewer)
# 		do_overviewer
# 		;;
# 	control)
# 		shift
# 		do_control $@
# 		;;
# 	say)
# 		shift
# 		say $@
# 		;;
# 	backup)
# 		shift
# 		do_backup $@
# 		;;
# 	restore)
# 		shift
# 		do_restore $@
# 		;;
# 	tracer)
# 		do_tracer
# 		;;
# 	whitelist)
# 		do_whitelist $2
# 		;;
# 	shell)
# 		do_shell
# 		;;
# 	log)
# 		do_log
# 		;;
# 	# module: irc
# 	irc)
# 		shift
# 		do_irc $@
# 		;;
# 	*)
# 		usage
# 		;;
# esac
# exit 0


