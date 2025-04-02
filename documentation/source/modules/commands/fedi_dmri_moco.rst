.. _fedi_dmri_moco:

fedi_dmri_moco
==============

Synopsis
--------

Motion correction of diffusion MRI data.

Usage
-----

::

    fedi_dmri_moco [-h] -d <file> -a <file> -e <file> -o <file> [-m <file>]

Options
-------

**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-d, --dmri <file>**  
   Path to the diffusion MRI file

-  **-a, --bval <file>**  
   Path to the b-values file

-  **-e, --bvec <file>**  
   Path to the b-vectors file

-  **-o, --output_dir <file>**  
   Output directory path

**Optional**

-  **-m, --mask <file>**  
   Path to the mask file (required for GMM weighting)

References
----------

Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
*Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience.
