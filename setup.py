"""setup.py"""
from os import path
from setuptools import setup, find_packages
from catcli import version

README = 'README.md'
here = path.abspath(path.dirname(__file__))
VERSION = version.__version__
REQUIRES_PYTHON = '>=3'


def read_readme(readme_path):
    """read readme content"""
    with open(readme_path, encoding="utf-8") as file:
        return file.read()


URL = f'https://github.com/deadc0de6/catcli/archive/v{VERSION}.tar.gz'
setup(
    name='catcli',
    version=VERSION,

    description='The command line catalog tool for your offline data',
    long_description=read_readme(README),
    long_description_content_type='text/markdown',
    license_files=('LICENSE',),
    url='https://github.com/deadc0de6/catcli',
    download_url=URL,
    options={"bdist_wheel": {"python_tag": "py3"}},
    # include anything from MANIFEST.in
    include_package_data=True,

    author='deadc0de6',
    author_email='deadc0de6@foo.bar',

    license='GPLv3',
    python_requires=REQUIRES_PYTHON,
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          ],

    keywords='catalog commandline indexer offline',
    packages=find_packages(exclude=['tests*']),
    install_requires=['docopt', 'anytree',
                      'types-docopt', 'pyfzf',
                      'fusepy'],

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
