from setuptools import setup

setup(
    name='rel',
    version='0.4.9.15',
    author='Mario Balibrera',
    author_email='mario.balibrera@gmail.com',
    license='MIT License',
    description='Registered Event Listener. Provides standard (pyevent) interface and functionality without external dependencies',
    long_description='Registered Event Listener (rel) is a cross-platform asynchronous event dispatcher primarily designed for network applications. Select your preferred event notification methods with initialize([methods in order of preference]). If initialize(...) is not called, methods are tried in the default order: epoll, kqueue, poll, select, pyevent. Code and docs live on github: https://github.com/bubbleboy14/registeredeventlistener',
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
