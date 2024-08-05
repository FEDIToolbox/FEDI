#!/usr/bin/env python3.10

import os
import numpy as np
import nibabel as nib
import argparse
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1 import make_axes_locatable

# Create an argument parser
parser = argparse.ArgumentParser(description="Figure for weights.")

# Add arguments for weights file, title, and output filename
parser.add_argument("-w", "--weights", required=True, help="Weights txt file")
parser.add_argument("-t", "--title", required=False, help="Title")
parser.add_argument("-f", "--filename", required=True, help="Output file name")

# Parse the command-line arguments
args = parser.parse_args()

weights_file = args.weights
title = args.title
figname_png = args.filename

# Load weights from the file
try:
    weights_raw = np.loadtxt(weights_file, delimiter=',')
except ValueError:
    weights_raw = np.loadtxt(weights_file, delimiter=' ')

def save_figure_2box(weights, clim_min, clim_max, title, figname_png):
    # Plot and save the 2D image
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(25, 15))  # Adjust figure size

    im = ax.imshow(weights, interpolation="nearest", cmap="cividis", origin="lower")  # Use 'cividis' colormap
    im.set_clim(clim_min, clim_max)
    ax.set_xlabel("Volume Index")
    ax.set_ylabel("Slice Index")
    ax.set_title(title, fontsize=16)  # Increase title font size
    ax.axis("scaled")
    
    # Customize x-axis ticks to appear for every five slices
    num_volumes = weights.shape[1]
    x_ticks = range(0, num_volumes, 5)
    ax.set_xticks(x_ticks)

    ax.set_aspect('auto')

    # Save the figure with a higher DPI
    fig.savefig(figname_png, dpi=300, bbox_inches='tight')

# Call the function to save the figure
clim_min, clim_max = 0, 1  # Define clim_min and clim_max values as needed
save_figure_2box(weights_raw, clim_min, clim_max, title, figname_png)






def main():

    bvecs = normalize_bvecs(bvecs)

    results_dict = {}

    for bval in np.unique(bvals[bvals > b0_thr]):
        shell_idx = np.where(bvals == bval)[0]
        shell = bvecs[shell_idx]
        results_dict[bval] = np.ones((len(shell), 3)) * -1
        for i, vec in enumerate(shell):
            if np.linalg.norm(vec) < 0.001:
                continue

            dot_product = np.clip(np.tensordot(shell, vec, axes=1), -1, 1)
            # print(dot_product)
            angle = np.arccos(dot_product) * 180 / math.pi
            angle[np.isnan(angle)] = 0

            idx = np.argpartition(angle, 4).tolist()
            idx.remove(i)

            avg_angle = np.average(angle[idx[:3]])
            corr = np.corrcoef([data[..., shell_idx[i]].ravel(),
                                data[..., shell_idx[idx[0]]].ravel(),
                                data[..., shell_idx[idx[1]]].ravel(),
                                data[..., shell_idx[idx[2]]].ravel()])
            results_dict[bval][i] = [shell_idx[i], avg_angle,
                                     np.average(corr[0, 1:])]

    for key in results_dict.keys():
        avg_angle = np.round(np.average(results_dict[key][:, 1]), 4)
        std_angle = np.round(np.std(results_dict[key][:, 1]), 4)

        avg_corr = np.round(np.average(results_dict[key][:, 2]), 4)
        std_corr = np.round(np.std(results_dict[key][:, 2]), 4)

        outliers_angle = np.argwhere(
            results_dict[key][:, 1] < avg_angle-(args.std_scale*std_angle))
        outliers_corr = np.argwhere(
            results_dict[key][:, 2] < avg_corr-(args.std_scale*std_corr))

        print('Results for shell {} with {} directions:'.format(
            key, len(results_dict[key])))
        print('AVG and STD of angles: {} +/- {}'.format(
            avg_angle, std_angle))
        print('AVG and STD of correlations: {} +/- {}'.format(
            avg_corr, std_corr))

        if len(outliers_angle) or len(outliers_corr):
            print('Possible outliers ({} STD below or above average):'.format(
                args.std_scale))
            print('Outliers based on angle [position (4D), value]')
            for i in outliers_angle:
                print(results_dict[key][i, :][0][0:2])
            print('Outliers based on correlation [position (4D), value]')
            for i in outliers_corr:
                print(results_dict[key][i, :][0][0::2])
        else:
            print('No outliers detected.')
        print()
