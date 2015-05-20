#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys

import datetime
import sqlite3 

import getopt
import traceback




def usage():
	print("""tracer-client.py [optional args] x z sqlfile [sqlfile ...]

	x			x-coordinate (integer)
	z 			z-coordinate (integer)
	sqlfile		SQLite File from tracer.py

optional arguments:

	-c usercache.json	Convert UUID to username with the usercache.json
	-y y				y-coordinate (integer)
	-d d				Dimension (-1, 0, 1)
	-r r				Search radius around x, z and y
	--since	YYYY-MM-DD	Showing entries newer or of the specified date
	--until YYYY-MM-DD	Stop showing entries newer or of the specified date
	-v --verbose		Shows the SQL Query
""")	
	sys.exit(2)


def main(argv):
	""" main method """
	
	# default values
	x = None
	y = None
	z = None
	d = 0
	r = 240
	until = None
	since = None

	usercache = None

	verbose = False

	try:
		# Option with ":" need an Argument
		opts, args = getopt.getopt(argv, "hvz:d:r:y:c:", ["help", "verbose", "since=", "until="] )
	except getopt.GetoptError:
		usage()
	
	# left over parameter length	
	p=0

	for opt, arg in opts:

		if opt in ("-h", "--help"):
			usage()
			
		elif opt in ("-v", "--verbose"):
			verbose = True
			p=p+1
			
		elif opt in "-r": 
			r = int(arg)
			p=p+2
			
		elif opt in "-y": 
			y = int(arg)
			p=p+2
			
		elif opt in "-d":
			d = int(arg)

		elif opt in "-c":
			p=p+2
			try:
				usercache=getUserDictFromUserCache(arg)
			except:
				print("ERROR: can't read usercache.json!")
				usage()

		elif opt in "--since":
			since = arg
			p=p+1

		elif opt in "--until":
			until = arg
			p=p+1

	# remove all
	argv = argv[p:]

	try:
		x = int(argv[0])
		z = int(argv[1])
	except:
		print("ERROR: x and z need to be Integer!")
		usage()
	
	filelist = argv[2:]

	if d not in (-1,0,1):
		print("ERROR: d can only be -1, 0 or 1")
		usage()

	# Create SQL Query
	sql = """SELECT time, uuid, dimension, pos_x, pos_y, pos_z 
FROM positions 
WHERE dimension = %s
AND pos_z >= %s AND pos_z <= %s 
AND pos_x >= %s AND pos_x <= %s
""" % (d, z-r, z+r, x-r, x+r)
	
	if y:
		sql = sql + " AND pos_y >= %s AND pos_y <= %s" % (y-r, y+r)

	if since:
		try:
			since = datetime.datetime.strptime(since,"%Y-%m-%d").strftime("%s")
			sql = sql + " AND time >= %s" % since
		except:
			print('ERROR: since Argument need to have the Format "YYYY-MM-DD"!')
			usage()

	if until:
		try:
			until = datetime.datetime.strptime(until,"%Y-%m-%d").strftime("%s")
			sql = sql + " AND time <= %s" % until
		except:
			print('ERROR: until Argument need to have the Format "YYYY-MM-DD"!')
			usage()
	
	if verbose:
		print("=== SQL-Query: ===")
		print(sql)	

	# datensätze holen
	ergebnis = []
	for db in filelist:
		query = getRecordsFromDb(db, sql)
		
		for satz in query:
			ergebnis.append(satz)

	# convert the uuid to username
	if usercache != None:
		tmp=ergebnis
		ergebnis= []
		for i in tmp:
			username = usercache.get(i[1], i[1])
			j = (i[0], username, i[2], i[3], i[4], i[5])
			ergebnis.append(j)

	if verbose:
		print("=== Result: ===")

	sort = sorted(ergebnis, key=lambda tup: tup[0])
	for i in sort:
		try:
			print(makePrintable(i))
		except IOError:
			exit(0)


def getRecordsFromDb(dbfile, sql):
	""" 
	returns a set of Records from the sqlite file with the specific 
	sql query
	"""

	# connect to dbfile
	connection = sqlite3.connect(dbfile)
	cursor = connection.cursor()

	# fetch from DB
	temp=[]
	try:
		cursor.execute(sql)
		temp = cursor.fetchall()
	except:
		print("ERROR: Could'n open SqliteDB %s" % dbfile)
		traceback.print_exc(file=sys.stdout)

	# disconnect from dbfile
	cursor.close()
	connection.close()
	return temp


def makePrintable(t):
	""" Makes the SQL-tubel printable """
	return "%s %s \t(%s: %.1f / %.1f / %.1f)" % (getPrintTime(t[0]), t[1], t[2], t[3], t[4], t[5] )



def getPrintTime(unixtime):
	""" Returns the Timeformat (YYYY-MM-DD) from the unixtime """
	return ( datetime.datetime.fromtimestamp(int(unixtime)).strftime('%Y-%m-%d %H:%M') )
	

def getUserDictFromUserCache(usercache):
	""" Returns a dict with of the uuids and their usernames """
	cache = {}

	f = open(usercache,'r')
	for line in f.read().split('},{'):	
		name=line.split('"name":"')[1].split("\",\"")[0]
		uuid=line.split('"uuid":"')[1].split("\",\"")[0].replace("-", "")
		cache[uuid] = name
	f.close()
	return cache




if __name__ == "__main__":
	main(sys.argv[1:])


