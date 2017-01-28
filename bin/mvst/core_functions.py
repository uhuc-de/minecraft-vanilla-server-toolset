#!/usr/bin/python2
# -*- coding: utf-8 -*-


import subprocess # used by qx
import os

class CoreFunctions(object):
	""" The core functions contain some static functions who are used by a bunch of mvst classes """


	""" Modes of the qx function """
	QX_SHELL = 1
	QX_RETURNCODE = 2
	QX_OUTPUT = 3


	def qx(cmd, mode=QX_RETURNCODE):
		"""
		Executes a command in the shell and returns the returncode or the output
		depending on the mode.

		Mode:
		1 - normale execution of the cmd
		2 - check only the return value of the cmd
		3 - return the output of the cmd via qx's return

		return values:
		0 - everything is alright
		1 - error occured

		TODO: http://xahlee.info/perl-python/system_calls.html
		"""

		if mode == 1:

			"""
			Starts the command in the shell without returning or printing something
			https://docs.python.org/3/library/subprocess.html#replacing-os-system
			"""
			try:
				subprocess.call(cmd, shell=True)
				return 0
			except OSError as e:
				print("Execution failed:", e, file=sys.stderr)
				#TODO: self.log.error("Execution failed:", e, file=sys.stderr)
				return 1

		elif mode == 2:

			try:
				subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
				return 0
			except subprocess.CalledProcessError as e: # Do if returncode != 0
				if e.returncode == None:
					print("CRITICAL: returncode in qx() is None")
				return e.returncode

		elif mode == 3:

			try:
				output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).splitlines()
			except subprocess.CalledProcessError as e: 
				pass

			out = ""
			for i in output:
				out = out+(i.decode('unicode_escape'))
				if len(output) > 1 and out[-1] != "\n":
					out = out+"\n"
			return out


	def echo( s):
		"""Do not output the trailing newline with print()"""
		print("%s " % s, end="", flush=True)
		#print('.',end="",flush=True)



	def getCommandList():
		return """	help 			Print this message

	start			Starts the server
	stop			Stops the server
	status			Shows the status of the server
	restart			Restarts the Server
	force-kill		Send SIGTERM to the java process

	log			Open the logfile with less
	shell			Show the tail of the logfile and starts the minecraft shell

	say <msg>		Say <msg> ingame
	control <cmd>		Sends a raw command to the server
	update <version>	Perform backup and change to <version> (eg. 1.5.6)
	whitelist <user> 	Perform backup and add <user> to whitelist

	backup <reason>		Backups the server
	restore (backup)	Restore a specific backup

	overviewer		Renders the overviewer map
	irc <start|stop|restart|status>	Controls the irc-bridge

	tracer			Logs the players positions
	tracer-client		View and filter the tracer positions

	reports		Let you select and view the logfiles and crash-reports
		"""


	def usage():
		"""
		Prints the manual and then exits.
		"""
#		helpmsg = """Usage: %s -c /path/to/config.ini -- <command> [<arguments>]
#
#Command:
#%s
#		"""
		helpmsg = """Usage: mvst.py -c /path/to/config.ini -- <command> [<arguments>]

Command:
%s
		""" % CoreFunctions.getCommandList()
		print(helpmsg)
		exit(1)









