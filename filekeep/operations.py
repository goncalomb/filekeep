import os
import stat

from .collection import Collection, Directory, File
from .logger import logger_create
from .utils import compare_times, sha1_file


def op_verify(c: Collection, fast=False, touch=False, flexible_times=False):
    logger = logger_create(c.size())
    paths_to_touch = []

    # directory entries referenced by relative path
    dirs = {
        c.path: c.directory
    }

    # function return value
    result = True

    for dirpath, dirnames, filenames in os.walk(c.path):
        if dirpath not in dirs:
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
                logger.error("extra directory '" + path + "'")
                found_error = True

        # process files
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if filename in entries and isinstance(entries[filename], File):
                st = os.lstat(path)
                needs_touch = False

                if not compare_times(entries[filename].mtime, st.st_mtime_ns, flexible_times):
                    logger.error("'" + path + "' different mtime")
                    if touch:
                        needs_touch = True
                    else:
                        found_error = True
                if entries[filename].mode != 0 and entries[filename].mode != stat.S_IMODE(st.st_mode):
                    logger.error("'{}' different mode ({} != {})".format(
                        path, str(stat.S_IMODE(st.st_mode)), str(entries[filename].mode)))
                    if touch:
                        needs_touch = True
                    else:
                        found_error = True

                if entries[filename].size != st.st_size:
                    logger.error("'" + path + "' different size")
                    logger.progress(entries[filename].size)
                    found_error = True
                elif (not fast or needs_touch) and entries[filename].sha1 != sha1_file(path, logger):
                    logger.error("'" + path + "' different sha1")
                    found_error = True
                elif needs_touch:
                    paths_to_touch.append((path, entries[filename]))
                elif fast:
                    logger.progress(entries[filename].size)

                del entries[filename]

            elif path != './filekeep.xml':
                logger.error("extra file '" + path + "'")
                found_error = True

        # handle missing entries
        for e in entries.values():
            found_error = True
            path = os.path.join(dirpath, e.name)
            if isinstance(e, Directory):
                logger.error("missing directory '" + path + "'")
                logger.progress(e.size())
            else:
                logger.error("missing file '" + path + "'")
                logger.progress(e.size)

        # process directory
        if dirpath != '.':
            st = os.lstat(dirpath)
            if not compare_times(d.mtime, st.st_mtime_ns, flexible_times):
                logger.error("'" + dirpath + "' (directory) different mtime")
                if touch and not found_error:
                    paths_to_touch.append((dirpath, d))
                else:
                    result = False
            if d.mode != 0 and d.mode != stat.S_IMODE(st.st_mode):
                logger.error("'{}' (directory) different mode ({} != {})".format(
                    dirpath, str(stat.S_IMODE(st.st_mode)), str(d.mode)))
                if touch and not found_error:
                    paths_to_touch.append((dirpath, d))
                else:
                    result = False

        if found_error:
            result = False

    if touch:
        if paths_to_touch:
            logger.print("touching")
            for (path, entry) in paths_to_touch:
                os.utime(path, ns=(entry.mtime, entry.mtime))
                if entry.mode != 0:
                    os.chmod(path, entry.mode)
        else:
            logger.print("nothing to touch")

    return result
