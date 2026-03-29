#!/usr/bin/env python3

class NecessaryUpstreamInterrupt(Exception):
    pass

class ValidationError(Exception):
    pass

class FileNotInDatabaseError(Exception):
    pass

class TagNotInDatabaseError(Exception):
    pass

class RelationshipExistsError(Exception):
    pass

class RelationshipDoesntExistError(Exception):
    pass

class OperationCancelledError(Exception):
    pass