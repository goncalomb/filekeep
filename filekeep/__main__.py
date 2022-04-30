import argparse
import os
import sys

from filekeep import utils
from filekeep.collection import Collection


def get_collection(args, ensure_exists=True):
    d = '.'
    if args.d:
        d = os.path.normpath(args.d)
        if os.path.dirname(d):
            print("directory '%s' invalid, must be a direct descendant of current path" %
                  d, file=sys.stdout)
            exit(1)
        elif not os.path.isdir(args.d):
            print("directory '%s' not found" % d, file=sys.stdout)
            exit(1)

    col = Collection(d)
    if ensure_exists:
        if not col.exists:
            print("collection not created")
            exit(1)
    elif col.exists:
        print("collection exists")
        exit(1)

    return col


def command_none(args):
    col = get_collection(args)
    print(col.name)
    s = col.size()
    print('{} ({} bytes)'.format(utils.format_size(s), s))


def command_create(args):
    col = get_collection(args, False)
    if args.name:
        col.set_name(args.name)
    if not args.quiet:
        print(col.name)
        print()
    (cd, cf) = col.create_from_path(args.quiet)
    col.write_data()
    if not args.quiet:
        print()
        print(str(cd) + " directories with " + str(cf) + " files")
        print("done")


def command_verify(args):
    col = get_collection(args)
    exit(0 if col.verify(args.fast, args.touch, args.flexible_mtime) else 1)


def command_duplicates(args):
    col = get_collection(args)
    for sha1, paths in col.find_duplicates().items():
        print(sha1)
        for path in paths:
            print('  ' + path)


def command_export(args):
    col = get_collection(args)
    if args.format == 'sha1sum':
        col.print_sha1sum()


def main():
    parser = argparse.ArgumentParser(prog='filekeep')
    parser.add_argument('-d', metavar='directory', help='directory to use')
    parser.set_defaults(fn=command_none)
    subparsers = parser.add_subparsers(title='commands', dest='command')

    parser_create = subparsers.add_parser(
        'create', description='create collection')
    parser_create.add_argument('--quiet', action="store_true")
    parser_create.add_argument('--name')
    parser_create.set_defaults(fn=command_create)

    parser_verify = subparsers.add_parser(
        'verify', description='verify collection')
    parser_verify.add_argument(
        '--fast', action="store_true", help='fast verify (skips checksum)')
    parser_verify.add_argument(
        '--touch', action="store_true", help='touch files (fix mtimes)')
    parser_verify.add_argument('--flexible-mtime', action="store_true",
                               help='ignore nanosecond precision when comparing mtimes')
    parser_verify.set_defaults(fn=command_verify)

    parser_duplicates = subparsers.add_parser(
        'duplicates', description='find duplicates')
    parser_duplicates.set_defaults(fn=command_duplicates)

    parser_export = subparsers.add_parser('export', description='export data')
    parser_export.add_argument(
        '--format', default='sha1sum', choices=['sha1sum'], help='export format')
    parser_export.set_defaults(fn=command_export)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\r\033[K", end="\r", file=sys.stderr)
        exit(1)
