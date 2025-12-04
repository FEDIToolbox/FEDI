import nibabel as nib
import numpy as np
import SimpleITK as sitk
from scipy.ndimage import binary_dilation
from utils import add_spine_label, ws_dilate

import sys

SPINE = 160
BRAINSTEM = 94

def dilate_in_axis(image, label=1, x=0, y=0, z=0):
    """Dilate the given label in the image along the specified axes.

    Args:
        image (NumPy array): Binary Mask
        label (int, optional): Label to dilate. Defaults to 1.
        x (int, optional): Dilate in the x-axis. Defaults to 0.
        y (int, optional): Dilate in the y-axis. Defaults to 0.
        z (int, optional): Delete in the z-axis.. Defaults to 0.

    Returns:
        NumPy array : Dilated binary mask.
    """
    mask = sitk.GetImageFromArray((image == label).astype(np.uint16))
    bd_img = sitk.BinaryDilate(mask, [x, y, z])
    return sitk.GetArrayFromImage(bd_img)

def parcellation_ctx_wm(seg_np, parcel_np, voxel_size):
    """
    Segments and divides pacortex parcellations into their white matter (WM) and cortical gray matter (GM) components 
    for tract extraction, ensuring compatibility with FreeSurfer parcellations. This is crucial for tractography-based 
    analysis, such as using `tractquerier`, by providing accurate delineation of cortical regions and white matter tracts.

    The function performs multiple steps to refine and split regions of interest (ROIs) based on tissue type and cortical 
    parcellations:
       
    1. **External Capsule Masks**: Creates a label mask for the external capsule.
       
    2. **Spine and Brainstem Labeling**: Ensures that there is a spine label in the segmentation image.
       
    3. **Parcellating Cortical Areas**: 
       - Subdivides specific cortical regions, such as the middle frontal gyrus and the Rollandic operculum, into more 
         detailed parts to support precise tract extraction.

    4. **Gray Matter and White Matter Segmentation**: 
       - Identifies cortical gray matter (GM) and white matter (WM) regions based on the input tissue segmentation (`seg_np`).
       - Applies a binary dilation to gray matter regions and adjusts neighboring white matter regions to ensure proper 
         boundaries between cortical gray matter and white matter.

    5. **Final Parcellation**: Combines the processed gray and white matter masks with the original cortical parcellation 
       to generate the final labeled image. White matter regions are differentiated by adding specific constants (e.g., 
       1000 for GM, 2000 for WM) to the labels.

    Args:
        seg_np (numpy.ndarray): Tissue type segmentation array, where different tissues (e.g., gray matter, white matter) 
                                are labeled with specific integers.
        parcel_np (numpy.ndarray): Cortical parcellation image array, with unique labels for different cortical regions.
        voxel_size (int): Voxel size used in the image, particularly for adding and refining labels in the parcellation.

    Returns:
        numpy.ndarray: A NumPy array representing the final parcellation, where the cortical gray matter and white 
                       matter have been appropriately segmented and labeled, ready for tractography.
    """
 
    # Right External Capsule Mask
    R_Lentiform_bd = dilate_in_axis(parcel_np, 74, z=4)
    R_Insula_bd = dilate_in_axis(parcel_np, 30, z=4)
    R_Lentiform_bd[R_Insula_bd == 0] = 0
    R_Lentiform_bd[np.isin(seg_np, [115, 117, 121], invert=True)] = 0
    R_Lentiform_bd = dilate_in_axis(R_Lentiform_bd, x=1)
    R_Lentiform_bd[R_Insula_bd == 0] = 0
    R_Lentiform_bd[np.isin(seg_np, [115, 117, 121], invert=True)] = 0

    # Left External Capsule Mask
    L_Lentiform_bd = dilate_in_axis(parcel_np, 73, z=4)
    L_Insula_bd = dilate_in_axis(parcel_np, 29, z=4)
    L_Lentiform_bd[L_Insula_bd == 0] = 0
    L_Lentiform_bd[np.isin(seg_np, [114, 116, 120], invert=True)] = 0
    L_Lentiform_bd = dilate_in_axis(L_Lentiform_bd, x=1)
    L_Lentiform_bd[L_Insula_bd == 0] = 0
    L_Lentiform_bd[np.isin(seg_np, [114, 116, 120], invert=True)] = 0

    # Add spine label to segmentation
    if not np.isin(parcel_np, [160]).any():
        parcel_np = add_spine_label(parcel_np, voxel_size=voxel_size, brainstem_label=BRAINSTEM, spine_label=SPINE)

    # Parcellate Middle Frontal Gyrus into rostral and caudal
    if not np.isin(parcel_np, [131, 132, 133, 134]).any():
        L_sensory_motor = parcel_np.copy()
        L_sensory_motor[np.isin(parcel_np, [1, 11, 19, 23], invert=True)] = 0
        L_sensory_motor[np.isin(parcel_np, [1, 19])] = 1
        L_sensory_motor[np.isin(parcel_np, [11, 23])] = 2
        L_sensory_motor = ws_dilate(L_sensory_motor, 30)
        parcel_np[np.logical_and(parcel_np == 7, L_sensory_motor == 1)] = 131
        parcel_np[np.logical_and(parcel_np == 7, L_sensory_motor == 2)] = 133

        R_sensory_motor = parcel_np.copy()
        R_sensory_motor[np.isin(parcel_np, [2, 12, 20, 24], invert=True)] = 0
        R_sensory_motor[np.isin(parcel_np, [2, 20])] = 1
        R_sensory_motor[np.isin(parcel_np, [12, 24])] = 2
        R_sensory_motor = ws_dilate(R_sensory_motor, 30)
        parcel_np[np.logical_and(parcel_np == 8, R_sensory_motor == 1)] = 132
        parcel_np[np.logical_and(parcel_np == 8, R_sensory_motor == 2)] = 134

    # Parcellate Rollandic Operculum
    if np.isin(parcel_np, [17, 18]).any():
        L_sensory_motor = parcel_np.copy()
        L_sensory_motor[np.isin(parcel_np, [19, 67, 1, 57, 11, 63, 3, 7, 59, 61], invert=True)] = 0
        L_sensory_motor[np.isin(parcel_np, [1, 3, 7, 11, 19])] = 1
        L_sensory_motor[np.isin(parcel_np, [57, 67, 63, 59, 61])] = 57
        L_sensory_motor = ws_dilate(L_sensory_motor, 15)
        parcel_np[parcel_np == 17] = L_sensory_motor[parcel_np == 17]

        R_sensory_motor = parcel_np.copy()
        R_sensory_motor[np.isin(parcel_np, [20, 68, 2, 58, 12, 64, 4, 8, 60, 62], invert=True)] = 0
        R_sensory_motor[np.isin(parcel_np, [2, 4, 8, 12, 20])] = 2
        R_sensory_motor[np.isin(parcel_np, [58, 60, 62, 64, 68])] = 58
        R_sensory_motor = ws_dilate(R_sensory_motor, 15)
        parcel_np[parcel_np == 18] = R_sensory_motor[parcel_np == 18]

    ctx_mask = np.isin(seg_np, [112, 113])
    ctx_mask_dilated = binary_dilation(ctx_mask, iterations=1)
    wm_mask = np.logical_and(np.isin(seg_np, [114, 115, 116, 117, 120, 121]), np.isin(parcel_np, [120, 121], invert=True))
    ctx_mask[np.logical_and(ctx_mask_dilated, wm_mask)] = 1
    wm_mask[np.logical_and(ctx_mask_dilated, wm_mask)] = 0
    parcel_np[ctx_mask] += 1000
    parcel_np[wm_mask] += 2000
    parcel_np[L_Lentiform_bd == 1] = 128
    parcel_np[R_Lentiform_bd == 1] = 129

    return parcel_np

def main():
    # Load the segmentation and parcel files in the main script
    file_name_seg = sys.argv[1]
    file_name_parcel = sys.argv[2]

    seg = nib.load(file_name_seg)
    parcel = nib.load(file_name_parcel)

    seg_np = seg.get_fdata()
    parcel_np = parcel.get_fdata()

    # Run the parcellation pipeline on numpy arrays
    parcellated_img = parcellation_ctx_wm(seg_np, parcel_np, voxel_size=parcel.affine[0,0])

    # Save the result
    parcellated_img = nib.Nifti1Image(parcellated_img.astype(np.float32), parcel.affine)
    nib.save(parcellated_img, file_name_seg.split(".nii")[0] + "_ctx_wm.nii.gz")

if __name__ == "__main__":
    main()