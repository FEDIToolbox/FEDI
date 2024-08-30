

from setuptools import setup, find_packages

setup(
    name='fedi',
    version='0.1',
    packages=find_packages(include=['FEDI', 'FEDI.*']),
    install_requires=[
        'numpy',
        'scipy',
        'nibabel',
        'matplotlib',
        'dipy',
        'cvxpy',
        # Add other dependencies here
    ],
    entry_points={
        'console_scripts': [
            'fedi_dmri_outliers=FEDI.scripts.fedi_dmri_outliers:main',
            'fedi_dmri_rotate_bvecs=FEDI.scripts.fedi_dmri_rotate_bvecs:main',
            'fedi_dmri_snr=FEDI.scripts.fedi_dmri_snr:main',
        ],
    },
)
