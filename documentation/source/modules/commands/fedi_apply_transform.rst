.. _fedi_apply_transform:

fedi_apply_transform
====================

.. rubric:: Synopsis
Apply affine or nonlinear transformations to dMRI data.

.. rubric:: Usage
::

    fedi_apply_transform [-h] -i INPUT -o OUTPUT -t TRANSFORM
                         [-r REFERENCE] [-m MASK] [-f]

.. rubric:: Options
**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-i, --input INPUT**  
   Path to the input dMRI file

-  **-o, --output OUTPUT**  
   Path to save the transformed dMRI file

-  **-t, --transform TRANSFORM**  
   Path to the transformation matrix or warp file

**Optional**

-  **-r, --reference REFERENCE**  
   Path to the reference image for transformation

-  **-m, --mask MASK**  
   Path to a binary mask to apply during transformation

-  **-f, --force**  
   Force overwrite of output files (default: False)

.. rubric:: References
Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
*Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience.
