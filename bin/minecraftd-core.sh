#!/bin/bash

#### VARIABLES ####

## Primary variables



_MC_USER=$MC_USER
_MC_GROUP=$MC_GROUP
_LOGLEVEL=$LOGFILE

_LOGFILE="$MAINDIR/logs/mvst_${_INSTANCE}.log"

_DIR_SERVER="${MAINDIR}/server/${_INSTANCE}"
_DIR_BACKUP="${MAINDIR}/backups/${_INSTANCE}"
_DIR_MVSTBIN="${MAINDIR}/bin"
_DIR_TMP="${MAINDIR}/tmp"
_DIR_LOGS="${MAINDIR}/logs"
_DIR_OVERVIEWER="${MAINDIR}/overviewer/${_INSTANCE}"


_BIN_PYTHON2=`which python2`
_BIN_DAEMON=`which start-stop-daemon`
_BIN_OVERVIEWER=`which overviewer.py`
_BIN_WGET=`which wget`

## Secondary variables

# Get name of the world
grep -q "level-name" "${_DIR_SERVER}/server.properties" 2> /dev/null 
if [[ $? == 2 ]] # grep file not found
then
	_MAPNAME=world
else
	_MAPNAME=$(grep "level-name" "${_DIR_SERVER}/server.properties" | cut -d "=" -f 2)
fi


_WRAPPER_SOCKET="${_DIR_TMP}/wrapper_${_INSTANCE}.socket"
_WRAPPER_PID="${_DIR_TMP}/wrapper_${_INSTANCE}.pid"
_WRAPPER_CMD="${_DIR_MVSTBIN}/wrapper.py -s $_WRAPPER_SOCKET -v ${_LOGLEVEL} -l $_LOGFILE --- java -jar minecraft_server.jar nogui"

_TRACER_DATABASE="${_DIR_SERVER}/${_MAPNAME}/tracer_data.sqlite"



## METHODS


#### TRACER ####


do_tracer() {
	tracerdb="${_TRACER_DATABASE}"
	playerdata="${_DIR_SERVER}/${_MAPNAME}/playerdata/"

	$_BIN_PYTHON2 $_DIR_MVSTBIN/tracer.py "$playerdata" "$tracerdb"
}


#### WRAPPER ####

# Starts the wrapper
do_start () {
	echo -n "Start minecraft-server... "

	if is_running; then
		echo "is already running."
		exit 1
	else
		${_BIN_DAEMON} -n "mcwrapper" --start --background \
			--user $_MC_USER --group $_MC_GROUP \
			--pidfile $_WRAPPER_PID --make-pidfile \
			--chdir $_DIR_SERVER \
			--exec $_BIN_PYTHON2 -- $_WRAPPER_CMD
		echo "Done." || echo "Fail."
	fi


}

# Stops the wrapper
do_stop () {
	echo -n "Stop minecraft server... "

	if is_running; then
		say "Server stops in 3 seconds."
		sleep 3
		${_BIN_DAEMON} --pidfile $_WRAPPER_PID --stop --signal INT --retry 10
		echo "Done." || echo "Fail."
		rm -f $_WRAPPER_PID
		rm -f $_WRAPPER_SOCKET 
	else
		echo "server is not running."
	fi
}

# Restart the wrapper
do_restart () {
	say "Restarting..."
	do_stop
	sleep 3
	do_start
}


do_status() {
	echo -n 'Checking minecraft-server status... '
	if is_running; then
		echo "Running."
		exit 0
	else
		echo "Stopped."
		exit 1
	fi

}

is_running() {
	$_BIN_PYTHON2 $_DIR_MVSTBIN/control.py -s $_WRAPPER_SOCKET --check 2> /dev/null

	if [[ $? == 0 ]]; then
		return 0
	else
		return 1
	fi
}


do_control() {
	if echo $@ | $_BIN_PYTHON2 $_DIR_MVSTBIN/control.py -s $_WRAPPER_SOCKET 2>> $_LOGFILE ; then
		return 0
	else
		return 1
	fi
}

say() {
	do_control /say $@
}

suspend_saves() {
	# id = lock reason
	id=$1
	shift
	if test '(' `find "$_DIR_TMP" -iname "${_INSTANCE}-save-lock-*" | wc -l` == 0 ')'; then
		do_control "save-off"
		do_control "save-all"
	fi
	touch "$_DIR_TMP/${_INSTANCE}-save-lock-$id"
}

start_saves() {
	id=$1
	shift
	[[ -f "${_DIR_TMP}/${_INSTANCE}-save-lock-$id" ]] && rm "${_DIR_TMP}/${_INSTANCE}-save-lock-$id"
	if test '(' `find "${_DIR_TMP}" -iname "${_INSTANCE}-save-lock-*" | wc -l` == 0 ')'; then
		do_control "save-on"
	fi
}

#### WHITELIST ####

do_whitelist() {
	if [ -z "$1" ]; then
		echo "And whats the name of the user??" 1>&2
		exit 1
	fi

	if [ ! is_running ]; then
		echo "Couldn't connect to the server!"
	else
		user=`echo $1 | tr '[:upper:]' '[:lower:]'`
		say "Whitelisting user ,,${user}''"

		do_backup "${user}"

		do_control whitelist add ${user}
		say "Added ,,${user}'' to whitelist."
	fi

}

#### OVERVIEWER ####

do_overviewer() {
	log "Perform overviewer"
	if test '(' `find "$_DIR_TMP" -iname "${_INSTANCE}-save-lock-overviewer" | wc -l` == 0 ')'; then
		touch "$_DIR_TMP/${_INSTANCE}-save-lock-overviewer"
	else
		s="Overviewer still running: abort rendering" 
		echo $s
		log $s
		exit 1
	fi		


	running=is_running
	if $running; then
		startt=$(date +%s)
		say "Start mapping..."
		suspend_saves overviewercopy
		sleep 3
	fi	

	rsync -a "${_DIR_SERVER}/${_MAPNAME}/" "$_DIR_OVERVIEWER/mapcopy"

	if $running; then
		start_saves overviewercopy
	fi

	nice -n 10 $OVERVIEWER_CMD 2>> $_LOGFILE >> /dev/null
	
	if $running; then
		endt=$(date +%s)
		diff=$(( $(($endt - $startt)) / 60 ))

		say "Finished mapping in $diff minutes"
	fi
	rm "$_DIR_TMP/${_INSTANCE}-save-lock-overviewer"
}

#### BACKUP ####

do_backup() {
	if [ -z "$1" ]; then
		echo "Too few arguments!" 1>&2
		exit 1
	fi

	reason=$(echo $1 | tr '[:upper:]' '[:lower:]' | sed -r 's/[^a-z0-9_\-]+//g' | tr '-' '_')
	time=`date '+%Y-%m-%d-%H%M%S'`
	backupfile=${_DIR_BACKUP}/${time}_${reason}

	log "Perform backup ${reason}"
	running=is_running
	if $running; then
		say "Performing world backup ,,${reason}''"
		suspend_saves backup
	fi	

	sleep 3

	tar -c -jh --exclude-vcs -C "${_DIR_SERVER}" -f "${backupfile}.tar.bz2" $_MAPNAME $BACKUP_FILELIST

	# generate md5sum
	cd $_DIR_BACKUP
	md5sum "${time}_${reason}.tar.bz2" > "${backupfile}.tar.bz2.md5"

	if $running; then
		start_saves backup
		say "Backup complete"
	fi	

	cd $_DIR_BACKUP
	# symlink the bz2
	if [ -e latest.tar.bz2 ]; then
		rm -f latest.tar.bz2
	fi
	ln -s `ls $_DIR_BACKUP/*.tar.bz2 | sort -n | tail -n 1` latest.tar.bz2

	# symlink the md5sum
	if [ -e latest.tar.bz2.md5 ]; then
		rm -f latest.tar.bz2.md5
	fi
	ln -s `ls $_DIR_BACKUP/*.tar.bz2.md5 | sort -n | tail -n 1` latest.tar.bz2.md5

}



#### UPDATER ####

do_update() {
	if [[ -z "$1" ]]; then
		usage
	fi

	echo "Update from $(cat ${_DIR_SERVER}/version) to $1"

	time=`date '+%Y-%m-%d-%H-%M-%S'`
	version=$1
	start="no"

	# Download the jars
	echo -n "Download server.jar... "
	$_BIN_WGET -q -O "${_DIR_TMP}/minecraft_server.jar" "http://s3.amazonaws.com/Minecraft.Download/versions/${version}/minecraft_server.${version}.jar"
	r1=$?
	echo "Done"
	echo -n "Download client.jar... "
	$_BIN_WGET -q -O "${_DIR_TMP}/minecraft_client.jar" "http://s3.amazonaws.com/Minecraft.Download/versions/${version}/${version}.jar"
	r2=$?
	echo "Done"

	# Check if download was successfull
	if [ "$r1" == "0" ] && [ "$r2" == "0" ]; then

		echo -n "Backup... "
		do_backup "update_$(echo "$version" | tr '.' '_')"
		echo "Done"

		if is_running; then
			echo -n "Shutdown server... "
			say "Update to version $version: Server is going to restart!"
			do_stop
			start="yes"
			echo "Done"
		fi

		# Move jars to serverdir
		mv "${_DIR_TMP}/minecraft_server.jar" "${_DIR_SERVER}/minecraft_server.jar"
		mv "${_DIR_TMP}/minecraft_client.jar" "${_DIR_SERVER}/minecraft_client.jar"

		# Changing ownership
		echo -n "Changing ownership... "
		chown $_MC_USER:$_MC_GROUP "${_DIR_SERVER}/minecraft_server.jar"
		chown $_MC_USER:$_MC_GROUP "${_DIR_SERVER}/minecraft_client.jar"
		echo "Done"

		# Write current version to file
		echo "$version" > "${_DIR_SERVER}/version"
	else
		# Download failed
		rm "${_DIR_TMP}/minecraft_server.jar" "${_DIR_TMP}/minecraft_client.jar"
		echo "Couldn't download the files. Maybe the version was wrong?"
		echo "exit codes of wget were $r1 and $r2"
	fi


	if [[ "${start}" == "yes" ]]; then
		echo -n "Start server... "
		do_start
		echo "Done"
	fi
}

#### SHELL ####

do_shell() {
	tail -n 25 ${_LOGFILE}
	echo ""
	${_BIN_PYTHON2} ${_DIR_MVSTBIN}/control.py -s ${_WRAPPER_SOCKET}
}

#### LOG ####

do_log() {
	less +G ${_LOGFILE}
}


### WRITES TO LOGFILE ###

log() {
	a=$(date +"%F %T,")
	b=$(date +%N | cut -b1-3)
	echo "$a$b|mvst|INFO|$@" >> $_LOGFILE
}




#### MAIN STUFF ####



usage() {
	echo """
Usage: $0 {command}

Command:
	start			Starts the server
	stop			Stops the server
	status			Shows the status of the server
	restart			Restarts the Server

	say <msg>		Say <msg> ingame
	control <cmd>		Sends a raw command to the server
	update <version>	Perform backup and change to <version> (eg. 1.5.6)
	whitelist <user> 	Perform backup and add <user> to whitelist
	tracer			Logs the players positions 
	backup <reason>		Backups the server
	overviewer		Renders the overviewer map

	log			Open the logfile with less
	shell			Show the tail of the logfile and starts the minecraft shell

"""
	exit 1
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
		do_restart
		;;
 	status)
		do_status
		;;
	update)
		do_update $2
		;;
	overviewer)
		do_overviewer
		;;
	control)
		shift
		do_control $@
		;;
	say)
		shift
		say $@
		;;
	backup)
		shift
		do_backup $@
		;;
	tracer)
		do_tracer
		;;	
	whitelist)
		do_whitelist $2
		;;	
	shell)
		do_shell
		;;
	log)
		do_log
		;;
	*)
		usage
		;;
esac
exit 0




