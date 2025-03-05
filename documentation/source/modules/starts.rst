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

---

Diffusion MRI
-------------

- **`fedi_dmri_moco`**: Corrects motion artifacts in diffusion MRI.  

  .. literalinclude:: help_outputs/fedi_dmri_moco.txt
     :language: bash

- **`fedi_dmri_reg`**: Performs image registration on dMRI data.  

  .. literalinclude:: help_outputs/fedi_dmri_reg.txt
     :language: bash

- **`fedi_dmri_recon`**: Computes diffusion signal reconstruction.  

  .. literalinclude:: help_outputs/fedi_dmri_recon.txt
     :language: bash

- **`fedi_dmri_qweights`**: Applies data weighting for q-shell dMRI acquisitions.  

  .. literalinclude:: help_outputs/fedi_dmri_qweights.txt
     :language: bash

- **`fedi_dmri_rotate_bvecs`**: Rotates b-vectors to match transformations.  

  .. literalinclude:: help_outputs/fedi_dmri_rotate_bvecs.txt
     :language: bash

- **`fedi_dmri_outliers`**: Identifies and removes outliers from dMRI datasets.  

  .. literalinclude:: help_outputs/fedi_dmri_outliers.txt
     :language: bash

- **`fedi_dmri_snr`**: Computes the signal-to-noise ratio (SNR) of dMRI data.  

  .. literalinclude:: help_outputs/fedi_dmri_snr.txt
     :language: bash

---

Miscellaneous
-------------

- **`fedi_apply_transform`**: Applies affine or nonlinear transformations to MRI data.  

  .. literalinclude:: help_outputs/fedi_apply_transform.txt
     :language: bash

---

Segmentation and Others
-----------------------

*(Coming Soon.)*
