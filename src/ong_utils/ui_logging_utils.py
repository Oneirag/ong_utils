"""
Some utils for visual logging using tkinter:
    - as handler to redirect prints to a tk Entry widget
    - a logging handler for logging directly to a tk Entry widget

You can implement child classes that override the LogTextHandler.emit_widget and the PrintHandler.write_widget to
write to tk Widgets different from a tk.Entry widget. These new classes can be passed as the handler_class parameters
to print2widget and logger2widget functions to activate them
"""

import logging
import sys
import tkinter as tk


class LogTextHandler(logging.Handler):
    """A logging handler that sends output to a read only tkinter widget"""

    def __init__(self, widget: tk.Text):
        logging.Handler.__init__(self)
        self.widget = widget

    def emit_widget(self, msg: str):
        """Overwrite this method in a child class to write to a different widget"""
        self.widget.configure(state='normal')
        self.widget.insert('end', msg + '\n')
        self.widget.configure(state='disabled')
        self.widget.update()

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.emit_widget(log_entry)
        except tk.TclError as te:
            sys.stderr.write(str(te))
            sys.stderr.flush()


class PrintHandler(object):
    """Handler used to redirect prints to a tk Entry widget"""

    def __init__(self, widget):
        self.widget = widget
        self.stdout = sys.stdout
        sys.stdout = self

    def write_widget(self, s: str):
        """Overwrite this method in a child class to write to a different widget"""
        self.widget.configure(state='normal')
        self.widget.insert('end', s)
        self.widget.configure(state='disabled')
        self.widget.update()

    def write(self, s):
        try:
            self.write_widget(s)
        except tk.TclError as te:
            sys.stderr.write(str(te))
            sys.stderr.flush()

    def flush(self):
        pass


def print2widget(widget: tk.Widget, handler_class=PrintHandler):
    """Redirects all class to print to the given tkinter widget"""
    handler_class(widget)


def logger2widget(logger: logging.Logger, widget: tk.Widget, level=logging.INFO, handler_class=LogTextHandler):
    """Adds a new LogTextHandler for the given logger to redirects its logs to the given tkinter Entry widget"""
    # Do not add logger if it already existed
    if not any(isinstance(h, handler_class) for h in logger.handlers):
        lh = handler_class(widget)
        lh.setLevel(level)
        logger.addHandler(lh)
