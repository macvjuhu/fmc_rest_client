from setuptools import find_packages
from setuptools import setup
from os import path
import sys

def readme():
    if sys.version_info[0] == 3:
        current_dir = path.abspath(path.dirname(__file__))
        with open(path.join(current_dir, 'README.rst'), encoding='utf-8') as f:
            return f.read()
    else:
        return 'Needs python >= 3'


setup(
    name='fmc_rest_client',
    version='0.5.4',
    python_requires='>=3',
    description='FMC REST API Client',
    long_description=readme(),

    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Security',
        'Topic :: System :: Networking :: Firewalls',
    ],
    keywords='firepower management rest-api',
    url='https://github.com/macvjuhu/fmc_rest_client',
    author='Vikas Sharma',
    author_email='macvjuhu@yahoo.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'requests'
    ],
    include_package_data=True,
    zip_safe=False)
