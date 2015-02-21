# -*- coding: utf-8 -*-
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
from django.shortcuts import render
from reversion.models import Revision

def show_revisions(request):
    SHOW_CHANGES = 50
    revision_list = []
    for r in Revision.objects.all().order_by('-date_created')[:250]:
        if revision_list and str(revision_list[-1][0]) == str(r):
            revision_list[-1][0].comment += "\n" + r.comment
            continue
        str_ver = []
        for version in r.version_set.all()[:SHOW_CHANGES]:
            try:
                str_ver.append(version.object.admin_change())
            except (AttributeError, ValueError):
                str_ver.append(unicode(version))
        total_changes = r.version_set.count()
        text = u', '.join(str_ver)
        if total_changes > SHOW_CHANGES:
            text = u"Totalt {0} endringar: {1} ...".format(total_changes, text)
        revision_list.append((r, text))

    return render(request, 'admin/revision_list.html', {
        'revision_list': revision_list,
        'title': 'Versjonar',
    })
