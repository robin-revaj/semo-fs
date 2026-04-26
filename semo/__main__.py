#!.venv/bin/python3

import argparse
from . import interface as cli, fs_watcher

def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help="Welcome to the help page")

    tag_parser = subparsers.add_parser("tag", help="assign to tag [tagname] file [filename], optionally with value [value]")
    tag_parser.add_argument("tagname")
    tag_parser.add_argument("filename")
    tag_parser.add_argument("value", nargs='?', default=None)
    tag_parser.set_defaults(func=cli.interface_translate_TAG)

    untag_parser = subparsers.add_parser("untag", help="remove tag [tagname] from file [filename] ")
    untag_parser.add_argument("tagname")
    untag_parser.add_argument("filename")
    untag_parser.set_defaults(func=cli.interface_translate_UNTAG)

    

    list_tags_parser = subparsers.add_parser("ls_tags", help="list all tags or list tags for given [filename]")
    list_tags_parser.add_argument("-f", "--filename", nargs='?', default="")
    list_tags_parser.set_defaults(func=cli.interface_translate_LISTTAGS)

    list_roots_parser = subparsers.add_parser("ls_roots", help="list root tags")
    list_roots_parser.set_defaults(func=cli.translate_LISTROOTS)

    list_subtags_parser = subparsers.add_parser("ls_subtags", help="list subtags for tag [tagname]")
    list_subtags_parser.add_argument("-d", "--direct", action=argparse._StoreTrueAction)
    list_subtags_parser.add_argument("tagname")
    list_subtags_parser.set_defaults(func=cli.interface_translate_LISTSUBTAGS)

    list_files_parser = subparsers.add_parser("ls_files", help="list all files or list files for given tags")
    list_files_parser.add_argument("-q", "--query", nargs='?', default="")
    list_files_parser.add_argument("-l", "--long", action="store_true", help="display long format")
    list_files_parser.set_defaults(func=cli.interface_translate_LISTFILES)

    delete_tag_parser = subparsers.add_parser("del_tag", help="delete tag [tagname] from all files")
    delete_tag_parser.add_argument("tagname")
    delete_tag_parser.set_defaults(func=cli.interface_translate_DELTAG)

    subtag_parser = subparsers.add_parser("subtag", help="Assign or deassign subtags to/from superior tag")
    subtag_parser.add_argument("superior_tag")
    subtag_parser.add_argument("-u", "--unassign", action=argparse._StoreTrueAction)
    subtag_parser.add_argument("inferior_tag", nargs='*', default=[])
    subtag_parser.set_defaults(func=cli.interface_translate_SUBTAG)

    select_database_parser = subparsers.add_parser("db", help="Select database file to use")
    select_database_parser.add_argument("database_path", nargs='?', default="")
    select_database_parser.set_defaults(func=cli.interface_command_SELECTDB)

    watcher_parser = subparsers.add_parser("watch", help="Watch a file or directory for changes and update tags accordingly")
    #watcher_parser.add_argument("path", nargs='?', default="")
    watcher_parser.set_defaults(func=fs_watcher._main)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()