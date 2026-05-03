#! /usr/bin/env python3

import inotify.adapters, inotify.constants as ic, os, signal, sys, logging
import data_repair, utils
#tmsu
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Watcher:
    def __init__(self):
        self.mask = ic.IN_DELETE_SELF | ic.IN_MOVE_SELF | ic.IN_UNMOUNT | ic.IN_DELETE | ic.IN_MOVED_FROM | ic.IN_MOVED_TO
        self.watches = utils.get_watches()
        print(self.watches)
    
    def refresh_watch_list(self):
        self.watches = utils.get_watches()

    def run(self):

        i = inotify.adapters.InotifyTrees(self.watches, self.mask)

        def watch_change_handler(signum, frame):
            print("\nCAUGHT WATCH CHANGE\n")
            self.refresh_watch_list()
            i._load_trees(self.watches)
        signal.signal(signal.SIGUSR1, watch_change_handler)

        def cookie_ttl(signum, frame):
            #print("alarm works")
            c = cookies.pop(0)
            #print("cookie {} expired".format(c))
            if cookies: signal.alarm(1)
            data_repair.in_moved_outside_watched_region(c[1][1], os.path.join(c[1][2], c[1][3]))
        signal.signal(signal.SIGALRM, cookie_ttl)

        cookies = []
        for event in i.event_gen(yield_nones=False):
            if not event: 
                continue
            (e, types, part_path, filename) = event
            path = os.path.join(part_path, filename)
            if utils.home()+"/databases" in path:
                continue
            print(path, filename, types)
            match (types[0]):
                case 'IN_DELETE_SELF' | 'IN_MOVE_SELF':
                    if path in self.watches:
                        utils.sleep_watch(path)
                        self.refresh_watch_list()
                        os.kill(os.getpid(), signal.SIGUSR1)
                case 'IN_UNMOUNT':
                    data_repair.in_umount(types, path)
                case 'IN_DELETE':
                    data_repair.in_delete(types,path)
                case 'IN_MOVED_FROM':
                    if e.cookie != 0: 
                        cookies.append((e.cookie, event))
                        signal.alarm(1)
                case 'IN_MOVED_TO':
                    for c in range(len(cookies)):
                        if cookies[c][0] == e.cookie:
                            signal.alarm(0)
                            preceding_event = cookies.pop(c)[1]
                            _, _, prev_path, prev_filename = preceding_event
                            data_repair.in_moved_within_watched_region(types, os.path.join(prev_path, prev_filename), path)        

def _main(*args):
    try:
        w = Watcher()
        w.run()
    except Exception as e:
        os.system(f"notify-send 'SemoFS daemon crashed: {str(e)}'")
        sys.exit(1)

if __name__ == '__main__':
    _main()
