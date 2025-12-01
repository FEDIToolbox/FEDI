FEDI Command-Line Tools
=======================

FEDI provides a suite of command-line tools for processing and analyzing **fetal and neonatal MRI data**.  
Each module name follows a **consistent naming convention**, starting with ``fedi_``, followed by the **MRI modality** (e.g., ``t1w``, ``t2w``, ``dmri``, ``fmri``) and a **descriptive method name**.

To list all available FEDI commands in your terminal, use:

.. code-block:: bash

   fedi_<TAB>

To view help for a specific tool, use the ``--help`` option:

.. code-block:: bash

   fedi_dmri_moco --help

The tools are categorized below for easier navigation.

.. toctree::
    :hidden:

    commands/fedi_dmri_outliers.rst
    commands/fedi_dmri_qweights.rst
    commands/fedi_dmri_recon.rst
    commands/fedi_dmri_moco.rst
    commands/fedi_apply_transform.rst
    commands/fedi_dmri_snr.rst
    commands/fedi_dmri_rotate_bvecs.rst
    commands/fedi_dmri_reg.rst
    commands/fedi_dmri_fod.rst
    commands/fedi_testing.rst


.. rubric:: Diffusion MRI

- :ref:`fedi_dmri_moco`: Corrects motion artifacts in diffusion MRI.  
- :ref:`fedi_dmri_reg`: Performs image registration on dMRI data.  
- :ref:`fedi_dmri_qweights`: Converts diffusion gradient scheme into Siemens-compatible format.  
- :ref:`fedi_dmri_rotate_bvecs`: Rotates b-vectors to match ANTs transformations.  
- :ref:`fedi_dmri_outliers`: Identifies and weights outliers (volume, slice, voxel) in dMRI data.  
- :ref:`fedi_dmri_snr`: Computes the signal-to-noise ratio (SNR) of dMRI data.  
- :ref:`fedi_dmri_recon`: Reconstructs the diffusion signal using 3D-SHORE.
- :ref:`fedi_dmri_fod`: estimates FODs for neonatal dMRI using a pretrained Spherical CNN model.

.. rubric:: Miscellaneous

- :ref:`fedi_apply_transform`: Applies affine or nonlinear transformations to MRI data.  
- :ref:`fedi_testing`: Generates test data and runs automated tests for all FEDI command-line tools.  


.. rubric:: Segmentation and Others

*(Coming Soon.)*
