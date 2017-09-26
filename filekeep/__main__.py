import os
import argparse

from filekeep.collection import Collection

def execute():
    parser = argparse.ArgumentParser(prog='filekeep')
    subparsers = parser.add_subparsers(title='commands', dest='command')

    parser_create = subparsers.add_parser('create', description='create collection')
    parser_export = subparsers.add_parser('export', description='export data')
    parser_export.add_argument('--format', default='sha1sum', choices=['sha1sum'], help='export format')

    args = parser.parse_args()

    col = Collection(os.getcwd())

    if args.command == 'create':
        if col.exists:
            print("collection exists")
        else:
            print("creating collection")
            col.create_from_path()
            col.write_data()
            print("done")
    elif args.command == 'export' and col.exists:
        if args.format == 'sha1sum':
            col.print_sha1sum()
    elif col.exists:
        print("collection exists")
        print(str(col.size()) + " bytes")
    else:
        print("collection not created")

if __name__ == "__main__":
    execute()
