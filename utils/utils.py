import os
import sys

def resource_path(relative_path):
    """Returns the absolute path to resource (handles PyInstaller's _MEIPASS)"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
