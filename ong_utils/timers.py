"""
Timer object for measuring elapsed time elapsed in some processes
"""
from time import time


class _OngTic:
    def __init__(self, msg):
        """Starts timer with a msg that identifies the timer"""
        self.start_t = time()
        self.total_t = 0
        self.msg = msg
        self.is_loop = False

    def tic(self):
        """Starts to count time"""
        self.start_t = time()

    def toc(self, loop=False):
        """Accumulates time from tic and  if loop=False (default) prints a message"""
        self.total_t += time() - self.start_t
        if not loop:
            self.print()
        else:
            self.is_loop = True

    def print(self, extra_msg: str = ""):
        """Prints a message showing total elapsed time in seconds"""
        print(f"Elapsed time for {self.msg}{extra_msg}: {self.total_t:.3f}s")
        self.is_loop = False  # To prevent further prints

    def __del__(self):
        """In case not printed, prints the total elapsed time """
        if self.is_loop:
            self.print(" (in total)")


def is_self_enabled(func, *args, **kwargs):
    """A decorator that executes decorated member function only if self.enabled is True"""

    def wrapper(*args, **kwargs):
        self = args[0]
        if self.enabled:
            func(*args, **kwargs)

    return wrapper


class OngTimer:
    def __init__(self, enabled=True, msg: str = None):
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
        """
        self.enabled = enabled
        self.msg = msg
        if not self.enabled:
            return
        self.__tics = dict()

    @is_self_enabled
    def tic(self, msg):
        """Starts timer for process identified by msg"""
        if msg not in self.__tics:
            self.__tics[msg] = _OngTic(msg)
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


if __name__ == '__main__':
    from time import sleep

    #############################################################################
    # Standard use (defining an instance and using tic, toc and toc_loop methods)
    #############################################################################
    tic = OngTimer()  # if used OngTimer(False), all prints would be disabled

    tic.tic("Starting")
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
