#!/usr/bin/python2
###############################################################################
# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
# -*- coding: utf-8 -*-
#

"""
Exception definitions for xCAT inventory import/export
"""
import sys
import traceback

class BaseException(Exception):
    """Base Command Exception."""

    message = "An unknown error occurred."

    def __init__(self, message=None, **kwargs):
        if message:
            self.message = message
        try:
            self._error_msg = self.message % kwargs
        except Exception:
            self._error_msg = self.message

    def __str__(self):
        return self._error_msg

class ObjTypeNonExistException(BaseException):
    pass
class ObjNonExistException(BaseException):
    pass
class CommandException(BaseException):
    pass
class FileNotExistException(BaseException):
    pass
class InvalidFileException(BaseException):
    pass
class InternalException(BaseException):
    pass
class InvalidValueException(BaseException):
    pass
class BadDBHdlException(BaseException):
    pass
class BadSchemaException(BaseException):
    pass
class DBException(BaseException):
    pass
class ParseException(BaseException):
    pass
class BackendNotInitException(BaseException):
    pass
class ShErrorReturnException(BaseException):
    pass
class DirNotExistException(BaseException):
    pass
