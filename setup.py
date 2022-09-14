import re

from setuptools import find_packages, setup

with open('requirements.txt') as f:
    required = f.read().splitlines()


PACKAGE_NAME = "staketaxcsv"
SOURCE_DIRECTORY = "src"

source_packages = find_packages()
source_package_regex = re.compile(f"^{SOURCE_DIRECTORY}")
project_packages = [source_package_regex.sub(PACKAGE_NAME, name) for name in source_packages]


setup(
    name=PACKAGE_NAME,
    version='0.0.1',
    install_requires=required,
    package_dir={PACKAGE_NAME: SOURCE_DIRECTORY},
    packages=project_packages,
)
