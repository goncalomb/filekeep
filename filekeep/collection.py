import os, hashlib, collections
from filekeep import logger, xml

def sha1_file(path, logger=None):
    sha1 = hashlib.sha1()
    with open(path, "rb", buffering=0) as f:
        while True:
            data = f.read(65536)
            if data:
                sha1.update(data)
                if logger:
                    logger.progress(len(data))
            else:
                return sha1.hexdigest()

def compare_times(a, b, flexible):
    if flexible:
        return a//1000000000 == b//1000000000
    return a == b

class File:
    @staticmethod
    def from_file(path, calculate_sha1=False):
        stat = os.lstat(path)
        f = File(os.path.basename(path), stat.st_size, stat.st_mtime_ns)
        f.path = path
        if calculate_sha1:
            f.sha1 = sha1_file(path)
        return f

    @staticmethod
    def from_xml(el):
        f = File(el.get("name"), int(el.get("size")), int(el.get("mtime")))
        f.sha1 = el.get("sha1")
        return f

    def __init__(self, name, size, mtime):
        self.path = None
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
        d = Directory(os.path.basename(path), os.lstat(path).st_mtime_ns)
        d.path = path
        return d

    @staticmethod
    def from_xml(el):
        d = Directory(el.get("name"), int(el.get("mtime") or "0"))
        for e in el:
            if e.tag == "directory":
                ee = Directory.from_xml(e)
                d.entries[ee.name] = ee
            elif e.tag == "file":
                ee = File.from_xml(e)
                d.entries[ee.name] = ee
        return d

    def __init__(self, name=None, mtime=0):
        self.path = None
        self.name = name
        self.mtime = mtime
        self.entries = collections.OrderedDict()

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
            self.name = "FileKeep Collection (" + os.path.abspath(self.path) + ")"
            self.directory = Directory()
            self.exists = False

        self.logger = logger.create(self.size())

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

    def create_from_path(self, quiet=False):
        dirs = {
            self.path: self.directory
        }
        cd = 1
        cf = 0
        for dirpath, dirnames, filenames in os.walk(self.path):
            d = dirs[dirpath]
            for dirname in dirnames:
                path = os.path.join(dirpath, dirname)
                d.entries[dirname] = dirs[path] = Directory.from_file(path)
                cd += 1
            if not quiet:
                print(dirpath)
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if not quiet:
                    print("  " + filename)
                d.entries[filename] = File.from_file(path, True)
                cf += 1
        return (cd, cf)

    def verify(self, fast=False, touch=False, flexible_times=False):
        paths_to_touch = []

        # directory entries referenced by relative path
        dirs = {
            self.path: self.directory
        }

        # function return value
        result = True

        for dirpath, dirnames, filenames in os.walk(self.path):
            if not dirpath in dirs:
                continue

            found_error = False
            d = dirs[dirpath]
            entries = d.entries.copy()

            # process directories
            for dirname in dirnames:
                path = os.path.join(dirpath, dirname)
                if dirname in entries and isinstance(entries[dirname], Directory):
                    dirs[path] = entries[dirname]
                    del entries[dirname]
                else:
                    self.logger.error("extra directory '" + path + "'")
                    found_error = True

            # process files
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if filename in entries and isinstance(entries[filename], File):
                    stat = os.lstat(path)
                    needs_touch = False

                    if not compare_times(entries[filename].mtime, stat.st_mtime_ns, flexible_times):
                        self.logger.error("'" + path + "' different mtime")
                        if touch:
                            needs_touch = True
                        else:
                            found_error = True

                    if entries[filename].size != stat.st_size:
                        self.logger.error("'" + path + "' different size")
                        self.logger.progress(entries[filename].size)
                        found_error = True
                    elif (not fast or needs_touch) and entries[filename].sha1 != sha1_file(path, self.logger):
                        self.logger.error("'" + path + "' different sha1")
                        found_error = True
                    elif needs_touch:
                        paths_to_touch.append((path, entries[filename].mtime))
                    elif fast:
                        self.logger.progress(entries[filename].size)

                    del entries[filename]

                elif path != "./filekeep.xml":
                    self.logger.error("extra file '" + path + "'")
                    found_error = True

            # handle missing entries
            for e in entries.values():
                found_error = True
                path = os.path.join(dirpath, e.name)
                if isinstance(e, Directory):
                    self.logger.error("missing directory '" + path + "'")
                    self.logger.progress(e.size())
                else:
                    self.logger.error("missing file '" + path + "'")
                    self.logger.progress(e.size)

            # process directory
            if dirpath != '.' and not compare_times(d.mtime, os.lstat(dirpath).st_mtime_ns, flexible_times):
                self.logger.error("'" + dirpath + "' (directory) different mtime")
                if touch and not found_error:
                    paths_to_touch.append((dirpath, d.mtime))
                else:
                    result = False

            if found_error:
                result = False

        if touch:
            if paths_to_touch:
                self.logger.print("touching")
                for (path, mtime) in paths_to_touch:
                    os.utime(path, ns=(mtime, mtime))
            else:
                self.logger.print("nothing to touch")

        return result

    def print_sha1sum(self):
        self.directory.print_sha1sum("")
