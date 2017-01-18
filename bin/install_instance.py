#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import traceback

try:
	from mvst.mvst import Mvst
	from mvst.core_functions import CoreFunctions
except ImportError:
	print("Failed to execute! Can't import the mvst package!")
	exit(1)

try:
	m = Mvst(sys.argv[2:], sys.argv[1])
	m.start()
except:
	print("usage: install_instance.py <ini-file> install <version>\n\neg. ./install_instance.py mvst-new.ini install 1.11.2\nOtherwise read the manual.")
	traceback.print_exc(file=sys.stdout)
