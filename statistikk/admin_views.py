from django.shortcuts import render
from reversion.models import Revision

def show_revisions(request):
    revision_list = []
    for r in Revision.objects.all().order_by('-date_created')[:100]:
        if revision_list and str(revision_list[-1][0]) == str(r):
            revision_list[-1][0].comment += "\n" + r.comment
            continue
        str_ver = []
        for version in r.version_set.all()[:50]:
            if hasattr(version.object, 'admin_change'):
                str_ver.append(version.object.admin_change())
            else:
                str_ver.append(str(version.object))
        text = ', '.join(str_ver)
        revision_list.append((r, text))

    return render(request, 'admin/revision_list.html', { 'revision_list': revision_list })
