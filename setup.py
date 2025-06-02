from setuptools import setup, find_packages

setup(
    name="betarxiv",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "psycopg",
        "python-dotenv",
        "ollama",
        "pydantic",
    ],
    python_requires=">=3.8",
)
