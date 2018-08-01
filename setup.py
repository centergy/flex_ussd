from setuptools import setup, find_packages


with open("README.md", "r") as fh:
	long_description = fh.read()


setup(
	name="FlexUssd",
	version="0.0.0",
	author="David Kyalo",
	author_email="davidmkyalo@gmail.com",
	description="USSD application framework",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/centergy/flex_ussd",
	packages=find_packages(include=['flex.*']),
	install_requires=[
		'Werkzeug',
	],
	classifiers=(
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
)