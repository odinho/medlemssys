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
            if hasattr(version.object, 'admin_change'):
                str_ver.append(version.object.admin_change())
            else:
                str_ver.append(str(version.object))
        total_changes = r.version_set.count()
        text = ', '.join(str_ver)
        if total_changes > SHOW_CHANGES:
            text = "Totalt {0} endringar: {1} ...".format(total_changes, text)
        revision_list.append((r, text))

    return render(request, 'admin/revision_list.html', {
        'revision_list': revision_list,
        'title': 'Versjonar',
    })
