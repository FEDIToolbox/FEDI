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

import sys
import numpy as np

def grad_index(grad4cls_file, grad_output_file, indx_output_file):
    # Load bvecs and bvals
    grad4cls = np.loadtxt(grad4cls_file)


    # Check if the dimensions match
    if grad4cls.shape[1] != 4 :
        print("Error: Incorrect dimensions of grad file!")
        return

    nb = grad4cls.shape[0]
    
    cycle_length = 1  # Length of the repeating sequence
    sequence = np.arange(0, nb)  # Generate a sequence from 0 to nb-1
    repeating_sequence = sequence % cycle_length + 1
    fifth_column = np.reshape(repeating_sequence, (nb, 1))
    fifth_column_oneline = np.reshape(repeating_sequence, (1, nb))


    grad = np.concatenate((grad4cls, fifth_column), axis=1)  # Append 0 0 0 0 row for b=0 direction

    # Save grad.txt and index files
    np.savetxt(grad_output_file, grad, fmt='%1.6f %1.6f %1.6f %i %i')
    np.savetxt(indx_output_file, fifth_column_oneline, fmt='%i')

    print("Conversion completed. Grad 5 cls and Index files saved")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_grad5_index.py <grad4cls_file> <grad_output_file> <indx_output_file>")
        sys.exit(1)

    grad4cls_file = sys.argv[1]
    grad_output_file = sys.argv[2]
    indx_output_file = sys.argv[3]

    grad_index(grad4cls_file, grad_output_file, indx_output_file)


