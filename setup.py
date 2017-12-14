from setuptools import setup, find_packages
from codecs import open
from os import path
import catcli

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

VERSION = catcli.__version__

setup(
    name='catcli',
    version=VERSION,

    description='The command line catalog tool for your offline data',
    long_description=long_description,
    url='https://github.com/deadc0de6/catcli',
    download_url = 'https://github.com/deadc0de6/catcli/archive/v'+VERSION+'.tar.gz',

    author='deadc0de6',
    author_email='deadc0de6@foo.bar',

    license='GPLv3',
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          ],

    keywords='catalog commandline indexer offline',
    packages=find_packages(exclude=['tests*']),
    install_requires=['docopt', 'anytree','psutil'],

    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },

    entry_points={
        'console_scripts': [
            'catcli=catcli:main',
        ],
    },
)
