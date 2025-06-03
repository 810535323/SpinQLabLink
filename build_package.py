#!/usr/bin/env python
"""
SpinQLabLink 打包脚本
用于生成分发包 (.whl 和 .tar.gz)
"""

import os
import shutil
import subprocess
import sys


def check_requirements():
    """检查打包所需的依赖是否已安装"""
    required_packages = ['wheel', 'setuptools', 'build', 'twine']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少必要的打包依赖: {', '.join(missing_packages)}")
        print("请先安装这些依赖:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', 'spinqlablink.egg-info']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)


def build_package():
    """构建Python包"""
    print("开始构建分发包...")
    
    # 使用 build 模块构建
    result = subprocess.run([sys.executable, '-m', 'build'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("构建失败:")
        print(result.stderr)
        return False
    
    print("构建成功!")
    print("\n构建的分发包:")
    
    # 列出生成的分发包
    for file in os.listdir('dist'):
        file_path = os.path.join('dist', file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"- {file} ({file_size:.1f} KB)")
    
    return True


def main():
    """主函数"""
    print("===== SpinQLabLink 打包工具 =====")
    
    # 检查依赖
    if not check_requirements():
        return 1
    
    # 清理旧的构建文件
    clean_build_dirs()
    
    # 构建包
    if not build_package():
        return 1
    
    print("\n分发包已成功生成在 'dist/' 目录下")
    print("\n安装说明:")
    print("1. 直接安装 .whl 文件:")
    print("   pip install dist/*.whl")
    print("\n2. 上传到PyPI (如需公开发布):")
    print("   twine upload dist/*")
    print("\n3. 开发模式安装:")
    print("   pip install -e .")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 