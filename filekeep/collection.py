import os, hashlib
from filekeep import xml

def sha1_file(path):
    sha1 = hashlib.sha1()
    with open(path, "rb", buffering=0) as f:
        while True:
            data = f.read()
            if data:
                sha1.update(data)
            else:
                return sha1.hexdigest()

class File:
    @staticmethod
    def from_file(path, calculate_sha1=False):
        f = File(os.path.basename(path), os.path.getsize(path), os.path.getmtime(path))
        if calculate_sha1:
            f.sha1 = sha1_file(path)
        return f

    @staticmethod
    def from_xml(el):
        f = File(el.get("name"), int(el.get("size")), float(el.get("mtime")))
        f.sha1 = el.get("sha1")
        return f

    def __init__(self, name, size, mtime):
        self.name = name
        self.size = size
        self.mtime = mtime
        self.sha1 = ""

    def to_xml(self):
        el = xml.ET.Element("file")
        el.set("name", self.name)
        el.set("mtime", str(self.mtime))
        el.set("size", str(self.size))
        el.set("sha1", self.sha1)
        return el

    def print_sha1sum(self, rel):
        if rel:
            rel += "/"
        print(self.sha1 + " *" + rel + self.name)

class Directory:
    @staticmethod
    def from_file(path):
        return Directory(os.path.basename(path), os.path.getmtime(path))

    @staticmethod
    def from_xml(el):
        d = Directory(el.get("name"), float(el.get("mtime") or "0"))
        for e in el:
            if e.tag == "directory":
                ee = Directory.from_xml(e)
                d.entries[ee.name] = ee
            elif e.tag == "file":
                ee = File.from_xml(e)
                d.entries[ee.name] = ee
        return d

    def __init__(self, name=None, mtime=0):
        self.name = name
        self.mtime = mtime
        self.entries = {}

    def to_xml(self):
        el = xml.ET.Element("directory")
        if self.name != None:
            el.set("name", self.name)
            el.set("mtime", str(self.mtime))
        for e in self.entries.values():
            el.append(e.to_xml())
        return el

    def size(self):
        s = 0
        for e in self.entries.values():
            if isinstance(e, File):
                s += e.size
            else:
                s += e.size()
        return s

    def print_sha1sum(self, rel):
        if rel:
            rel += "/"
        if self.name:
            rel += self.name
        for e in self.entries.values():
            e.print_sha1sum(rel)

class Collection:
    def __init__(self, path):
        self.path = path
        self.path_xml = os.path.join(self.path, "filekeep.xml")

        if os.path.isfile(self.path_xml):
            root = xml.read(self.path_xml)
            self.name = root.find("name").text
            self.directory = Directory.from_xml(root.find("directory"))
            self.exists = True
        else:
            self.name = "FileKeep Collection"
            self.directory = Directory()
            self.exists = False

    def write_data(self):
        root = xml.ET.Element("collection")
        name = xml.ET.Element("name")
        name.text = self.name
        root.append(name)
        root.append(self.directory.to_xml())
        xml.write(self.path_xml, root)

    def set_name(self, name):
        self.name = name

    def size(self):
        return self.directory.size()

    def create_from_path(self):
        dirs = {
            self.path: self.directory
        }
        for dirpath, dirnames, filenames in os.walk(self.path):
            d = dirs[dirpath]
            for dirname in dirnames:
                path = os.path.join(dirpath, dirname)
                d.entries[dirname] = dirs[path] = Directory.from_file(path)
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                d.entries[filename] = File.from_file(path, True)

    def print_sha1sum(self):
        self.directory.print_sha1sum("")
