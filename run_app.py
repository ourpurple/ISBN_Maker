#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Entry point script for PyInstaller packaging
PyInstaller打包入口脚本
"""

import sys
import os

# 确保src目录在路径中
if getattr(sys, 'frozen', False):
    # 运行在PyInstaller打包后的环境
    application_path = sys._MEIPASS
else:
    # 运行在开发环境
    application_path = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(application_path, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

from isbn_barcode_generator.gui import main

if __name__ == "__main__":
    main()
