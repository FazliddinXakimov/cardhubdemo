"""Standart kutubxona bilan BPMN 2.0 XML va uning SVG chizmasini yaratish."""

from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 900, 1270
INK, TEAL, RED = "#183044", "#007D78", "#AD3F3F"

# id, type, bounds (x,y,w,h), visual label lines, external label bounds
NODES = [
    ("Start", "startEvent", (212, 20, 36, 36), ["Boshlash"], (270, 24, 160, 30)),
    ("Input", "task", (80, 90, 300, 72), ["Kartalar, summa va", "komissiya usulini kiritish"], None),
    ("Valid", "exclusiveGateway", (190, 214, 80, 80), ["Summa, IDlar va", "usul to'g'rimi? [R1]"], (10, 221, 170, 58)),
    ("Active", "exclusiveGateway", (190, 356, 80, 80), ["Ikkala karta", "faolmi? [R2]"], (10, 363, 170, 58)),
    ("Fee", "task", (80, 490, 300, 96), ["Komissiya, jami yechim", "va oluvchiga tushadigan", "summani hisoblash"], None),
    ("Received", "exclusiveGateway", (190, 642, 80, 80), ["Oluvchiga kamida", "1 so'm tushadimi?"], (10, 649, 170, 58)),
    ("Funds", "exclusiveGateway", (190, 784, 80, 80), ["Balans jami", "yechimga yetadimi?"], (10, 791, 170, 58)),
    ("Update", "task", (80, 922, 300, 72), ["Ikkala balansni", "yangilash"], None),
    ("Save", "task", (80, 1048, 300, 72), ["Bitta tarix yozuvi", "yaratish va saqlash"], None),
    ("Success", "endEvent", (212, 1178, 36, 36), ["Bajarildi"], (270, 1182, 170, 30)),
    ("RejectMerge1", "exclusiveGateway", (654, 646, 72, 72), [], None),
    ("RejectMerge2", "exclusiveGateway", (654, 788, 72, 72), [], None),
    ("Reject", "task", (540, 922, 300, 96), ["Sababni ko'rsatish", "Holat o'zgarmaydi", "[R3]"], None),
    ("Rejected", "endEvent", (672, 1084, 36, 36), ["Rad etildi"], (730, 1088, 160, 30)),
]

# id, source, target, label, waypoints, label bounds, condition
FLOWS = [
    ("F1", "Start", "Input", "", [(230, 56), (230, 90)], None, None),
    ("F2", "Input", "Valid", "", [(230, 162), (230, 214)], None, None),
    ("F3", "Valid", "Active", "Ha", [(230, 294), (230, 356)], (245, 315, 40, 26), "valid_input"),
    ("F4", "Valid", "RejectMerge1", "Yo'q", [(270, 254), (690, 254), (690, 646)], (405, 220, 60, 26), None),
    ("F5", "Active", "Fee", "Ha", [(230, 436), (230, 490)], (245, 447, 40, 26), "cards_active"),
    ("F6", "Active", "RejectMerge1", "Yo'q", [(270, 396), (810, 396), (810, 682), (726, 682)], (405, 362, 60, 26), None),
    ("F7", "Fee", "Received", "", [(230, 586), (230, 642)], None, None),
    ("F8", "Received", "Funds", "Ha", [(230, 722), (230, 784)], (245, 739, 40, 26), "receiver_gets_money"),
    ("F9", "Received", "RejectMerge1", "Yo'q", [(270, 682), (654, 682)], (405, 648, 60, 26), None),
    ("F10", "Funds", "Update", "Ha", [(230, 864), (230, 922)], (245, 879, 40, 26), "balance_sufficient"),
    ("F11", "Funds", "RejectMerge2", "Yo'q", [(270, 824), (654, 824)], (405, 790, 60, 26), None),
    ("F12", "RejectMerge1", "RejectMerge2", "", [(690, 718), (690, 788)], None, None),
    ("F13", "Update", "Save", "", [(230, 994), (230, 1048)], None, None),
    ("F14", "Save", "Success", "", [(230, 1120), (230, 1178)], None, None),
    ("F15", "RejectMerge2", "Reject", "", [(690, 860), (690, 922)], None, None),
    ("F16", "Reject", "Rejected", "", [(690, 1018), (690, 1084)], None, None),
]

# Har bir qaror rombining "Yo'q" yo'li standart (default) oqim.
DEFAULT_FLOWS = {"Valid": "F4", "Active": "F6", "Received": "F9", "Funds": "F11"}

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


def create_xml():
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)
    def tag(prefix, name):
        return "{" + NS[prefix] + "}" + name
    root = ET.Element(tag("bpmn", "definitions"), {
        "id": "CardLabDefinitions", "targetNamespace": "urn:cardlab:training",
        "exporter": "CardLab", "exporterVersion": "1.1",
    })
    process = ET.SubElement(root, tag("bpmn", "process"), {
        "id": "TransferProcess", "name": "CardLab - pul o'tkazish", "isExecutable": "false",
    })
    ET.SubElement(process, tag("bpmn", "documentation")).text = (
        "O'quv jarayoni. Kiritma to'g'ri: summa R1ga mos, ikkala ID mavjud va turlicha, "
        "komissiya usuli additional yoki deduct. Komissiya 1%, yuqoriga yaxlitlanadi. "
        "Include commission yoqilganda komissiya summadan olinadi va oluvchiga kamida 1 so'm tushadi. "
        "Barcha rad etishlarda holat o'zgarmaydi."
    )
    for nid, kind, bounds, lines, label_bounds in NODES:
        attrs = {"id": nid}
        if lines:
            attrs["name"] = "\n".join(lines)
        if kind == "exclusiveGateway":
            attrs["gatewayDirection"] = "Diverging" if nid in DEFAULT_FLOWS else "Converging"
            if nid in DEFAULT_FLOWS:
                attrs["default"] = DEFAULT_FLOWS[nid]
        node = ET.SubElement(process, tag("bpmn", kind), attrs)
        for fid, source, target, *_ in FLOWS:
            if target == nid:
                ET.SubElement(node, tag("bpmn", "incoming")).text = fid
            if source == nid:
                ET.SubElement(node, tag("bpmn", "outgoing")).text = fid
    for fid, source, target, label, points, lb, condition in FLOWS:
        attrs = {"id": fid, "sourceRef": source, "targetRef": target}
        if label:
            attrs["name"] = label
        flow = ET.SubElement(process, tag("bpmn", "sequenceFlow"), attrs)
        if condition:
            ET.SubElement(flow, tag("bpmn", "conditionExpression"), {
                tag("xsi", "type"): "bpmn:tFormalExpression",
            }).text = condition
    diagram = ET.SubElement(root, tag("bpmndi", "BPMNDiagram"), {"id": "Diagram"})
    plane = ET.SubElement(diagram, tag("bpmndi", "BPMNPlane"), {
        "id": "Plane", "bpmnElement": "TransferProcess",
    })
    for nid, kind, bounds, lines, label_bounds in NODES:
        attrs = {"id": nid + "_di", "bpmnElement": nid}
        if kind == "exclusiveGateway":
            attrs["isMarkerVisible"] = "true"
        shape = ET.SubElement(plane, tag("bpmndi", "BPMNShape"), attrs)
        ET.SubElement(shape, tag("dc", "Bounds"), dict(zip(["x", "y", "width", "height"], map(str, bounds))))
        if label_bounds:
            label = ET.SubElement(shape, tag("bpmndi", "BPMNLabel"))
            ET.SubElement(label, tag("dc", "Bounds"), dict(zip(["x", "y", "width", "height"], map(str, label_bounds))))
    for fid, source, target, label, points, lb, condition in FLOWS:
        edge = ET.SubElement(plane, tag("bpmndi", "BPMNEdge"), {"id": fid + "_di", "bpmnElement": fid})
        for x, y in points:
            ET.SubElement(edge, tag("di", "waypoint"), {"x": str(x), "y": str(y)})
        if lb:
            label = ET.SubElement(edge, tag("bpmndi", "BPMNLabel"))
            ET.SubElement(label, tag("dc", "Bounds"), dict(zip(["x", "y", "width", "height"], map(str, lb))))
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(ROOT / "participant/transfer.bpmn", encoding="utf-8", xml_declaration=True)


def create_svg():
    output = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
              '<title id="title">CardLab: pul o‘tkazish BPMN jarayoni</title>',
              '<desc id="desc">Kiritma va karta holati tekshiriladi, tanlangan usul bo‘yicha komissiya hisoblanadi, oluvchiga kamida 1 so‘m tushsa va balans yetarli bo‘lsa o‘tkazma saqlanadi, aks holda rad etiladi.</desc>',
              '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L9,4.5 L0,9 Z" fill="#183044"/></marker></defs>',
              '<rect width="100%" height="100%" fill="white"/>']
    def text_box(lines, bounds, size=20, color=INK):
        x,y,w,h = bounds
        first_y = y + h/2 - (len(lines)-1)*size*1.2/2 + size*.34
        for index, line in enumerate(lines):
            output.append(f'<text x="{x+w/2}" y="{first_y+index*size*1.2}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size}" fill="{color}">{escape(line)}</text>')
    for fid, source, target, label, points, lb, condition in FLOWS:
        output.append('<polyline points="' + ' '.join(f'{x},{y}' for x,y in points) + f'" fill="none" stroke="{INK}" stroke-width="2.3" marker-end="url(#arrow)"/>')
        if fid in DEFAULT_FLOWS.values():
            x,y = points[0]
            output.append(f'<path d="M{x+13},{y-8} l10,16" stroke="{INK}" stroke-width="2.3"/>')
        if lb:
            text_box([label], lb, 19)
    for nid, kind, bounds, lines, label_bounds in NODES:
        x,y,w,h = bounds
        color = RED if nid in ("Reject", "Rejected") else INK
        if kind in ("startEvent", "endEvent"):
            output.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="{w/2-2}" fill="white" stroke="{color}" stroke-width="{5 if kind == "endEvent" else 2.5}"/>')
        elif kind == "exclusiveGateway":
            output.append(f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="#FFF7DF" stroke="{INK}" stroke-width="2.3"/>')
            text_box(["X"], bounds, 27)
        else:
            fill = "#FFF1EE" if nid == "Reject" else "#EDF8F7"
            output.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{color}" stroke-width="2.3"/>')
            text_box(lines, bounds, 22, color)
        if label_bounds:
            text_box(lines, label_bounds, 19, color)
    output.append('</svg>')
    (ROOT / "participant/transfer-bpmn.svg").write_text('\n'.join(output), encoding='utf-8')


if __name__ == "__main__":
    create_xml()
    create_svg()
    print("BPMN XML va SVG yaratildi.")
