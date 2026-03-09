#!/usr/bin/env python3

import argparse
from . import interface as cli

# TODO refactor to use a config file for settings
# TODO add logging
# TODO rewrite interface for changes in backend
# TODO handle missing database file


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help="subcommand help")

    tag_parser = subparsers.add_parser("tag", help="assign to file [filename] tag [tagname]")
    tag_parser.add_argument("filename")
    tag_parser.add_argument("tagname")
    tag_parser.set_defaults(func=cli.interface_translate_TAG)

    untag_parser = subparsers.add_parser("untag", help="remove from file [filename] tag [tagname]")
    untag_parser.add_argument("filename")
    untag_parser.add_argument("tagname")
    untag_parser.set_defaults(func=cli.interface_translate_UNTAG)

    list_tags_parser = subparsers.add_parser("list_tags", help="list all tags or list tags for given [filename]")
    list_tags_parser.add_argument("-f", "--filename", nargs='?', default="")
    list_tags_parser.set_defaults(func=cli.interface_translate_LISTTAGS)

    list_files_parser = subparsers.add_parser("list_files", help="list all files or list files for given tags")
    list_files_parser.add_argument("-q", "--query", nargs='+')
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

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()