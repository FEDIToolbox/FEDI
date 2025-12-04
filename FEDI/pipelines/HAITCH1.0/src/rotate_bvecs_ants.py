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
from scipy.io import loadmat
import numpy as np

# https://github.com/nipy/nipype/blob/f2bbcc917899c98102bdeb84db61ea4b84cbf2f5/nipype/workflows/dmri/fsl/utils.py#L516

"""
Rotates the input bvec file accordingly with a list of matrices.

.. note:: the input affine matrix transforms points in the destination
  image to their corresponding coordinates in the original image.
  Therefore, this matrix should be inverted first, as we want to know
  the target position of :math:`\\vec{r}`.

"""

# Define command-line arguments
parser = argparse.ArgumentParser(description="Apply transformation matrix to bvecs.")
parser.add_argument("-e", "--bvecs", required=True, help="Path to bvec file")
parser.add_argument("-n", "--bvecsnew", required=True, help="Path to new bvecs file")
parser.add_argument("-m", "--pathofmatfile", required=True, help="Path to the folder containing transformation matrices")
parser.add_argument("-s", "--startprefix", default="Transform_v", help="Prefix for transformation matrix files")
parser.add_argument("-d", "--endprefix", default="_0GenericAffine.mat", help="Suffix for transformation matrix files")
args = parser.parse_args()


bvecs = np.loadtxt(args.bvecs).T
new_bvecs = []

in_matrix = [f"{args.pathofmatfile}/{args.startprefix}{volumeindx}{args.endprefix}" for volumeindx in range(len(bvecs))]

if len(bvecs) != len(in_matrix):
    raise RuntimeError(('Number of b-vectors (%d) and rotation '
                        'matrices (%d) should match.') % (len(bvecs),
                                                          len(in_matrix)))

for bvec, mat in zip(bvecs, in_matrix):
    if np.all(bvec == 0.0):
        new_bvecs.append(bvec)
    else:
        trans = loadmat(mat)
        matrice = trans['AffineTransform_double_3_3'][:9].reshape((3, 3))
        invrot = np.linalg.inv(matrice)
        newbvec = invrot.dot(bvec)
        new_bvecs.append((newbvec / np.linalg.norm(newbvec)))

# Save new bvecs
np.savetxt(args.bvecsnew, np.array(new_bvecs).T, fmt=b'%0.15f')




