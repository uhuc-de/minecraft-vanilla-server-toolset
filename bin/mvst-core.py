#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from mvst.mvst import Mvst

if __name__ == "__main__":
	m = Mvst(sys.argv[1:])
	exit(m.start())

