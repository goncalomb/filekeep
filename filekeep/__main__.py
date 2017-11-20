import argparse

from filekeep.collection import Collection

def execute():
    parser = argparse.ArgumentParser(prog='filekeep')
    subparsers = parser.add_subparsers(title='commands', dest='command')

    parser_create = subparsers.add_parser('create', description='create collection')
    parser_create.add_argument('--quiet', action="store_true")
    parser_create.add_argument('--name')

    parser_verify = subparsers.add_parser('verify', description='verify collection')
    parser_verify.add_argument('--ignore-mtime', action="store_true", help='don\'t compare mtimes')
    parser_verify.add_argument('--flexible-mtime', action="store_true", help='ignore nanosecond precision when comparing mtimes')

    parser_touch = subparsers.add_parser('touch', description='touch collection (fix mtimes)')
    parser_touch.add_argument('--flexible-mtime', action="store_true", help='ignore nanosecond precision when comparing mtimes')

    parser_export = subparsers.add_parser('export', description='export data')
    parser_export.add_argument('--format', default='sha1sum', choices=['sha1sum'], help='export format')

    args = parser.parse_args()

    col = Collection(".")

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
        exit(0 if col.verify_and_touch(flexible_times=args.flexible_mtime, ignore_times=args.ignore_mtime) else 1)
    elif args.command == 'touch' and col.exists:
        exit(0 if col.verify_and_touch(True, args.flexible_mtime) else 1)
    elif args.command == 'export' and col.exists:
        if args.format == 'sha1sum':
            col.print_sha1sum()
    elif col.exists:
        print(col.name)
        print(str(col.size()) + " bytes")
    else:
        print("collection not created")

if __name__ == "__main__":
    execute()
