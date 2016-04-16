from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

version = {}
with open('impositioner/version.py') as f:
    exec(f.read(), version)

setup(
    name='impositioner',
    version=version['__version__'],
    description='Impose PDF file for booklet printing',
    long_description=readme,
    author='sgelb',
    url='https://github.com/sgelb/impositioner',
    license=license,
    packages=find_packages(exclude=('tests')),
    install_requires=[
        "pdfrw>=0.2",
    ],
    tests_require=['pytest', 'pytest-cov'],
    entry_points={
        'console_scripts': [
            'impositioner = impositioner.cli:main',
        ],
    },
)
