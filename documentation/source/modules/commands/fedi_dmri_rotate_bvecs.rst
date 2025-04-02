.. _fedi_dmri_rotate_bvecs:

fedi_dmri_rotate_bvecs
=======================

Synopsis
--------

Rotate the bvecs accordingly with a list of ANTs transformation matrices.

Usage
-----

::

    fedi_dmri_rotate_bvecs [-h] -e <file> -n <file> -m <folder>
                           [-s <str>] [-d <str>]

Options
-------

**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-e, --bvecs <file>**  
   Path to the input bvecs file (e.g., `bvecs`)

-  **-n, --robvecs <file>**  
   Path to the output rotated bvecs file (e.g., `rotated_bvecs`)

-  **-m, --pathofmatfile <folder>**  
   Path to the directory containing transformation matrices

**Optional**

-  **-s, --prefix <str>**  
   Prefix for transformation matrix files (default: `'Transform_v'`)

-  **-d, --suffix <str>**  
   Suffix for transformation matrix files (default: `'_0GenericAffine.mat'`).  
   Each matrix file is expected to follow the naming: `prefix + volume_index + suffix`

References
----------

Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
*Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience.
