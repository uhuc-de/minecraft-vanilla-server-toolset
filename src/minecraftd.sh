#!/bin/sh

# depends: wget, tar

#### VARIABLES ####

## Primary variables

_INSTANCE="default"

MAINDIR="/home/minecraft"
_DIR_SERVER="${MAINDIR}/server"
_DIR_BACKUP="${MAINDIR}/backup"
_DIR_MVSTBIN="${MAINDIR}/bin"
_DIR_TMP="${MAINDIR}/tmp"
_DIR_LOGS="${MAINDIR}/logs"

_MC_USER="minecraft"
_MC_GROUP="minecraft"

_CLIENT_JAR="/home/minecraft/.minecraft/bin/minecraft.jar"

_BIN_PERL=`which perl`
_BIN_PYTHON2=`which python2`

## Secondary variables

_MAPNAME=$(grep "level-name" "${_DIR_SERVER}/server.properties" | cut -d "=" -f 2)

_WRAPPER_SOCKET="${_DIR_TMP}/wrapper_${_INSTANCE}.socket"
_WRAPPER_PID="${_DIR_TMP}/wrapper_${_INSTANCE}.pid"
_WRAPPER_LOG="${_DIR_LOGS}/wrapper_${_INSTANCE}.log"
_WRAPPER_CMD="${_DIR_MVSTBIN}/wrapper.py -s $_WRAPPER_SOCKET -l $_WRAPPER_LOG --- java -jar minecraft_server.jar nogui"

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

	start-stop-daemon -n "mcwrapper" --start --background \
		--user $_MC_USER --group $_MC_GROUP \
		--pidfile $_WRAPPER_PID --make-pidfile \
		--chdir $_DIR_SERVER \
		--exec $_BIN_PYTHON2 -- $_WRAPPER_CMD
	echo "Done." || echo "Fail."
}

# Stops the wrapper
do_stop () {
	echo -n "Stop minecraft server... "
	do_control "/say Server stops in 3 seconds."
	sleep 3
	start-stop-daemon --pidfile $_WRAPPER_PID --stop --signal INT --retry 10
	echo "Done." || echo "Fail."
	rm $_WRAPPER_PID
	#rm $_WRAPPER_SOCKET
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
	if echo 'list' | $_BIN_PERL ${_DIR_MVSTBIN}/control.pm --force-raw 2> /dev/null ; then
		return 0
	else
		return 1
	fi
}

do_control() {
	echo $@ | $_BIN_PERL ${_DIR_MVSTBIN}/control.pm --force-raw 2> /dev/null
}

say() {
	do_control /say $@
}

suspend_saves() {
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

do_whitelist() {
	echo "Performing backup"
	do_backup "whitelist"

	for user in $@; do
		user=`echo $user | tr '[:upper:]' '[:lower:]'`
		echo "Whitelisting user ,,${user}''"
		if is_running; then
			do_control whitelist add ${user}
			say "Added ,,${user}'' to whitelist."
		else
			echo "Couldn't connect to the server!"
		fi
	done
}


#### BACKUP ####

do_backup() {
	link='no'
	clear_db='no'
	reason=''
	case $1 in
		daily)
			_bakDir="$_DIR_BACKUP/daily"
		;;
		weekly)
			_bakDir="$_DIR_BACKUP/weekly"
			link='yes'
			clear_db='yes'
		;;
		*)
			_bakDir="$_DIR_BACKUP/extra"
			reason=$2
			reason=$(echo $reason | tr '[:upper:]' '[:lower:]' | sed -r 's/[^a-z0-9_\-]+//g' | tr '-' '_')
			if [[ $reason != "" ]]; then
				$reason="-${reason}"
			fi
		;;
	esac
	time=`TZ='Europe/Berlin' date '+%Y-%m-%d-%H-%M-%S'`
	say 'Performing world backup'
	suspend_saves backup
	sleep 1
	tar -c -jh --exclude-vcs -C "${_DIR_SERVER}/${_MAPNAME}" -f "$_bakDir/${time}${reason}.tar.bz2" ./ 
	start_saves backup
	say 'Backup complete'

	if [[ $link == 'yes' ]]; then
		cd $_bakDir
		[[ -e latest.tar.bz2 ]] && rm -f latest.tar.bz2
		ln -s `ls $_bakDir | sort -n | tail -n 1` latest.tar.bz2
	fi

	if [[ $clear_db == 'yes' ]]; then
		do_tracer_clean
	fi
}



#### UPDATER ####

do_update() {
	if [[ -z "$1" ]]; then
		usage
	fi

	time=`date '+%Y-%m-%d-%H-%M-%S'`
	version=$1
	start="no"
	if is_running; then
		say "Server going down for update"
		do_stop
		start="yes"
	fi
	# Backup the jars
	if [[ -f "${_DIR_SERVER}/minecraft_server.jar" ]]; then
		echo -n "Saving jar "
		mv "${_DIR_SERVER}/minecraft_server.jar" "${_DIR_BACKUP}/server_jar/minecraft_server_${time}.jar"
		echo "Done"
	fi
	if [[ -f "$_CLIENT_JAR" ]]; then
		echo -n "Saving client jar "
		mv "$_CLIENT_JAR" "$_DIR_BACKUP/client_jar/minecraft_${time}.jar"
		echo "Done"
	fi
	# Download the jars
	wget -O "${_DIR_SERVER}/minecraft_server.jar" "http://s3.amazonaws.com/Minecraft.Download/versions/${version}/minecraft_server.${version}.jar"
	wget -O "$_CLIENT_JAR" "http://s3.amazonaws.com/Minecraft.Download/versions/${version}/${version}.jar"

	echo -n "Changing ownership "
	chown $_MC_USER:$_MC_GROUP "${_DIR_SERVER}/minecraft_server.jar"
	chown $_MC_USER:$_MC_GROUP "$_CLIENT_JAR"
	echo "Done"

	if [[ "${start}" == "yes" ]]; then
		do_start
	fi
}



#### MAIN STUFF ####

do_install() {
	# generate directories if needed
	mkdir -p "${_DIR_BACKUP}/weekly"
	mkdir -p "${_DIR_BACKUP}/daily"
	mkdir -p "${_DIR_BACKUP}/extra"
	mkdir -p "${_DIR_BACKUP}/server_jar"
	mkdir -p "${_DIR_BACKUP}/client_jar"

	mkdir -p "${_DIR_TMP}"
	mkdir -p "${_DIR_LOGS}"
}



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
	update <version>	Update to <version> (eg. 1.5.6)
	whitelist [<user> ...]	Perform extra backup and add <user> to whitelist
	tracer			Logs the players positions 

	backup <arg>		Backups the server


Backup arguments:
	daily			Perform the daily backup
	weekly			Perform the weekly backup
	<reason>		Perform an extra backup, named <reason>

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
		do_stop
		sleep 3
		do_start
		;;
 	status)
		do_status
		;;
	install)
		do_install
		;;
	update)
		do_update $2
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
		shift
		do_whitelist $@
		;;	
	*)
		usage
		;;
esac
exit 0



