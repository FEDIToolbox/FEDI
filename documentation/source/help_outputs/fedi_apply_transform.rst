fedi_apply_transform - Command Help
=================================

**Usage:**

.. code-block:: bash

usage: fedi_apply_transform [-h] -i INPUT -o OUTPUT -t TRANSFORM
                            [-r REFERENCE] [-m MASK] [-f]

DESCRIPTION: Apply affine or nonlinear transformations to dMRI data.

options:
  -h, --help            show this help message and exit

MANDATORY OPTIONS:
  -i INPUT, --input INPUT
                        Path to the input dMRI file. (default: None)
  -o OUTPUT, --output OUTPUT
                        Path to save the transformed dMRI file. (default:
                        None)
  -t TRANSFORM, --transform TRANSFORM
                        Path to the transformation matrix or warp file.
                        (default: None)

OPTIONAL OPTIONS:
  -r REFERENCE, --reference REFERENCE
                        Path to the reference image for transformation.
                        (default: None)
  -m MASK, --mask MASK  Path to a binary mask to apply during transformation.
                        (default: None)
  -f, --force           Force overwrite of output files. (default: False)

REFERENCES: Snoussi, H., et al., 2024. Haitch: A framework for
distortion and motion correction in fetal multi-shell diffusion-weighted MRI.
arXiv preprint arXiv:2406.20042.

