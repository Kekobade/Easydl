from setuptools import setup, find_packages

setup(
    name="easydl",
    version="2.2.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "yt-dlp>=2024.0.0",
    ],
    entry_points={
        "console_scripts": [
            "easydl = easydl.cli:main",
        ],
    },
)
