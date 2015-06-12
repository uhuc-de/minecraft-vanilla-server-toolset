#!/bin/sh


do_usage() {

	echo "${0} <version> [<instance>]"
	echo "default instance = default"


}


do_mkdirs() {
	_ROOT=$1
	_INSTANCE=$2

	echo "Make the directories..."
	mkdir -p -v  "$_ROOT/server/$_INSTANCE/"
	mkdir -p -v  "$_ROOT/backups/$_INSTANCE/"
	mkdir -p -v  "$_ROOT/logs/"
	mkdir -p -v  "$_ROOT/tmp/"
	mkdir -p -v  "$_ROOT/share/$_INSTANCE/mapcopy"
	mkdir -p -v  "$_ROOT/share/$_INSTANCE/overviewer"

# create the instance script
cat <<EOF > "$_ROOT/bin/minecraftd.$_INSTANCE.sh"
#!/bin/sh
# Dont change something you dont understand!

_INSTANCE=$_INSTANCE

# All Directories without tailing "/"!
MAINDIR="/home/minecraft"

# Level	Numeric value:
# 5 CRITICAL
# 4 ERROR
# 3 WARNING
# 2 INFO
# 1 DEBUG
LOGLEVEL=2

# user and group who should run the server
MC_USER="minecraft"
MC_GROUP="minecraft"

# line which executes the overviewer
OVERVIEWER_CMD="overviewer.py --quiet $MAINDIR/share/$_INSTANCE/mapcopy $MAINDIR/share/$_INSTANCE/overviewer "

# list files beside the map which should be inside the backupfile
# tar (..options..) $_MAPNAME $BACKUP_FILELIST
# the list need to inside double quotes
BACKUP_FILELIST="whitelist.json server.properties banned-players.json"

## END OF CONFIG ##
source "$_ROOT/bin/mvst-core.sh"
EOF


}


do_dependencies() {
	array=("tar" "wget" "less" "bash" "rsync" "java" "overviewer.py" "start-stop-daemon" "python2")
	for i in "${array[@]}"; do
		echo -e -n "$i... "
		if command -v $i >/dev/null 2>&1; then
			echo "found"	
		else
			echo >&2 "NOT FOUND"
		fi
	done

echo -e -n "nbt... \t"
python2 <<EOF
try:
 import nbt
 exit(0)
except ImportError, e:
 exit(1)
EOF

if test 0 -eq $? 2>&1; then
	echo "found"	
else
	echo >&2 "NOT FOUND"
fi


}



main() {

	if [ "$#" -eq 0 ] ; then
		echo "To few arguments"
		do_usage
		exit 1
	fi

	if test "$#" -gt 2; then
		echo "To many arguments"
		do_usage
		exit 1
	fi

	_VERSION=${1}

	if test "$#" -eq 2; then
		_INSTANCE=${2}
	else
		_INSTANCE=default
	fi

	_ROOT=$(dirname $(pwd))


	echo "*** Install ***"
	echo "Install with the options: "
	echo "Version: $_VERSION"
	echo "Instance: $_INSTANCE"
	echo "MVST root directory: $_ROOT"
	echo ""
	echo "*** Check for dependencies ***"
	do_dependencies
	echo ""
	echo "*** Create Directories ***"
	pause
	do_mkdirs $_ROOT ${_INSTANCE}


	echo ""
	echo "*** Get the JARs ***"
	wget -O "${_ROOT}/server/$_INSTANCE/minecraft_server.jar" "http://s3.amazonaws.com/Minecraft.Download/versions/${_VERSION}/minecraft_server.${_VERSION}.jar"
	wget -O "${_ROOT}/server/$_INSTANCE/minecraft_client.jar" "http://s3.amazonaws.com/Minecraft.Download/versions/${_VERSION}/${_VERSION}.jar"
	echo ""

	echo "eula=true" > "${_ROOT}/server/$_INSTANCE/eula.txt"
	echo "Installation complete!"
	echo ""	
	echo "Now edit the server.properties and the crontab"
	echo "After that , you can start the service with:"
	echo "$ minecraftd.$_INSTANCE.sh start"
}

pause(){
	echo ""
	read -p 'Press [ENTER] key to continue...'
}



case "$1" in

	--help)
		do_usage
		;;
	*)
		main $@
		#do_dependencies
		#do_install
		;;
esac
exit 0

