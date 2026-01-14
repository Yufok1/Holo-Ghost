"""
HOLO-GHOST Setup
"""

from setuptools import setup, find_packages

setup(
    name="holo-ghost",
    version="0.1.0",
    description="The Digital Holy Ghost - System-agnostic input observer & intelligence layer",
    author="Glass Box Games",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pynput>=1.7.0",
        "openai>=1.0.0",
        "psutil>=5.9.0",
        "pyyaml>=6.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "click>=8.0.0",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "recording": [
            "mss>=9.0.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
        ],
        "llm": [
            "vllm>=0.4.0",
        ],
        "windows": [
            "pywin32>=306",
            "keyboard>=0.13.5",
            "mouse>=0.7.1",
        ],
        "full": [
            "mss>=9.0.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
            "vllm>=0.4.0",
            "pywin32>=306",
            "keyboard>=0.13.5",
            "mouse>=0.7.1",
            "fastapi>=0.109.0",
            "uvicorn>=0.27.0",
            "websockets>=12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "holo-ghost=holo_ghost.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
