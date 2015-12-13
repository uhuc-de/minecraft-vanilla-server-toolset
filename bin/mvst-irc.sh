#!/bin/bash

#### VARIABLES ####

_IRC_NICK=$IRC_NICK
_IRC_REALNAME=$IRC_REALNAME
_IRC_HOST=$IRC_HOST
_IRC_PORT=$IRC_PORT
_IRC_CHANNEL=$IRC_CHANNEL # channelname without starting "#"

_IRCBRIDGE_PID="${_DIR_TMP}/irc_${_INSTANCE}.pid"
_IRCBRIDGE_CMD="$_DIR_MVSTBIN/irc.py -l $_LOGFILE -r $_IRC_REALNAME -n $_IRC_NICK $_WRAPPER_SOCKET $_IRC_HOST $_IRC_CHANNEL"


# Starts the wrapper
do_irc_start () {
	echo -n "Start irc-bridge... "

	if ! is_running; then
		echo "Fail. - wrapper is not running!"
		return 1
	fi

	if is_irc_running; then
		echo "is already running."
		exit 1
	else
		${_BIN_DAEMON} -n "mcircbridge" --start --background \
			--user $_MC_USER --group $_MC_GROUP \
			--pidfile $_IRCBRIDGE_PID --make-pidfile \
			--chdir $_DIR_MVSTBIN \
			--exec $_BIN_PYTHON2 -- $_IRCBRIDGE_CMD
		r=$?
		if [ $r == "0" ] ; then
			echo "Done."
			log "irc" $_INFO "Started irc-bridge"
			say "irc-bridge is back online..."
		else
			echo "Fail."
		fi
	fi


}

# Stops the wrapper
do_irc_stop () {
	echo -n "Stop irc-bridge... "

	if is_irc_running; then
		${_BIN_DAEMON} --pidfile $_IRCBRIDGE_PID --stop --signal INT --retry 10
		echo "Done." || echo "Fail."
		rm -f $_IRCBRIDGE_PID
		log "irc" $_INFO "Stopped irc-bridge"
		say "irc-bridge is now offline..."
	else
		echo "irc-bridge is not running."
	fi
	
}

# Restart the wrapper
do_irc_restart () {
	say "Restarting irc-bridge..."
	do_irc_stop
	sleep 3
	do_irc_start
}

do_irc_status() {
	echo -n 'Checking irc-bridge status... '
	if is_irc_running; then
		echo "Running."
		exit 0
	else
		echo "Stopped."
		exit 1
	fi
}


# check if irc-bridge ist running
# return 0 = running
# return 1 = is not running
is_irc_running() {
	$_BIN_DAEMON -T -p $_IRCBRIDGE_PID
	r=$?
	if [ $r == "0" ] ; then
		return 0
	elif [ $r == "3" ] ; then
		return 1
	fi
}



do_irc () {

	case "$1" in
		start)
			do_irc_start
			;;
		stop)
			do_irc_stop
			;;
		restart)
			do_irc_restart
			;;
		status)
			do_irc_status
			;;
		*)
			usage
			;;
	esac

}


