from setuptools import setup, find_packages

setup(
    name="ai-assistant",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "typer",
        "rich",
        "python-multipart",
        "pydantic",
        "langchain",
        "faiss-cpu",
        "torch",
        "transformers",
        "python-dotenv",
        "aiohttp",
        "structlog",
        "redis",
        "dependency-injector"
    ],
    python_requires=">=3.9",
) 