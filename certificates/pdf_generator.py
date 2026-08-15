from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor


def generate_certificate_pdf(certificate):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    brown = HexColor('#5c4033')
    cream = HexColor('#f7f3eb')

    c.setFillColor(cream)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setStrokeColor(brown)
    c.setLineWidth(2)
    c.rect(15 * mm, 15 * mm, width - 30 * mm, height - 30 * mm)

    c.setFillColor(brown)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width / 2, height - 40 * mm, 'GUJARAT VIDYAPITH')
    c.setFont('Helvetica', 11)
    c.drawCentredString(width / 2, height - 48 * mm, 'Medical Certificate')
    c.setFont('Helvetica', 9)
    c.drawCentredString(width / 2, height - 55 * mm, '(Institutional Healthcare – DEMO)')

    y = height - 75 * mm
    c.setFont('Helvetica', 11)
    lines = [
        f'Certificate No.: {certificate.certificate_number}',
        f'Patient: {certificate.patient.name} ({certificate.patient.patient_id})',
        f'Category: {certificate.patient.get_category_display()}',
        f'Consultation Date: {certificate.consultation_date}',
        f'Doctor: Dr. {certificate.doctor.name}',
        '',
        'Medical Advice:',
        certificate.medical_advice or '—',
    ]
    if certificate.rest_recommended:
        lines += [
            '',
            f'Rest Recommended: Yes ({certificate.rest_days or "—"} day(s))',
            f'From: {certificate.rest_start_date or "—"}  To: {certificate.rest_end_date or "—"}',
        ]
    if certificate.remarks:
        lines += ['', f'Remarks: {certificate.remarks}']

    for line in lines:
        for chunk in _wrap(line, 90):
            c.drawString(30 * mm, y, chunk)
            y -= 7 * mm
            if y < 40 * mm:
                break

    c.setFont('Helvetica', 9)
    c.drawString(30 * mm, 30 * mm, f'Status: {certificate.get_status_display()}')
    c.drawRightString(width - 30 * mm, 30 * mm, 'Authorized Doctor Signature')
    c.setFont('Helvetica-Oblique', 8)
    c.drawCentredString(width / 2, 20 * mm, 'This is a system-generated institutional record. Not a legal seal.')
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def _wrap(text, width):
    words = str(text).split()
    lines, cur = [], ''
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = f'{cur} {w}'.strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or ['']
