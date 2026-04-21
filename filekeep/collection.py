import collections
import os
import stat

from . import xml
from .utils import sha1_file


class File:
    @staticmethod
    def from_file(path, calculate_sha1=False):
        st = os.lstat(path)
        f = File(os.path.basename(path), st.st_size, st.st_mtime_ns, stat.S_IMODE(st.st_mode))
        f.path = path
        if calculate_sha1:
            f.sha1 = sha1_file(path)
        return f

    @staticmethod
    def from_xml(el):
        f = File(el.get('name'), int(el.get('size')), int(el.get('mtime')), int(el.get('mode') or 0))
        f.sha1 = el.get('sha1')
        return f

    def __init__(self, name, size, mtime, mode):
        self.path = None
        self.name = name
        self.size = size
        self.mtime = mtime
        self.mode = mode
        self.sha1 = ''

    def to_xml(self):
        el = xml.ET.Element('file')
        el.set('name', self.name)
        el.set('mtime', str(self.mtime))
        el.set('mode', str(self.mode))
        el.set('size', str(self.size))
        el.set('sha1', self.sha1)
        return el

    def print_sha1sum(self, rel):
        if rel:
            rel += '/'
        print(self.sha1 + " *" + rel + self.name)


class Directory:
    @staticmethod
    def from_file(path):
        st = os.lstat(path)
        d = Directory(os.path.basename(path), st.st_mtime_ns, stat.S_IMODE(st.st_mode))
        d.path = path
        return d

    @staticmethod
    def from_xml(el):
        d = Directory(el.get('name'), int(el.get('mtime') or 0), int(el.get('mode') or 0))
        for e in el:
            if e.tag == 'directory':
                ee = Directory.from_xml(e)
                d.entries[ee.name] = ee
            elif e.tag == 'file':
                ee = File.from_xml(e)
                d.entries[ee.name] = ee
        return d

    def __init__(self, name=None, mtime=0, mode=509):
        self.path = None
        self.name = name
        self.mtime = mtime
        self.mode = mode
        self.entries = collections.OrderedDict()

    def to_xml(self):
        el = xml.ET.Element('directory')
        if self.name is not None:
            el.set('name', self.name)
        el.set('mtime', str(self.mtime))
        el.set('mode', str(self.mode))
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
            rel += '/'
        if self.name:
            rel += self.name
        for e in self.entries.values():
            e.print_sha1sum(rel)


class Collection:
    def __init__(self, path):
        self.path = path
        if self.path == '.':
            self.path_xml = os.path.join(self.path, 'filekeep.xml')
        else:
            self.path_xml = self.path + '.filekeep.xml'

        if os.path.isfile(self.path_xml):
            root = xml.read(self.path_xml)
            self.name = root.find('name').text
            self.directory = Directory.from_xml(root.find('directory'))
            self.exists = True
        else:
            self.name = os.path.abspath(self.path) if self.path == '.' else self.path
            st = os.lstat(path)
            self.directory = Directory(os.path.basename(path), st.st_mtime_ns, stat.S_IMODE(st.st_mode))
            self.exists = False

    def write_data(self):
        root = xml.ET.Element('collection')
        name = xml.ET.Element('name')
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

    def all_files(self):
        def func(d, path=''):
            if d.name is not None:
                path += d.name + '/'
            for entry in d.entries.values():
                if isinstance(entry, Directory):
                    for a, b in func(entry, path):
                        yield a, b
                else:
                    yield path + entry.name, entry
        return func(self.directory)

    def all_files_by_sha1(self):
        ret = {}
        for path, entry in self.all_files():
            if entry.sha1 in ret:
                ret[entry.sha1].append(path)
            else:
                ret[entry.sha1] = [path]
        return ret

    def find_duplicates(self):
        dups = {}
        for sha1, paths in self.all_files_by_sha1().items():
            if len(paths) > 1:
                dups[sha1] = paths
        return dups

    def print_sha1sum(self):
        self.directory.print_sha1sum('')
