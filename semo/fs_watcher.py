import inotify.adapters, os
from . import data_repair

#tmsu

def _main(*args):
    i = inotify.adapters.InotifyTree(os.path.abspath("test/data"))

    cookies = {}
    for event in i.event_gen(yield_nones=False):
        if not event: 
            continue

        (e, types, path, filename) = event
        
        for event_type in types:
            match (event_type):
                case "IN_DELETE_SELF":
                    # delete corresponding paths
                    break
                case "IN_MOVE_SELF":
                    paths = os.scandir(path)
                    for newpath in paths:
                        data_repair.fix_path_from_path("", str(newpath))
                    # update all paths
                    break
                case "IN_UMOUNT":
                    break
                case "IN_DELETE":
                    # delete db entry
                    break
                case "IN_MOVED_FROM":
                    if e.cookie != 0: 
                        cookies[e.cookie] = event
                            
                    # mark cookie, ttl and wait
                    print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, types))
                    break
                case "IN_MOVED_TO":
                    if e.cookie in cookies:
                        preceding_event = cookies.pop(e.cookie)
                        _, _, prev_path, prev_filename = preceding_event
                        new_path = os.path.join(path, filename)
                        old_path = os.path.join(prev_path, prev_filename)
                        # print(data_repair.fix_path_from_path(old_path, new_path))
                        print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, types))
                    break

if __name__ == '__main__':
    _main()
