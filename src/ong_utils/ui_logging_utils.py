"""
Some utils for visual logging using tkinter:
    - as handler to redirect prints to a tk Entry widget
    - a logging handler for logging directly to a tk Entry widget

You can implement child classes that override the LogTextHandler.emit_widget and the PrintHandler.write_widget to
write to tk Widgets different from a tk.Entry widget. These new classes can be passed as the handler_class parameters
to print2widget and logger2widget functions to activate them
"""

import logging
import re
import sys
import tkinter as tk
from logging import Handler
from tkinter import font
from typing import Tuple


def _interpret_ansi(text):
    """
    Interpret ANSI escape sequences and separate the text into segments.

    :param text: The text containing ANSI escape sequences.
    :type text: str
    :return: A list of tuples where each tuple contains a segment of text and its associated ANSI code.
             If the segment is plain text, the ANSI code is None.
    :rtype: list
    """
    ansi_escape = re.compile(r'\x1b\[(?P<code>[0-9;]*m)')
    matches = list(ansi_escape.finditer(text))

    segments = []
    last_end = 0

    for match in matches:
        start, end = match.span()
        code = match.group('code')
        segments.append((text[last_end:start], None))  # Add the previous text segment without style
        segments.append((None, code))  # Add the ANSI style code
        last_end = end

    segments.append((text[last_end:], None))  # Add the remaining text segment

    return segments


def _ansi_to_tk_color(code) -> Tuple[str, bool, bool]:
    """
    Convert ANSI color codes to Tkinter color names.

    :param code: The ANSI code containing the color information.
    :type code: str
    :return: The corresponding Tkinter color name or hex value, a boolean for bold and a boolean for italic
    :rtype: tuple of string (color), bool (bold) and bool (italic)
    """
    color_code = list(map(int, code.lstrip('\x1b[').rstrip('m').split(';')))
    bold = italic = False
    retval_color = None
    if color_code[0] == 1:  # Bold
        bold = True
        color_code.pop(0)
    if color_code[0] == 3:  # Italic
        italic = True
        color_code.pop(0)
    while (len(color_code) > 1) and color_code[0] < 30:  # Remove any other ansi code
        color_code.pop(0)
    if len(color_code) > 2 and color_code[0] == 38 and color_code[1] == 5:
        index = color_code[2]
    elif len(color_code) == 2 and color_code[0] == 38:
        index = color_code[1]
    elif 30 <= color_code[0] <= 37:
        index = color_code[0] - 30
    else:
        index = None

    # if len(color_code) == 5 and color_code[0] == '38' and color_code[1] == '5':
    if index is not None:
        # index = int(color_code[2])
        # index = int(color_code[1])
        if 0 <= index <= 15:
            colors = [
                'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
                'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
                'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
            ]
            retval_color = colors[index]
        elif 16 <= index <= 231:
            index -= 16
            r = (index // 36) * 51
            g = ((index // 6) % 6) * 51
            b = (index % 6) * 51
            retval_color = f'#{r:02x}{g:02x}{b:02x}'
        elif 232 <= index <= 255:
            gray = (index - 232) * 10 + 8
            retval_color = f'#{gray:02x}{gray:02x}{gray:02x}'

    return retval_color, bold, italic


def _apply_ansi_styles(text_widget, segments):
    """
    Apply styles to a Tkinter Text widget based on ANSI escape sequences.

    :param text_widget: The Tkinter Text widget to which the styles will be applied.
    :type text_widget: tk.Text
    :param segments: A list of tuples where each tuple contains a segment of text and its associated ANSI code.
                     If the segment is plain text, the ANSI code is None.
    :type segments: list
    """
    color = None
    for text, code in segments:
        if code:
            # Interpret the style based on the ANSI sequence
            color, bold, italic = _ansi_to_tk_color(code)
        else:
            # Insert text with the current color
            if color:
                text_widget.insert(tk.END, text, (color,))
                text_widget.tag_config(color, foreground=color)
                new_font = font.Font(font=text_widget['font']).copy()
                new_font.configure(weight=font.BOLD if bold else font.NORMAL,
                                   slant=font.ITALIC if italic else font.ROMAN)
                text_widget.tag_config(color, font=new_font)
            else:
                text_widget.insert(tk.END, text)


class _WidgetWriter:
    """Writes messages to a widget, autoscrolling"""

    def __init__(self, widget: tk.Text, **kwargs):
        self.widget = widget
        self.colors = dict()

    def write_to_widget(self, msg: str):
        """appends given text to widget"""
        self.widget.configure(state='normal')
        segments = _interpret_ansi(msg)
        _apply_ansi_styles(self.widget, segments)

        # self.widget.insert('end', msg + '\n')
        # box.tag_config('name', foreground='green')  # <-- Change colors of texts tagged `name`
        # box.tag_config('time', foreground='red')  # <--  Change colors of texts tagged `time`

        self.widget.see("end")  # autoscroll
        self.widget.configure(state='disabled')
        self.widget.update()


class LogTextHandler(Handler, _WidgetWriter):
    """A logging handler that sends output to a read only tkinter widget"""

    green = "\x1b[32;20m"
    blue = "\x1b[34;20m"
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    default_color_map = {
            logging.DEBUG: blue,
            logging.INFO: green,
            logging.WARNING: yellow,
            logging.ERROR: red,
            logging.CRITICAL: bold_red
        }

    def __init__(self, widget: tk.Text, level: int, color_map: dict=None):
        """
        Inits the logging handler to send logs to the given text widget
        :param widget: text widget to receive logs
        :param level: level of the widget
        :param color_map: a dictionary Dict[int, str] with the mapping of the colors each logging level.
        Defaults to None. Pass an empty dict or LogTextHandler.default_color_map to use default colors
        """
        self.color_map = color_map or dict()
        if color_map is not None:
            self.color_map.update(self.default_color_map)
        Handler.__init__(self, level=level)
        _WidgetWriter.__init__(self, widget=widget)

    def emit(self, record):
        log_entry = self.format(record)
        try:
            if record.levelno in self.color_map:
                color = self.color_map.get(record.levelno, self.reset)
                log_entry = color + log_entry + self.reset
            self.write_to_widget(log_entry + '\n')
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


def logger2widget(logger: logging.Logger, widget: tk.Text, level=logging.INFO,
                  handler_class=LogTextHandler, **kwargs):
    """
    Adds a new LogTextHandler for the given logger to redirects its logs to the given tkinter Entry widget
    :param logger: logger to which the handler will be added
    :param widget: text widget that will be received the loggers
    :param level: logging level for the handler. Defaults to logging.INFO
    :param handler_class: class of the logger handler
    :param kwargs: additional kwargs to pass to constructor
    :return:
    """
    # Do not add logger if it already existed
    if not any(isinstance(h, handler_class) for h in logger.handlers):
        lh = handler_class(widget=widget, level=level, **kwargs)
        # lh.setLevel(level)
        logger.addHandler(lh)
