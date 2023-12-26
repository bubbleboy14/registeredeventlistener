#from rel.version import __version__
from setuptools import setup

setup(
    name='rel',
    version='0.4.9.2',
    author='Mario Balibrera',
    author_email='mario.balibrera@gmail.com',
    license='MIT License',
    description='Registered Event Listener. Provides standard (pyevent) interface and functionality without external dependencies',
    long_description='Select preferred event notification methods with initialize([methods in order of preference]). If initialize(...) is not called, methods are tried in default order: pyevent,epoll,poll,kqueue,select.',
    packages=[
        'rel',
    ],
    zip_safe = False,
    entry_points = '''
        [console_scripts]
        rtimer = rel.tools:timerCLI
    ''',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
