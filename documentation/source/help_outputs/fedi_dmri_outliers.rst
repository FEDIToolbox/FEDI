fedi_dmri_outliers - Command Help
=================================

**Usage:**

.. code-block:: bash


     Fetal and Neonatal Development Imaging - FEDI Toolbox


USAGE: 

    fedi_dmri_outliers [-h] -d <file> -b <file> -a <file> -e
                                         <file> -o <file> [-s <file>]
                                         [-f <file>] [-m <file>] [-k <file>]
                                         [-t <list>] [-c <str>] [-l <str>]
                                         [-z <file>] [-n <file>] [-y <file>]
                                         [-g <file>] [-r <file>]

DESCRIPTION: 

    Volume, slice and voxel weighting and outlier detection using many methods: SOLID, Gaussian Mixture Model (GMM), SHORE-based, Angular, and Correlation metrics with neighbors.

HELP:
  -h, --help            show this help message and exit

MANDATORY OPTIONS:
  -d, --dmri <file>     Path to dMRI file
  -b, --dmrigmm <file>  Path to dMRI file for GMM
  -a, --bval <file>     Path to bval file
  -e, --bvec <file>     Path to bvec file
  -o, --outpath <file>  Output directory path

OPTIONAL OPTIONS:
  -s, --spred <file>    Path to spred file
  -f, --spredgmm <file>
                        Path to spred file for GMM
  -m, --mask <file>     Path to mask file, required for GMM weighting
  -k, --maskgmm <file>  Path to mask file, required for GMM weighting
  -t, --thresholds <list>
                        Lower and upper modified Z-score thresholds as 'lower,upper'
  -c, --zscoremetric <str>
                        Modified Z-Score metric: var, mean, or iod
  -l, --scalingmethod <str>
                        Scaling method for slice weights: linear or sigmoid
  -z, --fsliceweights_mzscore <file>
                        Filename for sliceweights using modified Z-score
  -n, --fsliceweights_angle_neighbors <file>
                        Filename for sliceweights using angle with neighbors
  -y, --fsliceweights_corre_neighbors <file>
                        Filename for sliceweights using correlation with neighbors
  -g, --fsliceweights_gmmodel <file>
                        Filename for sliceweights using Gaussian mixture model (GMM)
  -r, --fvoxelweights_shorebased <file>
                        Filename.nii.gz (4D)  for voxelweights using shore-based residuals

REFERENCES:
  Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2024. Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI. arXiv preprint arXiv:2406.20042.

