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

import os
import numpy as np
import nibabel as nib
import argparse
import warnings
import time
# from dipy.reconst.brainsuite_shore import ShoreModel, shore_matrix
from dipy.reconst.brainsuite_shore import BrainSuiteShoreModel as ShoreModel
from dipy.reconst.brainsuite_shore import brainsuite_shore_basis as shore_matrix

from dipy.core.gradients import gradient_table
from dipy.data import get_fnames, get_sphere
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti, save_nifti
from dipy.align import motion_correction
from dipy.viz import window, actor
import dipy


###############################################################################
# Instantiate the SHORE Model.
# ``radial_order`` is the radial order of the SHORE basis.
# ``zeta`` is the scale factor of the SHORE basis.
# ``lambdaN`` and ``lambdaL`` are the radial and angular regularization constants, respectively.
# For details regarding these four parameters see [Cheng2011]_ and [Merlet2013]_.
###############################################################################



zeta = 700
tau=1 / (4 * np.pi**2)
lambdaN = 1e-8
lambdaL = 1e-8
S0=1

# Create an argument parser, Add arguments for directory path and mask prefix, Parse the command-line arguments
parser = argparse.ArgumentParser(description="Continuous and analytical diffusion signal modelling with 3D-SHORE.") 
parser.add_argument("-d", "--dmri", required=True, help="dmri")
parser.add_argument("-a", "--bval", required=True, help="bval")
parser.add_argument("-e", "--bvec_in", required=True, help="bvec of the input data")
parser.add_argument("-u", "--bvec_out", required=True, help="bvec for the output data")
parser.add_argument("-m", "--mask", required=False, help="Path to mask file, required to reduce computation time")
parser.add_argument("-do_not_use_mask", action="store_true", help="Flag to indicate not to use the mask, even if provided")
parser.add_argument("-w", "--weights", required=False, help="weights txt file")
parser.add_argument("-s", "--fspred", required=True, help="predicted dmri file name")
# parser.add_argument("-r", "--order", required=True, help="Shore order, 2: 8 coefs; 4:29 coefs; 6: 72 coefs; 8:145 coefs.")


args = parser.parse_args()


# variable
fdmri= args.dmri
fbval=args.bval
fbvec_in=args.bvec_in

fbvec_out=args.bvec_out


fspred=args.fspred
fname_weights=args.weights

dmri, affine = load_nifti(fdmri)


# Logic for handling the mask based on the -do_not_use_mask flag and presence of a mask path
if args.do_not_use_mask:
    # Creating a default mask with ones implies not masking out any part of the dmri data
    mask = np.ones((dmri.shape[0], dmri.shape[1], dmri.shape[2]), dtype=np.uint8)
elif args.mask:
    # If the -do_not_use_mask flag is not set and a mask path is provided, load the specified mask
    mask, affinemask = load_nifti(args.mask)
else:
	print("Check mask status...")
# Not sure, add small value for slices that contains only zeros (this make issues/warnings for fitting)
dmri=dmri

# Set negative values to 0
dmri[dmri < 0] = 0


# bvalsraw, bvecsraw = read_bvals_bvecs(fbval, fbvec)
bvals, bvecs_in = read_bvals_bvecs(fbval, fbvec_in)

bvals, bvecs_out = read_bvals_bvecs(fbval, fbvec_out)

gtab_in = gradient_table(bvals, bvecs_in, b0_threshold=0)

gtab_out = gradient_table(bvals, bvecs_out, b0_threshold=0)

# Load weights txt/niftii file
if fname_weights.endswith('.txt'):
    weightsraw = np.loadtxt(fname_weights, delimiter=',')
    fitting_method = "slice"
elif fname_weights.endswith('.nii.gz'):
    weightsraw, affine = load_nifti(fname_weights)
    fitting_method = "voxel"



# Set the radial_order based on the number of gradients (dmri.shape[3]).
# - More than 50 gradients: radial_order set to 6 (72 coefficients).
# - More than 24 but 50 or fewer gradients: radial_order set to 4 (29 coefficients).
# - More than 12 but 24 or fewer gradients: radial_order set to 2 (8 coefficients).
# - 12 or fewer gradients: This case is not covered. Assuming a default or error might be needed.

if dmri.shape[3] > 50:
    radial_order = 6
elif dmri.shape[3] > 24:
    radial_order = 4
elif dmri.shape[3] > 12:
    radial_order = 2




weightsraw = weightsraw * 1.5

weightsraw [weightsraw > 1]=1

# SHORE Fitting and Prediction per slice
# dmri=dmri[50:55,50:53,10:27,:]
# mask=mask[50:55,50:53,10:27]
spred4D=np.zeros_like(dmri)
dmri_slice=np.zeros_like(dmri)
print("-----------------------------------------------------------")
print("dmri.shape:", dmri.shape)
print("-----------------------------------------------------------")
print("Start SHORE Reconstruction. Fitting_method : ", fitting_method)
print("-----------------------------------------------------------")
start_time = time.time()

# constrain_e0=True should be always True to do weighted L2 Loss function

print("dmri.shape[2]",dmri.shape[2])
for indxslice in range(0,dmri.shape[2]):



	# print("--------------------------------------------------")
	print("-------------------------------------> Slice:", indxslice)
	# print("--------------------------------------------------")


	if fitting_method == "slice":
		
		dmri_slice = dmri[:,:,indxslice,:]
		mask_slice = mask[:,:,indxslice]
		mask_slice[0,0]=1 # to avoid some issues with the SHORE/CVXPY optimization process
		weights_slice = np.diag(np.sqrt(weightsraw[indxslice,:]))
		# print("------------------------------------")
		# print("dmri_slice.shape:", dmri_slice.shape)
		# print("mask_slice.shape:", mask_slice.shape)
		# print("------------------------------------")
		# print("1. Instantiate the SHORE Model")
		# shore_model = ShoreModel(gtab_in,radial_order=radial_order, zeta=zeta, lambdaN=lambdaN, lambdaL=lambdaL, constrain_e0=True, positive_constraint=False, weights=weights_slice)
		# shore_model = ShoreModel(gtab_in,radial_order=radial_order, zeta=zeta, lambdaN=lambdaN, lambdaL=lambdaL, regularization="L2")
		shore_model = ShoreModel(gtab_in,radial_order=radial_order, zeta=zeta, lambdaN=lambdaN, lambdaL=lambdaL, regularization="FEDI", weights=weights_slice)

		# print("2. Fit the SHORE model to the data")
		shore_fit = shore_model.fit(dmri_slice,mask_slice)

		# print("3. Generate fitted model coefficients:")
		shore_coeffs = shore_fit.shore_coeff
		print("shore_coeffs.shape: ", shore_coeffs.shape)
	 
		# print("4. Generate SHORE basis for prediction:")
		shore_basis = shore_matrix(radial_order=radial_order, zeta=zeta, gtab=gtab_out, tau=tau)
		# print("shore_basis", shore_basis.shape)

		# print("5. Calculate the signal prediction using the SHORE coefficients:")
		# B03D[:,:,indxslice] = S0 * shore_coeffs[:,:,0]
		spred4D[:,:,indxslice,:] = S0 * np.dot(shore_coeffs, shore_basis.T)
		# print("signal_prediction.shape :",spred4D.shape)

	elif fitting_method == "voxel":


		for i in range(dmri.shape[0]):
			for j in range(dmri.shape[1]):
				print("-------------------------------------> Slice:", indxslice)
				dmri_slice = dmri[i,j,indxslice,:]
				mask_slice = mask[i,j,indxslice]
				weights_voxel = np.diag(weightsraw[i,j,indxslice,:])
				print("Instantiate the SHORE Model:")
				# For cvxpy_solver: one of OSQP (default), ECOS, ECOS_BB,  SCIPY, SCS was expected.
				# shore_model = ShoreModel(gtab_in,radial_order=radial_order, zeta=zeta, lambdaN=lambdaN, lambdaL=lambdaL, constrain_e0=True, positive_constraint=False, weights=weights_voxel,cvxpy_solver='OSQP')
				shore_model = ShoreModel(gtab_in,radial_order=radial_order, zeta=zeta, lambdaN=lambdaN, lambdaL=lambdaL, regularization="FEDI", weights=weights_voxel)
				# shore_model = ShoreModel(gtab_in,radial_order=radial_order, zeta=zeta, lambdaN=lambdaN, lambdaL=lambdaL, regularization="L2")

				print("Fit the SHORE model to the data")
				shore_fit = shore_model.fit(dmri_slice,mask_slice)

				print("Generate the coffes of the fitted model:")
				shore_coeffs = shore_fit.shore_coeff
				print("shore_coeffs.shape: ", shore_coeffs.shape)
			 
				print("Generate the SHORE basis for prediction:")
				shore_basis = shore_matrix(radial_order=radial_order, zeta=zeta, gtab=gtab_out, tau=tau)
				print("shore_basis", shore_basis.shape)

				print("Calculate the signal prediction using the SHORE coefficients")
				# B03D[:,:,indxslice] = S0 * shore_coeffs[:,:,0]
				spred4D[i,j,indxslice,:] = S0 * np.dot(shore_coeffs, shore_basis.T)
				# print("signal_prediction.shape :",spred4D.shape)

end_time = time.time()
duration = end_time - start_time
print(f"The ShoreRecon block took {duration} seconds to execute.")

# Save the predicted diffusion signal
save_nifti(fspred, spred4D, affine)





