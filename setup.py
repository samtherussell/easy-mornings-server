from setuptools import setup, find_packages

setup(name='easy_mornings_server',
      version='0.1',
      package_dir={'': 'source'},
      packages=find_packages('source'),
      install_requires=['bottle', 'pigpio', 'attrs'],
     )
