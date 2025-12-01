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
import os
import subprocess

from FEDI.utils.common import FEDI_ArgumentParser, Metavar


def main():
    parser = argparse.ArgumentParser(
        description="Motion correction of diffusion MRI data.",
        epilog=(
            "References:\n"
            "Snoussi, Haykel, Davood Karimi, Onur Afacan, Mustafa Utkur, and Ali Gholipour. "
            "HAITCH: A framework for distortion and motion correction in fetal multi-shell "
            "diffusion-weighted MRI. Imaging Neuroscience 2025."
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

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Define constants (matching bash variable names)
    raw_working_dmri = args.dmri  # RAWWORKING_DMRI - original input, never changes
    working_dmri = args.dmri  # WORKING_DMRI - gets updated after registration
    working_dmri_gmm = args.dmri  # WORKING_DMRI_GMM
    epochs = 6
    iter_registration = [1, 2, 3, 4]  # ITER_REG
    reg_update = 0
    reg_counter = 0
    bvec_ste_in = args.bvec  # BVECSTEIN - gets updated after registration/reconstruction
    bvec_ste = args.bvec  # BVECSTE - original bvec, doesn't change

    # Main iteration loop
    for iteration in range(epochs):
        prev_iteration = iteration - 1  # ITERM

        print(f"\n{'='*120}")
        print(f"Iteration {iteration}/{epochs-1}")
        print(f"{'='*120}\n")

        # Build outliers command
        outliers_cmd = [
            "fedi_dmri_outliers",
            "--dmri", working_dmri,
            "--dmrigmm", working_dmri_gmm,
            "--bval", args.bval,
            "--bvec", bvec_ste,
            "--outpath", args.output_dir,
            "--fsliceweights_mzscore", f"fsliceweights_mzscore_{iteration}.txt",
            "--fsliceweights_angle_neighbors", f"fsliceweights_angle_neighbors_{iteration}.txt",
            "--fsliceweights_corre_neighbors", f"fsliceweights_corre_neighbors_{iteration}.txt",
            "--fsliceweights_gmmodel", f"fsliceweights_gmmodel_{iteration}.txt",
            "--fvoxelweights_shorebased", f"fvoxelweights_shore_{iteration}.nii.gz",
            "--spredgmm", args.output_dir,
        ]
        
        # Add spred only if prev_iteration >= 0 (not for iteration 0)
        if prev_iteration >= 0:
            outliers_cmd.extend(["--spred", os.path.join(args.output_dir, f"spred{prev_iteration}.nii.gz")])
        
        # Add mask arguments only if mask is provided
        if args.mask:
            outliers_cmd.extend([
                "--mask", args.mask,
                "--maskgmm", args.mask
            ])
        
        subprocess.run(outliers_cmd, check=True)

        print("=" * 120)
        # Select weighting method
        if iteration == 0:  # Initialization
            shore_weighting = os.path.join(args.output_dir, f"fsliceweights_mzscore_{iteration}.txt")
            print("Modified Z-score (slice-wise) weights will be used.")
        elif iteration == 98:  # Final iteration - alternative option (not used in epochs=6)
            iter_special = 1
            subprocess.run([
                "fedi_apply_transform",
                "-i", os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iter_special}.nii.gz"),
                "-o", os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iter_special}_reg.nii.gz"),
                "-t", os.path.join(args.output_dir, "registration_gmm"),
                "-r", os.path.join(args.output_dir, f"registration_iter{reg_counter}") if reg_counter > 0 else ""
            ], check=True)
            shore_weighting = os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iter_special}_reg.nii.gz")
            print("Shore-based (voxel-wise) weights will be used.")
        elif iteration == 99:  # Not used - alternative option
            shore_weighting = os.path.join(args.output_dir, f"fvoxelweights_shore_{iteration}.nii.gz")
            print("Shore-based (voxel-wise) weights will be used.")
        else:  # Default weighting after initial step
            shore_weighting = os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iteration}.txt")
            print("GMM (slice-wise) weights will be used.")

        print("=" * 120)
        
        # SHORE fitting
        recon_cmd = [
            "fedi_dmri_recon",
            "--dmri", working_dmri,
            "--bval", args.bval,
            "--bvec_in", bvec_ste_in,
            "--bvec_out", bvec_ste,
            "--weights", shore_weighting,
            "--fspred", os.path.join(args.output_dir, f"spred{iteration}.nii.gz"),
            "-do_not_use_mask"
        ]
        if args.mask:
            recon_cmd.extend(["--mask", args.mask])
        
        subprocess.run(recon_cmd, check=True)

        # Make sure that bvec_in is bvec_out after reconstruction done
        bvec_ste_in = bvec_ste

        print("=" * 120)
        
        # Registration of original data to SHORE-predicted data at specific iterations
        if iteration in iter_registration:
            print(f"Starting Registration: {iteration}")

            reg_counter += 1
            reg_working_path = os.path.join(args.output_dir, f"registration_iter{reg_counter}")

            # Volume-to-volume registration
            subprocess.run([
                "fedi_dmri_reg",
                "--input_dmri", raw_working_dmri,
                "--target_dmri", os.path.join(args.output_dir, f"spred{iteration}.nii.gz"),
                "--output_dir", reg_working_path,
                "--output_dmri", os.path.join(args.output_dir, f"working_updated{reg_update}.nii.gz")
            ], check=True)

            # Rotate bvecs per volume
            bvec_ste_rot = os.path.join(args.output_dir, f"rotated_bvecs{reg_update}")
            subprocess.run([
                "fedi_dmri_rotate_bvecs",
                "--bvecs", bvec_ste,
                "--robvecs", bvec_ste_rot,
                "--pathofmatfile", reg_working_path,
                "--prefix", "Transform_v",
                "--suffix", "_0GenericAffine.mat"
            ], check=True)

            # Update working variables after registration
            working_dmri = os.path.join(args.output_dir, f"working_updated{reg_update}.nii.gz")
            bvec_ste_in = bvec_ste_rot
            reg_update += 1

    print("\n" + "="*120)
    print("Motion correction completed successfully!")
    print(f"Final output: {working_dmri}")
    print("="*120)


if __name__ == "__main__":
    main()
