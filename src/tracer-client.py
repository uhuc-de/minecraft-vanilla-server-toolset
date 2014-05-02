#!/bin/python2
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

	verbose = False

	try:
		# Option with ":" need an Argument
		opts, args = getopt.getopt(argv, "hvz:d:r:y:", ["help", "verbose", "since=", "until="] )
	except getopt.GetoptError:
		usage()
		
		
	for opt, arg in opts:
		
		if opt == ("-h", "--help"):
			usage()
			
		elif opt in ("-v", "--verbose"):
			verbose = True
			
		elif opt in "-r": 
			r = int(arg)
			
		elif opt in "-y": 
			y = int(arg)
			
		elif opt in "-d":
			d = int(arg)

		elif opt in "--since":
			since = arg

		elif opt in "--until":
			until = arg

	if verbose:
		argv = argv[ (len(opts)*2) -1:]
	else:
		argv = argv[len(opts)*2:]


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

	if verbose:
		print("=== Result: ===")

	sort = sorted(ergebnis, key=lambda tup: tup[0])
	for i in sort:
		print(makePrintable(i))
	# datensätze sortieren (nach zeit)
	
	
	#for key, value in sorted(mydict.iteritems(), key=lambda (k,v): (v,k)):
    #print "%s: %s" % (key, value)
    
    
	# ausgeben





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
#(1360518780, u'S3l33ngrab', 0, -22.8724823461, 64.1040803781, -282.664357201)

	return "%s %s \t(%s: %.1f / %.1f / %.1f)" % (getPrintTime(t[0]), t[1], t[2], t[3], t[4], t[5] )



def getPrintTime(unixtime):
	""" Returns the Timeformat (YYYY-MM-DD) from the unixtime """
	return ( datetime.datetime.fromtimestamp(int(unixtime)).strftime('%Y-%m-%d %H:%M') )
	

if __name__ == "__main__":
	main(sys.argv[1:])


