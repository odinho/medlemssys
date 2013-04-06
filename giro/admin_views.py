from django.shortcuts import render

from medlemssys.medlem.models import Giro
from .views import send_ventande_rekningar

def send(request):
    if request.method == 'POST':
        sende = send_ventande_rekningar()
        successful = [r for r in sende if r.status == '1']
        unsuccessful = [r for r in sende if r.status != '1']
        return render(request, 'admin/giro/send_done.html', {
                'successful': successful,
                'unsuccessful': unsuccessful })
    ventar = Giro.objects.filter(status='V').select_related('medlem')
    return render(request, 'admin/giro/send.html', {
        'ventar': ventar,
        'title': 'Send ventande giroar',
    })
