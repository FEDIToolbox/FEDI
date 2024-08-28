from setuptools import setup

setup(
    name='FEDI',
    version='0.1',
    packages=['FEDI'],
    install_requires=[
        # List your dependencies here
    ],
    entry_points={
        'console_scripts': [
            'fedi_dmri_snr=FEDI.scripts.fedi_dmri_snr:main',
            'another_tool=FEDI.scripts.another_tool:main',
        ],
    },
)
