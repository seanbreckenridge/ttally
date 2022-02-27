from pathlib import Path
from setuptools import setup, find_packages

long_description = Path("README.md").read_text()
reqs = Path("requirements.txt").read_text().strip().splitlines()

pkg = "ttally"
setup(
    name=pkg,
    version="0.1.0",
    url="https://github.com/seanbreckenridge/ttally",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=(
        """interactive module to generate code/aliases to save things I do often"""
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(include=[pkg]),
    install_requires=reqs,
    package_data={pkg: ["py.typed"]},
    entry_points={"console_scripts": ["ttally = ttally.__main__:main"]},
    scripts=[str(f) for f in Path("bin").iterdir()],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
