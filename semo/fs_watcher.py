import inotify.adapters, os
import data_repair

def _main():
    i = inotify.adapters.InotifyTree("test/data")

    cookies = {}
    for event in i.event_gen(yield_nones=False):
        (e, type_name, path, filename) = event
                
        match (type_name):
            case "IN_DELETE_SELF":
                # delete corresponding paths
                break
            case "IN_MOVE_SELF":
                paths = os.scandir(path)
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
                break
            case "IN_MOVED_TO":
                if e.cookie in cookies:
                    preceding_event = cookies.pop(e.cookie)
                    _, _, prev_path, prev_filename = preceding_event
                    new_path = path + filename
                    old_path = prev_path + prev_filename
                    data_repair.fix_path_from_path(old_path, new_path)
                break

        print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, type_name))
if __name__ == '__main__':
    _main()
