from setuptools import setup, find_packages

setup(
    name="md2db",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pandas>=2.0.0",
        "sqlalchemy>=2.0.0",
        "markdown>=3.4.0",
        "pillow>=10.0.0",
        "python-multipart>=0.0.6",
    ],
    python_requires=">=3.8",
)