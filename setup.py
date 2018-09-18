from setuptools import setup
from os import path


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'requirements.txt')) as fd:
    install_requirements = fd.read().splitlines()

setup(
    install_requires=install_requirements,
)
