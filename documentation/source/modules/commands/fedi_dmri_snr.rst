.. _fedi_dmri_snr:

fedi_dmri_snr
=============

Synopsis
--------

Compute the Signal-to-Noise Ratio (SNR) for diffusion MRI.

Usage
-----

::

    fedi_dmri_snr [-h] -d <file> -a <file> -m <file> [-b <file>]

Options
-------

**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-d, --dmri <file>**  
   Input dMRI NIfTI image (e.g., `dmri.nii.gz`)

-  **-a, --bval <file>**  
   Bvals file (e.g., `bvals.txt`)

-  **-m, --mask <file>**  
   Binary mask within which SNR will be averaged (e.g., `brain_mask.nii.gz`)

**Optional**

-  **-b, --bvec <file>**  
   Bvecs file (e.g., `bvecs.txt`)

References
----------

Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
*Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience.
