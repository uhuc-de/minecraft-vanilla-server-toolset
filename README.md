Minecraft Vanilla Server Toolset
================================

... is a compilation of different Skripts. This Bundle isn't a "all-round 
carefree package" for wannabe serveradministrators who want an "easy to use" 
Window where they can click through. If you are familiar with Linux and the 
Shell you should have no problems to run the skripts and maybe edit them as you 
want.

Everything in this toolset is released under the terms of the GPL3. You can
send patches to mvst@noxzed.de.



wrapper.py
------------


Depencies:
	python 2.*


Description:
Starts the Minecraftserver and provides a unix-socket for incomming client 
connections. It broadcasts the output from the minecraft_server.jar to the 
clients and forward every input from a client to the Server.


Usage: 
	wrapper.py --help



control.pm
----------

Depencies:
	perl >= 2.5.10
	perl-curses
	perl-io-interactive
	perl-io-tty 
	perl-term-readkey
	perl-yaml





tracer.py
----------


Depencies:
	python 2.*
	nbt (https://github.com/twoolie/NBT)
	cron


Description:
	This tool gets the position of every Player on the server and saves it 
	in a database. There won't be a record, if the player doesn't move.

Usage:
	python2 tracer.py 

Installation:

	You have to run:
	$ python2 /path/to/playerlog.py install path/to/the/db.sql
	This will create database and table for the records.

	You need to add the line 
	*/1 * * * * python2 /path/to/tracer.py log mcmap/playerdata/ mc/db.sqlite
	to the crontab.


================================================================================
tracer-client.py

Depencies: 

	python 2.*
	
Description:

	A client to query the tracer.py SQLitefiles easily.
	

Usage:

	python2 tracer-client.py --help




