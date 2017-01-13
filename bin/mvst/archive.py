#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import logging	# used for logging
import time # needed for sleep() and duration
import re # regex

from .core_functions import CoreFunctions as Core
from .config import Config
from .wrapper_handler import WrapperHandler


class Archive:
	"""
	The Archive class handles, besides the backup and the restore
	of the server, every warking with the server files
	"""


	def __init__(self, config):
		if not isinstance(config, Config):
			print("CRITICAL: Backup.config ist not an instance of mvst.Config")
		self.config = config
		self.log = logging.getLogger('Archive')

		self.wrapper = WrapperHandler(self.config)



	### Server copy ###

	def copyServer(self):
		""" Copies the whole server directory to the share file """

		lockname = "servercopy"
		if self.setLock(lockname):
			self.log.error("Can't copy server. Lock is set.")
			print("Can't copy server. Lock is set.")
			return 1

		self.log.debug("Perform servercopy")

		if self.wrapper.isRunning():
			self.wrapper.sendToSocket("save-off");
			self.wrapper.sendToSocket("save-all");
			time.sleep(5)

		cmd = "rsync -a \"{0}\" \"{1}servercopy\"".format(self.config.getServerDir(), self.config.getShareDir())
		if Core.qx(cmd, Core.QX_RETURNCODE):
			print("error occured!")

		if self.wrapper.isRunning():
			self.wrapper.sendToSocket("save-on");

		if self.releaseLock(lockname):
			self.log.error("copyServer: Can't release lock »%s«." % lockname)
			print("copyServer: Can't release lock »%s«." % lockname)
			return 1
		return 0


	### Locking ###

	def setLock(self, name):
		"""
		Set a lockfile with a specific name
		returncodes:
		0 lockfile was created successfully
		1 lockfile already exists
		2 empty variable <name>
		"""
		if name != "":
			lockfile = "{0}{1}-{2}.lock".format(self.config.getTmpDir(), self.config.getInstance(), name)
			if os.path.isfile(lockfile): 
				self.log.warning("Lockfile »%s« already exists!" % lockfile)
				return 1
			else:
				cmd = "touch %s" % lockfile
				return Core.qx(cmd, Core.QX_RETURNCODE)
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
			lockfile = "%s%s-%s.lock" % (self.config.getTmpDir(), self.config.getInstance(), name)
			if os.path.isfile(lockfile):
				return Core.qx("rm %s" % lockfile, Core.QX_RETURNCODE)
			else:
				self.log.warning("Lockfile »%s« does not exist!" % lockfile)
				return 1
		else:
			self.log.error("None name set for lockfile!")
			return 2


	### Backup and restore ###

	def backup(self, reason=""):
		""" Backups the server """

		if len(reason) < 1:
			print("Too few arguments! (Backup needs a reason!)")
			return 1

		# sanitize the reason string
		reason = reason.lower()
		reason.replace(".", "_")
		p = re.compile("[^a-z0-9_\-]+")
		reason = p.sub("", reason)

		timestamp = time.strftime("%Y-%m-%d-%H%M%S")
		backupfile = "%s_%s" % (timestamp, reason)

		if self.copyServer():
			print("Abort backup!")
			self.log.error("abort backup")
			return 1

		self.log.debug("Perform backup »%s«" % reason)
		
		if self.wrapper.isRunning():
			self.wrapper.say("Performing world backup »%s«" % reason)

		cmd = "tar -c -jh --exclude-vcs -C \"%sservercopy\" -f \"%s%s.tar.bz2\" ./" \
				% (self.config.getShareDir(), self.config.getBackupDir(), backupfile)

		if Core.qx(cmd, Core.QX_RETURNCODE):
			self.log.error("Fail to create the tar.bz2 backup file!")
			return 1

		# generate md5sum
		if self.generateMd5(backupfile):
			self.log.error("Could not create the md5 sum!")

		# create the symlinks to the latest backup files
		self.createLatestLink(backupfile, ".tar.bz2")
		self.createLatestLink(backupfile, ".tar.bz2.md5")

		if self.wrapper.isRunning():
			self.wrapper.say("Backup complete")

		self.log.info("Backup saved as %s.tar.bz2" % backupfile)


	def createLatestLink(self, filename, extension):
		""" create the symlink that points to the latest backup """
		latest = "latest%s" % extension
		if os.path.exists("%s%s" %(self.config.getBackupDir(), latest)):
			os.remove("%s%s" %(self.config.getBackupDir(), latest))
		cmd = "cd %s && ln %s%s %s" % (self.config.getBackupDir(), filename, extension, latest)
		if Core.qx(cmd, Core.QX_RETURNCODE):
			self.log.error("Failure during the creation of the %s link!" % latest)


	def generateMd5(self, filename):
		""" Generates the md5 checksum of the given filename
			(without file extension) and saves the result in
			a file next to it
		"""
		cmd = "cd %s && md5sum %s.tar.bz2 > %s.tar.bz2.md5" %(self.config.getBackupDir(), filename, filename)
		return Core.qx(cmd, Core.QX_RETURNCODE)


	def checkMd5(self, filename):
		""" Checks the generated md5 checksum of the given
			filename (without file extension)
			return 0 if everything is OK and 1 if check failed
		"""
		cmd = "cd %s && md5sum -c %s.tar.bz2 --quiet" %(self.config.getBackupDir(), filename)
		return Core.qx(cmd, Core.QX_RETURNCODE)


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


	### Others ###


	def getVersion(self):
		""" Returns the current version of the minecraft server if possible """
		cmd = "cat %sversion" % self.config.getServerDir()
		if not Core.qx(cmd, Core.QX_RETURNCODE):
			return Core.qx(cmd, Core.QX_OUTPUT)
		else:
			return "No version available"
