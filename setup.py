from setuptools import setup, find_packages

setup(
    name="lazytag",
    version="0.1.0",
    description="CLI tool to append Jira-style tags to modified source code lines",
    author="Sebastian Rodriguez (semarova)",
    author_email="sebastian@apostrofo.com",
    packages=find_packages(),
    py_modules=["lazytag", "core", "installer"],
    entry_points={
        "console_scripts": [
            "lazytag = lazytag:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    include_package_data=True,
)