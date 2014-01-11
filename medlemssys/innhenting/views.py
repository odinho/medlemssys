# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
import logging
from django.shortcuts import render
from .ocr import OCR, OCRError

logger = logging.getLogger(__name__)


def import_ocr(request):
    errorlist = []
    if request.method == 'POST':
        ocr_data = request.POST.get('ocr_data', '')
        ocr = OCR()
        logger.debug("Running OCR file: {}".format(ocr_data))
        try:
            ocr.from_string(ocr_data)
        except OCRError as e:
            errorlist.append("Feil med OCR-fil: {}".format(unicode(e)))
        else:
            ocr.process_to_db()
            processed = filter(lambda o: o['processed'], ocr.data)
            not_processed = filter(lambda o: not o['processed'], ocr.data)
            return render(request, 'admin/import_ocr_done.htm', {
                    'not_processed': not_processed,
                    'processed': processed,
                    'title': u'OCR-køyring',
                })

    return render(request, 'admin/import_ocr.htm', {
        'title': u'OCR-køyring',
        'errorlist': errorlist,
    })
