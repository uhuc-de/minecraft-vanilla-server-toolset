Minecraft Vanilla Server Toolset
================================

The Minecraft Vanilla Server Toolset version 2 (mvst2) is a compilation of different skripts. This bundle isn't a "all-round carefree package" for wannabe serveradministrators who want an "easy to use" Window where they can click through. If you are familiar with Linux and the Shell you should have no problems to run the skripts and maybe edit them as you want.


Features
---------------

* provides 100% vanilla minecraft
* start/stop the minecraft server like a daemon
* creates a unix socket to talk to the server
* backup the map weekly and daily
* update minecraft easily
* records the positions of every player in the game and saves them into a sqlite file
* modular design
* every skript understands "--help", except control.pm

Download
-----------------

Visit https://gitorious.org/mvst2/mvst2 to download the source or clone it with git.


Dependencies:
-----------------

Install the dependencies of the toolset:

* python 2.*
* perl >= 2.5.10
* perl-curses
* perl-io-interactive
* perl-io-tty 
* perl-term-readkey
* perl-yaml
* start-stop-daemon
* tar
* wget 
* cron
* nbt (https://github.com/twoolie/NBT)


Configuration:
-------------------

Make minecraftd.sh executable:

	chmod +x minecraftd.sh

Change the global variables in minecraftd.sh to your needs:

	_DIR_SERVER		should point to the directory of the minecraft server
	_DIR_BACKUP		should point to your minecraft backup directory
	_DIR_MVSTBIN	inside this directory the mvst skripts should be found
	_DIR_TMP		point to your temporary directory
	_DIR_LOGS		inside this directory the logs are going to be found

	_INSTANCE		is the name of your world (same as "level-name" in server.properties)
	_MC_USER		the user who should own/run the server
	_MC_GROUP		the group of the server

	_CLIENT_JAR		points to the minecraft.jar of the client

Change at the end of control.pm the socket to the value of "\_WRAPPER\_SOCKET" in 
minecraftd.sh:

	    - '/tmp/mcwrapper.socket / UNIX'

To test your settings, start the server, stop it with a command and check the logs:

	$ minecraftd.sh start
	$ minecraftd.sh control stop
	$ less logs/wrapper_default.log

### Log player positions

If you want to log the movements of every player on your server you should add to your crontab:

	*/1 * * * * /path/to/minecraftd.sh tracer log

The variable "\_TRACER\_DATABASE" is the place of the records. The default file is "tracer\_data.sqlite" inside the map directory. If you want to read out the position records you should use tracer-client.py.

### backup automatically

Write to the crontab:

	0 0 * * * /path/to/minecraftd.sh backup daily
	59 23 * * 0 /path/to/minecraftd.sh backup weekly


Usage:
------------------


	minecraft.sh {command}

	Command:
		start			Starts the server
		stop			Stops the server
		status			Shows the status of the server
		restart			Restarts the Server

		say <msg>		Say <msg> ingame
		control <cmd>		Sends a raw command to the server
		update <version>	Update to <version> (eg. 1.5.6)

		backup <arg>		Backups the server
		tracer <arg>		Executes the tracer with <arg>

	Backup arguments:
		daily			Perform the daily backup
		weekly			Perform the weekly backup
		<reason>		Perform an extra backup, named <reason>

	Tracer arguments:
		log			Logs the positions of the players
		clean			Resets the database with the positions





#### tracer-client.py

With this client you can query the sqlitefiles with the positions from "minecraftd.sh tracer log" (tracer.py) easily.
	
	python2 tracer-client.py --help



Multiple instances:
-------------------

If you want to run multiple instances of minecraft on the same maschine you can copy the minecraftd.sh and just need to change the variables "\_DIR\_SERVER", "\_INSTANCE" and "\_DIR\_BACKUP".





Everything in this toolset is released under the terms of the GPL3. You can send patches to mvst@noxzed.de or merge requests on gitorious.
