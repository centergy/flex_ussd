from setuptools import setup, find_packages_ns


with open("README.md", "r") as fh:
	long_description = fh.read()


setup(
	name="Flex-Ussd",
	version="0.0.0dev1",
	author="David Kyalo",
	author_email="davidmkyalo@gmail.com",
	description="USSD application framework",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/pypa/sampleproject",
	packages=find_packages_ns(),
	classifiers=(
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
)