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
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti, save_nifti

# Create an argument parser
parser = argparse.ArgumentParser(description="Correct the size of b-values and b-vectors")

# Add required arguments for input file paths and output paths
parser.add_argument("-d", "--dmri", required=True, help="Path to dMRI file")
parser.add_argument("-a", "--bvals", required=True, help="Path to bval file")
parser.add_argument("-e", "--bvecs", required=True, help="Path to bvec file")
parser.add_argument("-g", "--grads", required=True, help="Path to mrtrix grad file")
parser.add_argument("-t", "--ntecho", type=int, required=True, help="Number of echo times")
parser.add_argument("-s", "--bvalsnew", required=True, help="Path to new bvals file")
parser.add_argument("-n", "--bvecsnew", required=True, help="Path to new bvecs file")
parser.add_argument("-r", "--gradsnew", required=True, help="Path to new mrtrix grad file")

# Parse the command-line arguments
args = parser.parse_args()

# Load dMRI data
fdmri = args.dmri
dmri, affine = load_nifti(fdmri)



# Load b-values and b-vectors
fbval = args.bvals
fbvec = args.bvecs
numberTEs = args.ntecho
bvalsraw, bvecsraw = read_bvals_bvecs(fbval, fbvec)

# Check if the number of volumes matches the specified number of echo times
if dmri.shape[3] != bvalsraw.shape[0]:
    indices = np.arange(0, bvalsraw.shape[0], numberTEs)
    bvals = bvalsraw[indices]
    bvecs = bvecsraw[indices, :]
else:
    bvals = bvalsraw
    bvecs = bvecsraw


if bvecs.shape[0] != 3:
    bvecs = bvecs.T

if bvals.shape[0] != 1:
    bvals = bvals.reshape(1, -1)

# Save the corrected b-values and b-vectors to the specified files
np.savetxt(args.bvalsnew, bvals, delimiter=" ",fmt='%.0f')
np.savetxt(args.bvecsnew, bvecs, delimiter=" ")







TIMES = numberTEs  # Set TIMES as needed

with open(args.grads, 'r') as file:
    lines = file.readlines()

# Skip the first line if it starts with '#'
start_index = 1 if lines[0].startswith('#') else 0


# Remove lines based on the TIMES value
filtered_lines = []
for i, line in enumerate(lines[start_index:], start=start_index):
    # Keep the line if it doesn't meet the removal criteria
    if (i - start_index) % TIMES == 0 :
        filtered_lines.append(line)


# Write the filtered lines to a new file, including the first line if it was skipped
with open(args.gradsnew, 'w') as file:
    if start_index == 1:
        file.write(lines[0])
    file.writelines(filtered_lines)




# # Read the data from the file
# with open(args.grads, 'r') as file:
#     lines = file.readlines()

# # Remove duplicates
# unique_lines = set(lines)

# # Write the unique lines to a new file
# with open(args.gradsnew, 'w') as file:
#     file.writelines(unique_lines)



