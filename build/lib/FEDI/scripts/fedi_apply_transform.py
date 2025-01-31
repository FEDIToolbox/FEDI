#!/usr/bin/env python3.10

##########################################################################
##                                                                      ##
##  Part of Fetal and Neonatal Development Imaging Toolbox (FEDI)       ##
##                                                                      ##
##                                                                      ##
##  Author:    Haykel Snoussi, PhD (dr.haykel.snoussi@gmail.com)        ##
##             IMAGINE Group | Computational Radiology Laboratory       ##
##             Boston Children's Hospital | Harvard Medical School      ##
##                                                                      ##
##########################################################################

import argparse
import numpy as np
import os
import subprocess
from dipy.io.image import load_nifti, save_nifti

# Define utility function
def apply_transform(input_file, output_file, transform_file, reference_file=None, mask_file=None, force=False):
    """
    Apply a transformation to the input image.

    Parameters:
    - input_file: str, path to the input image.
    - output_file: str, path to save the transformed image.
    - transform_file: str, path to the transformation matrix/warp.
    - reference_file: str, path to the reference image (optional).
    - mask_file: str, path to the binary mask (optional).
    - force: bool, whether to overwrite existing files.
    """
    command = [
        "antsApplyTransforms",
        "--dimensionality", "3",
        "--input", input_file,
        "--output", output_file,
        "--transform", transform_file
    ]

    if reference_file:
        command.extend(["--reference-image", reference_file])

    if mask_file:
        command.extend(["--mask", mask_file])

    if force:
        command.append("--overwrite")

    try:
        subprocess.run(command, check=True)
        print(f"Transformation applied successfully. Output saved to {output_file}.")
    except subprocess.CalledProcessError as e:
        print(f"Error during transformation: {e}")
        raise

# Main execution
def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m \n\n    "
            "Apply affine or nonlinear transformations to dMRI data."
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Snoussi, H., et al., 2024. Haitch: A framework for distortion and "
            "motion correction in fetal multi-shell diffusion-weighted MRI. "
            "arXiv preprint arXiv:2406.20042."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Mandatory arguments
    mandatory = parser.add_argument_group('\033[1mMANDATORY OPTIONS\033[0m')
    mandatory.add_argument("-i", "--input", required=True, help="Path to the input dMRI file.")
    mandatory.add_argument("-o", "--output", required=True, help="Path to save the transformed dMRI file.")
    mandatory.add_argument("-t", "--transform", required=True, help="Path to the transformation matrix or warp file.")

    # Optional arguments
    optional = parser.add_argument_group('\033[1mOPTIONAL OPTIONS\033[0m')
    optional.add_argument("-r", "--reference", required=False, help="Path to the reference image for transformation.")
    optional.add_argument("-m", "--mask", required=False, help="Path to a binary mask to apply during transformation.")
    optional.add_argument("-f", "--force", action="store_true", help="Force overwrite of output files.")

    args = parser.parse_args()

    apply_transform(
        input_file=args.input,
        output_file=args.output,
        transform_file=args.transform,
        reference_file=args.reference,
        mask_file=args.mask,
        force=args.force
    )

if __name__ == "__main__":
    main()
