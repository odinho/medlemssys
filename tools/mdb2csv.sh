#!/bin/bash

# Copyright 2009-2014 Odin Hørthe Omdal

# This file is part of Medlemssys.

# Medlemssys is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Medlemssys is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Medlemssys.  If not, see <http://www.gnu.org/licenses/>.
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
	mv "nmu-$1.csv" "nmu-$1.csv.old"
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

#GET http://medlem.nynorsk.no/import/
cd ..
. env/bin/activate

cd medlemssys/
./manage.py medlem_import --force-update
