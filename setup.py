from setuptools import setup, find_packages

setup(
    name="pytenable-was",
    version="0.1.0",
    description="A clean, modular Python client for the Tenable Web Application Scanning (WAS) v2 API.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "requests>=2.20.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "pytenable-was=pytenable_was.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
