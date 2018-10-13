import sys, os, argparse

from filekeep import utils
from filekeep.collection import Collection

def execute():
    parser = argparse.ArgumentParser(prog='filekeep')
    parser.add_argument('-d', metavar='directory', help='directory to use')
    subparsers = parser.add_subparsers(title='commands', dest='command')

    parser_create = subparsers.add_parser('create', description='create collection')
    parser_create.add_argument('--quiet', action="store_true")
    parser_create.add_argument('--name')

    parser_verify = subparsers.add_parser('verify', description='verify collection')
    parser_verify.add_argument('--fast', action="store_true", help='fast verify (skips checksum)')
    parser_verify.add_argument('--touch', action="store_true", help='touch files (fix mtimes)')
    parser_verify.add_argument('--flexible-mtime', action="store_true", help='ignore nanosecond precision when comparing mtimes')

    subparsers.add_parser('duplicates', description='find duplicates')

    parser_export = subparsers.add_parser('export', description='export data')
    parser_export.add_argument('--format', default='sha1sum', choices=['sha1sum'], help='export format')

    args = parser.parse_args()

    d = '.'
    if args.d:
        d = os.path.normpath(args.d)
        if os.path.dirname(d):
            print("directory '" + d + "' invalid, must be a direct descendant of current path", file=sys.stdout)
            exit(1)
        elif not os.path.isdir(args.d):
            print("directory '" + d + "' not found", file=sys.stdout)
            exit(1)

    col = Collection(d)

    if args.command == 'create':
        if col.exists:
            print("collection exists")
        else:
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
    elif args.command == 'verify' and col.exists:
        exit(0 if col.verify(args.fast, args.touch, args.flexible_mtime) else 1)
    elif args.command == 'duplicates' and col.exists:
        for sha1, paths in col.find_duplicates().items():
            print(sha1)
            for path in paths:
                print('  ' + path)
    elif args.command == 'export' and col.exists:
        if args.format == 'sha1sum':
            col.print_sha1sum()
    elif col.exists:
        print(col.name)
        s = col.size()
        print('{} ({} bytes)'.format(utils.format_size(s), s))
    else:
        print("collection not created")

if __name__ == "__main__":
    try:
        execute()
    except KeyboardInterrupt:
        print("\r\033[K", end="\r", file=sys.stderr)
        exit(1)
