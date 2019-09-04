#!/usr/bin/env python

from setuptools import setup

setup(name='run_and_monitorize',
      version='1.0',
      description='Euclid Process Runner and Monitor',
      author='Francesc Torradeflot',
      author_email='torradeflot@pic.es',
      packages=['var_monitor'],
      scripts=['scripts/run_and_monitorize'],
      data_files=[('run_and_monitorize', ['conf/run_and_monitorize.cfg'])],
      install_requires=['psutil>=5.2.0',
                        'numpy>=1.11.1',
                        'matplotlib>=2.0.0',
                        'pandas>=0.16.2']
     )