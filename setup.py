from setuptools import find_packages
from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='fmc_rest_client',
      version='0.1',
      description='FMC REST API Client',
      long_description=readme(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Security',
          'Topic :: System :: Networking :: Firewalls',
          'Topic :: System :: Security Administration'
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
