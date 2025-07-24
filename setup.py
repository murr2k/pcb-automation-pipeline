from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pcb-automation-pipeline",
    version="0.1.0",
    author="PCB Automation Team",
    author_email="murr2k@gmail.com",
    description="Automated PCB design pipeline from schematic to ordering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/murr2k/pcb-automation-pipeline",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "click>=8.1.0",
        "jsonschema>=4.0.0",
        "Pillow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pcb-pipeline=pcb_pipeline.cli:main",
        ],
    },
)