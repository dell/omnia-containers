from setuptools import setup
setup(name='xcclient',
      version='1.0',
      description='xCAT Python Utilities',
      packages=['xcclient', 'xcclient.inventory'],
      package_data={'xcclient': ['inventory/*.yaml']},
      scripts=['cli/xcat-inventory']
      )
