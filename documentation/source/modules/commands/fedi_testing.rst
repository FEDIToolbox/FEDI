.. _fedi_testing:

fedi_testing
============

.. rubric:: Synopsis
Generates synthetic NIfTI MRI test data and automatically tests all FEDI command-line tools to verify correct installation and functionality.

.. rubric:: Usage
::

    fedi_testing

    or

    python -m FEDI.scripts.fedi_testing_commands

.. rubric:: Description

The ``fedi_testing`` command performs two main functions:

1. **Generates synthetic test data**: Creates realistic 4D diffusion MRI data with fixed parameters:
   - Shape: (64, 64, 30, 100)
   - b-values: b=0 (x10), [400, 1000, 2600]
   - Directions per shell: [30, 30, 30]
   - SNR: 20.0
   
   Test data is saved to ``~/.fedi_test_data/`` (user's home directory).

2. **Runs automated tests**: Tests all FEDI command-line tools and verifies:
   - Command execution success
   - Expected output file generation
   - Proper error handling

This tool is useful for:
- Verifying FEDI installation is correct
- Testing that all dependencies are properly configured
- Ensuring command-line tools function as expected
- Debugging installation issues

.. rubric:: Test Coverage

The automated test suite includes tests for:

- :ref:`fedi_dmri_snr`: Signal-to-noise ratio computation
- :ref:`fedi_dmri_outliers`: Outlier detection and weighting
- :ref:`fedi_dmri_recon`: 3D-SHORE reconstruction
- :ref:`fedi_dmri_rotate_bvecs`: B-vector rotation
- :ref:`fedi_dmri_qweights`: Gradient scheme conversion
- :ref:`fedi_dmri_reg`: Image registration
- :ref:`fedi_apply_transform`: Transform application
- :ref:`fedi_dmri_fod`: FOD estimation (requires PyTorch and Hugging Face Hub)
- :ref:`fedi_dmri_moco`: Motion correction pipeline (requires MRtrix3 and ANTs)

Some tests may be skipped if required dependencies are not available.

.. rubric:: Output

The command provides detailed output including:

- Test data generation progress
- Individual test execution results
- File verification status
- Final test summary with pass/fail/skip counts

.. rubric:: Notes

- Test data generation may take a few minutes depending on system performance
- Some tests (especially ``fedi_dmri_moco``) may take several minutes to complete
- Tests require sufficient disk space in your home directory for test data
- Missing dependencies will result in skipped tests rather than failures

