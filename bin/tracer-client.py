#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys

import datetime
import sqlite3 

import getopt
import traceback
from os.path import isfile, getsize



def usage():
	print("""tracer-client.py [optional args] sqlfile [sqlfile ...]

	sqlfile		SQLite File from tracer.py

optional arguments:

	-x			x-coordinate (integer)
	-z			z-coordinate (integer)
	-y y				y-coordinate (integer)
	-d d				Dimension as number (-1 = nether, 0 = overworld, 1 = end)
	-r r				Search radius around x, z and y

	-n username		Query only this username (needs -c)
	-c usercache.json	Convert UUID to username with the usercache.json

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
	d = None
	r = 240
	until = None
	since = None

	usercache = None
	userfilter = ""

	verbose = False


	try:
		# Option with ":" need an Argument
		opts, args = getopt.getopt(argv, "hvz:d:r:y:x:z:c:n:", ["help", "verbose", "since=", "until="] )
	except getopt.GetoptError as err:
		print("GetoptError: %s" % err)
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
			r = arg
			p=p+2
			
		elif opt in "-y": 
			y = arg
			p=p+2
		elif opt in "-x": 
			x = arg
			p=p+2
		elif opt in "-z": 
			z = arg
			p=p+2
			
		elif opt in "-d":
			d = arg
			p=p+2

		elif opt in "-c":
			p=p+2
			try:
				usercache=getUserDictFromUserCache(arg)
			except:
				print("ERROR: can't read usercache.json!")
				usage()

		elif opt in "-n":
			userfilter = arg
			p=p+2

		elif opt in "--since":
			since = arg
			if len(since) < 10:
				print("ERROR: --since argument has wrong format!")
				usage()
			p=p+2

		elif opt in "--until":
			until = arg
			if len(until) < 10:
				print("ERROR: --until argument has wrong format!")
			p=p+2

	# remove all

	argv = argv[p:]
	filelist = argv



	## Check the variables and create the SQL query

	# Check the variable x
	if x != None:
		try:
			x = int(x)
		except ValueError:
			print("ERROR: x must be an integer!")
			usage()

	# Check the variable z
	if z != None:
		try:
			z = int(z)
		except ValueError:
			print("ERROR: z must be an integer!")
			usage()

	# Check the variable r
	if (z != None) and (y != None):
		try:
			r = int(r)
		except ValueError:
			print("ERROR: r must be an integer!")
			usage()
		where_pos = "AND pos_z >= {0} AND pos_z <= {1} AND pos_x >= {2} AND pos_x <= {3}".format(z-r, z+r, x-r, x+r)
	else:
		where_pos = ""

	sql = """SELECT time, uuid, dimension, pos_x, pos_y, pos_z 
FROM positions 
WHERE id IS NOT NULL {0}
""".format(where_pos)

	# Check the variable d
	if d:
		if d not in ("-1","0","1"):
			print("ERROR: d can only be -1, 0 or 1")
			usage()
		else:
			sql = sql + " AND dimension = %s" % (d)

	# Check the variable y
	if y:
		try:
			y = int(y)
			sql = sql + " AND pos_y >= %s AND pos_y <= %s" % (y-r, y+r)
		except ValueError:
			print("ERROR: z must be an integer!")
			usage()

	# Check the variable since
	if since:
		try:
			since = datetime.datetime.strptime(since,"%Y-%m-%d").strftime("%s")
			sql = sql + " AND time >= %s" % since
		except:
			print('ERROR: since Argument need to have the Format "YYYY-MM-DD"!')
			usage()

	# Check the variable until
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
		if not isSQLite3(db):
			print ("'%s' is not a SQLite3 database file" % db)
			sys.exit(2)

		query = getRecordsFromDb(db, sql)

		for satz in query:
			ergebnis.append(satz)

	# convert the uuid to username
	if usercache != None:
		tmp=ergebnis
		ergebnis= []
		for i in tmp:
			username = usercache.get(i[1], i[1])
			if not filterUsername(username, userfilter):
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
	if len(sort) == 0:
		print("No records found. Try another filter.")




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
	return "%s %s \t(%s: %.1f / %.1f / %.1f)" % (getPrintTime(t[0]), t[1], getDimensionValue(t[2]), t[3], t[4], t[5] )


def getDimensionValue(dim):
	""" 
	Returns the shortvalue of the dimension 
	-1 is the Nether, 0 is the Overworld, 1 is the End
	"""
	if dim == "-1": # Nether
		return "N"
	elif dim == "1": # End
		return "E"
	else: # Overworld
		return "O"

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

def isSQLite3(filename):
	"""
	Check if the sqlite3file is valid
	credits to: http://stackoverflow.com/questions/12932607/
	"""

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
Check if this username can be printed
0 = Dont filter
1 = Filter this name out
"""
def filterUsername(username, filterName):
	if filterName == "":
		return 0
	if filterName.lower() not in username.lower():
		return 1


if __name__ == "__main__":
	main(sys.argv[1:])


