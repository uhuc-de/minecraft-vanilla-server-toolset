Minecraft Vanilla Server Toolset
================================

The Minecraft Vanilla Server Toolset version 2 (mvst2) is a compilation of different skripts. This bundle isn't a "all-round carefree package" for wannabe serveradministrators who want an "easy to use" Window where they can click through. If you are familiar with Linux and the Shell you should have no problems to run the skripts and maybe edit them as you like.


Features
---------------

* provides 100% vanilla minecraft
* start/stop the minecraft server like a daemon
* creates a unix socket to talk to the server
* backup the map weekly and daily
* update minecraft easily
* records the positions of every player in the game and saves them into a sqlite file
* modular design
* every skript understands "--help"

Download
-----------------

Visit https://gitorious.org/mvst2/mvst2 to download the source or clone it with git.


Dependencies:
-----------------

Install the dependencies of the toolset:

* python 2.7
* start-stop-daemon
* tar
* java
* wget 
* cron
* less
* coreutils
* bash 
* nbt (https://github.com/twoolie/NBT / https://pypi.python.org/pypi/NBT)
* minecraft-overviewer (http://overviewer.org/)
* rsync

Installation: 
------------------

* add a user named "minecraft" to your system
* login as user "minecraft"
* install all needed dependencies
* chmod +x ~/bin/*
* change the global variables in minecraftd.sh to your needs (if you need to):
	* "\_MC\_GROUP" and "\_MC\_USER" 
* change to the ~/bin directory
* to install run: ~/bin/install.sh <version> [<instance>]
	* eg: install.sh 1.7.10 default
* change to the directory ~/server/default/
* edit the server.properties if you need to

To test your settings, start the server, stop it with a command and check the logs:

	$ minecraftd.default.sh start
	$ minecraftd.default.sh control stop
	$ minecraftd.default.sh log



### Log player positions

If you want to log the movements of every player every minute on your server you should add to your crontab:

	* * * * * /path/to/minecraftd.default.sh tracer 

The variable "\_TRACER\_DATABASE" is the place of the records. The default file is "tracer\_data.sqlite" inside the map directory. If you want to read out the position records, use tracer-client.py.

### daily backup 

Write to the crontab:

	0 0 * * * /path/to/minecraftd.default.sh backup daily

### render the overviewer 

If you want to have an updated overviewer map every 3 hours, write to the crontab:

	0 */3 * * * /path/to/minecraftd.default.sh overviewer

The html outcome is saved under overviewer/$instance/html. You can symlink it to your homepage or edit the minecraftd-core.sh function do_overviewer() to your need.


Usage:
------------------


	minecraftd.sh {command}

	Command:
		start			Starts the server
		stop			Stops the server
		status			Shows the status of the server
		restart			Restarts the Server

		say <msg>		Say <msg> ingame
		control <cmd>		Sends a raw command to the server
		update <version>	Change to <version> (eg. 1.5.6)

		whitelist <user> 	Perform backup and add <user> to whitelist
		tracer			Logs the players positions 
		backup <reason>		Backups the server
		overviewer		Renders the overviewer map

		log				Shows the logfile with less
		shell			Shows the tail of the logfile and starts the minecraft shell



Multiple instances:
-------------------

If you want to run multiple instances of minecraft on the same maschine you just need to run the installer with a different instance parameter:
eg.: $ install.sh <version> otherworld


Troubleshooting:
------------------

### If the user minecraft can't execute start-stop-daemon, edit the /etc/sudoers with visudo
	minecraft       ALL = NOPASSWD: /usr/sbin/start-stop-daemon



Everything in this toolset is released under the terms of the GPL3. You can send patches or bugreports to mvst@noxzed.de or merge requests on github.
