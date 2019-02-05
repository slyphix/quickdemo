import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="quickdemo",
    version="0.0.3",
    author="Justus 'slyphiX' Henneberg",
    author_email="slyphiX@users.noreply.github.com",
    description="Small Python library for quick prototyping and code demonstrations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/slyphiX/quickdemo",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Education",
        "License :: Free For Educational Use",
        "License :: Free For Home Use",
        "Operating System :: OS Independent",
    ],
)
