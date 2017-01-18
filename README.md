Minecraft Vanilla Server Toolset
================================

The Minecraft Vanilla Server Toolset is a compilation of different skripts. This bundle isn't a "all-round carefree package" for wannabe serveradministrators who want an "easy to use" window, where they can click through. If you are familiar with Linux, Python and the Shell you should have no problems to run the skripts and maybe edit them as you like.


Features
---------------

* provides 100% vanilla minecraft
* using start-stop-daemon to start/stop the minecraft server like a daemon
* creates a unix socket to talk to the server
* backup the map daily
* update minecraft easily
* records the positions of every player in the game and saves them into a sqlite file
* modular design
* every skript understands "--help"

Download
-----------------

Visit https://github.com/uhuc-de/minecraft-vanilla-server-toolset to download the source or clone it with git.


Dependencies:
-----------------

Install the dependencies of the toolset:

### Core functionality

* python 2.7
* python 3
* start-stop-daemon
* tar
* java
* wget
* less
* coreutils
* bash

### optional dependencies

* cron
* nbt (https://github.com/twoolie/NBT / https://pypi.python.org/pypi/NBT)
* minecraft-overviewer (http://overviewer.org/)
* rsync


Installation:
------------------

* install all needed dependencies
* add a user named "minecraft" to your system (optional)
* login as user "minecraft" (optional)
* clone the git-repo into the directory you wanna have the mvst (eg. ~/ )
* rename the git-repo to »mvst« (optional)
* change to the »bin« directory of the MVST
* copy the mvst-default.ini to mvst-INSTANCENAME.ini and edit it, till it fits your needs
* run »$ python3 install_instance.py mvst-INSTANCENAME.ini install VERSION« to create the directories of the instance and download the minecraft_server.jar in the given version (eg. »$ python3 install_instance.py mvst-myinstance.ini install 1.10.3«)
* you can now use the shortcut script (eg. »mvst-myinstance.py«) to control your instance
* change to the directory mvst/server/default/ and edit the server.properties if you need to
* accept the eula.txt in the server directory

To test your settings: start the server, stop it and check the log with the shortcut script:

	$ ./mvst-INSTANCENAME.py start
	$ ./mvst-INSTANCENAME.py stop
	$ ./mvst-INSTANCENAME.py log

Now your server should be usable!


### Log player positions

If you want to log the movements of every player every minute on your server you should add to your crontab:

	* * * * * /path/to/mvst-INSTANCENAME.py tracer

Use »shortcut.sh tracer-client« to read out the sqlite file.

### daily backup

Write to the crontab:

	0 0 * * * /path/to/mvst-INSTANCENAME.py backup daily

### render the overviewer

If you want to have an updated overviewer map every 3 hours, write to the crontab:

	0 */3 * * * /path/to/mvst-INSTANCENAME.py overviewer

You must create a settings.py for minecraft-overviewer and name the path in the INI-file of the instance


Usage:
------------------


	Usage: mvst-INSTANCENAME.py {command} <options>

	Command:
		start			Starts the server
		stop			Stops the server
		status			Shows the status of the server
		restart			Restarts the Server
		force-kill		Send SIGTERM to the java process

		say <msg>		Say <msg> ingame
		control <cmd>		Sends a raw command to the server
		update <version>	Perform backup and change to <version> (eg. 1.5.6)
		whitelist <user> 	Perform backup and add <user> to whitelist

		tracer			Logs the players positions
		tracer-client	Reads the players position and filters them

		backup <reason>		Backups the server

		overviewer		Renders the overviewer map
		irc <start|stop|restart|status>	Controls the irc-bridge

		log			Open the logfile with less
		crash-reports	List and view the crash-reports of the minecraft server
		shell			Show the tail of the logfile and starts the minecraft shell
		remote <user>		Start a remote session with the given user


	Loglevels:
		CRITICAL	5
		ERROR		4
		WARNING		3
		INFO		2
		DEBUG		1



Multiple instances:
-------------------

If you want to have more than one server instance, then you need to copy the ini-file and execute the install command for this ini-file


Modules:
-------------------

Most of the modules can be used standalone (without the mvst) or they can be replaced by another program.

### wrapper.py

Starts the minecraft_server.jar and provides a unix socket that other processes can "talk" to the minecraft server.

### irc.py

Connects to the unix socket and an irc channel and bridges the chat between these two chatrooms.

### tracer.py

A simple programm that logs the players in-game position inside a sqlite file.

### tracer-client.py

A command tool skript to filter the sqlite file of the tracer.py

### control.py

Sends a control command to the minecraft server over the unix socket. Can be used for all minecraft ingame admin commands.



Troubleshooting:
------------------

### If the user who uses the mvst can't execute start-stop-daemon, edit the /etc/sudoers with visudo
	myuser       ALL = NOPASSWD: /usr/sbin/start-stop-daemon



Everything in this toolset is released under the terms of the GPL3. You can send patches or bugreports to mvst@noxzed.de or merge requests on github.
