Install
================

Get the minecraft vanilla server toolset version 2:
---------------------------------------------------

Visit https://gitorious.org/mvst2/mvst2 and download the source or clone it with git.


Depencies:
-----------------

Install the depencies of the toolset:


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
* nbt (https://github.com/twoolie/NBT)
* cron


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

Change at the end of control.pm the socket to the value of »_WRAPPER_SOCKET« in minecrafd.sh:

	    - '/tmp/mcwrapper.socket / UNIX'

To test you settings, start the server, stop it with a command and check the logs:

	$ minecraftd.sh start
	$ minecraftd.sh control stop
	$ less logs/wrapper_default.log

### Log player positions

If you want to log the movements of every player on your server you should add:

	*/1 * * * * /path/to/minecraftd.sh tracer log

The variable »_TRACER_DATABASE« is the place of the records. The default file is »tracer_data.sqlite« inside the map directory. If you want to read out the position records you should use tracer-client.py.


Multiple instances:
-------------------

If you want to run multiple instances of minecraft on the same maschine you can copy the minecraftd.sh and just need to change the variables »_DIR_SERVER« and »_INSTANCE«.





