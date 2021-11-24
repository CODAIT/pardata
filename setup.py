#
# Copyright 2020--2021 IBM Corp. All Rights Reserved.
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
#

import pathlib
import setuptools


setuptools.setup(
    name="pardata",
    description=("A Python API that enables data consumers and distributors to easily use and share datasets, "
                 "and establishes a standard for exchanging data assets."),
    long_description=pathlib.Path('README.rst').read_text(),
    long_description_content_type="text/x-rst",
    keywords="machine-learning data-mining data-science",
    author="IBM Center for Open Source Data and AI Technologies (CODAIT)",
    license="Apache v2",
    packages=setuptools.find_packages(),
    data_files=[("", ["LICENSE"])],
    python_requires=">=3.7",
    install_requires=[
        "packaging >= 20.4",
        "pandas >= 1.1.0",
        "Pillow >= 8.2.0",
        "pydantic >= 1.7.2",
        "PyYAML >= 5.3.1",
        "requests >= 2.24.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
    ],
    use_scm_version={'write_to': 'pardata/_version.py'},
    setup_requires=['setuptools_scm']
)
