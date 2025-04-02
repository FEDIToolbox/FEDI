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




.. csv-table::
    :header: "Command", "Synopsis"

    :ref:`fedi_dmri_outliers`, "Weighting and outlier detection using: SOLID, GMM, SHORE-based, Angular, and Correlation with neighbors."
    :ref:`fedi_dmri_qweights`, "Process diffusion MRI scheme and generate Siemens scanner compatible output."










---

Diffusion MRI
-------------

- **`fedi_dmri_moco`**: Corrects motion artifacts in diffusion MRI.  

  .. include:: ../help_outputs/fedi_dmri_moco.txt

- **`fedi_dmri_reg`**: Performs image registration on dMRI data.  

  .. include:: ../help_outputs/fedi_dmri_reg.txt

- **`fedi_dmri_qweights`**: Converts dMRI scheme into a Siemens scanner-compatible format.  

  .. include:: ../help_outputs/fedi_dmri_qweights.txt

- **`fedi_dmri_rotate_bvecs`**: Rotates b-vectors to match transformations.  

  .. include:: ../help_outputs/fedi_dmri_rotate_bvecs.txt

- **`fedi_dmri_outliers`**: Identifies and weights outliers (volume, slice, and voxel) in dMRI data.  

  .. include:: ../help_outputs/fedi_dmri_outliers.txt

- **`fedi_dmri_snr`**: Computes the signal-to-noise ratio (SNR) of dMRI data.  

  .. include:: ../help_outputs/fedi_dmri_snr.txt

---

Miscellaneous
-------------

- **`fedi_apply_transform`**: Applies affine or nonlinear transformations to MRI data.  

  .. include:: ../help_outputs/fedi_apply_transform.txt

---

Segmentation and Others
-----------------------

*(Coming Soon.)*
