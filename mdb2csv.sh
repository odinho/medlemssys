#!/bin/bash
if [[ $# > 0 ]]; then
	namn=$1
else
	namn=nmu.mdb
fi

mdb-export $namn medl > nmu-medl.csv
mdb-export $namn lag > nmu-lag.csv
mdb-export $namn bet > nmu-bet.csv
