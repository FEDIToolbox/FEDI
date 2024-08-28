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

import re
import os
import numpy as np
import nibabel as nib
import argparse
import matplotlib.pyplot as plt

# Create an argument parser
parser = argparse.ArgumentParser(description="Detect outlier masks based on z-scores and visualize mask properties.")

# Add arguments for directory path and mask prefix
parser.add_argument("-d", "--directory", required=True, help="Directory containing mask files")
parser.add_argument("-s", "--startswith", required=True, help="Startswith prefix of mask files")
parser.add_argument("-e", "--endswith", required=True, help="Endswith prefix of mask files")
parser.add_argument("-o", "--outputsub", required=True, help="outputdir/subjectname of the subject")

args = parser.parse_args()

# Define the directory containing your brain mask files
mask_directory = args.directory

# List all mask files in the directory with the specified prefix
mask_files = [f for f in os.listdir(mask_directory) if f.startswith(args.startswith) and f.endswith(args.endswith)]


# Function to extract the index from the file name
def extract_index(filename):
    match = re.search('_v(\d+)_', filename)
    return int(match.group(1)) if match else -1

# Sort the files based on the extracted index
mask_files.sort(key=extract_index)


# Create empty lists to store the z-scores and non-zero voxel counts
z_scores = []
non_zero_counts = []

# Calculate the volume and z-score for each brain mask
for mask_file in mask_files:
    # Load the mask using NiBabel
    mask_path = os.path.join(mask_directory, mask_file)
    mask_data = nib.load(mask_path).get_fdata()

    # Calculate the volume by counting non-zero elements in the mask
    volume = np.count_nonzero(mask_data)
    non_zero_counts.append(volume)

# Compute the mean and standard deviation for non-zero voxel counts
mean_non_zero = np.mean(non_zero_counts)
std_non_zero = np.std(non_zero_counts)

# Compute z-scores for non-zero voxel counts
z_scores = [(volume - mean_non_zero) / std_non_zero if std_non_zero != 0 else 0 for volume in non_zero_counts]

# Define a threshold for the z-scores (you can adjust this as needed)
z_score_threshold = 2  # You can adjust this value based on your dataset

# Create an empty list to store the names of outlier masks
outlier_mask_names = []


# Create a list to store colors for scatter points based on outlier status
scatter_colors = ['red' if abs(z_score) > z_score_threshold else 'blue' for z_score in z_scores]

figname= str(args.outputsub) + "non_zero_counts.png"
# Plot and save non-zero voxel counts with colors indicating outlier status
plt.figure(figsize=(14, 9))
plt.scatter(range(len(mask_files)), non_zero_counts, c=scatter_colors, label='Outliers (Red) / Non-Outliers (Blue)')
plt.xlabel("Mask Index")
plt.ylabel("Number of Non-zero Voxels")
plt.title("Non-zero Voxel Counts for Brain Masks")
plt.axhline(y=mean_non_zero, color='green', linestyle='--', label='Mean Non-zero Voxel Count')
plt.axhline(y=mean_non_zero + z_score_threshold * std_non_zero, color='orange', linestyle='--', label='Threshold')
plt.axhline(y=mean_non_zero - z_score_threshold * std_non_zero, color='orange', linestyle='--', label='Threshold')
plt.legend(loc='lower right')
plt.savefig(figname)
# plt.close()

# Identify masks with z-scores beyond the threshold as outliers
for i, z_score in enumerate(z_scores):
    if abs(z_score) > z_score_threshold:
        outlier_mask_names.append(mask_files[i])

# Print the names of outlier masks
print("Names of outlier segmentations:")
print(outlier_mask_names)

file_path = str(args.outputsub) + "_outliers_volume_index.txt"
# Open the file in write mode and write each name to a new line
with open(file_path, 'w') as file:
    for name in outlier_mask_names:
        print(name)
        file.write(name + '\n')