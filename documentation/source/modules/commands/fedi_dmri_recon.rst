.. _fedi_dmri_recon:

fedi_dmri_recon
===============

.. rubric:: Synopsis
Continuous and analytical diffusion signal reconstruction with 3D-SHORE.

.. rubric:: Usage
::

    fedi_dmri_recon [-h] -d <file> -a <file> -e <file> -u <file> -s <file>
                    [-m <file>] [--do_not_use_mask] [-w <file>]

.. rubric:: Options
**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-d, --dmri <file>**  
   Path to the input dMRI file

-  **-a, --bval <file>**  
   Path to the bval file

-  **-e, --bvec_in <file>**  
   Path to the input bvec file

-  **-u, --bvec_out <file>**  
   Path to the output bvec file

-  **-s, --fspred <file>**  
   Path to save the reconstructed dMRI file

**Optional**

-  **-m, --mask <file>**  
   Path to the mask file to reduce computation time

-  **--do_not_use_mask**  
   Ignore the mask even if provided

-  **-w, --weights <file>**  
   Path to the weights file (TXT or NIfTI)

.. rubric:: References
Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
*Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience.
