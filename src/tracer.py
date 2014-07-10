#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
import sys
import traceback
from os.path import isfile, getsize
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
	print("""tracer.py <playerdata> <tracerdatabase> 

Arguments:
	playerdata	Directory that contains the playerdata
	tracerdatabase	Sqlite File

Example:
	tracer.py /home/mc/map/playerdata/ /home/mc/player_positions.sqlite
""")	
	sys.exit(2)



"""
Main method
"""
def main():

	if len(sys.argv) < 2:
		help()

	else: 
		argData = sys.argv[1]
		argDb = sys.argv[2]


		if not isfile(argDb):
			install(argDb)

		if not isSQLite3(argDb):
			print ("'%s' is not a SQLite3 database file" % argDb)
			sys.exit(2)

		logPlayers(argDb, argData)


"""
Logs the players position to the database
"""
def logPlayers(db, players):

	timestamp = getTime()

	# append "/" to the end of the string
	if players[-1] is not "/":
		players += "/"

	playerlist = []
	for i in os.listdir(players):
		playerstats = getPlayerStats(players+i) # name, dimension, pos_x, pos_y, pos_z
		playerstats.append(timestamp)
		playerlist.append(playerstats)


	addEntries(playerlist, db)



"""
Adds a list of tupel to the database
"""
def addEntries(playerlist, db):
	connection = sqlite3.connect(db)
	cursor = connection.cursor()

	for playerstats in playerlist:

		# Check if the position had chanced
		sql = ("SELECT * FROM positions WHERE uuid='%s' AND dimension='%s' AND pos_x='%s' AND pos_y='%s' AND pos_z='%s'" % (playerstats[0],playerstats[1],playerstats[2],playerstats[3],playerstats[4]) )
		cursor.execute(sql)
		vergleich = cursor.fetchall()

		# if different position -> save
		if len(vergleich) == 0:

			try:
				t = "INSERT INTO positions (uuid, dimension, pos_x, pos_y, pos_z, time) VALUES ('%s',%s,%s,%s,%s,%s )" % (playerstats[0],playerstats[1],playerstats[2],playerstats[3],playerstats[4],playerstats[5])
				cursor.execute(t)
				
			except:
				print("ERROR: addEntry()")
				traceback.print_exc(file=sys.stdout)

	try:
		connection.commit()
	except:
		print("ERROR: commit failed")
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
Check if the sqlite3file is valid
credits to: http://stackoverflow.com/questions/12932607/
"""
def isSQLite3(filename):
	if not isfile(filename):
		return False
	if getsize(filename) < 100: # SQLite database file header is 100 bytes
		return False
	else:
		fd = open(filename, 'rb')
		Header = fd.read(100)
		fd.close()

		if Header[0:16] == 'SQLite format 3\000':
			return True
		else:
			return False



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
		print("Not able to create a database at %s" % db)
		traceback.print_exc(file=sys.stdout)


"""
Get the current unixtime
"""
def getTime():
	return int(time.time())



#####################################################

main()

