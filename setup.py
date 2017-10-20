from setuptools import setup, find_packages

try:
    with open('README.md') as f:
        readme = f.read()
except IOError:
    readme = ''

setup(
    name='ngdl',
    version='0.1.3',
    author='Mitsuo Heijo',
    author_email='mitsuo_h@outlook.com',
    description='HTTP/2 parallel downloading client for Python',
    long_description=readme,
    packages=find_packages(),
    license='MIT',
    url='http://github.com/johejo/ngdl',
    py_modules=['ngdl'],
    keywords=['HTTP', 'HTTP/2', 'http/2', 'http-client', 'multi-http'],
    install_requires=[
        'hyper>=0.7.0',
        'requests>=2.18.4'
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ]
)
