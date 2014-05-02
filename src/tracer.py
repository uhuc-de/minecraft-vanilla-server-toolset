#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Written in Python 2
# By CyD 
# 
# 1.0 - 2012-11-15
# 1.1 - 2012-11-18
# 2.0 - 2014-04-30


import os
import sys
import traceback
import time
import urllib2	# needed by getUsernameByUuid()
import json		# needed by getUsernameByUuid()
import sqlite3 
from nbt import * # https://github.com/twoolie/NBT.git


###############################################
# PROGRAM


"""
Print the usage to the screen
"""
def help():
	print("""tracer.py {command} 

Commands: 

	install {tracerdatabase}
	log {playerdata} {tracerdatabase}
	clean {tracerdatabase}

Arguments:
	tracerdatabase	Sqlite File
	playerdata	Directory that contains the playerdata

Examples:
	tracer.py install /home/mc/player_positions.sqlite
	tracer.py clean /home/mc/player_positions.sqlite
	tracer.py log /home/mc/map/playerdata/ /home/mc/player_positions.sqlite
""")	
	sys.exit(2)



"""
Main method
"""
def main():

	if len(sys.argv) < 2:
		help()

	else: 
		action = sys.argv[1]

		if action == "install":
			install(sys.argv[2]) # argv[2] = DB

		elif action == "clean":
			# argv[2] = DB
			cleanDb(sys.argv[2])
			install(sys.argv[2])

		elif action == "log":
			# argv[2] = playerdata, argv[3] = DB
			logPlayers(sys.argv[3], sys.argv[2])

		else: 
			print("Wrong arguments!\n")
			help()


"""
Logs the players position to the database
"""
def logPlayers(db, players):

	timestamp = getTime()

	# append "/" to the end of the string
	if players[-1] is not "/":
		players += "/"

	for i in os.listdir(players):
		playerstats = getPlayerStats(players+i) # name, dimension, pos_x, pos_y, pos_z
		playerstats.append(timestamp)

		# add the tupel to the DB
		addEntry(playerstats, db)



"""
Adds a tupel to the database
"""
def addEntry(playerstats, db):
	connection = sqlite3.connect(db)
	cursor = connection.cursor()

	# Check if the position had chanced
	sql = ("SELECT * FROM positions WHERE uuid='%s' AND dimension='%s' AND pos_x='%s' AND pos_y='%s' AND pos_z='%s'" % (playerstats[0],playerstats[1],playerstats[2],playerstats[3],playerstats[4]) )
	cursor.execute(sql)
	vergleich = cursor.fetchall()

	# if different position -> save
	if len(vergleich) == 0:

		try:
			t = "INSERT INTO positions (uuid, dimension, pos_x, pos_y, pos_z, time) VALUES ('%s',%s,%s,%s,%s,%s )" % (playerstats[0],playerstats[1],playerstats[2],playerstats[3],playerstats[4],playerstats[5])
			cursor.execute(t)
			connection.commit()
		except:
			print("ERROR: addEntry()")
			traceback.print_exc(file=sys.stdout)

	cursor.close()
	connection.close()



def getPlayerStats(playerfile):
	# aufbau: name, dimension, x, y, z
	name = os.path.basename(playerfile).split(".")[0].replace("-","")
 	player = []
	nbtfile = nbt.NBTFile(playerfile,'rb')

	player.append(name) # name
	player.append(nbtfile["Dimension"]) # dimension
	player.append(nbtfile["Pos"][0]) # x
	player.append(nbtfile["Pos"][1]) # y
	player.append(nbtfile["Pos"][2]) # z
	return player




"""
Deletes every entry inside the DB
"""
def cleanDb(DB):
	try:
		connection = sqlite3.connect(DB)
		c = connection.cursor()

		c.execute("DROP TABLE positions")
		connection.commit()

		c.close()
		connection.close()
	except:
		print("ERROR: cleanDb()")
		traceback.print_exc(file=sys.stdout)


"""
Creates the database
"""
def install(db):
	""" 
	uuid playerid
	INTEGER dimension
	REAL pos_x
	REAL pos_y	
	REAL pos_z
	INTEGER unixtime
	"""
	try:

		connection = sqlite3.connect(db)
		c = connection.cursor()

		p = "CREATE TABLE positions ( id INTEGER PRIMARY KEY, uuid STRING not null, dimension INTEGER not null, pos_x REAL not null, pos_y REAL not null, pos_z REAL not null, time INTEGER not null)" 
		c.execute(p)
		connection.commit()

		c.close()
		connection.close()
	except: 
		print("ERROR: install()")
		traceback.print_exc(file=sys.stdout)



"""
Get the Username to the UUID using http://connorlinfoot.com/uuid/
"""
def getUsernameByUuid(uuid):
	"""
	POST https://api.mojang.com/profiles/page/1
	Content-Type: application/json
	{"name":"notch","agent":"minecraft"}
	"""


	data = {'name': 'thedudemaster', 'agent': 'minecraft'}
	#data = {'id': '4c104fd1ef9c4883917b58ceba010d37', 'agent': 'minecraft'}

	req = urllib2.Request('https://api.mojang.com/profiles/page/1')
	req.add_header('Content-Type', 'application/json')

	response = urllib2.urlopen(req, json.dumps(data))

	return response.read()




"""
Get the current unixtime
"""
def getTime():
	return int(time.time())



#####################################################

main()

#print( getUsernameByUuid("4c104fd1ef9c4883917b58ceba010d37") )





