"""
Timer object for measuring elapsed time elapsed in some processes
"""
import logging
from datetime import timedelta
from time import time


def format_hours_min_seconds(total_seconds: float, decimal_places=3) -> str:
    """Format seconds in hh:mm:ss way including decimals"""
    retval = str(timedelta(seconds=total_seconds))
    decimal = retval.rfind(".")
    if decimal > 0:
        retval = retval[:decimal + decimal_places + 1]
    return retval


class _OngTic:
    def __init__(self, msg, logger=None, log_level: str = logging.DEBUG, decimal_places=3):
        """Starts timer with a msg that identifies the timer"""
        self.start_t = time()
        self.total_t = 0
        self.msg = msg
        self.is_loop = False
        self.logger = logger
        self.log_level = log_level
        self.printed = False
        self.decimal_places = decimal_places
        self.__msg = "Elapsed time for"

    def tic(self):
        """Starts to count time"""
        self.start_t = time()
        self.printed = False

    def toc(self, loop=False):
        """Accumulates time from tic and  if loop=False (default) prints a message"""
        self.total_t += time() - self.start_t
        if not loop:
            self.print()
        else:
            self.is_loop = True

    def print(self, extra_msg: str = ""):
        """Prints a message showing total elapsed time in seconds"""
        self.printed = True
        print_msg = f"{self.__msg} {self.msg}{extra_msg}: {self.total_t:.{self.decimal_places}f}s"
        if self.total_t > 60:
            # It more than 60 seconds, format time
            print_msg += "({})".format(format_hours_min_seconds(self.total_t, decimal_places=self.decimal_places))
        # If there is a logger, print just to the logger and don't use print
        if self.logger:
            self.logger.log(self.log_level, print_msg)
        else:
            print(print_msg)
        self.is_loop = False  # To prevent further prints

    def __del__(self):
        """In case not printed, prints the total elapsed time """
        if self.is_loop:
            self.print(" (in total)")
        else:
            if not self.printed:
                self.__msg = "Closing elapsed time for"
                self.toc()


def is_self_enabled(func, *args, **kwargs):
    """A decorator that executes decorated member function only if self.enabled is True"""

    def wrapper(*args, **kwargs):
        self = args[0]
        if self.enabled:
            func(*args, **kwargs)

    return wrapper


class OngTimer:
    def __init__(self, enabled=True, msg: str = None, logger=None, log_level=logging.DEBUG, decimal_places=3):
        """
        Creates a timer, but it does not start it.
        The class can be used as a context manager, e.g.:

        with OngTimer(msg="This is a test"):
            do_something()

        or declaring an instance

        timer = OngTimer()
        timer.tic("This is a test")
        do_something()
        timer.toc("This is a test")

        :param enabled: If enabled=False (defaults to True) does nothing
        :param msg: Needed only for using as a context manager (using the with keyword)
        :param logger: optional logger to write messages (default value of None disables it)
        :param log_level: optional log level for logger (defaults to DEBUG)
        :param decimal_places: optional number of decimals of second to print (defaults to 3)
        """
        self.enabled = enabled
        self.msg = msg
        if not self.enabled:
            return
        self.__tics = dict()
        self.logger = logger
        self.log_level = log_level
        self.decimal_places = decimal_places

    @is_self_enabled
    def tic(self, msg):
        """Starts timer for process identified by msg"""
        if msg not in self.__tics:
            self.__tics[msg] = _OngTic(msg, logger=self.logger, log_level=self.log_level, decimal_places=self.decimal_places)
        ticobj = self.__tics.get(msg)
        ticobj.tic()

    def _get_ticobj(self, msg):
        if msg not in self.__tics:
            raise ValueError(f"The tick '{msg}' has not been initialized")
        return self.__tics[msg]

    @is_self_enabled
    def toc(self, msg):
        """Stops accumulating time for process identified by msg and prints message. No more printing will be done"""
        self._get_ticobj(msg).toc()

    @is_self_enabled
    def toc_loop(self, msg):
        """Stops accumulating time for process identified by msg and DOES NOT prints message"""
        self._get_ticobj(msg).toc(loop=True)

    def print_loop(self, msg):
        """Prints total elapsed time of all steps of a loop"""
        self._get_ticobj(msg).print(" (in total)")

    def elapsed(self, msg):
        """Returns total elapsed time of a timer"""
        return self._get_ticobj(msg).total_t

    def __enter__(self):
        """Allows using timer as a context manager. Needs that param msg has been previously defined in constructor"""
        if self.msg is None:
            raise ValueError("A msg arg must be passed in OngTimer constructor")
        self.tic(self.msg)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Allows using timer as a context manager"""
        self.toc(self.msg)

    def context_manager(self, msg):
        """Allows an existing instance to be used as a context manager"""
        self.msg = msg
        return self

    @property
    def msgs(self):
        """Gets list of tics of all opened msg. Useful for iterating over all and printing"""
        return self.__tics.keys()


if __name__ == '__main__':
    from time import sleep
    # Example for formatting time for really long times
    print(format_hours_min_seconds(10))
    print(format_hours_min_seconds(100))
    print(format_hours_min_seconds(1000))
    print(format_hours_min_seconds(10000.323239392331))

    #########################################################################################################
    # Standard use (defining an instance and using tic, toc and toc_loop methods, changing decimal places)
    #########################################################################################################
    tic = OngTimer()  # if used OngTimer(False), all prints would be disabled
    more_precise_tic = OngTimer(decimal_places=6)     # Use decimals parameter to increase decimals (defaults to 3)

    tic.tic("Starting")
    more_precise_tic.tic("Starting (6 decimals)")
    for i in range(10):
        tic.tic("Without loop")
        sleep(0.15)
        tic.toc("Without loop")
        tic.tic("Loop")
        sleep(0.1)
        if i != 5:
            tic.toc_loop("Loop")  # Will print elapsed time up to iter #5
        else:
            tic.toc("Loop")  # Will print in this case
    sleep(1)
    tic.print_loop("Loop")  # Forces print In any case it would be printed in destruction of tic instance
    tic.toc("Starting")  # Will print total time of the whole loop
    more_precise_tic.toc("Starting (6 decimals)")  # Will print total time with 6 decimals

    ########################################################################################
    # Using toc/toc_loop with a non previously defined msg will raise a ValueError Exception
    ########################################################################################
    try:
        tic.toc("This msg has not been defined in a previous tick so ValueError Exception will be risen")
    except ValueError as ve:
        print(ve)

    #############################################################
    # Use as a context manager. Won't work accumulating in a loop
    #############################################################
    with OngTimer(msg="Testing sleep"):
        print("hello context manager")
        sleep(0.27)
    with OngTimer().context_manager("Testing sleep"):  # Exactly same as above
        print("hello context manager")
        sleep(0.27)
    # Use context manager (but testing that it can be disabled)
    with OngTimer(msg="Testing sleep disabled", enabled=False):
        print("hello disabled context manager")
        sleep(0.22)
    # use global timer as context manager
    existing_instance = OngTimer()
    with existing_instance.context_manager("Example using an existing context manager instance"):
        sleep(.19)

    # Optionally: write also tick using a logger
    import logging
    logging.basicConfig(level=logging.DEBUG)
    with OngTimer(msg="Using a logger", logger=logging, log_level=logging.DEBUG):
        sleep(0.2)

    ##############################################################
    # When a timer is deleted, any tic without toc will be printed
    ##############################################################
    forgoten_toc_timer = OngTimer()             # This timer will have tics without corresponding toc
    standard_timer = OngTimer(decimal_places=6)
    forgoten_toc_timer_disabled = OngTimer(enabled=False)
    forgoten_toc_timer.tic("forgotten timer1")
    forgoten_toc_timer.tic("forgotten timer2")
    standard_timer.tic("unforgotten timer")
    forgoten_toc_timer_disabled.tic("forgotten disabled timer")
    sleep(0.1)
    standard_timer.toc("unforgotten timer")
    del forgoten_toc_timer   # Will print elapsed time, as are pending tocs
    del standard_timer   # Prints nothing (as there is not pending tic)
    del forgoten_toc_timer_disabled     # Prints nothing (is disabled)

    #####################################################
    # Use .msgs property to iterate over all named timers
    #####################################################
    loop_timer = OngTimer()
    for _ in range(10):
        loop_timer.tic("hello1")
        loop_timer.tic("hello2")
        sleep(0.1)
        loop_timer.toc_loop("hello1")
        loop_timer.toc_loop("hello2")
    for msg in loop_timer.msgs:
        loop_timer.print_loop(msg)
