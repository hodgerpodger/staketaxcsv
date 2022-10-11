import re

from setuptools import find_packages, setup

with open('requirements.txt') as f:
    required = f.read().splitlines()


PACKAGE_NAME = "staketaxcsv"
SOURCE_DIRECTORY = "src/staketaxcsv"

setup(
    name=PACKAGE_NAME,
    version='0.0.1',
    install_requires=required,
    package_dir={PACKAGE_NAME: SOURCE_DIRECTORY},
    packages=["staketaxcsv"],
    include_package_data=True,
)
