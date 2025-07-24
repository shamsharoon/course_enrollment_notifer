from setuptools import setup, find_packages
import os

setup(
    name="course-availability-notifier",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Monitor university course availability and send SMS notifications",
    long_description=open("README.md").read() if os.path.exists("README.md") else "Monitor university course availability and send SMS notifications",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "selenium>=4.15.0",
        "beautifulsoup4>=4.12.0",
        "twilio>=8.10.0",
        "APScheduler>=3.10.0",
        "python-dotenv>=1.0.0",
        "lxml>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "course-notifier=main:main",
        ],
    },
) 