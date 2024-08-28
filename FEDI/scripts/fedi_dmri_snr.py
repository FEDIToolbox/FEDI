#!/usr/bin/env python3.10

import nibabel as nib
import numpy as np
from scipy.ndimage import binary_erosion
import argparse

from FEDI.utils.common import FEDI_ArgumentParser, Metavar


def compute_snr(dmri_file, bval_file, mask_file=None):
    """
    Compute the Signal-to-Noise Ratio (SNR) for diffusion MRI data.

    Parameters:
    - dmri_file: str, path to the dMRI NIfTI file
    - bval_file: str, path to the bvals file
    - mask_file: str, optional, path to the binary mask NIfTI file

    Returns:
    - SNR: float, the computed SNR value
    - SNR_std: float, the standard deviation of the SNR
    """
    if mask_file:
        mask = binary_erosion(nib.load(mask_file).get_fdata().astype(bool), iterations=3)
    else:
        raise ValueError("A binary mask file is required.")

    bvals = np.loadtxt(bval_file)
    dmri_data = nib.load(dmri_file).get_fdata()

    b0_indices = np.where(bvals == 0)[0]
    b0_data = dmri_data[mask][:, b0_indices]

    normalized_b0_data = b0_data / np.nanmean(b0_data, axis=1)[:, np.newaxis]
    concatenated_b0_data = normalized_b0_data

    SNRs = 1 / np.nanstd(concatenated_b0_data, axis=1)
    SNR_mean = np.round(SNRs.mean(), 1)
    SNR_std = np.round(SNR_std := SNRs.std(), 1)

    return SNR_mean, SNR_std

def main():
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m \n\n    "
            "This function computes the Signal-to-Noise Ratio (SNR) for diffusion MRI.\n"
            "\n"
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2024. "
            "Haitch: A framework for distortion and motion correction in fetal multi-shell "
            "diffusion-weighted MRI. arXiv preprint arXiv:2406.20042."
        ),
        formatter_class=FEDI_ArgumentParser
    )

    # Mandatory arguments
    mandatory = parser.add_argument_group('\033[1mMANDATORY OPTIONS\033[0m')
    mandatory.add_argument("-d", "--dmri", required=True, metavar=Metavar.file, help="Input dMRI NIfTI image. Example: dmri.nii.gz")
    mandatory.add_argument("-a", "--bval", required=True, metavar=Metavar.file, help="Bvals file. Example: bvals.txt")
    mandatory.add_argument("-m", "--mask", required=True, metavar=Metavar.file, help="Binary mask within which SNR will be averaged. Example: brain_mask.nii.gz")

    # Optional arguments
    optional = parser.add_argument_group('\033[1mOPTIONAL OPTIONS\033[0m')
    optional.add_argument("-b", "--bvec", required=False,  metavar=Metavar.file, help="Bvecs file. Example: bvecs.txt")


    args = parser.parse_args()

    try:
        snr_mean, snr_std = compute_snr(args.dmri, args.bval, args.mask)
        print(f"SNR = {snr_mean.astype(int)} ± {snr_std.astype(int)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
