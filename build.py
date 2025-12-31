#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build script for ISBN Barcode Generator
ISBN条码生成器打包脚本

使用方法:
    python build.py

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} 已安装")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("  请运行: pip install pyinstaller")
        return False


def check_dependencies():
    """检查必要的依赖"""
    dependencies = ['PyQt6', 'PIL']
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"✗ {dep} 未安装")
            missing.append(dep)
    
    return len(missing) == 0


def clean_build():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name}/ ...")
            shutil.rmtree(dir_name)
    
    print("✓ 清理完成")


def run_pyinstaller():
    """运行PyInstaller打包"""
    spec_file = 'isbn_barcode_generator.spec'
    
    if not os.path.exists(spec_file):
        print(f"✗ 找不到spec文件: {spec_file}")
        return False
    
    print(f"\n开始打包...")
    print(f"使用spec文件: {spec_file}")
    print("-" * 50)
    
    # 运行PyInstaller
    result = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', spec_file, '--clean'],
        capture_output=False
    )
    
    return result.returncode == 0


def verify_output():
    """验证输出文件"""
    exe_path = Path('dist') / 'ISBN条码生成器.exe'
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✓ 打包成功!")
        print(f"  输出文件: {exe_path}")
        print(f"  文件大小: {size_mb:.2f} MB")
        return True
    else:
        print(f"\n✗ 打包失败: 找不到输出文件")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("ISBN条码生成器 - 打包脚本")
    print("=" * 50)
    
    # 检查环境
    print("\n[1/4] 检查环境...")
    if not check_pyinstaller():
        return 1
    
    if not check_dependencies():
        print("\n请先安装缺失的依赖")
        return 1
    
    # 清理
    print("\n[2/4] 清理旧文件...")
    clean_build()
    
    # 打包
    print("\n[3/4] 执行打包...")
    if not run_pyinstaller():
        print("\n✗ 打包过程出错")
        return 1
    
    # 验证
    print("\n[4/4] 验证输出...")
    if not verify_output():
        return 1
    
    print("\n" + "=" * 50)
    print("打包完成!")
    print("=" * 50)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
