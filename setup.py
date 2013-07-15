import setuptools

from savannadashboard.openstack.common import setup as common_setup

requires = common_setup.parse_requirements()
depend_links = common_setup.parse_dependency_links()
project = 'savanna-dashboard'

setuptools.setup(
    name=project,
    version=common_setup.get_version(project, '0.2'),
    description='The Savanna dashboard',
    author='OpenStack',
    author_email='openstack-dev@lists.openstack.org',
    url='https://savanna.readthedocs.org',
    classifiers=[
        'Environment :: OpenStack',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    license='Apache Software License',
    cmdclass=common_setup.get_cmdclass(),
    packages=setuptools.find_packages(exclude=['bin']),
    package_data={'savannadashboard': [
        '*.html',
    ]},
    install_requires=requires,
    dependency_links=depend_links,
    setup_requires=['setuptools-git>=0.4'],
    include_package_data=True,
    test_suite='nose.collector',
    py_modules=[],
)
