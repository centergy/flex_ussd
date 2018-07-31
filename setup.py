import setuptools


with open("README.md", "r") as fh:
	long_description = fh.read()


setuptools.setup(
	name="flex_ussd",
	version="0.0.1",
	author="David Kyalo",
	author_email="davidmkyalo@gmail.com",
	description="A USSD application framework",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/pypa/sampleproject",
	packages=setuptools.find_packages(),
	classifiers=(
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
)