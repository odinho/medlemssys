from django.shortcuts import render
from medlemssys.innhenting.ocr import OCR

def import_ocr(request):
    if request.method == 'POST':
        ocr_data = request.POST.get('ocr_data', '')
        ocr = OCR()
        ocr.from_string(ocr_data)
        ocr.process_to_db()
        processed = filter(lambda o: o['processed'], ocr.data)
        not_processed = filter(lambda o: not o['processed'], ocr.data)
        return render(request, 'admin/import_ocr_done.htm', {
                'not_processed': not_processed,
                'processed': processed })

    return render(request, 'admin/import_ocr.htm')
