from setuptools import (
    find_packages,
    setup,
    )
from textwrap import dedent
import os
import re


with open(os.path.join('kamatis', '__init__.py'), 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

long_desc = '''\
    Kamatis is a Pomodoro Technique timer written in PyQt5. Features include:

    - customizable work, short break, and long break periods
    - sound and desktop notifications
    - app control through the tray icon on supported desktop environments
    - remaining time indication
    '''


def main():
    setup(
        name='kamatis',
        version=version,
        author='Luis Manuel R. Pugoy',
        author_email='luipugs@gmail.com',
        maintainer='Luis Manuel R. Pugoy',
        maintainer_email='luipugs@gmail.com',
        url='https://github.com/luipugs/kamatis/',
        description='Pomodoro Technique timer',
        long_description=dedent(long_desc).strip(),
        classifiers=(
            'Development Status :: 3 - Alpha',
            'Environment :: X11 Applications :: Qt',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: BSD License',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            ),
        license='BSD',
        packages=find_packages('.'),
        entry_points={
            'console_scripts': [
                'kamatis=kamatis.app:main',
                ],
            },
        )


if __name__ == "__main__":
    main()
