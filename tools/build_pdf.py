"""BT.md matnidan tartiblangan PDF. Muallif uchun: pip install reportlab."""

import math
import os
import re
import shutil
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                               PageBreak, Preformatted, Flowable)
from build_materials import NODES, FLOWS, WIDTH, HEIGHT, DEFAULT_FLOWS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/BT-CardLab-Python.pdf"
INK = colors.HexColor("#183044")
TEAL = colors.HexColor("#007D78")
GRAY = colors.HexColor("#526477")
RED = colors.HexColor("#AD3F3F")
BODY_WIDTH = A4[0] - 92


def register_fonts():
    regular = os.environ.get("CARDLAB_FONT_REGULAR")
    bold = os.environ.get("CARDLAB_FONT_BOLD")
    candidates = [
        (regular, bold),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for normal, strong in candidates:
        if normal and strong and Path(normal).exists() and Path(strong).exists():
            pdfmetrics.registerFont(TTFont("Body", normal))
            pdfmetrics.registerFont(TTFont("BodyBold", strong))
            pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")
            return
    raise RuntimeError("Arial yoki DejaVu Sans kerak. CARDLAB_FONT_REGULAR va CARDLAB_FONT_BOLD bilan yo'lni bering.")


register_fonts()
styles = {
    "body": ParagraphStyle("body", fontName="Body", fontSize=10, leading=14, textColor=INK, spaceAfter=8),
    "h1": ParagraphStyle("h1", fontName="BodyBold", fontSize=27, leading=31, textColor=INK, spaceAfter=15),
    "h2": ParagraphStyle("h2", fontName="BodyBold", fontSize=16, leading=21, textColor=TEAL, spaceBefore=8, spaceAfter=11, keepWithNext=True),
    "h3": ParagraphStyle("h3", fontName="BodyBold", fontSize=11.5, leading=16, textColor=INK, spaceBefore=7, spaceAfter=7, keepWithNext=True),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=9, leading=12, textColor=INK),
    "small": ParagraphStyle("small", fontName="Body", fontSize=8.7, leading=12, textColor=GRAY, spaceAfter=7),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.1, leading=12, textColor=INK, backColor=colors.HexColor("#EFF5F6"), borderPadding=8, spaceAfter=12),
}


def inline(text):
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#007D78">\1</link>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" size="8.7">\1</font>', text)
    return text


def make_table(lines):
    rows = [[cell.strip() for cell in line.strip().strip('|').split('|')] for line in lines]
    rows = [row for row in rows if not all(re.fullmatch(r'[:\- ]+', cell) for cell in row)]
    header = rows[0]
    if header[0] == "ID" and len(header) == 3:
        widths = [32, 189, BODY_WIDTH-221]
    elif len(header) == 4:
        widths = [38, 169, 118, BODY_WIDTH-325]
    else:
        widths = [BODY_WIDTH-55, 55]
    data = [[Paragraph(inline(cell if r else '**'+cell+'**'), styles['cell']) for cell in row] for r,row in enumerate(rows)]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DDEEEB')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F8FA')]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LINEBELOW', (0,0), (-1,0), .7, colors.HexColor('#A1C5C2')),
    ]))
    return [table, Spacer(1, 12)]


def markdown(text):
    result, lines, i = [], text.strip().splitlines(), 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            block = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                block.append(lines[i]); i += 1
            result.extend(make_table(block)); continue
        if line.startswith('```'):
            code = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i]); i += 1
            result.append(Preformatted('\n'.join(code), styles['code'])); i += 1; continue
        if line.startswith('!['):
            i += 1; continue
        level = 'h3' if line.startswith('### ') else 'h2' if line.startswith('## ') else 'h1' if line.startswith('# ') else 'body'
        content = re.sub(r'^#{1,3} ', '', line)
        result.append(Paragraph(inline(content), styles[level])); i += 1
    return result


class BpmnDiagram(Flowable):
    def __init__(self, width=BODY_WIDTH, max_height=None):
        Flowable.__init__(self)
        if max_height:
            width = min(width, max_height / HEIGHT * WIDTH)
        self.width = width
        self.height = width / WIDTH * HEIGHT
        self.hAlign = 'CENTER'

    def draw(self):
        c = self.canv
        scale = self.width / WIDTH
        c.saveState(); c.scale(scale, scale)
        def text_box(lines, bounds, size=20, color=INK):
            x,y,w,h = bounds
            first_y = y+h/2-(len(lines)-1)*size*1.2/2+size*.34
            c.setFillColor(color); c.setFont('Body', size)
            for index,line in enumerate(lines):
                c.drawCentredString(x+w/2, HEIGHT-first_y-index*size*1.2, line)
        for fid, source, target, label, points, lb, condition in FLOWS:
            c.setStrokeColor(INK); c.setLineWidth(2.3)
            path = c.beginPath(); path.moveTo(points[0][0], HEIGHT-points[0][1])
            for x,y in points[1:]: path.lineTo(x, HEIGHT-y)
            c.drawPath(path)
            x,y = points[-1]; previous_x,previous_y = points[-2]
            angle = math.atan2(y-previous_y, x-previous_x)
            tip = c.beginPath(); tip.moveTo(x, HEIGHT-y)
            for delta in (-.5, .5):
                tip.lineTo(x-10*math.cos(angle+delta), HEIGHT-y+10*math.sin(angle+delta))
            tip.close(); c.setFillColor(INK); c.drawPath(tip, fill=1, stroke=0)
            if fid in DEFAULT_FLOWS.values():
                x,y=points[0]; c.line(x+13,HEIGHT-y+8,x+23,HEIGHT-y-8)
            if lb: text_box([label],lb,19)
        for nid, kind, bounds, lines, lb in NODES:
            x,y,w,h=bounds
            color=RED if nid in ('Reject','Rejected') else INK
            c.setStrokeColor(color); c.setFillColor(colors.white); c.setLineWidth(2.3)
            if kind in ('startEvent','endEvent'):
                c.setLineWidth(5 if kind=='endEvent' else 2.5)
                c.circle(x+w/2,HEIGHT-y-h/2,w/2-2,fill=1,stroke=1)
            elif kind=='exclusiveGateway':
                c.setFillColor(colors.HexColor('#FFF7DF'))
                p=c.beginPath(); p.moveTo(x+w/2,HEIGHT-y)
                p.lineTo(x+w,HEIGHT-y-h/2);p.lineTo(x+w/2,HEIGHT-y-h);p.lineTo(x,HEIGHT-y-h/2);p.close()
                c.drawPath(p,fill=1,stroke=1); text_box(['X'],bounds,27)
            else:
                c.setFillColor(colors.HexColor('#FFF1EE' if nid=='Reject' else '#EDF8F7'))
                c.roundRect(x,HEIGHT-y-h,w,h,12,fill=1,stroke=1);text_box(lines,bounds,22,color)
            if lb:text_box(lines,lb,19,color)
        c.restoreState()


def furniture(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D5E1E5')); canvas.setLineWidth(.6)
    canvas.line(46,A4[1]-37,A4[0]-46,A4[1]-37)
    canvas.setFont('BodyBold',8);canvas.setFillColor(TEAL)
    canvas.drawString(46,A4[1]-28,'CARDLAB / PYTHON HAKATONI')
    canvas.setFont('Body',8);canvas.setFillColor(GRAY)
    canvas.drawRightString(A4[0]-46,A4[1]-28,'ISHTIROKCHI UCHUN · BT v1.2')
    canvas.line(46,37,A4[0]-46,37)
    canvas.drawString(46,24,"Demo ma'lumotlar | 120 daqiqa | 2-3 kishilik jamoa")
    canvas.drawRightString(A4[0]-46,24,str(doc.page))
    canvas.restoreState()


def build():
    text=(ROOT/'participant/BT.md').read_text()
    intro,rest=text.split('## 3.',1)
    rules,rest=('## 3.'+rest).split('### C.',1)
    operations,rest=('### C.'+rest).split('## 5.',1)
    bpmn,rest=('## 5.'+rest).split('## 6.',1)
    scenarios,rest=('## 6.'+rest).split('## 7.',1)
    technical,assessment=('## 7.'+rest).split('## 8.',1)
    scenario_intro,tabletext=scenarios.split('| ID |',1)
    table_lines=('| ID |'+tabletext).strip().splitlines()
    first_tests='\n'.join(table_lines[:12])
    next_tests='\n'.join(table_lines[:2]+table_lines[12:])
    story=[]
    intro=intro.replace('# CARDLAB - KARTALAR BILAN AMALIYOTLAR', '# CardLab\n## Kartalar bilan amaliyotlar')
    story+=markdown(intro)
    story.append(PageBreak());story+=markdown(rules)
    story.append(PageBreak());story+=markdown('## 4. Amaliyotlar (davomi)\n'+operations)
    story.append(PageBreak());story+=markdown("## 5. BPMN - pul o'tkazish\nKiritma to'g'ri: summa R1ga mos, ikkala ID mavjud va turlicha, komissiya usuli additional yoki deduct.")
    story.append(BpmnDiagram(BODY_WIDTH-36, max_height=575))
    story.append(Paragraph("Aylana - hodisa. Yumaloq to'rtburchak - vazifa. X romb - bitta yo'l tanlash yoki yo'llarni birlashtirish. Strelka - ketma-ketlik. Yo'q yo'llari rad etishga olib boradi.",styles['small']))
    story.append(Paragraph('Tahrirlash: transfer.bpmn. Notatsiya: <link href="https://www.omg.org/spec/BPMN/2.0.2/" color="#007D78">OMG BPMN 2.0.2</link>. Qolgan amaliyotlar 4-bo\'limda.',styles['small']))
    story.append(PageBreak());story+=markdown(scenario_intro+first_tests)
    story.append(PageBreak());story+=markdown('## 6. Qabul ssenariylari (davomi)\n'+next_tests)
    story.append(PageBreak());story+=markdown(technical+'## 8.'+assessment)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=53,bottomMargin=50,
                          title='CardLab - Python hakatoni: biznes talablar va BPMN',author='CardLab',pageCompression=1)
    doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
    shutil.copyfile(OUTPUT,ROOT/'participant/BT.pdf')
    print(OUTPUT)


if __name__=='__main__':build()
