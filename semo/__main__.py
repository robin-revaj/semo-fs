#! /usr/bin/env python3

import argparse
import interface as cli

def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help="Interface to interact with and manage semo data and tags")

    tag_parser = subparsers.add_parser("tag", help="Function assigns given tag (optionally with given value) to given filepath. Format: tag [tag_name] [value] [filename]")
    tag_parser.add_argument("tagname", help="Name of existing or new tag")
    tag_parser.add_argument("value", nargs='?', default=None, help="Optional string or integer value")
    tag_parser.add_argument("filename", help="Absolute or relative path to file")
    tag_parser.set_defaults(func=cli.translate_TAG)

    untag_parser = subparsers.add_parser("utag", help="Function removes given tag from given filepath. Format: untag [tag_name] [filename]")
    untag_parser.add_argument("tagname", help="Name of tag")
    untag_parser.add_argument("filename", help="Absolute or relative path to file")
    untag_parser.set_defaults(func=cli.translate_UNTAG)

    list_tags_parser = subparsers.add_parser("ls_tags", help="Lists all tags and their values associated with the given filename. If no file is provided, lists all tags.")
    list_tags_parser.add_argument("filename", nargs='?', default="", help="Optional absolute or relative path to file")
    list_tags_parser.set_defaults(func=cli.translate_LISTTAGS)

    list_roots_parser = subparsers.add_parser("ls_roots", help="Lists root tags. A root tag is a tag that is not a subtag to any other tags.")
    list_roots_parser.set_defaults(func=cli.translate_LISTROOTS)

    list_subtags_parser = subparsers.add_parser("ls_subtags", help="Lists subtags for given tag.")
    list_subtags_parser.add_argument("-d", "--direct", action=argparse._StoreTrueAction)
    list_subtags_parser.add_argument("tagname", help="Name of tag")
    list_subtags_parser.set_defaults(func=cli.translate_LISTSUBTAGS)

    list_files_parser = subparsers.add_parser("ls_files", help="Lists files that correspond to query conditions. If no query is provided, lists all files in database.")
    list_files_parser.add_argument("query", nargs='*', default="", help="Space separated. Acceptable query format: \n\
                                   [tagname], \n\
                                   [tagname] == [value] (for str and int valued tags), \n\
                                   [tagname] [> < >= <=] [value] (for int valued tags), \n\
                                   Set Operations: Processed from left to right unless specified otherwise by parentheses \n\
                                   OR:    [tag1] [| +] [tag2] \n\
                                   AND:   [tag1] [& *] [tag2] \n\
                                   MINUS (ANDNOT):    [tag1] [/ -] [tag2]")
    #list_files_parser.add_argument("-l", "--long", action="store_true", help="display long format")
    list_files_parser.set_defaults(func=cli.translate_LISTFILES)

    delete_tag_parser = subparsers.add_parser("deltag", help="Deletes tag and all its relationships")
    delete_tag_parser.add_argument("tagname", help="Name of tag")
    delete_tag_parser.set_defaults(func=cli.translate_DELTAG)

    subtag_parser = subparsers.add_parser("subtag", help="Assigns subtags to superior tag")
    subtag_parser.add_argument("superior_tag", help="Name of tag")
    subtag_parser.add_argument("inferior_tag", nargs='*', default=[], help="Space separated list of tags to assign as inferiors")
    subtag_parser.set_defaults(func=cli.translate_SUBTAG)

    usubtag_parser = subparsers.add_parser("usubtag", help="Unassigns subtags from superior tag")
    usubtag_parser.add_argument("superior_tag", help="Name of tag")
    usubtag_parser.add_argument("inferior_tag", nargs='*', default=[], help="Space separated list of tags to remove as inferiors")
    usubtag_parser.set_defaults(func=cli.translate_UNSUBTAG)

    select_database_parser = subparsers.add_parser("db", help="Selects database file to use")
    select_database_parser.add_argument("database_path", nargs='?', default="", help="Absolute or relative path to file")
    select_database_parser.set_defaults(func=cli.translate_SELECTDB)

    watch_parser = subparsers.add_parser("watch", help="Adds directory to watchlist. Watchlist is used to catch file changes and update tags accordingly.")
    watch_parser.add_argument("path", nargs='?', default="", help="Absolute or relative path to directory")
    watch_parser.set_defaults(func=cli.translate_WATCH)

    unwatch_parser = subparsers.add_parser("uwatch", help="Removes directory from watchlist. Watchlist is used to catch file changes and update tags accordingly.")
    unwatch_parser.add_argument("path", nargs='?', default="", help="Absolute or relative path to directory")
    unwatch_parser.set_defaults(func=cli.translate_UNWATCH)

    list_watches_parser = subparsers.add_parser("ls_watches", help="List the current watch tree roots.")
    list_watches_parser.set_defaults(func=cli.translate_LISTWATCHES)

    mount_parser = subparsers.add_parser("mount", help="Mounts the semo FUSE filesystem at provided mountpoint.")
    mount_parser.add_argument("path", nargs='?', default="", help="Optional absolute or relative path to directory, if not provided the default mountpoint will be used.")
    mount_parser.add_argument("-d", "--debug", action="store_true", help="Mount in fuse debug mode")
    mount_parser.set_defaults(func=cli.translate_MOUNT)

    umount_parser = subparsers.add_parser("umount", help="Unmounts the semo FUSE filesystem from mountpoint.")
    umount_parser.add_argument("path", nargs='?', default="", help="Optional absolute or relative path to directory, if not provided the default mountpoint will be used.")
    umount_parser.set_defaults(func=cli.translate_UMOUNT)

    clean_parser = subparsers.add_parser("clean", help="Clears the database of damaged or outdated entries.")
    clean_parser.set_defaults(func=cli.translate_CLEAN)

    export_parser = subparsers.add_parser("export", help="Exports tag data for given directory to the files' extended attributes.")
    export_parser.add_argument("path", help="Absolute or relative path to directory.")
    export_parser.set_defaults(func=cli.translate_EXPORT)


    import_parser = subparsers.add_parser("import", help="Attempts to import tag data in given directory from the available options. Option sets [-a], [-x], [-fi], [-mfi], [-mf] guarantee full recovery. For other combinations (eg. [-m]) only partial recovery may be possible.")
    import_parser.add_argument("path", help="Absolute or relative path to file")
    import_parser.add_argument("-a", "--guarantee_abspath", action="store_true", help="The absolute paths of the directory and its contents have not changed while not being watched")
    import_parser.add_argument("-m", "--guarantee_mountpath", action="store_true", help="The given directory is the mountpoint of its filesystem and the paths of its contents have not changed while not being watched")
    import_parser.add_argument("-f", "--guarantee_fsid", action="store_true", help="The given directory has not changed filesystems while not being watched")
    import_parser.add_argument("-i", "--guarantee_inodes", action="store_true", help="The filesystem of given directory supports inodes and therefore they weren't regenerated while not being watched")
    import_parser.add_argument("-x", "--guarantee_xattr", action="store_true", help="Tag data for directory was exported into xattr before being removed from watchlist")
    import_parser.set_defaults(func=cli.translate_IMPORT)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()