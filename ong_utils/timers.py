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
        self.is_loop = False        # To prevent further prints

    def __del__(self):
        """In case not printed, prints the total elapsed time """
        if self.is_loop:
            self.print(" (in total)")


class OngTimer:
    def __init__(self, enabled=True):
        """Starts timer. If enabled=False (defaults to True) does nothing"""
        self.enabled = enabled
        if not self.enabled: return
        self.__tics = dict()

    def tic(self, msg):
        """Starts timer for process identified by msg"""
        if not self.enabled: return
        if msg not in self.__tics:
            self.__tics[msg] = _OngTic(msg)
        ticobj = self.__tics.get(msg)
        ticobj.tic()

    def _get_ticobj(self, msg):
        if msg not in self.__tics:
            raise ValueError(f"The tick '{msg}' has not been initialized")
        return self.__tics[msg]

    def toc(self, msg):
        """Stops accumulating time for process identified by msg and prints message. No more printing will be done"""
        if not self.enabled: return
        self._get_ticobj(msg).toc()

    def toc_loop(self, msg):
        """Stops accumulating time for process identified by msg and DOES NOT prints message"""
        if not self.enabled: return
        self._get_ticobj(msg).toc(loop=True)

    def print_loop(self, msg):
        """Prints total elapsed time of all steps of a loop"""
        if not self.enabled: return
        self._get_ticobj(msg).print(" (in total)")

    def elapsed(self, msg):
        """Returns total elapsed time of a timer"""
        return self._get_ticobj(msg).total_t


if __name__ == '__main__':
    from time import sleep

    tic = OngTimer()    # if used OngTimer(False), all prints would be disabled

    tic.tic("Starting")
    for i in range(10):
        tic.tic("Without loop")
        sleep(0.15)
        tic.toc("Without loop")
        tic.tic("Loop")
        sleep(0.1)
        if i != 5:
            tic.toc_loop("Loop")        # Will print elapsed time up to iter #5
        else:
            tic.toc("Loop")             # Will print in this case
    sleep(1)
    tic.print_loop("Loop")           # Forces print In any case it would be printed in destruction of tic instance
    tic.toc("Starting")     # Will print total time of the whole loop
    tic.toc("This msg has not been defined in a previous tick so exception will be risen")
