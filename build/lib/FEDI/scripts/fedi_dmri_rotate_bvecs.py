#!/usr/bin/env python3.10


# See https://github.com/nipy/nipype/blob/f2bbcc917899c98102bdeb84db61ea4b84cbf2f5/nipype/workflows/dmri/fsl/utils.py#L516

"""
Rotates the input bvec file accordingly with a list of matrices.

.. note:: the input affine matrix transforms points in the destination
  image to their corresponding coordinates in the original image.
  Therefore, this matrix should be inverted first, as we want to know
  the target position of :math:`\\vec{r}`.

"""

import argparse
from scipy.io import loadmat
import numpy as np

from FEDI.utils.common import FEDI_ArgumentParser, Metavar


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m \n\n    "
            "Rotate the bvec accordingly with a list of ANTs transformation matrices.\n"
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2024. "
            "Haitch: A framework for distortion and motion correction in fetal multi-shell "
            "diffusion-weighted MRI. arXiv preprint arXiv:2406.20042."
        ),
        formatter_class=FEDI_ArgumentParser
    )

    mandatory = parser.add_argument_group('\033[1mMANDATORY OPTIONS\033[0m')

    mandatory.add_argument("-e", "--bvecs", required=True, metavar=Metavar.file, help="Path to the input bvecs file. Example: bvecs")
    mandatory.add_argument("-n", "--robvecs", required=True, metavar=Metavar.file, help="Path to the output rotated bvecs file. Example: rotated_bvecs.")
    mandatory.add_argument("-m", "--pathofmatfile", required=True, metavar=Metavar.folder, help="Path to the directory containing transformation matrices.")
    mandatory.add_argument("-s", "--prefix", default="Transform_v", metavar=Metavar.str, help="Prefix for transformation matrix files (default: 'Transform_v').")
    mandatory.add_argument("-d", "--suffix", default="_0GenericAffine.mat", metavar=Metavar.str, help="Suffix for transformation matrix files (default: '_0GenericAffine.mat'). Name of matrice should prefix+volume_index+suffix")

    
    return parser.parse_args()



def main():
    args = parse_arguments()

    # Ensure the input files and directories exist
    if not os.path.isfile(args.bvecs):
        raise FileNotFoundError(f"Input bvecs file not found: {args.bvecs}")
    if not os.path.isdir(args.pathofmatfile):
        raise FileNotFoundError(f"Transformation matrix directory not found: {args.pathofmatfile}")

    bvecs = np.loadtxt(args.bvecs).T
    new_bvecs = []

    in_matrix = [os.path.join(args.pathofmatfile, f"{args.prefix}{volumeindx}{args.suffix}")
                 for volumeindx in range(len(bvecs))]

    if len(bvecs) != len(in_matrix):
        raise RuntimeError(('Number of b-vectors (%d) and rotation matrices (%d) should match.')
                           % (len(bvecs), len(in_matrix)))

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
    np.savetxt(args.robvecs, np.array(new_bvecs).T, fmt='%0.15f')

    print(f"Rotated bvecs saved to: {args.robvecs}")

if __name__ == "__main__":
    main()

