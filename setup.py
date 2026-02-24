import os
import pkg_resources
from setuptools import setup, find_packages

setup(
    name="clip-interrogator-average",
    version="0.6.1",
    author='seedmanc',
    author_email='seedmanc@yahoo.com',
    url='https://github.com/seedmanc/clip-interrogator-average',
    description="Generate an average prompt for a set of images",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        str(r)
        for r in pkg_resources.parse_requirements(
            open(os.path.join(os.path.dirname(__file__), "requirements.txt"))
        )
    ],
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Education',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    keywords=['blip','clip','prompt-engineering','stable-diffusion','text-to-image'],
)
