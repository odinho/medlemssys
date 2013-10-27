# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

import os

from cStringIO import StringIO
from django.http import HttpResponse
from django.shortcuts import render

from .models import Communication, CommunicationIntent

def process_communications(request):
    if request.method == 'POST':
        email_pks = request.POST.getlist('email_ids', [])
        pdf_pks = request.POST.getlist('pdf_ids', [])
        emails = Communication.objects.filter(
          pk__in=email_pks,
        )
        pdfs = Communication.objects.filter(
          pk__in=pdf_pks,
        )
        for e in emails:
            e.email.send()

        # PDF
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        pdfmetrics.registerFont(TTFont('OCRB',
            os.path.dirname(__file__) + '/../giro/OCRB.ttf'))
        response = HttpResponse(mimetype="application/pdf")
        response['Content-Disposition'] = 'filename=girosending.pdf'

        # Create the PDF object, using the StringIO object as its "file."
        buf = StringIO()
        pdf = canvas.Canvas(buf)

        for e in pdfs:
            if e.pdf.layout == e.pdf.LAYOUT_GIRO:
                pdf = _giro_medlemskort(pdf, request, e.medlem, e.giro)
            elif e.pdf.layout == e.pdf.LAYOUT_FAKTURA:
                pdf = _giro_faktura(pdf, request, e.medlem, e.giro)
            pdf.showPage()

        # Close the PDF object cleanly.
        pdf.save()

        # Get the value of the StringIO buffer and write it to the response.
        pdf = buf.getvalue()
        buf.close()
        response.write(pdf)
        return response
        pass
    waiting_emails = Communication.objects.filter(
        processed__isnull=True, type=CommunicationIntent.TYPE_EMAIL)
    waiting_pdfs = Communication.objects.filter(
        processed__isnull=True, type=CommunicationIntent.TYPE_PDF)
    return render(request, 'admin/process_communications.html', {
        'waiting_emails': waiting_emails,
        'waiting_pdfs': waiting_pdfs,
        'title': "Process communications",
    })

def _pdf_p(pdf, text, x, y, size_w=None, size_h=None):
    from reportlab.lib.units import cm #, mm
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    if not size_w:
        size_w = 19
    if not size_h:
        size_h = size_w

    style = getSampleStyleSheet()['BodyText']
    p = Paragraph(text, style)
    used_w, used_h = p.wrap(size_w*cm, size_h*cm)
    p.wrapOn(pdf, size_w*cm, size_h*cm)
    p.drawOn(pdf, x*cm, y*cm - used_h)

def _giro_faktura(pdf, request, m, giro):
    from reportlab.lib.units import cm #, mm

    pdf.setFont('Helvetica', 16)
    pdf.drawString(1.0*cm, 16*cm, u"%s" % request.POST.get('title'))

    pdf.setFontSize(11)
    text = request.POST.get('text')
    text_content = Template(text).render(Context({'medlem': m, 'giro': giro})).replace('\n', '<br/>')
    _pdf_p(pdf, text_content, 1, 15.5, size_w=19, size_h=13)
    _pdf_p(pdf, m.full_betalingsadresse().replace('\n', '<br/>\n'), 1, 26, size_w=8, size_h=6)
    _pdf_p(pdf, u"""\
        Kundenr: {m.pk}<br/>
        Fakturanr: {g.pk}<br/>
        Fakturadato: {now}<br/>
        Betalingsfrist: {frist}<br/>
        Til konto: <b>{kontonr}</b><br/>
        KID-nummer: <b>{g.kid}</b><br/>
        Å betala: <b>{g.belop},00</b><br/>
        """.format(m=m,
                   g=giro,
                   kontonr=settings.KONTONUMMER,
                   now=datetime.date.today(),
                   frist=request.POST.get('frist')),
        15, 26, size_w=4, size_h=6)

    return pdf

def _giro_medlemskort(pdf, request, m, giro):
    from reportlab.lib.units import cm #, mm

    from mod10 import mod10

    pdf.setFont('Helvetica', 16)
    pdf.drawString(1.0*cm, 26*cm, u"%s" % request.POST.get('title'))
    pdf.setFontSize(12)

    text_template = Template(request.POST.get('text'))
    text_context = Context({'medlem': m, 'giro': giro})
    text_content = text_template.render(text_context).replace('\n', '<br/>')

    _pdf_p(pdf, text_content, 1, 25.5, size_w=18, size_h=13)

    pdf.setFont('OCRB', 11)
    tekst = pdf.beginText(1.2*cm, 5.5*cm)
    for adrdel in m.full_betalingsadresse().split('\n'):
        tekst.textLine(adrdel.strip())
    pdf.drawText(tekst)

    pdf.drawString(13*cm, 12.8*cm, u"%s" % giro.belop)
    pdf.drawString(15*cm, 12.8*cm, u"%s" % '00')
    pdf.drawString(14*cm, 14.2*cm, u"%s" % m.pk)
    pdf.drawString(18.3*cm, 14.2*cm, u"%s" % giro.gjeldande_aar)

    if m.har_betalt():
        pdf.drawString(18*cm, 12.8*cm, "BETALT")
        pdf.setFillColorRGB(0, 0, 0)
        pdf.rect(0,  5.3*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0, 4.85*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0,  1.9*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0, 1.45*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
    else:
        pdf.drawString(17.1*cm, 9.3*cm, u"%s" % request.POST.get('frist'))

        pdf.drawString(5.0*cm,  1.58*cm, u"%s" % giro.kid)
        pdf.drawString(8.5*cm,  1.58*cm, u"%s" % giro.belop)
        pdf.drawString(10.6*cm, 1.58*cm, u"%s" % '00')
        pdf.drawString(11.9*cm, 1.58*cm,
                       u"%s" % mod10(unicode(giro.belop) + '00'))
        pdf.drawString(13.2*cm, 1.58*cm, u"%s" % settings.KONTONUMMER)

    return pdf
def process_waiting_communications():
    waiting_emails = Communication.objects.filter(
        processed__isnull=True, type=CommunicationIntent.TYPE_EMAIL)
    waiting_pdf = Communication.objects.filter(
        processed__isnull=True, type=CommunicationIntent.TYPE_PDF)

    for com_email in waiting_emails:
        email = com_email.email
        msg = EmailMultiAlternatives(email.subject,
                body=email.text_body,
                to=email.to)
        if email.html_body:
            msg.attach_alternative(email.html_body, "text/html")
        msg.send()
