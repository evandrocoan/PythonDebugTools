#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

####################### Licensing #######################################################
#
# Debug Tools, Logging utilities
# Copyright (C) 2017 Evandro Coan <https://github.com/evandrocoan>
#
#   Originally written on:
#   https://github.com/evandrocoan/SublimeAMXX_Editor/blob/888c6822047d84e2370348b6cf5f4ac509f77b32/AMXXEditor.py#L1741-L1804
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################################
#

import os
import io
import sys
import copy

import timeit
import datetime
import platform

import logging
import logging.handlers

from logging import Logger
from logging import Manager
from logging import PlaceHolder
from logging import StreamHandler

from logging import DEBUG
from logging import WARNING
from logging import ERROR

from logging import _srcfile
from logging import getLevelName

from concurrent_log_handler import ConcurrentRotatingFileHandler


is_python2 = False
EMPTY_KWARG = -sys.maxsize

if sys.version_info[0] < 3:
    is_python2 = True


if hasattr(sys, '_getframe'):
    currentframe = lambda level: sys._getframe(level)

else: #pragma: no cover
    def currentframe(level):
        """Return the frame object for the caller's stack frame."""
        try:
            raise Exception
        except Exception:
            return sys.exc_info()[level-1].tb_frame.f_back


class Debugger(Logger):
    """
        https://docs.python.org/2.6/library/logging.html

        How to define global function in Python?
        https://stackoverflow.com/questions/27930038/how-to-define-global-function-in-python

        How to print list inside python print?
        https://stackoverflow.com/questions/45427500/how-to-print-list-inside-python-print
    """
    logger = None

    def __init__(self, logger_name, logger_level=None):
        """
            What is a clean, pythonic way to have multiple constructors in Python?
            https://stackoverflow.com/questions/682504/what-is-a-clean-pythonic-way-to-have-multiple-constructors-in-python

            @param `logger_name` the name of this logger accordingly with the standard logging.Logger() documentation.
            @param `logger_level` an integer with the current bitwise enabled log level
        """
        super( Debugger, self ).__init__( logger_name, logger_level or "DEBUG" )

        # Initialize the first last tick as the current tick
        self.lastTick = timeit.default_timer()

        self.file_handler = None
        self.stream_handler = None

        self.reset()
        self._setup_find_caller()

        # Enable debug messages: (bitwise)
        # 0 - Disabled debugging
        # 1 - Errors messages
        self._stderr = None
        self._frame_level = 4
        self._debug_level = 127

    @property
    def output_file(self):

        if self.file_handler:
            return self.file_handler.baseFilename

        return None

    @property
    def debug_level(self):
        return self._debug_level

    @debug_level.setter
    def debug_level(self, value):

        if isinstance( value, int ):
            self._debug_level = value

        else:
            raise ValueError( "Error: The debug_level `%s` must be an integer!" % debug_level )

    def __call__(self, debug_level, msg, *args, **kwargs):
        """
            Log to the current active handlers its message based on the bitwise `self._debug_level`
            value. Note, differently from the standard logging level, each logger object has its own
            bitwise logging level, instead of all sharing the main `level`.
        """

        if self._debug_level & debug_level != 0:
            kwargs['debug_level'] = debug_level
            self._log( DEBUG, msg, args, **kwargs )

    def reset(self):
        """
            Reset all remembered parameters values set on the subsequent calls to `setup()`.

            Call this if you want to reset to remove all handlers and set all parameters values to
            their default.
        """
        self._arguments = self._formatter_arguments()
        self.removeHandlers()

        self.full_formatter = self._setup_formatter( self._arguments )
        self.clean_formatter = logging.Formatter( "", "" )
        self.setup_basic( function=False, tick=False )

    def setup_basic(self, **kwargs):
        """
            Configure the `basic_formatter` used by `Debugger.basic` logging function.

            @param `**kwargs` the same formatting arguments passed to `Debugger.setup`
        """
        basic_arguments = self._formatter_arguments()
        basic_arguments.update( kwargs )
        self.basic_formatter = self._setup_formatter( basic_arguments )

    def _formatter_arguments(self):
        return \
        {
            "file": None,
            "mode": 'a',
            "delete": True,
            "date": False,
            "level": False,
            "function": True,
            "name": True,
            "time": True,
            "tick": True,
            "separator": True,
            "formatter": None,
            "rotation": 0,
            "msecs": True,
        }

    def active(self):
        """
            Works accordingly with super::hasHandlers(), except that this returns the activate
            logger object if it has some activate handler, or None if there are not loggers with
            active handlers.

            The root logger is not returned, unless it is already setup with handlers.
        """
        current = self

        while current:

            if current.handlers:
                return current

            if not current.propagate:
                break

            else:
                current = current.parent

        return None

    def newline(self, level=1, count=1):
        """
            Prints a clean new line, without any formatter header.
        """
        self.clean( level, "" )

    def new_line(self, level=1, count=1):
        """
            Prints a clean new line, without any formatter header.
        """
        self.clean( level, "" )

    def clean(self, debug_level, msg, *args, **kwargs):
        """
            Prints a message without the time prefix as `[plugin_name.py] 11:13:51:0582059`

            How to insert newline in python logging?
            https://stackoverflow.com/questions/20111758/how-to-insert-newline-in-python-logging
        """

        if self._debug_level & debug_level != 0:
            file_handler = self.file_handler
            stream_handler = self.stream_handler

            if stream_handler:
                stream_handler_formatter = stream_handler.formatter
                stream_handler.formatter = self.clean_formatter

            if file_handler:
                file_handler_formatter = file_handler.formatter
                file_handler.formatter = self.clean_formatter

            kwargs['debug_level'] = debug_level
            self._log_clean( msg % args )

            if self.stream_handler:
                stream_handler.formatter = stream_handler_formatter

            if self.file_handler:
                file_handler.formatter = file_handler_formatter

    def basic(self, debug_level, msg, *args, **kwargs):
        """
            Prints the bitwise logging message with the standard basic formatter, which uses by
            default the format: [%(name)s] %(asctime)s:%(msecs)010.6f %(tickDifference).2e %(message)s

            The basic logger format can be configured setting the standard formatter with
            setup() and calling invert() to set the `full_formatter` as
            the basic formatter.
        """

        if self._debug_level & debug_level != 0:
            file_handler = self.file_handler
            stream_handler = self.stream_handler

            if stream_handler:
                stream_handler_formatter = stream_handler.formatter
                stream_handler.formatter = self.basic_formatter

            if file_handler:
                file_handler_formatter = file_handler.formatter
                file_handler.formatter = self.basic_formatter

            kwargs['debug_level'] = debug_level
            self._log( DEBUG, msg, args, **kwargs )

            if self.stream_handler:
                stream_handler.formatter = stream_handler_formatter

            if self.file_handler:
                file_handler.formatter = file_handler_formatter

    def clear(self, delete=False):
        """
            Clear the log file contents.

            @param `delete` if True, the log file will also be removed/deleted and the current file
                handler will be removed.
        """
        active = self.active()

        if active and active.output_file:
            output_file = active.output_file

            sys.stderr.write( "Cleaning (delete=%s) the file: %s\n" % ( delete, output_file ) )
            active._create_file_handler( output_file, active._arguments['rotation'], active._arguments['mode'], True, delete )

    def invert(self):
        """
            Inverts the default formatter between the preconfigured `basic` and `full_formatter`.
        """
        self.basic_formatter, self.full_formatter = self.full_formatter, self.basic_formatter

    def handle_strerr(self, enable=True):
        """
            Register a exception hook if the logger is capable of logging then to alternate streams.
        """

        if enable:
            self._stderr = TeeNoFile.lock( self )

        else:
            self._stderr = TeeNoFile.unlock()

    def disable(self, stream=False, file=False):
        """
            Delete all automatically setup handlers created by the automatic `setup()`.
        """

        if stream \
                and self.stream_handler:

            self.removeHandler( self.stream_handler )
            self.stream_handler = None

        if file:
            self.handle_strerr( False )

            if self.file_handler:
                self.removeHandler( self.file_handler )
                self.file_handler.close()
                self.file_handler = None

    def setup(self, file=EMPTY_KWARG, mode=EMPTY_KWARG, delete=EMPTY_KWARG, date=EMPTY_KWARG, level=EMPTY_KWARG,
            function=EMPTY_KWARG, name=EMPTY_KWARG, time=EMPTY_KWARG, msecs=EMPTY_KWARG, tick=EMPTY_KWARG,
            separator=EMPTY_KWARG, formatter=EMPTY_KWARG, rotation=EMPTY_KWARG, **kwargs):
        """
            If `file` parameter is passed, instead of output the debug to the standard output
            stream, send it a file on the file system, which is faster for large outputs.

            As this function remembers its parameters passed from previous calls, you need to
            explicitly pass `file=None` with `delete=True` if you want to disable the file
            system output after setting up it to log to a file. See the function Debugger::reset()
            for the default parameters values used on this setup utility.

            If the parameters `date`, `level`, `function`, `name`, `time`, `tick` and `msecs` are
            strings nonempty, their value will be used to defining their configuration formatting.
            For example, if you pass name="%(name)s: " the function name will be displayed as
            `name: `, instead of the default `[name] `.

            If you change your `sys.stderr` after creating an StreamHandler, you need to pass `force=True`
            to make it to recreate the StreamHandler because of the old reference to `sys.stderr`.

            Single page cheat-sheet about Python string formatting pyformat.info
            https://github.com/ulope/pyformat.info

            Override a method at instance level
            https://stackoverflow.com/questions/394770/override-a-method-at-instance-level

            @param `file`  a relative or absolute path to the log file. If empty the output
                                will be sent to the standard output stream.

            @param `mode`       the file write mode on the file system. It can be `a` to append to the
                                existent file, or `w` to erase the existent file before start. If the
                                parameter `rotation` is set to non zero, then this will be an integer value
                                setting how many backups are going to be keep when doing the file rotation as
                                specified on logging::handlers::RotatingFileHandler documentation.

            @param `delete`     if True, it will delete the other handler before activate the
                                current one, otherwise it will only activate the selected handler.
                                Useful for enabling multiple handlers simultaneously.

            @param `date`       if True, add to the `full_formatter` the date on the format `%Y-%m-%d`.
            @param `level`      if True, add to the `full_formatter` the log levels.
            @param `function`   if True, add to the `full_formatter` the function name.
            @param `name`       if True, add to the `full_formatter` the logger name.
            @param `time`       if True, add to the `full_formatter` the time on the format `%H:%M:%S:microseconds`.
            @param `msecs`      if True, add to the `full_formatter` the current milliseconds on the format ddd,ddddd.
            @param `tick`       if True, add to the `full_formatter` the time.perf_counter() difference from the last call.
            @param `separator`  if True, add to the `full_formatter` the a ` - ` to the end of the log record header.
            @param `formatter`  if not None, replace this `full_formatter` by the logging.Formatter() provided.

            @param `rotation`   if non zero, creates a RotatingFileHandler with the specified size
                                in Mega Bytes instead of FileHandler when creating a log file by the
                                `file` option. See logging::handlers::RotatingFileHandler for more information.

            @param `force`      if True (default False), it will force to create the handlers,
                                even if there are not changes on the current saved default parameters.
                                Its value is not saved between calls to this setup().

            @param `active`     if True (default True), it will search for any other active logger in
                                the current logger hierarchy and do the setup call on him. If no active
                                logger is found, it will do the setup on the current logger object,
                                Its value is not saved between calls to this setup().
        """
        self._setup( file=file, mode=mode, delete=delete, date=date, level=level,
                function=function, name=name, time=time, msecs=msecs, tick=tick,
                separator=separator, formatter=formatter, rotation=rotation, **kwargs )

    def _setup(self, **kwargs):
        """
            Allow to pass positional arguments to `setup()`.
        """
        force = kwargs.pop( 'force', False )
        _fix_children = kwargs.pop( '_fix_children', False )

        active = self.active()
        logger = active or self if kwargs.pop( 'active', True ) else self

        has_changes = False
        arguments = logger._arguments

        for kwarg in kwargs:
            value = kwargs[kwarg]

            if value != EMPTY_KWARG:

                if value != arguments[kwarg]:
                    has_changes = True
                    arguments[kwarg] = value

        if has_changes \
                or force \
                or ( not logger.stream_handler \
                    and not logger.file_handler ):

            if _fix_children:
                logger._fixChildren()

            logger.full_formatter = logger._setup_formatter( logger._arguments )
            logger._setup_log_handlers()

    def _setup_log_handlers(self):
        arguments = self._arguments

        # import traceback
        # traceback.print_stack()

        if arguments['file']:
            output_file = self.get_debug_file_path( arguments['file'] )

            sys.stderr.write( "".join( self._get_time_prefix( datetime.datetime.now() ) )
                    + "Logging to the file %s\n" % output_file )

            self._create_file_handler( output_file, arguments['rotation'], arguments['mode'] )
            self.disable( stream=arguments['delete'] )

        else:
            self.disable( stream=True )

            self.stream_handler = logging.StreamHandler()
            self.stream_handler.formatter = self.full_formatter

            self.addHandler( self.stream_handler )
            self.disable( file=arguments['delete'] )

    def _create_file_handler(self, output_file, rotation, mode, clear=False, delete=False):
        backup_count = mode
        mode = 'w' if clear else mode

        if self.file_handler:
            self.disable( file=True )

            if delete:
                os.remove( output_file )
                return

            elif clear:

                with open( output_file, 'w' ) as file:
                    file.truncate()

        if rotation > 0:
            rotation = rotation * 1024 * 1024

            backup_count = abs( backup_count ) if isinstance( backup_count, int ) else 2
            self.file_handler = ConcurrentRotatingFileHandler( output_file, maxBytes=rotation, backupCount=backup_count )

        else:

            if not isinstance( mode, str ):
                raise ValueError( "The mode argument `%s` must be instance of string." % mode )

            self.file_handler = logging.FileHandler( output_file, mode )

        self.file_handler.formatter = self.full_formatter
        self.addHandler( self.file_handler )
        self.handle_strerr( True )

    def warn(self, msg, *args, **kwargs):
        """
            Fix second indirection created by the super().warn() method, by directly calling _log()
        """

        if self.isEnabledFor( WARNING ):
            self._log( WARNING, msg, args, **kwargs )

    def exception(self, msg, *args, **kwargs):
        """
            Fix second indirection created by the super().error() method, by directly calling _log()
        """
        if self.isEnabledFor(ERROR):
            self._log(ERROR, msg, args, exc_info=True, **kwargs)

    def _log(self, level, msg, args, exc_info=None, extra={}, stack_info=False, debug_level=0):
        self.currentTick = timeit.default_timer()

        debug_level = "(%d)" % debug_level if debug_level else ""
        extra.update( {"debugLevel": debug_level, "tickDifference": self.currentTick - self.lastTick} )

        if is_python2:
            super( Debugger, self )._log( level, msg, args, exc_info, extra )

        else:
            super( Debugger, self )._log( level, msg, args, exc_info, extra, stack_info )

        self.lastTick = self.currentTick

    def _log_clean(self, msg):
        record = CleanLogRecord( self.level, self.name, msg )
        self.handle( record )

    @classmethod
    def _setup_formatter(cls, arguments):

        if arguments['formatter']:

            if isinstance( arguments['formatter'], logging.Formatter ):
                return arguments['formatter']

            else:
                raise ValueError( "Error: The formatter %s must be an instance of logging.Formatter" % arguments['formatter'] )

        else:
            # These 2 do not need extra spacing because they are the last of their chain
            tick  = cls.getFormat( arguments, 'tick', "%(tickDifference).2e" )
            level = cls.getFormat( arguments, 'level', "%(levelname)s%(debugLevel)s" )

            separator = cls.getFormat( arguments, 'separator', " - " )
            msecs = cls.getFormat( arguments, 'msecs', ":%(msecs)010.6f", tick )

            time_format = cls.getFormat( arguments, 'time', "%H:%M:%S", not msecs )
            date_format = cls.getFormat( arguments, 'date', "%Y-%m-%d", time_format )

            date_format += time_format

            time  = "%(asctime)s" if len( date_format ) else ""
            time += "" if msecs else " " if arguments['time'] else ""

            function = cls.getFormat( arguments, 'function', "%(funcName)s:%(lineno)d", level )
            name     = cls.getFormat( arguments, 'name', "%(name)s", level and not function )

            name += "." if name and function else ""
            extra_spacing = " - " if name or level or function else ""

            return logging.Formatter( "{}{}{}{}{}{}{}{}%(message)s".format(
                    time, msecs, tick, extra_spacing, name, function, level, separator ), date_format )

    @staticmethod
    def getFormat(arguments, setting, default, next_parameter=""):
        value = arguments[setting]

        if isinstance( value, str ):
            return value

        if value:
            value = default + ( " " if next_parameter else "" )

        else:
            value = ""

        return value

    def _get_time_prefix(self, currentTime):
        return [ "[%s]" % self.name,
                " %02d" % currentTime.hour,
                ":%02d" % currentTime.minute,
                ":%02d" % currentTime.second,
                ":%07d " % currentTime.microsecond ]

    def removeHandlers(self):
        self.disable( True, True )

        for handler in self.handlers:
            self.removeHandler( handler )

    def _fixChildren(self):
        """
            When automatically creating loggers, some children logger can be setup before the
            parent logger, if the children logger is instantiated on module level and its module
            is imported before the parent logger to be setup.

            Then this will cause the the both parent and child logger to be setup and have handlers
            outputting data to theirs output stream. Hence, here we fix that by disabling the
            children logger when they are setup before the parent logger.

            This method is only called automatically by this module level function `getLogger()`
            when is set to automatically setup the logger. If you are not using the automatic setup
            you do not need to use this function because you should know what you are doing and how
            you should setup your own loggers.
        """
        loggers = Debugger.manager.loggerDict
        parent_name = self.name
        parent_name_length = len( parent_name )

        for logger_name in loggers:
            logger = loggers[logger_name]

            if not isinstance( logger, PlaceHolder ):

                # i.e., if logger.parent.name.startswith( parent_name )
                if logger.parent.name[:parent_name_length] == parent_name:
                    logger.removeHandlers()

    @classmethod
    def get_debug_file_path(cls, file_path):
        """
            Reliably detect Windows in Python
            https://stackoverflow.com/questions/1387222/reliably-detect-windows-in-python

            Convert "D:/User/Downloads/debug.txt"
            To "/cygwin/D/User/Downloads/debug.txt"
            To "/mnt/D/User/Downloads/debug.txt"
        """
        is_absolute   = os.path.isabs( file_path )
        platform_info = platform.platform( True ).lower()

        if is_absolute \
                and not file_path.startswith( "/cygdrive/" ) \
                and "cygwin" in platform_info:

            new_output = "/cygdrive/" + cls.remove_windows_driver_letter( file_path )

        elif is_absolute \
                and not file_path.startswith( "/mnt/" ) \
                and "linux" in platform_info \
                and "microsoft" in platform_info:

            new_output = cls.remove_windows_driver_letter( file_path )
            new_output = "/mnt/" + new_output[0].lower() + new_output[1:]

        else:
            new_output = os.path.abspath( file_path )

        # print( "Debugger, is_absolute:   %s" % is_absolute )
        # print( "Debugger, new_output:    %s" % new_output )
        # print( "Debugger, isabs:         %s" % str( os.path.isabs( new_output ) ) )
        # print( "Debugger, platform_info: %s" % platform_info )
        return new_output

    @classmethod
    def remove_windows_driver_letter(cls, file_path):
        file_path = file_path.replace( ":", "", 1 )
        file_path = file_path.replace( "\\", "/", 1 )
        return file_path.replace( "\\\\", "/", 1 )

    @classmethod
    def getRootLogger(cls):
        """
            Return the main root logger `root_debugger` used by this extension of the standard
            logging module.
        """
        return cls.root

    def __str__(self):
        total_loggers = [0]
        representations = []

        place_holders = []
        loggers = [self.root]
        loggers_dict = Debugger.manager.loggerDict

        def add(logger):
            total_loggers[0] += 1
            current_logger = "True_" if logger == self else "False"

            if isinstance( logger, PlaceHolder ):
                representations.append( "%2s. name(%s), %s" %
                        ( str( total_loggers[0] ), current_logger, "".join(
                                ["loggerMap(%s): %s" % (item.name, logger.loggerMap[item])
                                for item in logger.loggerMap] ) ) )

            else:
                representations.append( "%2s. _debug_level: %3d, level: %2s, propagate: %5s, "
                    "_frame_level: %2d, name(%s): %s, stream_handler: %s, file_handler: %s, arguments: %s" %
                    ( str( total_loggers[0] ), logger._debug_level, logger.level, logger.propagate,
                    logger._frame_level, current_logger, logger.name, logger.stream_handler, logger.file_handler,
                    logger._arguments ) )

        for logger_name in loggers_dict:
            logger = loggers_dict[logger_name]

            if isinstance( logger, PlaceHolder ):
                place_holders.append( logger )

            else:
                loggers.append( logger )

        loggers.sort( key=lambda item: item.name, reverse=True )
        loggers.extend( place_holders )

        for logger in loggers:
            add( logger )

        return "\n%s" % "\n".join( reversed( representations ) )

    def _setup_find_caller(self):
        """
            Copied from the python 3.6.3 and 2.7.14 implementation, only changing the `sys._getframe(3)`
            to `sys._getframe(4)` because due the inheritance, we need to take a higher frame to get
            the correct function name, otherwise the result would always be `__call__`, which is the
            internal function we use here.

            Find the stack frame of the caller so that we can note the source file name, line number
            and function name.
        """

        def findCallerPython3(stack_info=False):
            f = currentframe(self._frame_level)
            #On some versions of IronPython, currentframe() returns None if
            #IronPython isn't run with -X:Frames.
            if f is not None:
                f = f.f_back
            rv = "(unknown file)", 0, "(unknown function)", None
            while hasattr(f, "f_code"):
                co = f.f_code
                filename = os.path.normcase(co.co_filename)
                if filename == _srcfile:
                    f = f.f_back
                    continue
                sinfo = None
                if stack_info:
                    sio = io.StringIO()
                    sio.write('Stack (most recent call last):\n')
                    traceback.print_stack(f, file=sio)
                    sinfo = sio.getvalue()
                    if sinfo[-1] == '\n':
                        sinfo = sinfo[:-1]
                    sio.close()
                rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
                break
            return rv

        def findCallerPython2():
            f = currentframe(self._frame_level)
            #On some versions of IronPython, currentframe() returns None if
            #IronPython isn't run with -X:Frames.
            if f is not None:
                f = f.f_back
            rv = "(unknown file)", 0, "(unknown function)"
            while hasattr(f, "f_code"):
                co = f.f_code
                filename = os.path.normcase(co.co_filename)
                if filename == _srcfile:
                    f = f.f_back
                    continue
                rv = (co.co_filename, f.f_lineno, co.co_name)
                break
            return rv

        if is_python2:
            self.findCaller = findCallerPython2

        else:
            self.findCaller = findCallerPython3


class CleanLogRecord(object):

    def __init__(self, level, name, msg):
        self.name = name
        self.msg = msg
        self.levelno = level

        self.levelname = getLevelName(level)
        self.pathname = "No Path Name"
        self.filename = "No Filename"
        self.module = "Unknown module"

        self.debugLevel = ""
        self.tickDifference = 0.0

        self.exc_info = None
        self.exc_text = None
        self.stack_info = None
        self.lineno = 0

        self.args = "No Args"
        self.funcName = "No Function"
        self.created = 0
        self.msecs = 0
        self.relativeCreated = 0

        self.thread = None
        self.threadName = None
        self.processName = None
        self.process = None

    def __str__(self):
        return '<CleanLogRecord: "%s">' % ( self.msg )

    def getMessage(self):
        return str( self.msg )


_stderr_singleton = None


class TeeNoFile(object):
    """
        How do I duplicate sys.stdout to a log file in python?
        https://stackoverflow.com/questions/616645/how-do-i-duplicate-sys-stdout-to-a-log-file-in-python

        How to redirect stdout and stderr to logger in Python
        https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python

        Set a Read-Only Attribute in Python?
        https://stackoverflow.com/questions/24497316/set-a-read-only-attribute-in-python
    """
    is_active = False

    @classmethod
    def lock(cls, logger):
        global _stderr_default
        global _stderr_singleton
        global _stderr_class_type

        # On Sublime Text, the `sys.__stderr__` is None
        try:
            _stderr_default
            _stderr_class_type

        except NameError:

            if sys.__stderr__:
                _stderr_default = sys.__stderr__

            else:
                _stderr_default = sys.stderr

            _stderr_class_type = type( _stderr_default )

        class TeeNoFileHidden(_stderr_class_type):

            def __init__(self):
                pass

            def __getattribute__(self, item):
                print( "__getattribute__, item: %s, _sys_stderr_write: %s" % ( item, _sys_stderr_write ) )

                if item == 'write':
                    return _sys_stderr_write

                try:

                    return _stderr_default.__getattribute__( item )

                except AttributeError:
                    return super( _stderr_class_type, _stderr_default ).__getattribute__( item )

            def __del__(self):
                global _stderr_default
                global _stderr_singleton

                if sys and _stderr_default:
                    sys.stderr = _stderr_default
                    _stderr_singleton = None
                    TeeNoFile.is_active = False

                    del _stderr_default
                    del _stderr_class_type

        # import inspect
        # print( "_stderr_default:", _stderr_default )
        # print( "_stderr_default.__dict__:", dir( _stderr_default ) )
        # print( "_stderr_default.inspect:", inspect.getfullargspec( _stderr_default.__init__ ) )

        if not cls.is_active:
            cls.is_active = True
            _stderr_write = _stderr_default.write

            logger_call = logger._log_clean
            clean_formatter = logger.clean_formatter

            global _sys_stderr_write
            global _sys_stderr_write_hidden

            def _sys_stderr_write(*args, **kwargs):
                """
                    Hides the actual function pointer. This allow the external function pointer to
                    be cached while the internal written can be exchanged between the standard
                    `sys.stderr.write` and our custom wrapper around it.
                """
                return _sys_stderr_write_hidden( *args, **kwargs )

            def _sys_stderr_write_hidden(*args, **kwargs):
                """
                    Suppress newline in Python logging module
                    https://stackoverflow.com/questions/7168790/suppress-newline-in-python-logging-module
                """

                try:
                    _stderr_write( data )
                    file_handler = logger.file_handler

                    formatter = file_handler.formatter
                    file_handler.formatter = clean_formatter

                    terminator = StreamHandler.terminator
                    StreamHandler.terminator = ""

                    logger_call( data )

                    file_handler.formatter = formatter
                    StreamHandler.terminator = terminator

                except Exception:
                    logger.exception( "Could not write to the file_handler" )
                    cls.unlock()

        # Create the singleton instance
        if _stderr_singleton:

            try:
                _stderr_singleton = copy.copy( _stderr_default )
                _stderr_singleton.write = _sys_stderr_write

            except TypeError:
                _stderr_singleton = TeeNoFileHidden()

            sys.stderr = _stderr_singleton

        return _stderr_singleton

    @classmethod
    def unlock(cls):

        if cls.is_active:
            global _sys_stderr_write_hidden

            cls.is_active = False
            _sys_stderr_write_hidden = _stderr_default.write

        return _stderr_singleton


# Setup the alternate debugger, completely independent of the standard logging module Logger class
root = Debugger( "root_debugger", "WARNING" )
Debugger.root = root

Debugger.manager = Manager( root )
Debugger.manager.setLoggerClass( Debugger )


def getLogger(debug_level=127, logger_name=None,
            file=EMPTY_KWARG, mode=EMPTY_KWARG, delete=EMPTY_KWARG, date=EMPTY_KWARG, level=EMPTY_KWARG,
            function=EMPTY_KWARG, name=EMPTY_KWARG, time=EMPTY_KWARG, msecs=EMPTY_KWARG, tick=EMPTY_KWARG,
            separator=EMPTY_KWARG, formatter=EMPTY_KWARG, rotation=EMPTY_KWARG, **kwargs):
    """
    Return a logger with the specified name, creating it if necessary. If no name is specified,
    return a new logger based on the main logger file name. See also logging::Manager::getLogger()

    It has the same parameters as Debugger::setup with the addition of the following parameters:

    @param `debug_level` and `logger_name` are the same parameters passed to the Debugger::__init__() constructor.

    @param `level` if True, add to the `full_formatter` the log levels. If not a boolean,
        it should be the initial logging level accordingly to logging::Logger::setLevel(level)

    @param from `file` until `**kwargs` are the named parameters passed to the Debugger.setup() member function.

    @param `setup` if True (default), ensure there is at least one handler enabled in the hierarchy,
        then the current created active Logger setup method will be called.
    """
    return _getLogger( debug_level, logger_name,
            file=file, mode=mode, delete=delete, date=date, level=level,
            function=function, name=name, time=time, msecs=msecs, tick=tick,
            separator=separator, formatter=formatter, rotation=rotation, **kwargs )


def _getLogger(debug_level=127, logger_name=None, **kwargs):
    """
        Allow to pass positional arguments to `getLogger()`.
    """
    level = kwargs.get( "level", EMPTY_KWARG )
    debug_level, logger_name = _get_debug_level( debug_level, logger_name )

    logger = Debugger.manager.getLogger( logger_name )
    logger.debug_level = debug_level

    if level != EMPTY_KWARG \
            and not isinstance( level, bool ):

        kwargs.pop( "level" )
        logger.setLevel( level )

    if kwargs.pop( "setup", True ) == True:
        logger._setup( _fix_children=True, **kwargs )

    return logger


def _get_debug_level(debug_level, logger_name):

    if logger_name:

        if isinstance( logger_name, int ):
            debug_level, logger_name = logger_name, debug_level

            if isinstance( logger_name, int ):
                raise ValueError( "The variable `logger_name` must be an instance of string, instead of `%s`." % str( logger_name ) )

        else:

            if not isinstance( debug_level, int ):
                raise ValueError( "The variable `logger_name` must be an instance of int, instead of `%s`." % logger_name )

    else:

        if isinstance( debug_level, int ):
            logger_name = os.path.basename( "logger" )

        else:
            logger_name = debug_level
            debug_level = 127

    return debug_level, logger_name

