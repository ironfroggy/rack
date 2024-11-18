from functools import partialmethod, partial
import logging

# Verbosity levels
# Output only the specific results and responses from the given command
V_CONCISE = 0
# Include progress related information and other informative messages
V_INFORMATIVE = 1
# Include detailed information about the command and its results
V_VERBOSE = 2
# Include diagnostic information about the command and its results
V_DIAGNOSTIC = 3

# Extra debugging messages only for developers
L_DEBUG = logging.DEBUG
# Informational messages
L_INFO = logging.INFO
# Problems that may be ignored
L_WARNING = logging.WARNING
# Recoverable errors
L_ERROR = logging.ERROR
# Unrecoverable errors
L_CRITICAL = logging.CRITICAL


ROOT_VLOGGER = None


def msgout(verbosity, msg=None, *args, **kwargs):
    # self.log(verbosity, L_INFO, msg, *args, **kwargs)
    if ROOT_VLOGGER.verbosity >= verbosity:
        print(msg, *args, **kwargs)


msgout_v = partial(msgout, 1)
msgout_vv = partial(msgout, 2)
msgout_vvv = partial(msgout, 3)


class VerbosityLogger(logging.Logger):
    verbosity: int

    def __init__(self, name, *args, **kwargs):
        global ROOT_VLOGGER
        ROOT_VLOGGER = self

        self.setVerbosity(kwargs.pop("verbosity", V_CONCISE))
        super().__init__(name, *args, **kwargs)

    @classmethod
    def getLogger(cls, name, *args, **kwargs):
        return cls(name, *args, **kwargs)

    def setVerbosity(self, verbosity):
        self.verbosity = verbosity

    def log_verbose(self, verbosity, level, msg, *args, **kwargs):
        if verbosity <= self.verbosity:
            extra = kwargs.get("extra", {})
            extra["verbosity"] = verbosity
            kwargs["extra"] = extra
            super().log(level, msg, *args, **kwargs)

    _print = print

    def print(self, _verbosity, msg=None, *args, **kwargs):
        # self.log(verbosity, L_INFO, msg, *args, **kwargs)
        if self.verbosity >= _verbosity:
            print(msg, *args, **kwargs)

    print_v = partialmethod(print, 1)
    print_vv = partialmethod(print, 2)
    print_vvv = partialmethod(print, 3)

    def debug(self, verbosity, msg, *args, **kwargs):
        if self.verbosity >= verbosity:
            return super().debug(msg, *args, **kwargs)

    debug_v = partialmethod(debug, 1)
    debug_vv = partialmethod(debug, 2)
    debug_vvv = partialmethod(debug, 3)

    def info(self, verbosity, msg, *args, **kwargs):
        if self.verbosity >= verbosity:
            return super().info(msg, *args, **kwargs)

    info_v = partialmethod(info, 1)
    info_vv = partialmethod(info, 2)
    info_vvv = partialmethod(info, 3)

    def warning(self, verbosity, msg, *args, **kwargs):
        if self.verbosity >= verbosity:
            return super().warning(msg, *args, **kwargs)

    warning_v = partialmethod(warning, 1)
    warning_vv = partialmethod(warning, 2)
    warning_vvv = partialmethod(warning, 3)

    def error(self, verbosity, msg, *args, **kwargs):
        if self.verbosity >= verbosity:
            return super().error(msg, *args, **kwargs)

    error_v = partialmethod(error, 1)
    error_vv = partialmethod(error, 2)
    error_vvv = partialmethod(error, 3)

    def critical(self, verbosity, msg, *args, **kwargs):
        if self.verbosity >= verbosity:
            return super().critical(msg, *args, **kwargs)

    critical_v = partialmethod(critical, 1)
    critical_vv = partialmethod(critical, 2)
    critical_vvv = partialmethod(critical, 3)
