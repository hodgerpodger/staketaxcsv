
from setuptools import find_packages, setup

with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='staketaxcsv',
    version='0.0.1',
    install_requires=required,
    packages=find_packages(),
)
