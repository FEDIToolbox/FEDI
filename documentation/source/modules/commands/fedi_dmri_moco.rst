.. _fedi_dmri_fod:

fedi_dmri_fod
=============

Synopsis
--------

FOD estimation for neonatal dMRI using a pretrained Spherical CNN model.


Usage
-----

::

    fedi_dmri_fod [-h] -d <file> -a <file> -e <file> -o <file> [-m <file>]

Options
-------

**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-d, --dmri <file>**  
   Path to the input dMRI file

-  **-a, --bval <file>**  
   Path to the b-values file

-  **-e, --bvec <file>**  
   Path to the b-vectors file

-  **-o, --out <file>**  
   Output filename (NIfTI format)

**Optional**

-  **-m, --mask <file>**  
   Path to brain mask file

References
----------

Snoussi, H. and Karimi, D., 2025.  
*Equivariant Spherical CNNs for Accurate Fiber Orientation Distribution Estimation in Neonatal Diffusion MRI with Reduced Acquisition Time.*  
arXiv preprint [arXiv:2504.01925](https://arxiv.org/abs/2504.01925)
