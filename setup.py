#
# Copyright 2020 IBM Corp. All Rights Reserved.
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

import setuptools

from pydax.version import __version__

with open('README.md') as f:
    long_description = f.read()

setuptools.setup(
    name="pydax",
    version=__version__,
    description="Access DAX datasets.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="machine-learning data-mining data-science",
    author="IBM Center for Open Source Data and AI Technologies (CODAIT)",
    license="Apache v2",
    packages=setuptools.find_packages(),
    data_files=[("", ["LICENSE"])],
    python_requires=">=3.7",
    install_requires=[
        "pandas >= 1.1.0",
        "PyYAML >= 5.3.1",
        "requests >= 2.24.0"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering",
    ],
)
