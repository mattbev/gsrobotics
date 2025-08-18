"""
PyPI build file
"""

import setuptools

setuptools.setup(
    name="gsrobotics",
    version="0.1.0",
    install_requires=[
        "numpy",
        "scipy>=1.13.0",
        "opencv-python",
        "pygrabber",
        "scikit-image>=0.24.0",
        "torch==2.6.0",
        "ffmpeg-python"
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
