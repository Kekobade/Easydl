from setuptools import setup, find_packages

setup(
    name="easydl",
    version="2.4.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "yt-dlp>=2024.0.0",
        "spotdl>=4.2.0",
    ],
    entry_points={
        "console_scripts": [
            "easydl = easydl.cli:main",
        ],
    },
)
