import SimpleITK as sitk
import numpy as np

def dilate_image(image, radius):
    """Binary dilates an image using SimpleITK.

    Args:
        image (numpy array): Image in NumPy array format
        radius (integer): Radius of dilation

    Returns:
        NumPy array: Numpy array of dilated_image
    """
    
    sitk_image = sitk.GetImageFromArray(image)
    sitk_image = sitk.Cast(sitk_image, sitk.sitkUInt16)
    dilated_image = sitk.BinaryDilate(sitk_image != 0, [radius] * 3)
    return sitk.GetArrayFromImage(dilated_image)

def add_spine_label(image, voxel_size,  brainstem_label=94, spine_label=160):
    """Convert the bottom part of the brainstem to a spine label to be used for tractography.

    Args:
        image (NumPy array): Segmentation Image
        voxel_size (int): Voxel size of the image
        brainstem_label (int): Label ID for the brainstem.
        spine_label (int): Label ID to be assigned to the new spine label.

    Returns:
        numpy array: Segmentation image with the spine label attached.
    """
    # Find the indices where the segmentation contains the number 94
    indices = np.where(image == brainstem_label)

    # Calculate the length in the z-axis (assuming the z-axis is the third dimension, index 2)
    min_z = np.min(indices[2])
    max_z = np.max(indices[2])
    length_z = max_z - min_z + 1  # Add 1 because indices are 0-based
    thickness = np.round(length_z * voxel_size / 6, 0).astype(int)  # Thickness of the cylinder region

    # Find slices containing the brainstem label
    brainstem_slices = np.any(image == brainstem_label, axis=(0, 1))

    # Find the last three inferior slices of the brainstem
    last_three_slices = np.argwhere(brainstem_slices)[0:thickness]

    # Create a mask for the cylinder region
    cylinder_mask = np.zeros_like(image, dtype=bool)
    for i in last_three_slices:
        cylinder_mask[..., i] = (image[..., i] == brainstem_label)

    # Replace values in the cylinder region with spine label
    image[cylinder_mask] = spine_label

    return image.astype(np.uint16)

def ws_dilate(image, radius):
    """Dilates the image using a morphological watershed algorithm.

    Args:
        image (NumPy array): Segmentation image in NumPy array format
        radius (int): Delayation size for all labels

    Returns:
        NumPy array: Segmentation image in NumPy array with all labels dilated using Watershed method.
    """
    sitk_image = sitk.GetImageFromArray(image.astype(np.uint16))
    binary_image = sitk.BinaryDilate(sitk_image != 0, [radius] * 3)
    distance_map = sitk.SignedMaurerDistanceMap(sitk_image != 0, insideIsPositive=False, squaredDistance=False)
    watershed_image = sitk.MorphologicalWatershedFromMarkers(distance_map, sitk_image, markWatershedLine=False)
    masked_image = sitk.Mask(watershed_image, binary_image)
    return sitk.GetArrayFromImage(masked_image)