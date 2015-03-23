import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['pyramid', 'WebError', 'pyramid_jinja2','ztq_core' ]

setup(name='ztq_console',
      version='1.2.5',
      description='Zopen Task Queue Console',
      long_description=README + '\n\n' +  CHANGES,
      license = "MIT",
      author='edo',
      author_email="service@everydo.com",
      url="http://everydo.com/",
      keywords='Everydo queue monitor console async',
      packages=['ztq_console'],
      package_dir={'ztq_console': 'ztq_console'},
      package_data={'ztq_console': ['templates/*.html', 
                                  'static/*.js', 
                                  'static/*.css', 
                                  'static/images/*.gif', 
                                  'static/images/*.jpg',
                                  'utils/*.py',
                                  ]},
      data_files=[('config', ['app.ini']),],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="ztq_console",
      classifiers = [
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Topic :: Internet :: WWW/HTTP',
          'Framework :: Pyramid',
          ],
      entry_points = """\
      [paste.app_factory]
      main = ztq_console:main
      """,
      paster_plugins=['pyramid'],
      )

