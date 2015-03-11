
import os.path


is_dir = os.path.isdir
is_file = os.path.isfile
exists = os.path.exists

def is_empty(path):
    return os.path.getsize(path) == 0
