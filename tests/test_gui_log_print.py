"""
Tests for print/log messages
"""
import unittest
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from ong_utils import OngConfig, logger2widget, print2widget


class TestPrintLog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.logger = OngConfig("ong_utils_test_gui", default_app_cfg={},
                               write_default_file=False).logger

    def setUp(self):
        self.root = tk.Tk()
        self.ui_text_area = scrolledtext.ScrolledText(self.root)
        self.ui_text_area.pack()
        logger2widget(self.logger, self.ui_text_area)
        print2widget(self.ui_text_area)

    def test_log(self):
        print("hola")
        self.logger.info("hola que tal")
        print("caracola")
        print("y aquí sigue el log")
        self.root.mainloop()
