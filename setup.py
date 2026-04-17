from setuptools import setup, find_packages
import os

# Membaca isi file requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as req:
        # Abaikan baris kosong atau baris komentar
        return [line.strip() for line in req if line.strip() and not line.startswith('#')]

# Membaca README untuk long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="poros-one",
    version="1.0.0",
    author="AI Architect & Lead Programmer",
    description="Poros One: Autonomous Continuous Learning AI Agent with Dual-Node Soul Synchronization.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/poros-one",
    packages=find_packages(include=["poros_one", "poros_one.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "poros=poros_one.cli:main",
        ],
    },
)