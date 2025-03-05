fedi_dmri_moco - Command Help
=================================

**Usage:**

.. code-block:: bash


     Fetal and Neonatal Development Imaging - FEDI Toolbox


USAGE: 

    fedi_dmri_moco [-h] -d <file> -a <file> -e <file> -o
                                     <file> [-m <file>]

Motion correction of diffusion MRI data.

HELP:
  -h, --help            show this help message and exit

Mandatory Arguments:
  -d, --dmri <file>     Path to the diffusion MRI file.
  -a, --bval <file>     Path to the b-values file.
  -e, --bvec <file>     Path to the b-vectors file.
  -o, --output_dir <file>
                        Output directory path.

Optional Arguments:
  -m, --mask <file>     Path to the mask file (required for GMM weighting).

References:
Snoussi, H., Karimi, D., Afacan, O., Utkur, M., and Gholipour, A., 2024. Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI. arXiv preprint arXiv:2406.20042.

