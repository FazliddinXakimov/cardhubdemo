"""Standart kutubxona bilan BPMN 2.0 XML va uning SVG chizmasini yaratish."""

from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 900, 1100
INK, TEAL, RED = "#183044", "#007D78", "#AD3F3F"

# id, type, bounds (x,y,w,h), visual label lines, external label bounds
NODES = [
    ("Start", "startEvent", (212, 20, 36, 36), ["Boshlash"], (270, 24, 160, 30)),
    ("Input", "task", (80, 90, 300, 72), ["Yuboruvchi, oluvchi va", "summani kiritish"], None),
    ("Valid", "exclusiveGateway", (190, 214, 80, 80), ["Summa va IDlar", "to'g'rimi? [R1]"], (10, 221, 170, 58)),
    ("Active", "exclusiveGateway", (190, 356, 80, 80), ["Ikkala karta", "faolmi? [R2]"], (10, 363, 170, 58)),
    ("Fee", "task", (80, 490, 300, 72), ["Komissiya va jami", "yechimni hisoblash"], None),
    ("Funds", "exclusiveGateway", (190, 618, 80, 80), ["Balans jami", "yechimga yetadimi?"], (10, 625, 170, 58)),
    ("Update", "task", (80, 756, 300, 72), ["Ikkala balansni", "yangilash"], None),
    ("Save", "task", (80, 882, 300, 72), ["Bitta tarix yozuvi", "yaratish va saqlash"], None),
    ("Success", "endEvent", (212, 1012, 36, 36), ["Bajarildi"], (270, 1016, 170, 30)),
    ("RejectMerge", "exclusiveGateway", (654, 622, 72, 72), [], None),
    ("Reject", "task", (540, 756, 300, 96), ["Sababni ko'rsatish", "Holat o'zgarmaydi", "[R3]"], None),
    ("Rejected", "endEvent", (672, 918, 36, 36), ["Rad etildi"], (730, 922, 160, 30)),
]

# id, source, target, label, waypoints, label bounds, condition
FLOWS = [
    ("F1", "Start", "Input", "", [(230, 56), (230, 90)], None, None),
    ("F2", "Input", "Valid", "", [(230, 162), (230, 214)], None, None),
    ("F3", "Valid", "Active", "Ha", [(230, 294), (230, 356)], (245, 315, 40, 26), "valid_input"),
    ("F4", "Valid", "RejectMerge", "Yo'q", [(270, 254), (690, 254), (690, 622)], (405, 220, 60, 26), None),
    ("F5", "Active", "Fee", "Ha", [(230, 436), (230, 490)], (245, 447, 40, 26), "cards_active"),
    ("F6", "Active", "RejectMerge", "Yo'q", [(270, 396), (810, 396), (810, 658), (726, 658)], (405, 362, 60, 26), None),
    ("F7", "Fee", "Funds", "", [(230, 562), (230, 618)], None, None),
    ("F8", "Funds", "Update", "Ha", [(230, 698), (230, 756)], (245, 711, 40, 26), "balance_sufficient"),
    ("F9", "Funds", "RejectMerge", "Yo'q", [(270, 658), (654, 658)], (405, 624, 60, 26), None),
    ("F10", "Update", "Save", "", [(230, 828), (230, 882)], None, None),
    ("F11", "Save", "Success", "", [(230, 954), (230, 1012)], None, None),
    ("F12", "RejectMerge", "Reject", "", [(690, 694), (690, 756)], None, None),
    ("F13", "Reject", "Rejected", "", [(690, 852), (690, 918)], None, None),
]

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
        "exporter": "CardLab", "exporterVersion": "1.0",
    })
    process = ET.SubElement(root, tag("bpmn", "process"), {
        "id": "TransferProcess", "name": "CardLab - pul o'tkazish", "isExecutable": "false",
    })
    ET.SubElement(process, tag("bpmn", "documentation")).text = (
        "O'quv jarayoni. Kiritma to'g'ri: summa R1ga mos, ikkala ID mavjud va turlicha. "
        "Komissiya 1%, yuqoriga yaxlitlanadi. Barcha rad etishlarda holat o'zgarmaydi."
    )
    for nid, kind, bounds, lines, label_bounds in NODES:
        attrs = {"id": nid}
        if lines:
            attrs["name"] = "\n".join(lines)
        if kind == "exclusiveGateway":
            attrs["gatewayDirection"] = "Converging" if nid == "RejectMerge" else "Diverging"
            if nid != "RejectMerge":
                attrs["default"] = {"Valid": "F4", "Active": "F6", "Funds": "F9"}[nid]
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
              '<desc id="desc">Kiritma va karta holati tekshiriladi, komissiya hisoblanadi, balans yetarli bo‘lsa o‘tkazma saqlanadi, aks holda rad etiladi.</desc>',
              '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L9,4.5 L0,9 Z" fill="#183044"/></marker></defs>',
              '<rect width="100%" height="100%" fill="white"/>']
    def text_box(lines, bounds, size=20, color=INK):
        x,y,w,h = bounds
        first_y = y + h/2 - (len(lines)-1)*size*1.2/2 + size*.34
        for index, line in enumerate(lines):
            output.append(f'<text x="{x+w/2}" y="{first_y+index*size*1.2}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size}" fill="{color}">{escape(line)}</text>')
    for fid, source, target, label, points, lb, condition in FLOWS:
        output.append('<polyline points="' + ' '.join(f'{x},{y}' for x,y in points) + f'" fill="none" stroke="{INK}" stroke-width="2.3" marker-end="url(#arrow)"/>')
        if fid in ("F4", "F6", "F9"):
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
