import sys
import numpy as np
import nibabel as nib
from utils import ws_dilate

def adjust_parcellation(seg_data, regional_data):
    """
    Ensures that the white matter regions in the parcellation segmentation (regional_data)
    overlap white matter as in the tissue segmentation (seg_data).
    
    This function processes the input segmentation and parcellation arrays to align their white
    matter regions by adjusting the labels accordingly. Specifically:
    
    - The tissue segmentation (seg_data) may include white matter regions (e.g., IZ and SP for left and right hemispheres),
      and this function modifies the parcellation segmentation (regional_data) to include the same white matter areas.
    - Conflicting regions between the parcellation and tissue segmentations are removed.
    - Watershed dilation is applied to expand the areas for labels in the parcellation.
    - The final result ensures that the white matter parts in the parcellation segmentation overlap correctly with the
      tissue segmentation.
    
    Parameters:
    ----------
    seg_data : numpy array
        The segmentation data array representing tissue segmentation, including different brain regions and labels.
    
    regional_data : numpy array
        The parcellation data array representing the parcellation segmentation. This array will be adjusted to ensure
        it shares the same white matter as the tissue segmentation.
    
    Returns:
    -------
    numpy array
        The modified parcellation data array, where white matter regions are aligned with those in the tissue segmentation.
    """

    # Prepare segmentation image for registration
    seg_data[np.isin(seg_data, np.array([114, 116]))] = 120  # Left IZ and SP
    seg_data[np.isin(seg_data, np.array([115, 117]))] = 121  # Right IZ and SP

    # Define cortex labels
    cortex_labels = np.concatenate(
        (
            np.arange(1, 37),
            np.arange(39, 41),
            np.arange(43, 71),
            np.arange(79, 91),
            np.arange(131, 137),
        ),
        axis=0,
    )

    # Extract odd and even labels
    odd_labels = cortex_labels[cortex_labels % 2 != 0]
    even_labels = cortex_labels[cortex_labels % 2 == 0]

    # Filter out irrelevant regional data
    regional_data[np.isin(regional_data, cortex_labels, invert=True)] = 0
    regional_data[seg_data == 0] = 0

    # Create masks for odd and even labels
    odd_labels_mask = np.logical_and(
        np.isin(regional_data, even_labels), np.isin(seg_data, np.array([120, 112]))
    )
    even_labels_mask = np.logical_and(
        np.isin(regional_data, odd_labels), np.isin(seg_data, np.array([121, 113]))
    )

    # Remove conflicting regions
    regional_data[odd_labels_mask] = 0
    regional_data[even_labels_mask] = 0

    # Dilate watershed areas

    regional_data_even = regional_data.copy()
    regional_data_even[np.isin(regional_data_even, even_labels, invert=0)] = 0

    regional_data_odd = regional_data.copy()
    regional_data_odd[np.isin(regional_data_odd, odd_labels, invert=0)] = 0

    wsd_img_even = ws_dilate(regional_data_even, 20)
    wsd_img_odd = ws_dilate(regional_data_odd, 20)

    # Add new labels
    mask = np.logical_and(
        regional_data != 0, np.isin(seg_data, np.array([112, 113, 120, 121]))
    )

    parcel_data = seg_data.copy()
    parcel_data[mask] = regional_data[mask]
    parcel_data[np.isin(parcel_data, np.array([112, 113]))] = 0

    # Assign watershed-dilated areas
    parcel_data[seg_data == 112] = wsd_img_even[seg_data == 112]
    parcel_data[seg_data == 113] = wsd_img_odd[seg_data == 113]

    return parcel_data

def main():
    # Load the segmentation and parcellation data from files
    path_seg = sys.argv[1]
    path_parcel = sys.argv[2]

    seg = nib.load(path_seg)
    seg_data = seg.get_fdata()

    regional = nib.load(path_parcel)
    regional_data = regional.get_fdata()

    # Process the segmentation and parcellation data
    parcel_data = adjust_parcellation(seg_data, regional_data)

    # Convert the array to signed integer type using nibabel and save the result
    output_seg = nib.Nifti1Image(parcel_data.astype(np.int32), seg.affine, seg.header)
    nib.save(output_seg, path_parcel.split(".nii")[0] + "_adjusted.nii.gz")


if __name__ == "__main__":
    main()