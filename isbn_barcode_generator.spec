# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ISBN Barcode Generator
ISBN条码生成器打包配置文件

Requirements: 10.1, 10.3, 10.6
- 打包为独立的Windows可执行文件
- 包含所有必要的依赖库和资源文件
- 包含应用程序图标
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
project_root = os.path.abspath(os.path.dirname(SPEC))

# 源代码目录
src_dir = os.path.join(project_root, 'src')

# 资源文件目录
resources_dir = os.path.join(src_dir, 'isbn_barcode_generator', 'resources')

# 图标文件路径
icon_file = os.path.join(resources_dir, 'icon.ico')

# 分析配置
a = Analysis(
    # 入口脚本 - 使用专门的打包入口
    [os.path.join(project_root, 'run_app.py')],
    
    # 路径设置
    pathex=[src_dir],
    
    # 二进制文件（无额外二进制）
    binaries=[],
    
    # 数据文件 - 包含资源文件
    datas=[
        # 图标文件
        (os.path.join(resources_dir, 'icon.ico'), 'isbn_barcode_generator/resources'),
        (os.path.join(resources_dir, 'icon.png'), 'isbn_barcode_generator/resources'),
    ],
    
    # 隐式导入 - PyQt6和Pillow的子模块
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.TiffImagePlugin',
        'PIL.TiffTags',
        # 核心模块
        'isbn_barcode_generator',
        'isbn_barcode_generator.core',
        'isbn_barcode_generator.core.validator',
        'isbn_barcode_generator.core.encoder',
        'isbn_barcode_generator.core.addon_encoder',
        'isbn_barcode_generator.core.renderer',
        'isbn_barcode_generator.core.template_manager',
        'isbn_barcode_generator.core.batch_processor',
        'isbn_barcode_generator.gui',
        'isbn_barcode_generator.gui.main_window',
    ],
    
    # 钩子路径
    hookspath=[],
    
    # 运行时钩子
    runtime_hooks=[],
    
    # 排除的模块（减小文件大小）
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'pytest',
        'hypothesis',
        'unittest',
        '_pytest',
    ],
    
    # 不检查的导入
    noarchive=False,
)

# PYZ归档
pyz = PYZ(
    a.pure,
    a.zipped_data,
)

# EXE配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ISBN条码生成器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩（如果可用）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI应用，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,  # 应用程序图标
    version_file='version_info.txt',  # 版本信息文件
)
