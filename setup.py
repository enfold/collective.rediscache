from setuptools import setup, find_packages

setup(name='collective.rediscache',
      version='0.2.0',
      url='http://pypi.python.org/pypi/collective.rediscache',
      license='ZPL 2.1',
      description="Redis cache manager for Zope 2.",
      author='Plone Foundation and Contributors',
      author_email='zope-dev@zope.org',
      long_description=(open('README.md').read() + '\n' +
                        open('CHANGES.rst').read()),
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      classifiers=[
          "Environment :: Web Environment",
          "Framework :: Zope2",
          "License :: OSI Approved :: Zope Public License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: Implementation :: CPython",
      ],
      install_requires=[
          'setuptools',
          'six',
          'AccessControl',
          'transaction',
          'Zope2',
          'zope.component',
          'redis',
          'dogpile.cache',
      ],
      include_package_data=True,
      zip_safe=False,
      entry_points="""
          # -*- Entry points: -*-
          [z3c.autoinclude.plugin]
          target = plone
      """
      )
