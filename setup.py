from setuptools import setup, find_packages

setup(
    name="ai-assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "ollama>=0.1.0",
        "typer[all]>=0.9.0",
    ],
    python_requires=">=3.11",
) 