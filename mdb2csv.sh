#!/bin/bash
if [[ $# > 0 ]]; then
	namn=$1
else
	namn=nmu.mdb
fi

rsync -e "ssh -i $HOME/.ssh/fosse" -avzP aasen.nynorsk.no:"/srv/vinje/0\ MEDLEM/nmu.mdb" "$namn"

mdb-export $namn medl > nmu-medl.csv
mdb-export $namn lag > nmu-lag.csv
mdb-export $namn bet > nmu-bet.csv
