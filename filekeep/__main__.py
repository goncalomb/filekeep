import os, sys

from filekeep.collection import Collection

def execute():
    col = Collection(os.getcwd())
    if col.exists:
        if len(sys.argv) == 2 and sys.argv[1] == "dump":
            col.print_sha1sum()
        else:
            print("collection exists")
            print(str(col.size()) + " bytes")
            print("use 'filekeep dump' to print in sha1sum format")
    else:
        print("creating collection")
        col.create_from_path()
        col.write_data()
        print("done")

if __name__ == "__main__":
    execute()
