fedi_dmri_snr - Command Help
=================================

**Usage:**

.. code-block:: bash


     Fetal and Neonatal Development Imaging - FEDI Toolbox


USAGE: 

    fedi_dmri_snr [-h] -d <file> -a <file> -m <file>
                                    [-b <file>]

DESCRIPTION: 

    This function computes the Signal-to-Noise Ratio (SNR) for diffusion MRI.

HELP:
  -h, --help         show this help message and exit

MANDATORY OPTIONS:
  -d, --dmri <file>  Input dMRI NIfTI image. Example: dmri.nii.gz
  -a, --bval <file>  Bvals file. Example: bvals.txt
  -m, --mask <file>  Binary mask within which SNR will be averaged. Example: brain_mask.nii.gz

OPTIONAL OPTIONS:
  -b, --bvec <file>  Bvecs file. Example: bvecs.txt

REFERENCES:
  Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2024. Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI. arXiv preprint arXiv:2406.20042.

