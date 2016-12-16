#!/bin/bash

# overviewer.py needs to be in the $PATH

usage() {
	echo "overviewer.sh [<options> ...] -c {settings} 
	
Arguments
-c {settings}	path to the settings for the rendering

Options:
-n {nice}	change the nice value
-l {logfile} 	logfile"

	exit 1
}

# default values
nice=10
settings=""
logfile=""

# getopts
while getopts c:n:l: opt
do
	case $opt in
		n) nice="$OPTARG";;
		c) settings="$OPTARG";;
		l) logfile="$OPTARG";;
	esac
done

# check parameters
if [[ ! -f "$settings" ]]; then
	echo "Abort: given settings is not a file"
	usage
fi

if [[ ! -f "$logfile" ]]; then
	echo "Abort: no logfile defined"
	usage
fi

logstr=""
if [[ ! -z "$logfile" ]]; then
	logstr=" 2>>$logfile "
fi

# render
nice -n $nice overviewer.py --quiet -c $settings $logstr 1>/dev/null
nice -n $nice overviewer.py --quiet -c $settings --genpoi $logstr 1>/dev/null



