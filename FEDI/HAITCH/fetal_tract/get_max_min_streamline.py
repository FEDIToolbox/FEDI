import nibabel as nib
import numpy as np
import sys

def calculate_streamline_lengths(seg_data, voxel_dimensions, analysis_type='tract'):
    """
    Calculate the minimum and maximum stremline lengths in mm based on the provided mask volume.

    This function computes the minimum and maximum stremline lengths derived from a volumetric
    mask of the brain. The mask is typically obtained as the whole brain mask generated 
    using the `5TTgen` function from the MRtrix3 toolkit. The stremline lengths are 
    calculated based on the cube root of the mask volume, which is derived from the 
    voxel size and the sum of all voxel values within the mask.

    Parameters:
    ----------
    file_name_mask : str
        The file path to the NIfTI file containing the whole brain mask output from 
        the `5TTgen` function. This mask should represent the brain's volume used 
        in subsequent tractography or connectivity analyses.
    
    analysis_type : str, optional
        Specifies the type of analysis to guide the calculation of stremline lengths. 
        Valid options are:
        - 'tract': For tract analysis (default).
        - 'connectivity': For connectivity analysis.
    
    Returns:
    -------
    tuple
        A tuple containing two integers:
        - minlength : int
            The minimum stremline length in mm rounded to the nearest integer.
        - maxlength : int
            The maximum stremline length in mm rounded to the nearest integer.

    Note:
    -----
    - The mask provided as `file_name_mask` should be the output from the `5TTgen` function,
      typically representing the whole brain mask.
    - The stremline length calculations are based on the volume of the mask. The minimum stremline length
      differs depending on whether the analysis is for tractography or connectivity.

    """

    # Calculate the mask volume
    mask_volume = sum(seg_data.flatten()) * np.prod(voxel_dimensions)

    # Calculate stremline length based on volume
    stremline_length = np.cbrt(mask_volume)

    # Determine minlength based on analysis type
    if analysis_type == 'connectivity':
        minlength = stremline_length / 4.5
    else:
        minlength = stremline_length / 1.6

    # Calculate maxlength
    maxlength = stremline_length / 0.5

    # Return rounded lengths
    return round(minlength), round(maxlength)

def main():
    # Get file name from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python script.py <file_name_mask> [analysis_type (0 for tract, 1 for connectivity)]")
        sys.exit(1)
    
    file_name_mask = sys.argv[1]

    # Load the segmentation file
    seg = nib.load(file_name_mask)
    seg_data = seg.get_fdata()

    # Get voxel size
    voxel_dimensions = seg.header.get_zooms()

    # Determine analysis type from the second argument
    analysis_type = 'tract'
    if len(sys.argv) > 2 and sys.argv[2] == '1':
        analysis_type = 'connectivity'

    # Call the function and get the result
    minlength, maxlength = calculate_streamline_lengths(seg_data, voxel_dimensions, analysis_type)

    # Print the result
    print(minlength, maxlength)

if __name__ == "__main__":
    main()