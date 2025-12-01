.. _fedi_dmri_outliers:

fedi_dmri_outliers
==================

.. rubric:: Synopsis
Volume, slice and voxel weighting and outlier detection using multiple methods:  
SOLID, Gaussian Mixture Model (GMM), SHORE-based, angular, and correlation with neighbors.

.. rubric:: Usage
::

    fedi_dmri_outliers [-h] -d <file> -b <file> -a <file> -e <file> -o <file>
                       [-s <file>] [-f <file>] [-m <file>] [-k <file>]
                       [-t <list>] [-c <str>] [-l <str>] [-z <file>]
                       [-n <file>] [-y <file>] [-g <file>] [-r <file>]

.. rubric:: Options
**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-d, --dmri <file>**  
   Path to dMRI file

-  **-b, --dmrigmm <file>**  
   Path to dMRI file for GMM

-  **-a, --bval <file>**  
   Path to bval file

-  **-e, --bvec <file>**  
   Path to bvec file

-  **-o, --outpath <file>**  
   Output directory path

**Optional**

-  **-s, --spred <file>**  
   Path to spred file

-  **-f, --spredgmm <file>**  
   Path to spred file for GMM

-  **-m, --mask <file>**  
   Path to mask file, required for GMM weighting

-  **-k, --maskgmm <file>**  
   Path to mask file, required for GMM weighting

-  **-t, --thresholds <list>**  
   Lower and upper modified Z-score thresholds as 'lower,upper'

-  **-c, --zscoremetric <str>**  
   Modified Z-score metric: `var`, `mean`, or `iod`

-  **-l, --scalingmethod <str>**  
   Scaling method for slice weights: `linear` or `sigmoid`

-  **-z, --fsliceweights_mzscore <file>**  
   Output filename for slice weights using modified Z-score

-  **-n, --fsliceweights_angle_neighbors <file>**  
   Output filename for slice weights using angular comparison with neighbors

-  **-y, --fsliceweights_corre_neighbors <file>**  
   Output filename for slice weights using correlation with neighbors

-  **-g, --fsliceweights_gmmodel <file>**  
   Output filename for slice weights using Gaussian Mixture Model (GMM)

-  **-r, --fvoxelweights_shorebased <file>**  
   Output 4D `.nii.gz` file of voxel weights using SHORE-based residuals

.. rubric:: References
Snoussi, Haykel, Davood Karimi, Onur Afacan, Mustafa Utkur, and Ali Gholipour.  
*HAITCH: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience 2025.
