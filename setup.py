# Copyright 2025 SpinQ Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages
import os
import sys
import platform

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
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS"
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
        "pydantic>=2.0.0",
        "protobuf>=3.19.0"
    ],
    keywords="quantum computing, remote experiments, spinq lab",
    # entry_points={
    #     'console_scripts': [
    #         'spinqlablink=src.cli:main',
    #     ],
    # },
) 