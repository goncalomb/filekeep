import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

def read(path):
    root = ET.parse(path).getroot()
    for elem in root.iter('*'):
        if elem.text != None and elem.text.strip() == "":
            elem.text = None
        if elem.tail != None and elem.tail.strip() == "":
            elem.tail = None
    return root

def write(path, root):
    xml = ET.tostring(root, encoding="UTF-8")
    xml = minidom.parseString(xml).toprettyxml(indent="  ", encoding="UTF-8")
    with open(path, "wb") as f:
        f.write(xml)
