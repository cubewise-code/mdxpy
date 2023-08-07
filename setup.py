from setuptools import setup, find_packages

DESCRIPTION = open('readme.md').read()

setup(
    name="mdxpy",
    version='1.3.2',
    maintainer='Marius Wirtz',
    maintainer_email='MWirtz@cubewise.com',
    license="MIT-LICENSE",
    url='https://github.com/cubewise-code/mdxpy',
    platforms=["any"],
    description="A simple, yet elegant MDX library for TM1",
    long_description=DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=["mdxpy"],
    include_package_data=False,
    keywords=['MDX', 'TM1', 'IBM Cognos TM1', 'Planning Analytics', 'PA', 'Cognos'],
    tests_require=['pytest'],
    python_requires='>=3.5',
    install_requires=[],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
