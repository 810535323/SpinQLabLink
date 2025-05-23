from setuptools import setup, find_packages
import os
from setuptools.command.develop import develop
from setuptools.command.install import install


class PostDevelopCommand(develop):
    """安装后的开发模式设置"""
    def run(self):
        develop.run(self)
        # 安装后的开发模式设置，例如创建日志目录
        self._create_log_directory()
        print("开发模式安装完成，创建了日志目录")
    
    def _create_log_directory(self):
        log_dir = os.path.join(os.path.expanduser("~"), ".spinq", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"创建日志目录: {log_dir}")


class PostInstallCommand(install):
    """安装后的设置"""
    def run(self):
        install.run(self)
        # 安装后的设置，例如创建日志目录
        self._create_log_directory()
        print("安装完成，创建了日志目录")
    
    def _create_log_directory(self):
        log_dir = os.path.join(os.path.expanduser("~"), ".spinq", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"创建日志目录: {log_dir}")


setup(
    name="spinqlablink",
    version="0.1.0",
    description="SpinQLabLink - SpinQ Lab Remote Experiment Python Interface",
    author="SpinQ",
    author_email="support@spinq.com",
    url="https://github.com/spinqtech",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
    ],
    keywords="quantum computing, remote experiments, spinq",
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'spinqlablink=src.cli:main',
        ],
    },
) 