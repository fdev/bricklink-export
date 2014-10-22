import os
from setuptools import setup, find_packages

description = "BrickLink wanted list export."
cur_dir = os.path.dirname(__file__)
try:
	long_description = open(os.path.join(cur_dir, 'README.md')).read()
except:
	long_description = description

setup(
	name = "bricklink-export",
	version = "1.0",
	url = 'http://github.com/fdev/bricklink-export/',
	license = 'GPL2',
	description = description,
	long_description = long_description,
	author = 'Folkert de Vries',
	author_email = 'bricklink-export@fdev.nl',
	packages = find_packages('src'),
	package_dir = {'': 'src'},
	install_requires = ['requests', 'pyquery'],
	entry_points="""
	[console_scripts]
	bricklink-export = bricklink_export:main
	""",
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
		'Operating System :: MacOS :: MacOS X',
		'Operating System :: Unix',
		'Operating System :: POSIX',
		'Programming Language :: Python',
		'Topic :: Games/Entertainment',
		'Topic :: Utilities',
	]
)
