#!/usr/bin/env python3.10

##########################################################################
##                                                                      ##
##  Part of Fetal and Neonatal Development Imaging Toolbox (FEDI)       ##
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
import numpy.matlib as matlib
import math

# Matplotlib setup for non-interactive backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Import functions from Dipy and SciPy
from scipy import stats
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti, save_nifti

from FEDI.utils.common import FEDI_ArgumentParser, Metavar


parser = argparse.ArgumentParser(
    description="Motion correction of diffusion MRI data.",
    epilog=(
        "References:\n"
        "Snoussi, H., Karimi, D., Afacan, O., Utkur, M., and Gholipour, A., 2024. "
        "Haitch: A framework for distortion and motion correction in fetal multi-shell "
        "diffusion-weighted MRI. arXiv preprint arXiv:2406.20042."
    ),
    formatter_class=FEDI_ArgumentParser
)

# Mandatory arguments
mandatory_args = parser.add_argument_group("Mandatory Arguments")

mandatory_args.add_argument("-d", "--dmri", required=True, metavar=Metavar.file, help="Path to the diffusion MRI file.")
mandatory_args.add_argument("-a", "--bval", required=True, metavar=Metavar.file, help="Path to the b-values file.")
mandatory_args.add_argument("-e", "--bvec", required=True, metavar=Metavar.file, help="Path to the b-vectors file.")
mandatory_args.add_argument("-o", "--output_dir", required=True, metavar=Metavar.file, help="Output directory path.")

# Optional arguments
optional_args = parser.add_argument_group("Optional Arguments")
optional_args.add_argument("-m", "--mask", required=False, metavar=Metavar.file, help="Path to the mask file (required for GMM weighting).")

# Parse the command-line arguments
args = parser.parse_args()

# Define constants
raw_working_dmri = args.dmri
epochs = 6
iter_registration = [1, 2, 3, 4]
reg_update = 0
reg_counter = 0
bvec_ste_in = args.bvec

for iteration in range(epochs):
    prev_iteration = iteration - 1

    subprocess.run([
        "fedi_dmri_outliers",
        "--dmri", args.dmri,
        "--dmrigmm", args.dmri,  # Assuming WORKING_DMRI_GMM = dmri
        "--bval", args.bval,
        "--bvec", args.bvec,
        "--outpath", args.output_dir,
        "--fsliceweights_mzscore", f"fsliceweights_mzscore_{iteration}.txt",
        "--fsliceweights_angle_neighbors", f"fsliceweights_angle_neighbors_{iteration}.txt",
        "--fsliceweights_corre_neighbors", f"fsliceweights_corre_neighbors_{iteration}.txt",
        "--fsliceweights_gmmodel", f"fsliceweights_gmmodel_{iteration}.txt",
        "--fvoxelweights_shorebased", f"fvoxelweights_shore_{iteration}.nii.gz",
        "--spred", os.path.join(args.output_dir, f"spred{prev_iteration}.nii.gz"),
        "--spredgmm", args.output_dir,  # Assuming SPRED_GMM = output_dir
        "--mask", args.mask if args.mask else "",
        "--maskgmm", args.mask if args.mask else ""
    ], check=True)

    # Select weighting method
    if iteration == 0:  # Initialization
        shore_weighting = os.path.join(args.output_dir, f"fsliceweights_mzscore_{iteration}.txt")
        print("Modified Z-score (slice-wise) weights will be used.")

    elif iteration == 15:  # Finalization (Not used in current implementation)
        subprocess.run([
            "fedi_apply_applytransform",
            "--weights4D", os.path.join(args.output_dir, "fsliceweights_gmmodel_1.nii.gz"),
            "--workpath", os.path.join(args.output_dir, "registration_gmm"),
            "--transformspath", os.path.join(args.output_dir, "registration_working"),
            "--weights4Dreg", os.path.join(args.output_dir, "fsliceweights_gmmodel_1_reg.nii.gz")
        ], check=True)

        shore_weighting = os.path.join(args.output_dir, "fsliceweights_gmmodel_1_reg.nii.gz")
        print("Shore-based (voxel-wise) weights will be used.")

    elif iteration == 18:  # Not used
        shore_weighting = os.path.join(args.output_dir, f"fvoxelweights_shore_{iteration}.nii.gz")
        print("Shore-based (voxel-wise) weights will be used.")

    else:
        shore_weighting = os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iteration}.txt")
        print("GMM (slice-wise) weights will be used.")

    print("=" * 120)
    
    # SHORE fitting
    subprocess.run([
        "fedi_dmri_recon",
        "--dmri", args.dmri,
        "--bval", args.bval,
        "--bvec_in", bvec_ste_in,
        "--bvec_out", args.bvec,
        "--mask", args.mask if args.mask else "",
        "--weights", shore_weighting,
        "--fspred", os.path.join(args.output_dir, f"spred{iteration}.nii.gz"),
        "-do_not_use_mask"
    ], check=True)

    # Ensure that bvec_in is updated to match bvec_out after reconstruction
    bvec_ste_in = args.bvec

    print("=" * 120)
    
    # Registration of original data to SHORE-predicted data at specific iterations
    if iteration in iter_registration:
        print(f"Starting Registration: {iteration}")

        reg_counter += 1
        reg_working_path = os.path.join(args.output_dir, f"registration_iter{reg_counter}")

        # Volume-to-volume registration
        subprocess.run([
            "fedi_dmri_registration",
            "--rdmri", raw_working_dmri,
            "--spred", os.path.join(args.output_dir, f"spred{iteration}.nii.gz"),
            "--workingpath", reg_working_path,
            "--rdmrireg", os.path.join(args.output_dir, f"working_updated{reg_update}.nii.gz")
        ], check=True)

        # Rotate b-vectors per volume
        bvec_ste_rot = os.path.join(args.output_dir, f"rotated_bvecs{reg_update}")
        subprocess.run([
            "fedi_dmri_rotate_bvecs",
            "--bvecs", args.bvec,
            "--bvecsnew", bvec_ste_rot,
            "--pathofmatfile", reg_working_path,
            "--startprefix", "Transform_v",
            "--endprefix", "_0GenericAffine.mat"
        ], check=True)

        raw_working_dmri = os.path.join(args.output_dir, f"working_updated{reg_update}.nii.gz")
        bvec_ste_in = bvec_ste_rot
        reg_update += 1
