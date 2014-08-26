import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

setup (
    name='ztq_worker',
    version='1.2.9',
    author = "xutaozhe",
    author_email = "xutaozhe@zopen.cn",
    description=u"Zopen Task Queue Worker",
    long_description=README + '\n\n' +  CHANGES,
    license = "MIT",
    keywords='Everydo queue async ztq_worker',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        ],
    packages = ['ztq_worker'],
    #package_dir={'ztq_worker': 'ztq_worker'},
    #package_data={'ztq_worker': ['system_info/*.vbs'] },
    data_files=[('config', ['worker.ini']),],
    include_package_data = True,
    install_requires = [
        "ztq_core",
        ],
    entry_points = """\
      [console_scripts]
      ztq_worker = ztq_worker.main:run
      """,
    zip_safe = False,
)
