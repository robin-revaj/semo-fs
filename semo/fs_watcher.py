import inotify.adapters
from . import settings

def main():
    i = inotify.adapters.InotifyTree("test/data")

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event

        print(f"PATH=[{path}] FILENAME=[{filename}] EVENT_TYPES={type_names}")

        

