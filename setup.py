from setuptools import setup, find_packages


def main():
    setup(
        name='kamatis',
        description='Pomodoro timer',
        packages=find_packages('.'),
        entry_points={
            'console_scripts': [
                'kamatis=kamatis.app:main',
                ],
            },
        )


if __name__ == "__main__":
    main()
