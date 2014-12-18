"""
Flask-Goat
-------------

Flask-Goat is a plugin for to support security and user administration via GitHub OAuth and organization structure. The plugin assumes membership in an organization as a basic requirement for authorization. User privilege level can be determined from team membership. A request context is built to support these concepts and can be used by endpoints. The plugin is intended to implemented via the 'before_request' handler.
"""

from setuptools import setup


setup(
    name='Flask-Goat',
    version='0.1',
    url='http://incontextsolutions.github.io/flask-goat/',
    license='MIT',
    author='Tristan Wietsma',
    author_email='tristan.wietsma@incontextsolutions.com',
    description='Flask plugin for security and user administration via GitHub OAuth & organization',
    long_description=__doc__,
    packages=['flask_goat'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    tests_requires=[
        'coverage',
        'nose',
        'httmock',
        'pep8',
        'pyflakes',
    ],
    install_requires=[
        'Flask',
        'redis',
        'simplejson',
        'requests',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
