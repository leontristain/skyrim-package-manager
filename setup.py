from setuptools import setup, find_packages

setup(name='skyrim-package-manager',
      packages=find_packages(exclude=['test']),
      version='0.1',
      description='skyrim package manager',
      author='leontristain',
      keywords=[],
      classifiers=[],
      setup_requires=[],
      install_requires=[],
      tests_require=['pytest==4.3.0'],
      test_suite='test',
      entry_points='''
          [console_scripts]
          skypackages=skypackages.cli.skypackages:cli
      ''')
