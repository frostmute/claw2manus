from setuptools import setup, find_packages

setup(
    name='claw2manus',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'PyYAML',
        'markdown',
        'requests',
        'beautifulsoup4',
    ],
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'claw2manus = claw2manus.cli:main',
        ],
    },
    author='frostmute',
    author_email='frostmute@users.noreply.github.com',
    description='A tool to convert ClawHub (OpenClaw) SKILL.md skills into Manus-compatible skills.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/frostmute/claw2manus',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
