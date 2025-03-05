fedi_dmri_rotate_bvecs - Command Help
=================================

**Usage:**

.. code-block:: bash


     Fetal and Neonatal Development Imaging - FEDI Toolbox


USAGE: 

    fedi_dmri_rotate_bvecs [-h] -e <file> -n <file> -m
                                             <folder> [-s <str>] [-d <str>]

DESCRIPTION: 

    Rotate the bvec accordingly with a list of ANTs transformation matrices.

HELP:
  -h, --help            show this help message and exit

MANDATORY OPTIONS:
  -e, --bvecs <file>    Path to the input bvecs file. Example: bvecs
  -n, --robvecs <file>  Path to the output rotated bvecs file. Example: rotated_bvecs.
  -m, --pathofmatfile <folder>
                        Path to the directory containing transformation matrices.
  -s, --prefix <str>    Prefix for transformation matrix files (default: 'Transform_v').
  -d, --suffix <str>    Suffix for transformation matrix files (default: '_0GenericAffine.mat'). Name of matrice should prefix+volume_index+suffix

REFERENCES:
  Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2024. Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI. arXiv preprint arXiv:2406.20042.

