from setuptools import setup, find_packages

extras_require = {
    "docs": [
        "sphinx",
        "sphinx_rtd_theme",
    ],
}

with open("app/requirements.txt", "r") as f:
    app = []
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            # Ignore comments and empty lines
            package = line.split("==")[0]  # Get the package name
            app.append(package)
    extras_require["app"] = app


extras_require["all"] = []
for k, v in extras_require.items():
    if k not in ("all", "docs"):
        extras_require["all"].extend(v)


setup(
    name="frankenmsa",
    version="0.1.3",
    description="FrankenMSA is a package for protein design and folding",
    author="Noah Kleinschmidt, Jannik Gut, Thommas Lemmin",
    author_email="noah.kleinschmidt@unibe.ch, jannik.gut@unibe.ch, thommas.lemmin@unibe.ch",
    url="https://github.com/ibmm-unibe-ch/frankenmsa",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pathlib",
        "pandas",
        "loguru",
        "requests",
        "scikit-learn",
        "scipy",
        "afcluster>=0.1.2",
        "pybiolib",
        "dash",
        "dash_bio",
        "GitPython",
        "pymsaviz",
        "matplotlib",
        "plotly",
        "dash-bootstrap-components",
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
