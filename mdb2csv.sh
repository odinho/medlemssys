#!/bin/bash
if [[ $# > 0 ]]; then
	namn=$1
else
	namn=nmu.mdb
fi

rsync -e "ssh -i $HOME/.ssh/fosse" -avzP aasen.nynorsk.no:"/srv/vinje/0\ MEDLEM/nmu.mdb" "$namn"

mv nmu-medl.csv nmu-medl.csv.old
mv nmu-lag.csv  nmu-lag.csv.old
mv nmu-bet.csv  nmu-bet.csv.old

mdb-export $namn medl > nmu-medl.csv
mdb-export $namn lag  > nmu-lag.csv
mdb-export $namn bet  > nmu-bet.csv

makediff() {
	head -n 1 $1 > $1.new
	diff $1.old $1 | egrep "^> " | sed 's/^> //' >> $1.new
}

makediff nmu-medl.csv
makediff nmu-lag.csv
makediff nmu-bet.csv

GET http://medlem.nynorsk.no/import/
