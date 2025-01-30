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
import time
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti, save_nifti
from dipy.core.gradients import gradient_table
from dipy.reconst.brainsuite_shore import BrainSuiteShoreModel as ShoreModel
from dipy.reconst.brainsuite_shore import brainsuite_shore_basis as shore_matrix

# Main execution
def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m \n\n    "
            "Continuous and analytical diffusion signal reconstruction with 3D-SHORE."
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Snoussi, H., et al., 2024. Haitch: A framework for distortion and "
            "motion correction in fetal multi-shell diffusion-weighted MRI. "
            "arXiv preprint arXiv:2406.20042."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-d", "--dmri", required=True, help="Path to the input dMRI file.")
    parser.add_argument("-a", "--bval", required=True, help="Path to the bval file.")
    parser.add_argument("-e", "--bvec_in", required=True, help="Path to the input bvec file.")
    parser.add_argument("-u", "--bvec_out", required=True, help="Path to the output bvec file.")
    parser.add_argument("-m", "--mask", required=False, help="Path to the mask file to reduce computation time.")
    parser.add_argument("--do_not_use_mask", action="store_true", help="Flag to ignore the mask, even if provided.")
    parser.add_argument("-w", "--weights", required=False, help="Path to the weights file (txt or nifti).")
    parser.add_argument("-s", "--fspred", required=True, help="Path to save the reconstructed dMRI file.")

    args = parser.parse_args()

    # Initialize SHORE parameters
    zeta = 700
    tau = 1 / (4 * np.pi**2)
    lambdaN = 1e-8
    lambdaL = 1e-8
    S0 = 1

    # Load data
    dmri, affine = load_nifti(args.dmri)
    mask = None
    if not args.do_not_use_mask and args.mask:
        mask, _ = load_nifti(args.mask)
    else:
        mask = np.ones(dmri.shape[:3], dtype=np.uint8)

    dmri[dmri < 0] = 0  # Set negative values to 0

    # Load gradients and weights
    bvals, bvecs_in = read_bvals_bvecs(args.bval, args.bvec_in)
    _, bvecs_out = read_bvals_bvecs(args.bval, args.bvec_out)

    gtab_in = gradient_table(bvals, bvecs_in, b0_threshold=0)
    gtab_out = gradient_table(bvals, bvecs_out, b0_threshold=0)

    if args.weights.endswith('.txt'):
        weights = np.loadtxt(args.weights, delimiter=',')
        fitting_method = "slice"
    elif args.weights.endswith('.nii.gz'):
        weights, _ = load_nifti(args.weights)
        fitting_method = "voxel"
    else:
        raise ValueError("Unsupported weights file format.")

    weights = np.clip(weights * 1.5, 0, 1)

    # Determine radial order based on the number of gradients
    if dmri.shape[3] > 50:
        radial_order = 6
    elif dmri.shape[3] > 24:
        radial_order = 4
    elif dmri.shape[3] > 12:
        radial_order = 2
    else:
        raise ValueError("Insufficient gradient directions for SHORE fitting.")

    # Initialize the predicted 4D array
    spred4D = np.zeros_like(dmri)

    print("Starting SHORE Reconstruction with method:", fitting_method)
    start_time = time.time()

    for slice_idx in range(dmri.shape[2]):
        print(f"Processing slice {slice_idx + 1}/{dmri.shape[2]}.")

        if fitting_method == "slice":
            dmri_slice = dmri[:, :, slice_idx, :]
            mask_slice = mask[:, :, slice_idx]
            mask_slice[0, 0] = 1  # Avoid issues with SHORE optimization
            weights_slice = np.diag(np.sqrt(weights[slice_idx, :]))

            shore_model = ShoreModel(
                gtab_in,
                radial_order=radial_order,
                zeta=zeta,
                lambdaN=lambdaN,
                lambdaL=lambdaL,
                regularization="FEDI",
                weights=weights_slice
            )
            shore_fit = shore_model.fit(dmri_slice, mask_slice)
            shore_basis = shore_matrix(radial_order, zeta, gtab_out, tau)
            spred4D[:, :, slice_idx, :] = S0 * np.dot(shore_fit.shore_coeff, shore_basis.T)

        elif fitting_method == "voxel":
            for i in range(dmri.shape[0]):
                for j in range(dmri.shape[1]):
                    if not mask[i, j, slice_idx]:
                        continue

                    dmri_voxel = dmri[i, j, slice_idx, :]
                    weights_voxel = np.diag(weights[i, j, slice_idx, :])

                    shore_model = ShoreModel(
                        gtab_in,
                        radial_order=radial_order,
                        zeta=zeta,
                        lambdaN=lambdaN,
                        lambdaL=lambdaL,
                        regularization="FEDI",
                        weights=weights_voxel
                    )
                    shore_fit = shore_model.fit(dmri_voxel)
                    shore_basis = shore_matrix(radial_order, zeta, gtab_out, tau)
                    spred4D[i, j, slice_idx, :] = S0 * np.dot(shore_fit.shore_coeff, shore_basis.T)

    end_time = time.time()
    print(f"SHORE Reconstruction completed in {end_time - start_time:.2f} seconds.")

    # Save the predicted diffusion signal
    save_nifti(args.fspred, spred4D, affine)
    print(f"Predicted dMRI signal saved to {args.fspred}.")

if __name__ == "__main__":
    main()
