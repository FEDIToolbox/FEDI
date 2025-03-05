fedi_dmri_reg - Command Help
=================================

**Usage:**

.. code-block:: bash

usage: fedi_dmri_reg [-h] --input_dmri INPUT_DMRI --target_dmri TARGET_DMRI
                     --output_dir OUTPUT_DIR --output_dmri OUTPUT_DMRI

DESCRIPTION: Perform volume-by-volume registration of 4D diffusion MRI
data using ANTs.

options:
  -h, --help            show this help message and exit
  --input_dmri INPUT_DMRI
                        Path to the 4D input diffusion MRI file. (default:
                        None)
  --target_dmri TARGET_DMRI
                        Path to the 4D target diffusion MRI file. (default:
                        None)
  --output_dir OUTPUT_DIR
                        Directory for intermediate and output files. (default:
                        None)
  --output_dmri OUTPUT_DMRI
                        Filename for the registered diffusion MRI output.
                        (default: None)

REFERENCES: Snoussi, H., et al., 2024. Haitch: A framework for
distortion and motion correction in fetal multi-shell diffusion-weighted MRI.
arXiv preprint arXiv:2406.20042.

