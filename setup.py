from setuptools import setup, find_packages

setup(
    name="ptirtools",
    version="0.5.0",
    description="PTIR Tools",
    author="Felix H. Patzschke",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[
        "h5py>=3.14",
        "numpy>=2.2",
        "scipy>=1.15",
        "matplotlib>=3.10",
        "colorama"
    ]
)