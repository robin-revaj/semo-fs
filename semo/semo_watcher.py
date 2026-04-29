#!/usr/bin/env python3

import inotify.adapters, inotify.constants as ic, os, signal, time
from semo import data_repair, utils

#tmsu

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
            self.refresh_watch_list()
            i._load_trees(self.watches)
        signal.signal(signal.SIGUSR1, watch_change_handler)

        def cookie_ttl(signum, frame):
            print("alarm works")
            c = cookies.pop(0)
            print("cookie {} expired".format(c))
            if cookies: signal.alarm(1)
        signal.signal(signal.SIGALRM, cookie_ttl)

        cookies = []
        for event in i.event_gen(yield_nones=False):
            if not event: 
                continue
            
            (e, types, path, filename) = event
            print(path, filename, types)
            match (types[0]):
                case 'IN_DELETE_SELF' | 'IN_MOVE_SELF':
                    if os.path.join(path, filename) in self.watches:
                        utils.sleep_watch(os.path.join(path, filename))
                        self.refresh_watch_list()
                        os.kill(os.getpid(), signal.SIGUSR1)
                    data_repair.in_delete(types, path, filename)
                case 'IN_UNMOUNT':
                    data_repair.in_umount(types, path, filename)
                case 'IN_DELETE':
                    data_repair.in_delete(types,path, filename)
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
                            data_repair.in_moved_within_watched_region(types, path, filename)        

def _main(*args):
    w = Watcher()
    w.run()

if __name__ == '__main__':
    _main()
