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
import os
import subprocess

# Utility function to execute a shell command
def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")
        raise

# Main execution
def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m \n\n    "
            "Perform volume-by-volume registration of 4D diffusion MRI data using ANTs."
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Snoussi, H., et al., 2024. Haitch: A framework for distortion and "
            "motion correction in fetal multi-shell diffusion-weighted MRI. "
            "arXiv preprint arXiv:2406.20042."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--input_dmri", required=True, help="Path to the 4D input diffusion MRI file.")
    parser.add_argument("--target_dmri", required=True, help="Path to the 4D target diffusion MRI file.")
    parser.add_argument("--output_dir", required=True, help="Directory for intermediate and output files.")
    parser.add_argument("--output_dmri", required=True, help="Filename for the registered diffusion MRI output.")


    args = parser.parse_args()

    # Validate input arguments
    if not os.path.isfile(args.input_dmri):
        raise FileNotFoundError(f"Input file {args.input_dmri} does not exist.")
    if not os.path.isfile(args.target_dmri):
        raise FileNotFoundError(f"Input file {args.target_dmri} does not exist.")

    os.makedirs(args.output_dir, exist_ok=True)

    # Extract the number of volumes
    result = subprocess.run(["mrinfo", "-size", args.input_dmri, "-quiet"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Error retrieving number of volumes.")

    n_volumes = int(result.stdout.split()[3])
    print(f"Number of volumes: {n_volumes}")

    # Split 4D volume into 3D volumes
    warped_volumes = []
    for v_idx in range(n_volumes):
        raw_volume_path = os.path.join(args.output_dir, f"input_dmri_v{v_idx}.nii.gz")
        spred_volume_path = os.path.join(args.output_dir, f"target_dmri_v{v_idx}.nii.gz")

        run_command(["mrconvert", "-coord", "3", str(v_idx), args.input_dmri, raw_volume_path, "-force", "-quiet"])
        run_command(["mrconvert", "-coord", "3", str(v_idx), args.target_dmri, spred_volume_path, "-force", "-quiet"])

        # Perform antsRegistration
        transform_prefix = os.path.join(args.output_dir, f"Transform_v{v_idx}_")
        warped_volume_path = os.path.join(args.output_dir, f"input_dmri_v{v_idx}_warped.nii.gz")

        ants_command = [
            "antsRegistration",
            "--collapse-output-transforms", "1",
            "--dimensionality", "3",
            "--initialize-transforms-per-stage", "0",
            "--interpolation", "BSpline",
            "--output", f"[{transform_prefix}, {warped_volume_path} ]",  
            "--transform", "Rigid[0.01]",
            "--metric", f"GC[{spred_volume_path}, {raw_volume_path}, 1, 32, Regular, 0.25]",
            "--convergence", "[2000x1000x500,1e-07,10]",  
            "--smoothing-sigmas", "1x1x1vox",
            "--shrink-factors", "4x2x1",
            "--use-histogram-matching", "1",
            "--winsorize-image-intensities", "[0.01,0.99]"
        ]


        # Perform antsRegistration
        print("ANTS Registration Command:")
        print(" ".join(ants_command))  # Debug print to check command format

        print(".")



        print(f"Performing registration for volume {v_idx}.")
        subprocess.run(" ".join(ants_command), shell=True, check=True)


        warped_volumes.append(warped_volume_path)

    # Concatenate registered volumes into a single 4D volume
    run_command(["mrcat", "-axis", "3"] + warped_volumes + [args.output_dmri, "-quiet"])
    print(f"Registration completed successfully. Registered dMRI saved to {args.output_dmri}.")

if __name__ == "__main__":
    main()
