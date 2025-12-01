.. _fedi_dmri_moco:

fedi_dmri_moco
==============

.. rubric:: Synopsis
Motion correction of diffusion MRI data using an iterative pipeline with outlier detection, SHORE fitting, registration, and b-vector rotation.

.. rubric:: Usage
::

    fedi_dmri_moco [-h] -d <file> -a <file> -e <file> -o <file> [-m <file>]

.. rubric:: Options
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

.. rubric:: References
Snoussi, Haykel, Davood Karimi, Onur Afacan, Mustafa Utkur, and Ali Gholipour.  
*HAITCH: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience 2025.
