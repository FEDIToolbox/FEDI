from setuptools import setup, find_packages

setup(
    name='fedi',
    version='0.1.33',
    packages=find_packages(include=['FEDI', 'FEDI.*']),
    install_requires=[
        'numpy',
        'scipy',
        'nibabel',
        'matplotlib',
        'dipy',
        'cvxpy',
        'healpy',
        'huggingface_hub',
        'torch'
    ],
    entry_points={
        'console_scripts': [
            'fedi_dmri_outliers=FEDI.scripts.fedi_dmri_outliers:main',
            'fedi_dmri_rotate_bvecs=FEDI.scripts.fedi_dmri_rotate_bvecs:main',
            'fedi_dmri_snr=FEDI.scripts.fedi_dmri_snr:main',
            'fedi_dmri_qweights=FEDI.scripts.fedi_dmri_qweights:main',
            'fedi_apply_transform=FEDI.scripts.fedi_apply_transform:main',
            'fedi_dmri_reg=FEDI.scripts.fedi_dmri_reg:main',
            'fedi_dmri_recon=FEDI.scripts.fedi_dmri_recon:main',
            'fedi_dmri_moco=FEDI.scripts.fedi_dmri_moco:main',
            'fedi_dmri_fod=FEDI.scripts.fedi_dmri_fod:main'

        ],
    },
    python_requires='>=3.7',  # Adjust according to your requirements
    package_data={
        'FEDI': [
            'Sampling_Scheme/*.dvs',
            'models/pytorch/**/*.py',
            'models/common/*.py',
            'pipelines/HAITCH/*.py',
        ],
    },
    test_suite='tests',
    license='MIT',
    author='Haykel Snoussi',
    author_email='dr.haykel.snoussi@gmail.com',
    long_description=open('documentation/README.rst').read(),
    long_description_content_type='text/x-rst',
    include_package_data=True
)
