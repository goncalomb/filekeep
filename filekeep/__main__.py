import os

from filekeep.collection import Collection

def execute():
    col = Collection(os.getcwd())
    if col.exists:
        print("collection exists")
        print(str(col.size()) + " bytes")
    else:
        print("creating collection")
        col.create_from_path()
        col.write_data()
        print("done")

if __name__ == "__main__":
    execute()
