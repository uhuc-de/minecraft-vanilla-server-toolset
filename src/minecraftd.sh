#!/bin/sh

## VARIABLES

_MCDIR="/home/minecraft/"
_MAPNAME=world

_MC_USER="minecraft"
_MC_GROUP="minecraft"

_WRAPPER_JAVA_CMD="java -jar minecraft_server.jar nogui"
_WRAPPER_SOCKET="/tmp/mcwrapper.socket"
_WRAPPER_LOG="/tmp/wrapper.log"
_WRAPPER_PID="/tmp/wrapper.pid"
_WRAPPER_CMD="/home/minecraft/wrapper.py -s $_WRAPPER_SOCKET -l $_WRAPPER_LOG --- $_WRAPPER_JAVA_CMD"


## METHODS

# Starts the wrapper
do_start () {
	echo "Start minecraft-server..."

	start-stop-daemon -n "mcwrapper" --start --background \
		--user $_MC_USER --group $_MC_GROUP \
		--pidfile $_WRAPPER_PID --make-pidfile \
		--chdir $_MCDIR \
		--exec /usr/bin/python2 -- $_WRAPPER_CMD
	echo "Done." || echo "Fail."
}

# Stops the wrapper
do_stop () {
	echo "Stop minecraft server"
	start-stop-daemon --pidfile $_WRAPPER_PID --stop --signal INT --retry 10
	echo "Done." || echo "Fail."
	#rm $_WRAPPER_PID
}

do_status() {
	start-stop-daemon --pidfile $_WRAPPER_PID --status
	echo "Running." || echo "Not Running."
}


## MAIN

case "$1" in

	start)
		do_start
		;;
	stop)
		do_stop
		;;
	restart)
		do_stop
		sleep 3
		do_start
		;;
 
	status)
		do_status
		;;
	*)
		echo "Usage: $0 {start|stop|restart}"
		exit 1
		;;
 
esac
exit 0

