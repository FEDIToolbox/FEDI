#!/usr/bin/env python3.10

##########################################################################
##                                                                      ##
##  Part of Fetal and Neonatal Development Imaging Toolbox (FEDI)       ##
##                                                                      ##
##  Author:    Haykel Snoussi, PhD (dr.haykel.snoussi@gmail.com)        ##
##                                                                      ##
##########################################################################


import argparse
import os
import subprocess
import numpy as np
import nibabel as nib

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
    optional_args.add_argument("--epochs", type=int, default=6, metavar=Metavar.int, help="Number of reconstruction iterations (default: 6).")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Determine AXSLICES (slice axis) - matching bash lines 124-137
    # Find minimum dimension to determine slice axis
    dmri_img = nib.load(args.dmri)
    x_size, y_size, z_size = dmri_img.shape[:3]
    
    # Determine the number of slices: the minimum dimension size
    n_slices = min(x_size, y_size, z_size)
    
    # Define the Z-axis number (AXSLICES)
    if n_slices == x_size:
        ax_slices = 0
    elif n_slices == y_size:
        ax_slices = 1
    else:  # n_slices == z_size
        ax_slices = 2
    
    print(f"Image dimensions: {x_size}x{y_size}x{z_size}")
    print(f"Number of slices: {n_slices}")
    print(f"Slice axis (AXSLICES): {ax_slices}")

    # Define constants (matching bash variable names from STEP 8)
    raw_working_dmri = args.dmri  # RAWWORKING_DMRI - original input, never changes
    working_dmri = args.dmri  # WORKING_DMRI - gets updated after registration
    working_dmri_gmm = None  # WORKING_DMRI_GMM - will be set in reorientation section
    working_dmri_mask = args.mask  # WORKING_DMRIMASK
    working_dmri_mask_gmm = None  # WORKING_DMRIMASK_GMM - will be set in reorientation section
    
    epochs = args.epochs  # EPOCHS
    # ITER_REG: registration iterations (adjust based on epochs)
    if epochs >= 4:
        iter_registration = [1, 2, 3, 4]  # Default for 6 epochs
    elif epochs >= 3:
        iter_registration = [1, 2]  # For 3 epochs
    elif epochs >= 2:
        iter_registration = [1]  # For 2 epochs
    else:
        iter_registration = []  # No registration for 1 epoch
    reg_update = 0  # REG_UPDATE
    reg_counter = 0  # REG_COUNTER
    bvec_ste_in = args.bvec  # BVECSTEIN - gets updated after registration/reconstruction
    bvec_ste = args.bvec  # BVECSTE - original bvec, doesn't change

    # Main iteration loop (matching STEP 8, lines 1699-1825, including reorientation section)
    for iteration in range(epochs):
        prev_iteration = iteration - 1  # ITERM

        print(f"\n{'='*120}")
        print(f"Reorient data for GMM slice weighting : {iteration}")
        print(f"{'='*120}\n")

        # Reorientation section (matching bash lines 1703-1747)
        if ax_slices == 0:
            print(f"Applying Transformation Axis as Slice's Axis = {ax_slices}")
            
            # Create transformation matrix for axis 0
            trans_matrix_file = os.path.join(args.output_dir, "trans_axis0.txt")
            with open(trans_matrix_file, 'w') as f:
                f.write("0 0  1 0\n")
                f.write("1 0 0 0\n")
                f.write("0 1  0 0\n")
                f.write("0 0  0 1\n")
            
            # Apply transformation using mrtransform
            working_dmri_gmm = os.path.join(args.output_dir, f"working_TE1_GMM_iter{iteration}.nii.gz")
            subprocess.run([
                "mrtransform",
                "-linear", trans_matrix_file,
                working_dmri,
                working_dmri_gmm,
                "-force"
            ], check=True)
            
            if working_dmri_mask:
                working_dmri_mask_gmm = os.path.join(args.output_dir, f"working_mask_TE1_GMM_iter{iteration}.nii.gz")
                subprocess.run([
                    "mrtransform",
                    "-linear", trans_matrix_file,
                    working_dmri_mask,
                    working_dmri_mask_gmm,
                    "-force"
                ], check=True)
            else:
                working_dmri_mask_gmm = None
            
            # Transform spred if it exists
            spred_gmm = None
            if prev_iteration >= 0:
                spred_path = os.path.join(args.output_dir, f"spred{prev_iteration}.nii.gz")
                if os.path.exists(spred_path):
                    spred_gmm = os.path.join(args.output_dir, f"spred{prev_iteration}_GMM.nii.gz")
                    subprocess.run([
                        "mrtransform",
                        "-linear", trans_matrix_file,
                        spred_path,
                        spred_gmm,
                        "-force"
                    ], check=True)
        
        elif ax_slices == 1:
            print(f"Applying Transformation Axis as Slice's Axis = {ax_slices}")
            
            # Create transformation matrix for axis 1
            trans_matrix_file = os.path.join(args.output_dir, "trans_axis1.txt")
            with open(trans_matrix_file, 'w') as f:
                f.write("1 0  0 0\n")
                f.write("0 0 -1 0\n")
                f.write("0 1  0 0\n")
                f.write("0 0  0 1\n")
            
            # Apply transformation using mrtransform
            working_dmri_gmm = os.path.join(args.output_dir, f"working_TE1_GMM_iter{iteration}.nii.gz")
            subprocess.run([
                "mrtransform",
                "-linear", trans_matrix_file,
                working_dmri,
                working_dmri_gmm,
                "-force"
            ], check=True)
            
            if working_dmri_mask:
                working_dmri_mask_gmm = os.path.join(args.output_dir, f"working_mask_TE1_GMM_iter{iteration}.nii.gz")
                subprocess.run([
                    "mrtransform",
                    "-linear", trans_matrix_file,
                    working_dmri_mask,
                    working_dmri_mask_gmm,
                    "-force"
                ], check=True)
            else:
                working_dmri_mask_gmm = None
            
            # Transform spred if it exists
            spred_gmm = None
            if prev_iteration >= 0:
                spred_path = os.path.join(args.output_dir, f"spred{prev_iteration}.nii.gz")
                if os.path.exists(spred_path):
                    spred_gmm = os.path.join(args.output_dir, f"spred{prev_iteration}_GMM.nii.gz")
                    subprocess.run([
                        "mrtransform",
                        "-linear", trans_matrix_file,
                        spred_path,
                        spred_gmm,
                        "-force"
                    ], check=True)
        
        elif ax_slices == 2:
            # No transformation needed - just copy references
            working_dmri_gmm = working_dmri
            working_dmri_mask_gmm = working_dmri_mask
            if prev_iteration >= 0:
                spred_path = os.path.join(args.output_dir, f"spred{prev_iteration}.nii.gz")
                if os.path.exists(spred_path):
                    spred_gmm = spred_path
                else:
                    spred_gmm = None
            else:
                spred_gmm = None

        print(f"\n{'='*120}")
        print(f"Start Reconstruction Iteration : {iteration}")
        print(f"{'='*120}\n")

        # Outlier Detection (matching bash lines 1754-1770)
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
        ]
        
        # Add spred and spredgmm (matching bash script - always pass both when spred exists)
        if prev_iteration >= 0:
            spred_path = os.path.join(args.output_dir, f"spred{prev_iteration}.nii.gz")
            if os.path.exists(spred_path):
                outliers_cmd.extend(["--spred", spred_path])
                # spred_gmm is set in the reorientation section above
                if spred_gmm and os.path.exists(spred_gmm):
                    outliers_cmd.extend(["--spredgmm", spred_gmm])
        
        # Add mask arguments only if mask is provided
        if working_dmri_mask:
            outliers_cmd.extend([
                "--mask", working_dmri_mask,
                "--maskgmm", working_dmri_mask_gmm
            ])
        
        subprocess.run(outliers_cmd, check=True)

        print("=" * 120)
        # Select weighting method (matching bash lines 1759-1787)
        if iteration == 0:  # Initialization
            shore_weighting = os.path.join(args.output_dir, f"fsliceweights_mzscore_{iteration}.txt")
            print("Modified Z-score (slice-wise) weights will be used.")
        elif iteration == 98:  # Final iteration - alternative option (not used in epochs=6)
            iter_special = 1
            weights_4d = os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iter_special}.nii.gz")
            weights_4d_reg = os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iter_special}_reg.nii.gz")
            reg_working_path = os.path.join(args.output_dir, f"registration_iter{reg_counter}") if reg_counter > 0 else ""
            
            if reg_working_path and os.path.exists(weights_4d):
                subprocess.run([
                    "fedi_apply_transform",
                    "-i", weights_4d,
                    "-o", weights_4d_reg,
                    "-t", os.path.join(args.output_dir, "registration_gmm"),
                    "-r", reg_working_path
                ], check=True)
                shore_weighting = weights_4d_reg
            else:
                shore_weighting = weights_4d
            print("Shore-based (voxel-wise) weights will be used.")
        elif iteration == 99:  # Not used - alternative option
            shore_weighting = os.path.join(args.output_dir, f"fvoxelweights_shore_{iteration}.nii.gz")
            print("Shore-based (voxel-wise) weights will be used.")
        else:  # Default weighting after initial step
            shore_weighting = os.path.join(args.output_dir, f"fsliceweights_gmmodel_{iteration}.txt")
            print("GMM (slice-wise) weights will be used.")

        print("=" * 120)
        
        # SHORE Fitting (matching bash lines 1789-1794)
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
        if working_dmri_mask:
            recon_cmd.extend(["--mask", working_dmri_mask])
        
        subprocess.run(recon_cmd, check=True)

        # Make sure that bvec_in is bvec_out after reconstruction done (matching bash line 1797)
        bvec_ste_in = bvec_ste

        print("=" * 120)
        
        # Registration of original data to SHORE-predicted data at specific iterations
        # (matching bash lines 1799-1824)
        if iteration in iter_registration:
            print(f"Start Registration : {iteration}")

            reg_counter += 1
            reg_working_path = os.path.join(args.output_dir, f"registration_iter{reg_counter}")

            # Volume-to-volume registration (matching bash lines 1807-1810)
            subprocess.run([
                "fedi_dmri_reg",
                "--input_dmri", raw_working_dmri,
                "--target_dmri", os.path.join(args.output_dir, f"spred{iteration}.nii.gz"),
                "--output_dir", reg_working_path,
                "--output_dmri", os.path.join(args.output_dir, f"working_updated{reg_update}.nii.gz")
            ], check=True)

            # Rotate bvecs per volume (matching bash lines 1814-1819)
            bvec_ste_rot = os.path.join(args.output_dir, f"rotated_bvecs{reg_update}")
            subprocess.run([
                "fedi_dmri_rotate_bvecs",
                "--bvecs", bvec_ste,
                "--robvecs", bvec_ste_rot,
                "--pathofmatfile", reg_working_path,
                "--prefix", "Transform_v",
                "--suffix", "_0GenericAffine.mat"
            ], check=True)

            # Update working variables after registration (matching bash lines 1821-1823)
            working_dmri = os.path.join(args.output_dir, f"working_updated{reg_update}.nii.gz")
            bvec_ste_in = bvec_ste_rot
            reg_update += 1

    print("\n" + "="*120)
    print("Motion correction completed successfully!")
    print(f"Final output: {working_dmri}")
    print("="*120)


if __name__ == "__main__":
    main()
