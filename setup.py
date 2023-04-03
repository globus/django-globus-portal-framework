import os.path
from setuptools import setup, find_namespace_packages


# single source of truth for package version
version_ns = {}
with open(os.path.join('globus_portal_framework', 'version.py')) as f:
    exec(f.read(), version_ns)

install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)


setup(name='django-globus-portal-framework',
      version=version_ns['__version__'],
      description='A framework for collating Globus Search data for use with '
                  'various Globus services. ',
      long_description=open('README.rst').read(),
      long_description_content_type='text/x-rst',
      python=">=3.7",
      author='Globus Team',
      author_email='support@globus.org',
      url='https://github.com/globus/django-globus-portal-framework',
      packages=find_namespace_packages(include=['globus_portal_framework*']),
      install_requires=install_requires,
      include_package_data=True,
      keywords=['globus', 'django'],
      license='apache 2.0',
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Topic :: Communications :: File Sharing',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      )
