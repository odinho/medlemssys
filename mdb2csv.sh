#!/bin/bash

if [[ $# > 0 ]]; then
	namn=$1
else
	namn=nmu.mdb
fi


####################### FUNCTIONS ##########################

import()
{
	rsync -e "ssh -i $HOME/.ssh/fosse" -aq aasen.nynorsk.no:"/srv/vinje/0\ MEDLEM/nmu.mdb" "$namn"
}

make_diff()
{
	# Roter og ta inn nyimportert fil
	#mv "nmu-$1.csv" "nmu-$1.csv.old"
	mdb-export "$namn" "$1" > "nmu-$1.csv"

	# fix rn to n
	perl -p -i -e 's/\r\n/\\n/' "nmu-$1.csv"

	head -n 1 "nmu-$1.csv" > "nmu-$1.csv.new"
	diff "nmu-$1.csv.old" "nmu-$1.csv" |
		egrep "^> " |
		sed 's/^> //' >> "nmu-$1.csv.new"
}

############################################################


#import

make_diff medl
make_diff lag
make_diff bet

GET http://medlem.nynorsk.no/import/
