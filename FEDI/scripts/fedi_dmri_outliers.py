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
import math
import subprocess
import numpy.matlib as matlib

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
    description=(
        "\033[1mDESCRIPTION:\033[0m \n\n    "
        "Volume, slice and voxel weighting and outlier detection using many methods: SOLID, Gaussian Mixture Model (GMM), SHORE-based, Angular, and Correlation metrics with neighbors.\n"
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

# Add required arguments for input file paths and output path
mandatory.add_argument("-d", "--dmri", required=True, metavar=Metavar.file, help="Path to dMRI file")
mandatory.add_argument("-b", "--dmrigmm", required=True, metavar=Metavar.file, help="Path to dMRI file for GMM")

mandatory.add_argument("-a", "--bval", required=True, metavar=Metavar.file, help="Path to bval file")
mandatory.add_argument("-e", "--bvec", required=True, metavar=Metavar.file, help="Path to bvec file")
mandatory.add_argument("-o", "--outpath", required=True, metavar=Metavar.file, help="Output directory path")

optional = parser.add_argument_group('\033[1mOPTIONAL OPTIONS\033[0m')

# Add optional arguments with default values
optional.add_argument("-s", "--spred", required=False, metavar=Metavar.file, help="Path to spred file")
optional.add_argument("-f", "--spredgmm", required=False, metavar=Metavar.file, help="Path to spred file for GMM")

optional.add_argument("-m", "--mask", required=False, metavar=Metavar.file, help="Path to mask file, required for GMM weighting")
optional.add_argument("-k", "--maskgmm", required=False, metavar=Metavar.file, help="Path to mask file, required for GMM weighting")

optional.add_argument("-t", "--thresholds", required=False, metavar=Metavar.list, type=str, default="3.5,6.0", help="Lower and upper modified Z-score thresholds as 'lower,upper'")
optional.add_argument("-c", "--zscoremetric", required=False, metavar=Metavar.str, default="mean", choices=["var", "mean", "iod"], help="Modified Z-Score metric: var, mean, or iod")
optional.add_argument("-l", "--scalingmethod", required=False, metavar=Metavar.str, default="linear", choices=["linear", "sigmoid"], help="Scaling method for slice weights: linear or sigmoid")

# Add optional arguments for various sliceweights methods

optional.add_argument("-z", "--fsliceweights_mzscore", required=False, metavar=Metavar.file, help="Filename for sliceweights using modified Z-score")
optional.add_argument("-n", "--fsliceweights_angle_neighbors", required=False, metavar=Metavar.file, help="Filename for sliceweights using angle with neighbors")
optional.add_argument("-y", "--fsliceweights_corre_neighbors", required=False, metavar=Metavar.file, help="Filename for sliceweights using correlation with neighbors")
optional.add_argument("-g", "--fsliceweights_gmmodel", required=False, metavar=Metavar.file, help="Filename for sliceweights using Gaussian mixture model (GMM)")
optional.add_argument("-r", "--fvoxelweights_shorebased", required=False, metavar=Metavar.file, help="Filename.nii.gz (4D)  for voxelweights using shore-based residuals")

# Parse the command-line arguments
args = parser.parse_args()




def save_figure_onebox(weights, clim_min, clim_max, title, outpath, fignamepng):
    # Plot and save the 2D image
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(25, 7.5))  # Adjust figure size

    im = ax.imshow(weights, interpolation="nearest", cmap="Blues", origin="lower")  # Use 'viridis or cividis' as an alternative colormap
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label(title)

    im.set_clim(clim_min, clim_max)
    ax.set_xlabel("Volume Index")
    ax.set_ylabel("Slice Index")
    ax.set_title(title, fontsize=16)  # Increase title font size
    ax.axis("scaled")
    
    # Customize x-axis ticks to appear for every five slices
    num_volumes = weights.shape[1]
    x_ticks = range(0, num_volumes, 5)
    ax.set_xticks(x_ticks)
    ax.set_xticks(range(0, weights.shape[1], 2))
    ax.set_yticks(range(0, weights.shape[0], 2))

    ax.set_aspect('auto')
    ax.grid(linestyle='-', linewidth=0.3) 

    # Save the figure with a higher DPI
    fig.savefig(os.path.join(outpath, fignamepng), dpi=300, bbox_inches='tight')


def save_figure_twobox(first_box, second_box, clim1_min, clim1_max, clim2_min, clim2_max, first_title, second_title, fignamepng, outpath):
    # Create a 2x1 subplot
    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(25, 15))

    # Plot and customize the first box
    im1 = ax[0].imshow(first_box, interpolation="nearest", cmap="Blues", origin="lower")
    divider1 = make_axes_locatable(ax[0])
    cax1 = divider1.append_axes("right", size="5%", pad=0.05)
    cbar1 = fig.colorbar(im1, cax=cax1)
    cbar1.set_label(first_title)
    im1.set_clim(clim1_min, clim1_max)
    ax[0].set_title(first_title, fontsize=16)

    # Plot and customize the second box
    im2 = ax[1].imshow(second_box, interpolation="nearest", cmap="Blues", origin="lower")
    divider2 = make_axes_locatable(ax[1])
    cax2 = divider2.append_axes("right", size="5%", pad=0.05)
    cbar2 = fig.colorbar(im2, cax=cax2)
    cbar2.set_label(second_title)
    im2.set_clim(clim2_min, clim2_max)
    ax[1].set_title(second_title, fontsize=16)

    # Define common properties for both subplots
    for i in range(2):
        ax[i].set_xlabel("Volume Index")
        ax[i].set_ylabel("Slice Index")
        ax[i].axis("scaled")
        ax[i].set_xticks(range(0, first_box.shape[1], 2))
        ax[i].set_yticks(range(0, first_box.shape[0], 2))
        ax[i].set_aspect('auto')
        # ax[i].grid(True)
        ax[i].grid(linestyle='-', linewidth=0.3) 

    # Save the figure with a higher DPI
    fig.savefig(os.path.join(outpath, fignamepng), dpi=300, bbox_inches='tight')



def calculate_mzscore_weightts(Zscores, lowerThreshold, upperThreshold, weightscalingmethod):

    weights = Zscores
    weights[weights < lowerThreshold] = lowerThreshold
    weights[weights > upperThreshold] = upperThreshold

    if weightscalingmethod == "linear":
        # Linear scaling
        weights = (weights - lowerThreshold) / (upperThreshold - lowerThreshold)
    elif weightscalingmethod == "sigmoid":
        # Sigmoid scaling
        k = 1  # You may adjust the k value as needed
        weights = (weights - lowerThreshold) * 2.0 / (upperThreshold - lowerThreshold) - 1.0
        weights = 1 / (1 + np.exp(-weights / k))

    weights = 1 - weights

    # Replace NaN with 0
    weights = np.nan_to_num(weights)

    # Ensure that at least some values are > 0
    for i in range(weights.shape[0]):
        if np.all(weights[i, :] <= 0):
            weights[i, 0] = 1
            weights[i, -1] = 1

    return weights


def mzscore_weighting(dmri, fmask, bvals, outpath, metric, lowerThreshold, upperThreshold, weightscalingmethod, fsliceweights_mzscore):

    print("Calculate Modified Z-Score Weights")
    bvalsunique = np.unique(bvals.round(-2))
    shape = dmri.shape
    NorZscore = np.zeros((shape[2], shape[3]))
    NorZscore.fill(np.nan)
    ModZscore = np.zeros((shape[2], shape[3]))
    ModZscore.fill(np.nan)

    for b in bvalsunique:
        # for each dwi bvalues
        inds = np.where(bvals.round(-2) == b)[0]
        # print("Modified Z-Score for bvalue : ",b)
        # print("Index are :",inds)
        if inds.size < 2:
            continue

        shell = dmri[:, :, :, inds].astype(np.float32)
        if fmask is not None:
            mask = fmask.astype(int) == 0
            # shell[mask] = np.nan
            shell[mask] = 0

        # not useful line : return indices of that shell has of the True values
        #  tmp = np.argwhere(np.isnan(shell))
        dims = shell.shape

        # reshape the shell to new size : dims[0] * dims[1] , dims[2], dims[3]
        shell = shell.reshape((dims[0] * dims[1], dims[2], dims[3]))
        # print("---bvalue is:", b)
        # print("---dmri.shape:", dmri.shape)
        # print("---shell.shape: ",shell.shape)

        # 1. Normal Zscore calculation
        # zscore = (shell-shell_mean)/std
        norZ=stats.zscore(np.nanmean(shell, axis=0), axis=1, nan_policy='raise')
        NorZscore[:, inds] = norZ


        # 2. Modified Zscore
        # get y following the chosen metric
        if metric == "var":
            y = np.nanvar(shell, axis=0)
        if metric == "mean":
            y = np.nanmean(shell, axis=0)
        if metric == "iod":
            y = np.nanvar(shell, axis=0) / np.nanmean(shell, axis=0)

        # print("y.shape: ",y.shape)
        # calculates the mean along axis 1 of y, then replicates the meadian values dims[3] times along first axis, then transpose
        ymean = matlib.repmat(np.nanmedian(y, axis=1), dims[3], 1).T
        # print("ymean.shape: ",ymean.shape)
        # Median Absolute Deviation (MAD) = k-factor * median(|y - ymean|)
        # k-factor =  For normally distributed data k is taken to be 1.4826
        MAD = 1.4826 * np.nanmedian(np.abs(y - ymean), axis=1) + 0.0001

        # Calculate modified Zscore = (y-ymean)/MAD
        modZ = np.abs(y - ymean) /  (matlib.repmat(MAD, dims[3], 1).T )

        # print("modZ.shape: ",modZ.shape)
        ModZscore[:, inds] = modZ
        # print("ModZscore.shape", ModZscore.shape)

    NorZscore_weights = calculate_mzscore_weightts(NorZscore, lowerThreshold, upperThreshold, weightscalingmethod)
    ModZscore_weights = calculate_mzscore_weightts(ModZscore, lowerThreshold, upperThreshold, weightscalingmethod)

    # # Save ModZscore as a text file
    # np.savetxt(outpath +"/"+ "Zscoressss.txt", NorZscore, delimiter=", ")

    # Save ModZscore as a text file
    # np.savetxt(outpath + "/fslicemodified_zscore.txt", ModZscore, delimiter=',', fmt='%.6f')

    # Save Weights as a text file
    np.savetxt(os.path.join(outpath, fsliceweights_mzscore), ModZscore_weights, delimiter=',', fmt='%.6f')


    ModZscore_data = ModZscore
    ModZscore_data[np.isnan(ModZscore_data)] = 0

    ModZscore_weights_data = ModZscore_weights
    ModZscore_weights_data[np.isnan(ModZscore_weights_data)] = 0

    fsliceweights_mzscore_png = fsliceweights_mzscore.replace(".txt", ".png")

    save_figure_twobox(first_box =upperThreshold-ModZscore_data+lowerThreshold,second_box=ModZscore_weights_data,clim1_min=lowerThreshold,clim1_max=upperThreshold,clim2_min=0,clim2_max=1, \
        first_title="Modified-Zscore per slice",second_title="Slice weights using Modified-Zscore",fignamepng=fsliceweights_mzscore_png, outpath=outpath)

    return ModZscore_weights_data

def normalize_bvecs(bvecs):
    """
    Normalize b-vectors

    Parameters
    ----------
    bvecs : (N, 3) array
        input b-vectors (N, 3) array

    Returns
    -------
    bvecs : (N, 3)
       normalized b-vectors
    """
    # add a check if bvec is Nx3 array.

    bvecs_norm = np.linalg.norm(bvecs, axis=1)
    idx = bvecs_norm != 0
    bvecs[idx] /= bvecs_norm[idx, None]

    return bvecs




def neighbors_weighting(dmri, bvals, bvecs, b0_threshold, std_scale, filename_angle_neighbors, filename_correlation_neighbors):

    print("Calculate Neighbors Weights")

    AngleMatrix = np.ones((dmri.shape[2], dmri.shape[3]))
    CorreMatrix = np.ones((dmri.shape[2], dmri.shape[3]))

    bvecs = normalize_bvecs(bvecs)
    for slice_idx in range(dmri.shape[2]-2):
        slice_dmri = dmri[:, :, slice_idx:slice_idx+2, :]

        results_dict = {}
        # print("slice:", slice_idx)
        for bval in np.unique(bvals[bvals > b0_threshold]):
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
                corr = np.corrcoef([slice_dmri[..., shell_idx[i]].ravel(),
                                    slice_dmri[..., shell_idx[idx[0]]].ravel(),
                                    slice_dmri[..., shell_idx[idx[1]]].ravel(),
                                    slice_dmri[..., shell_idx[idx[2]]].ravel()])
                results_dict[bval][i] = [shell_idx[i], avg_angle,
                                         np.average(corr[0, 1:])]

        for key in results_dict.keys():
            # print("key:", key)
            avg_angle = np.round(np.average(results_dict[key][:, 1]), 4)
            std_angle = np.round(np.std(results_dict[key][:, 1]), 4)

            avg_corr = np.round(np.average(results_dict[key][:, 2]), 4)
            std_corr = np.round(np.std(results_dict[key][:, 2]), 4)

            outliers_angle = np.argwhere(
                results_dict[key][:, 1] < avg_angle-(std_scale*std_angle))
            outliers_corr = np.argwhere(
                results_dict[key][:, 2] < avg_corr-(std_scale*std_corr))

            # print('Results for shell {} with {} directions:'.format(key, len(results_dict[key])))
            # print('AVG and STD of angles: {} +/- {}'.format(avg_angle, std_angle))
            # print('AVG and STD of correlations: {} +/- {}'.format(avg_corr, std_corr))

            if len(outliers_angle) or len(outliers_corr):
                # print('Possible outliers ({} STD below or above average):'.format(std_scale))
                # print('Outliers based on angle [position (4D), value]')
                for i in outliers_angle:
                    # print(results_dict[key][i, :][0][0:2])
                    AngleMatrix[slice_idx, int(results_dict[key][i, :][0][0])] = 0
                # print('Outliers based on correlation [position (4D), value]')
                for i in outliers_corr:
                    # print(results_dict[key][i, :][0][0])
                    CorreMatrix[slice_idx, int(results_dict[key][i, :][0][0])] = 0

            else:
                # print('No outliers detected.')
                DoNotPrint=1
            # print()

    np.savetxt(os.path.join(outpath, filename_angle_neighbors), AngleMatrix, delimiter=',', fmt='%.6f')
    # Save Weights as a text file
    np.savetxt(os.path.join(outpath, filename_correlation_neighbors), CorreMatrix, delimiter=',', fmt='%.6f')
    filename_angle_neighbors, filename_correlation_neighbors

    filename_correlation_neighbors_png = filename_correlation_neighbors.replace(".txt", ".png")

    save_figure_twobox(first_box =AngleMatrix,second_box=CorreMatrix,clim1_min=0,clim1_max=1,clim2_min=0,clim2_max=1, \
        first_title="Angle neighbors",second_title="Slice Correlations",fignamepng=filename_correlation_neighbors_png, outpath=outpath)


    return AngleMatrix, CorreMatrix


def shorebased_zscore_residuals_voxelwise(dmri, spred):
    """
    Calculate voxel-wise standardized residuals.

    Args:
        dmri (numpy.ndarray): Raw diffusion MRI data.
        spred (numpy.ndarray): Predicted data from a model (e.g., SHORE).

    Returns:
        numpy.ndarray: Voxel-wise standardized residuals.
    """
    # Calculate residuals
    residualsraw = dmri - spred

    # Initialize array for standardized residuals
    zscores = np.zeros_like(residualsraw)

    # Iterate over each voxel
    for i in range(dmri.shape[0]):
        for j in range(dmri.shape[1]):
            for k in range(dmri.shape[2]):
                # print("i,j,k: ",i,j,k)
                # voxel_residuals = residualsraw[i, j, k, :]
                for bval in np.unique(bvals):
                    bval_idx = np.where(bvals == bval)[0]
                    # print("bval_idx: ",bval_idx)
                    voxel_residuals_bval=residualsraw[i,j,k,bval_idx]    
                    sigma_hat = 1.4826 * stats.median_abs_deviation(voxel_residuals_bval)
                    zscores[i, j, k, bval_idx] = voxel_residuals_bval / sigma_hat

    print("zscores.shape: ",zscores.shape)
    return zscores


def shorebased_weighting_voxelwise(dmri, affine, spred,outpath,filename):
    """
    Calculate voxel-wise shore-based weights.

    Args:
        dmri (numpy.ndarray): Raw diffusion MRI data.
        spred (numpy.ndarray): Predicted data from a model (e.g., SHORE).

    Returns:
        numpy.ndarray: Voxel-wise SHORE-based weights.
    """
    # Calculate voxel-wise standardized residuals
    zscores = shorebased_zscore_residuals_voxelwise(dmri, spred)

    # Initialize array for weights
    weights_4D = np.zeros_like(zscores)

    # Compute weights for each voxel
    for i in range(dmri.shape[0]):
        for j in range(dmri.shape[1]):
            for k in range(dmri.shape[2]):
                weights_4D[i, j, k, :] = np.sqrt(1 / np.square(np.square(zscores[i, j, k, :]) + 1))




    save_nifti(os.path.join(outpath, filename), weights_4D, affine)


    print("--> weights_shore_based_4D.shape: ",weights_4D.shape)
    return weights_4D



# def shore_weighting(dmri, spred, fsliceweights_shore):
#     """
#     Calculate shore-based weights based on the paper (section 2.1.2) by Alexandra Koch et al. MRM 2019 
#     "Shore-based detection and imputation of dropout in diffusion MRI"

#     Args:
#     dmri (numpy.ndarray): Raw diffusion MRI data.
#     spred (numpy.ndarray): Predicted data from a model (e.g., SHORE).

#     Returns:
#     numpy.ndarray: Shore-based weights.
#     """
#     # Calculate standardized residuals
#     zscores = shorebased_standard_residuals(dmri, spred)

#     # Calculate weights
#     weights = np.sqrt(1 / np.square(np.square(zscores) + 1))

#     # add saving weights as a text file
#     np.savetxt(outpath + "/" + fsliceweights_shore, weights, delimiter=',', fmt='%.6f')

#     fsliceweights_shore_png = fsliceweights_shore.replace(".txt", ".png")
#     save_figure_twobox(fistbox=zscores,secondbox=weights,clim1_min=np.min(zscores),clim1_max=np.max(zscores), \
#                     clim2_min=np.min(weights),clim2_max=np.max(weights),firsttitle="Residuals Zscore", \
#                     secondtitle="Residualts-Weights",fignamepng=fsliceweights_shore_png)

#     return weights


# def shorebased_dropout(dmri, spredw, threshold_dropout, alpha=1):
#     """
#     Detect dropout in diffusion MRI data using shore-based method based on the paper (section 2.1.3) by Alexandra Koch et al. MRM 2019 
#     "Shore-based detection and imputation of dropout in diffusion MRI"

#     Args:
#     dmri (numpy.ndarray): Raw diffusion MRI data.
#     spredw (numpy.ndarray): Predicted data from a model (e.g., SHORE) with weights.
#     threshold_dropout (float): Threshold for dropout detection.
#     alpha (float): Power parameter (default is 1).

#     Returns:
#     numpy.ndarray: Binary mask indicating dropout regions.
#     """
#     # Calculate standardized residuals
#     zscores = shorebased_standard_residuals(dmri, spredw)

#     # Ensure spredw is not too small
#     spredw = np.maximum(spredw, 0.001)

#     # Calculate dropout scores voxel-wise
#     d_voxelwise = zscores / np.power(spredw, alpha)

#     # Reshape to a 3D volume and calculate the slice-wise median
#     dims = dmri.shape
#     d_isn = d_voxelwise.reshape((dims[0] * dims[1], dims[2], dims[3]))
#     d_slicewise = np.median(d_isn, axis=0)

#     # Estimate the standard deviation using MAD
#     sigma_hat = 1.4826 * stats.median_absolute_deviation(d_slicewise)
#     dscore_slice = (d_slicewise - np.median(d_slicewise, axis=0)) / sigma_hat

#     # Detect dropout based on the threshold
#     # dropout_slice = [ dscore_slice =< - threshold_dropout ] = 0
#     # dropout_slice = [ dscore_slice > - threshold_dropout ] = 1
#     dropout_slice = (dscore_slice <= -threshold_dropout).astype(int)


#     return dropout_slice



class GMModel:
    """
    2-component Gaussian Mixture Model for outlier detection
    Based on the C++ implementation in dwisliceoutliergmm.cpp
    """
    
    def __init__(self, max_iters=50, eps=1e-3, reg_covar=1e-6):
        self.niter = max_iters
        self.tol = eps
        self.reg = reg_covar
        
    def fit(self, x):
        """Fit GMM to vector x using Expectation-Maximization"""
        x = np.asarray(x).flatten()
        
        # Initialize
        self._init(x)
        
        ll0 = -np.inf
        
        # EM algorithm
        for n in range(self.niter):
            ll = self._e_step(x)
            self._m_step(x)
            
            # Check convergence
            if np.abs(ll - ll0) < self.tol:
                break
            ll0 = ll
            
    def posterior(self):
        """Get posterior probability of inlier class"""
        return np.exp(self.Rin)
    
    def _init(self, x):
        """Initialize inlier and outlier classes"""
        med = np.median(x)
        mad = np.median(np.abs(x - med)) * 1.4826
        
        # Initialize means (shift +1 for log-Gaussians)
        self.Min = med
        self.Mout = med + 1.0
        
        # Initialize standard deviations
        self.Sin = mad
        self.Sout = mad + 1.0
        
        # Initialize mixing proportions
        self.Pin = 0.9
        self.Pout = 0.1
        
    def _e_step(self, x):
        """E-step: update sample log-responsibilities and return log-likelihood"""
        # Compute log responsibilities
        self.Rin = self._log_gaussian(x, self.Min, self.Sin) + np.log(self.Pin)
        self.Rout = self._log_gaussian(x, self.Mout, self.Sout) + np.log(self.Pout)
        
        # Normalize
        log_prob_norm = np.logaddexp(self.Rin, self.Rout)
        self.Rin -= log_prob_norm
        self.Rout -= log_prob_norm
        
        return np.mean(log_prob_norm)
    
    def _m_step(self, x):
        """M-step: update component mean and variance"""
        eps = np.finfo(float).eps
        
        # Compute weights
        w1 = np.exp(self.Rin) + eps
        w2 = np.exp(self.Rout) + eps
        
        # Update mixing proportions
        self.Pin = np.mean(w1)
        self.Pout = np.mean(w2)
        
        # Update means
        self.Min = self._average(x, w1)
        self.Mout = self._average(x, w2)
        
        # Update standard deviations
        self.Sin = np.sqrt(self._average((x - self.Min)**2, w1) + self.reg)
        self.Sout = np.sqrt(self._average((x - self.Mout)**2, w2) + self.reg)
    
    def _log_gaussian(self, x, mu, sigma):
        """Compute log probability under Gaussian"""
        resp = (x - mu) / sigma
        resp = -(resp**2 + np.log(2 * np.pi)) / 2 - np.log(sigma)
        return resp
    
    def _average(self, x, w):
        """Weighted average"""
        return np.dot(x, w) / np.sum(w)


def organize_shells(bvals, threshold=50):
    """
    Organize gradient directions into shells
    
    Parameters:
    -----------
    bvals : ndarray
        B-values
    threshold : float
        Threshold for grouping b-values into shells
        
    Returns:
    --------
    shells : list of lists
        Each shell contains volume indices
    """
    unique_bvals = []
    shells = []
    
    for i, bval in enumerate(bvals):
        # Find matching shell
        matched = False
        for j, ubval in enumerate(unique_bvals):
            if np.abs(bval - ubval) < threshold:
                shells[j].append(i)
                matched = True
                break
        
        if not matched:
            unique_bvals.append(bval)
            shells.append([i])
    
    return shells


def compute_rmse_slicewise(data, pred, mask, mb=1):
    """
    Compute root mean squared error for each slice
    
    Parameters:
    -----------
    data : ndarray (nx, ny, nz, nv)
        DWI data
    pred : ndarray (nx, ny, nz, nv)
        Signal prediction
    mask : ndarray (nx, ny, nz)
        Brain mask
    mb : int
        Multiband factor
        
    Returns:
    --------
    E : ndarray (ne, nv)
        RMSE matrix (ne = nz/mb excitations, nv = volumes)
    """
    nx, ny, nz, nv = data.shape
    ne = nz // mb  # Number of excitations
    
    # Initialize error and count matrices
    E_full = np.zeros((nz, nv))
    N_full = np.zeros((nz, nv), dtype=int)
    
    # For each volume and slice
    for v in range(nv):
        for z in range(nz):
            # Compute error for this slice
            data_slice = data[:, :, z, v]
            pred_slice = pred[:, :, z, v]
            mask_slice = mask[:, :, z]
            
            # Apply mask
            valid = mask_slice > 0
            
            if np.any(valid):
                diff = data_slice[valid] - pred_slice[valid]
                E_full[z, v] = np.sum(diff**2)
                N_full[z, v] = np.sum(valid)
    
    # Combine multiband slices
    E_mb = np.zeros((ne, nv))
    N_mb = np.zeros((ne, nv), dtype=int)
    
    for b in range(nz // ne):
        E_mb += E_full[b*ne:(b+1)*ne, :]
        N_mb += N_full[b*ne:(b+1)*ne, :]
    
    # Compute RMSE
    E = np.zeros((ne, nv))
    valid_mask = N_mb > 0
    E[valid_mask] = np.sqrt(E_mb[valid_mask] / N_mb[valid_mask])
    
    return E


def fedi_dmri_outliersgmm(data, pred, mask, bvals, mb=1):
    """
    Detect and reweigh outlier slices using Bayesian GMM modeling
    
    Parameters:
    -----------
    data : ndarray (nx, ny, nz, nv)
        DWI data
    pred : ndarray (nx, ny, nz, nv)
        Signal prediction
    mask : ndarray (nx, ny, nz)
        Brain mask
    bvals : ndarray (nv,)
        B-values
    mb : int
        Multiband factor
        
    Returns:
    --------
    W : ndarray (nz, nv)
        Slice weights
    """
    nx, ny, nz, nv = data.shape
    ne = nz // mb
    
    # Organize into shells
    shells = organize_shells(bvals)
    
    # Compute RMSE
    E = compute_rmse_slicewise(data, pred, mask, mb)
    
    # Compute weights using GMM
    W = np.ones_like(E)
    gmm = GMModel()
    
    for s, shell in enumerate(shells):
        # Collect residuals for this shell
        res = []
        for v in shell:
            res.extend(E[:, v])
        res = np.array(res)
        
        # Clip at non-zero minimum
        nzmin = np.min(res[res > 0]) if np.any(res > 0) else 1e-10
        logres = np.log(np.maximum(res, nzmin))
        
        # Fit GMM
        gmm.fit(logres)
        
        # Get posterior probabilities
        p = gmm.posterior()
        
        # Assign to weight matrix
        k = 0
        for v in shell:
            W[:, v] = p[k*ne:(k+1)*ne]
            k += 1
    
    # Replicate for multiband and round to 6 decimals
    W_full = W.repeat(mb, axis=0)
    W_full = np.round(W_full * 1e6) * 1e-6
    
    return W_full


def gmm_weighting(fdmri, fspred, mask, bvals, bvecs, outpath, filename_gmm):
    """
    Calculate GMM weights using integrated Python implementation.
    """
    print("Calculate GMM Weights")
    
    # Load data
    dmri, affine = load_nifti(fdmri)
    spred, _ = load_nifti(fspred)
    mask_data, _ = load_nifti(mask)
    
    # Load bvals
    if isinstance(bvals, str):
        bvals_array = np.loadtxt(bvals)
    else:
        bvals_array = bvals
    
    # Ensure mask is binary
    mask_data = (mask_data > 0).astype(float)
    
    # Compute weights using integrated GMM function
    weights_raw = fedi_dmri_outliersgmm(dmri, spred, mask_data, bvals_array, mb=1)
    
    # Take square root (as in original implementation)
    weights_raw = np.sqrt(weights_raw)
    
    # Save weights
    output_path = os.path.join(outpath, filename_gmm)
    np.savetxt(output_path, weights_raw, delimiter=',', fmt='%.6f')

    # Call the function to save the figure
    filename_gmm_png = filename_gmm.replace(".txt", ".png")
    save_figure_onebox(weights=weights_raw, clim_min=0, clim_max=1, title="Gaussian Mixture Model", outpath=outpath,fignamepng=filename_gmm_png)

    # save weights as a 4D-volume
    weights_4D=np.zeros_like(dmri)

    # weights 2D --> 4D
    for s in range(weights_raw.shape[0]):
        for v in range(weights_raw.shape[1]):
            weights_4D[:,:,s,v]=weights_raw[s,v]

    filename_gmm_nii = filename_gmm.replace(".txt", ".nii.gz")
    save_nifti(os.path.join(outpath, filename_gmm_nii), weights_4D, affine)

    return weights_raw


# Parse the command-line arguments
args = parser.parse_args()

fdmri = args.dmri
fspred= args.spred
fdmrigmm = args.dmrigmm
fspredgmm= args.spredgmm

mask = args.mask
maskgmm = args.maskgmm

fbval = args.bval
fbvec = args.bvec


outpath = args.outpath

# Extract and split the thresholds from the parsed arguments
thresholds = args.thresholds.split(",")
lowerThreshold, upperThreshold = float(thresholds[0]), float(thresholds[1])

zscoremetric=args.zscoremetric
weightscalingmethod = args.scalingmethod


# fsliceweights_mzscore = args.fsliceweights_mzscore
# fsliceweights_= args.fsliceweights_angle_neighbors
# fsliceweights_corre_neighbors = args.fsliceweights_corre_neighbors
# fsliceweights_gmmodel = args.fsliceweights_gmmodel
# fsliceweights_shore=args.fsliceweights_shore



dmri, affine = load_nifti(fdmri)
print("dmri.shape: ", dmri.shape)


if fspred is not None and os.path.isfile(fspred):
    spred, saffine = load_nifti(fspred)
    print("spred.shape:", spred.shape)
else:
    fspred = None

    print("No spred given")

bvals, bvecs = read_bvals_bvecs(fbval, fbvec)




print("bvals.shape: ", bvals.shape)
print("bvecs.shape: ", bvecs.shape)

# Check if a mask filename was provided
fmask = None  # Initialize the mask as None
if mask is not None:
    fmask, affinemask = load_nifti(mask)
    print("fmask.shape: ", fmask.shape)

# add if mask provided, it should be multiplied by the dmri and spred file.


if args.fsliceweights_gmmodel is not None and fspred is not None:

    gmm_weighting(fdmri=fdmrigmm, fspred=fspredgmm, mask=maskgmm, bvals=fbval, bvecs=fbvec, outpath=outpath, filename_gmm=args.fsliceweights_gmmodel)

if args.fsliceweights_mzscore is not None:
    if fspred is not None:
        dmri_mzscore = spred
    else:
        dmri_mzscore = dmri

    mzscore_weighting(dmri=dmri_mzscore, fmask=fmask, bvals=bvals,  \
        outpath=outpath, \
        metric=zscoremetric, \
        lowerThreshold=lowerThreshold, \
        upperThreshold=upperThreshold, \
        weightscalingmethod=weightscalingmethod, \
        fsliceweights_mzscore=args.fsliceweights_mzscore)

if args.fsliceweights_angle_neighbors is not None:
    if fspred is not None:
        dmri_neighbors = spred
    else:
        dmri_neighbors = dmri

    neighbors_weighting(dmri=dmri_neighbors, bvals=bvals, bvecs=bvecs, b0_threshold=0, 
        std_scale=3, filename_angle_neighbors=args.fsliceweights_angle_neighbors, filename_correlation_neighbors=args.fsliceweights_corre_neighbors)




if args.fvoxelweights_shorebased is not None and fspred is not None:
    shorebased_weighting_voxelwise(dmri=dmri,affine=affine,spred=spred,outpath=outpath,filename=args.fvoxelweights_shorebased)
    # shore_weighting(dmri=dmri, spred=spred, fsliceweights_shore=args.fsliceweights_shore)