from setuptools import setup, find_packages

extras_require = {
    "cluster": [
        "afcluster>=0.1.2",
    ],
    "filter": [
        "hh-suite",
    ],
    "torch": [
        "torch",
    ],
    "docs": [
        "sphinx",
        "sphinx_rtd_theme",
    ],
}
extras_require["all"] = []
for k, v in extras_require.items():
    if k not in ("all", "docs"):
        extras_require["all"].extend(v)


setup(
    name="frankenmsa",
    version="0.1.2",
    description="FrankenMSA is a package for protein design and folding",
    author="Jannik Gut, Noah Kleinschmidt, Thommas Lemmin",
    author_email="jannik.gut@unibe.ch, noah.kleinschmidt@unibe.ch, thommas.lemmin@unibe.ch",
    url="https://github.com/ibmm-unibe-ch/frankenmsa",
    packages=find_packages(),
    install_requires=[
        # Add your project dependencies here
        "numpy",
        "pathlib",
        "pandas",
        "loguru",
        "requests",
        "scikit-learn",
        "scipy",
    ],
    extras_require=extras_require,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Protein Design",
    ],
    python_requires=">=3.8",
)
