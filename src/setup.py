"""
    https://packaging.python.org/distributing/
    https://pypi.python.org/pypi?%3Aaction=list_classifiers
    http://semver.org/

    zero or more dev releases (denoted with a ”.devN” suffix)
    zero or more alpha releases (denoted with a ”.aN” suffix)
    zero or more beta releases (denoted with a ”.bN” suffix)
    zero or more release candidates (denoted with a ”.rcN” suffix)
"""

from setuptools import setup, find_packages

setup(name='ingreso',
          version='1.0.2.a2',
          description='Proyecto que implementa la api de ingreso',
          url='https://github.com/pablodanielrey/ingreso-api',
          author='Desarrollo DiTeSi, FCE',
          author_email='ditesi@econo.unlp.edu.ar',
          classifiers=[
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 3 - Alpha',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6'
          ],
          packages=find_packages(exclude=['contrib', 'docs', 'test*']),
          install_requires=['psycopg2',
                            'dateutils>=0.6.6',
                            'requests',
                            'redis==2.10.6',
                            'SQLAlchemy',
                            'httplib2',
                            'pyjwt',
                            'Flask',
                            'flask_jsontools',
                            'jinja2',
                            'gunicorn',
                            'microservices_common>=2.0.4a4',
                            'warden-api',
                            'ptvsd',
                            'google-api-python-client',
                            'oauth2client'],
          entry_points={
            'console_scripts': [
                'rest=ingreso.api.rest.main:main'
            ]
          }

      )
