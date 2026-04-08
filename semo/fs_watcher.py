import inotify.adapters

def _main():
    i = inotify.adapters.InotifyTree("test/data")

    with open('test/data/test_file', 'w'):
        pass

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event

        print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, type_names))
if __name__ == '__main__':
    _main()
