"""
Some utils for visual logging using tkinter:
    - as handler to redirect prints to a tk Entry widget
    - a logging handler for logging directly to a tk Entry widget

You can implement child classes that override the LogTextHandler.emit_widget and the PrintHandler.write_widget to
write to tk Widgets different from a tk.Entry widget. These new classes can be passed as the handler_class parameters
to print2widget and logger2widget functions to activate them
"""

import logging
from logging import Handler
import sys
import tkinter as tk


class _WidgetWriter:
    """Writes messages to a widget, autoscrolling"""
    def __init__(self, widget: tk.Text):
        self.widget = widget

    def write_to_widget(self, msg: str):
        """appends given text to widget"""
        self.widget.configure(state='normal')
        self.widget.insert('end', msg + '\n')
        self.widget.see("end")  # autoscroll
        self.widget.configure(state='disabled')
        self.widget.update()


class LogTextHandler(Handler, _WidgetWriter):
    """A logging handler that sends output to a read only tkinter widget"""
    def __init__(self, widget: tk.Text, level: int):
        Handler.__init__(self, level=level)
        _WidgetWriter.__init__(self, widget=widget)

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.write_to_widget(log_entry)
        except tk.TclError as te:
            sys.stderr.write(str(te))
            sys.stderr.flush()


class PrintHandler(_WidgetWriter):
    """Handler used to redirect prints to a tk Entry widget"""

    def __init__(self, widget: tk.Text):
        super().__init__(widget)
        self.stdout = sys.stdout
        sys.stdout = self

    def write(self, s):
        try:
            self.write_to_widget(s)
        except tk.TclError as te:
            sys.stderr.write(str(te))
            sys.stderr.flush()

    def flush(self):
        pass


def print2widget(widget: tk.Text, handler_class=PrintHandler):
    """Redirects all class to print to the given tkinter widget"""
    handler_class(widget)


def logger2widget(logger: logging.Logger, widget: tk.Text, level=logging.INFO, handler_class=LogTextHandler):
    """Adds a new LogTextHandler for the given logger to redirects its logs to the given tkinter Entry widget"""
    # Do not add logger if it already existed
    if not any(isinstance(h, handler_class) for h in logger.handlers):
        lh = handler_class(widget=widget, level=level)
        # lh.setLevel(level)
        logger.addHandler(lh)
