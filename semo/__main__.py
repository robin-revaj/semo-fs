#!/usr/bin/env python3

import argparse
import interface as cli

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

    list_tags_parser = subparsers.add_parser("tags", help="list all tags or list tags for given [filename]")
    list_tags_parser.add_argument("filename", nargs='?')
    list_tags_parser.set_defaults(func=cli.interface_translate_LISTTAGS)

    delete_tag_parser = subparsers.add_parser("del", help="delete tag [tagname] from all files")
    delete_tag_parser.add_argument("tagname")
    delete_tag_parser.set_defaults(func=cli.interface_translate_DELTAG)

    subtag_parser = subparsers.add_parser("subtag", help="Manage subtags for root tag")
    subtag_parser.add_argument("superior_tag")
    subtag_parser.add_argument("-u", "--unassign", action=argparse._StoreTrueAction)
    subtag_parser.add_argument("inferior_tag", nargs='*', default=[])
    subtag_parser.set_defaults(func=cli.interface_translate_SUBTAG)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()