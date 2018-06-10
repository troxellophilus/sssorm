from setuptools import find_packages, setup


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="sssorm",
    version="1.0.0",
    author="Drew Troxell",
    author_email="code@trox.space",
    description="Somewhat small sqlite3 object relational mapping for Python.",
    license="MIT",
    keywords="sssorm python sqlite3 orm",
    url="https://gitlab.com/dtrox/sssorm",
    install_requires=[],
    packages=find_packages(),
    long_description=long_description,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
