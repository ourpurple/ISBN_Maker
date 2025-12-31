"""
Main entry point - 应用程序入口
"""

import sys


def main():
    """应用程序主入口"""
    from .gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    sys.exit(main() or 0)
