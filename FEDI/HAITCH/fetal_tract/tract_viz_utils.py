import os
import pandas as pd
import numpy as np
from dipy.viz import actor, window
from dipy.io.streamline import load_tck
from skimage.filters import threshold_multiotsu
import matplotlib.pyplot as plt
from IPython.display import Image, display
import nibabel as nib
import tempfile
import subprocess

def display_scene(scene):
    """
    Display the current scene.

    Parameters:
    scene: window.Scene
        The 3D scene to be displayed.

    This function renders the current scene to an image file, displays it
    in the notebook, and then removes the temporary file.
    """

    # Change the function to use tempfile instead of a fixed filename
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        window.record(scene, out_path=temp_file.name, size=(800, 800))
        display(Image(filename=temp_file.name))
        os.remove(temp_file.name)

def hex_to_rgb(hex_color):
    """
    Convert a hex color to RGB.

    Parameters:
    hex_color: str
        The hexadecimal color code (e.g., '#ff0000').

    Returns:
    tuple:
        A tuple representing the color in RGB format (each value between 0 and 1).
    """
    if pd.isna(hex_color):
        return (1, 1, 1)  # Default to white if NaN
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))

def adjust_window_level(image, window, level):
    """
    Apply window and level adjustments to an image for better visualization.

    Parameters:
    -----------
    image: np.array
        The image data to adjust.
    window: float
        The window value, controlling the contrast range.
    level: float
        The level value, controlling the brightness.

    Returns:
    np.array:
        The image data adjusted for window and level.
    """
    min_val = level - window / 2
    max_val = level + window / 2
    adjusted_image = np.clip(image, min_val, max_val)
    adjusted_image = (adjusted_image - min_val) / (max_val - min_val)
    return adjusted_image

def add_tract_to_scene(scene, tract_file, reference_image_path, color=None):
    """
    Add tractography data to the scene.

    Parameters:
    -----------
    scene: window.Scene
        The 3D scene where the tractography data will be added.
    tract_file: str
        The file path of the .tck tractography file to load.
    reference_image_path: str
        The path to the reference NIfTI image.
    color: tuple, optional
        RGB values (0 to 1) for the tract color. If not provided, default color is used.

    This function loads tractography streamlines and adds them to the scene.
    """
    tract_data = load_tck(tract_file, reference_image_path)
    streamlines = tract_data.streamlines

    # Add the tractography as streamtubes, with an optional color
    if color is None:
        tract_actor = actor.streamtube(streamlines)
    else:
        tract_actor = actor.streamtube(streamlines, color)
    
    scene.add(tract_actor)

def add_image_slice(scene, image_data, affine, slice_coords, window_size=None, level=None):
    """
    Add a 2D slice of a 3D image to the scene, with optional window/level adjustments.

    Parameters:
    -----------
    scene: window.Scene
        The 3D scene where the image slice will be added.
    image_data: np.array
        The image data to be sliced.
    affine: np.array
        The affine transformation matrix for the image.
    slice_coords: dict
        Dictionary specifying which axis (x, y, z) to slice and at which position.
    window_size: float, optional
        The window value for contrast adjustment.
    level: float, optional
        The level value for brightness adjustment.

    This function adds a 2D slice from a 3D image into the scene. If no specific slice
    coordinates are provided, the entire image is added.
    """
    # Apply window/level adjustments if provided
    if window_size is not None and level is not None:
        image_data = adjust_window_level(image_data, window_size, level)
    
    slice_actor = actor.slicer(image_data, affine)
    
    # If specific slice coordinates are provided, add slices at those positions
    if slice_coords:
        if 'x' in slice_coords:
            slice_actor_x = slice_actor.copy()
            slice_actor_x.display(x=int(slice_coords['x']))
            scene.add(slice_actor_x)
        if 'y' in slice_coords:
            slice_actor_y = slice_actor.copy()
            slice_actor_y.display(y=int(slice_coords['y']))
            scene.add(slice_actor_y)
        if 'z' in slice_coords:
            slice_actor_z = slice_actor.copy()
            slice_actor_z.display(z=int(slice_coords['z']))
            scene.add(slice_actor_z)
    else:
        # If no slice coordinates provided, add the whole image
        scene.add(slice_actor)

def add_brain(scene, md_image, affine):
    """
    Add brain structure (CSF and brain matter) actors to the scene using thresholding.

    Parameters:
    -----------
    scene: window.Scene
        The 3D scene where the brain structures will be added.
    md_image: np.array
        The mean diffusivity image used for brain structure segmentation.
    affine: np.array
        The affine transformation matrix for the image.

    This function segments the brain into CSF and brain matter using multi-Otsu
    thresholding and adds these regions to the scene as 3D actors.
    """
    # Perform multi-Otsu thresholding to segment the image into CSF and brain matter
    thresholds = threshold_multiotsu(md_image, classes=3)
    csf_mask = (md_image > thresholds[0]) & (md_image <= thresholds[1])
    brain_matter_mask = md_image > thresholds[1]

    # Create 3D actors for CSF and brain matter with different colors and opacities
    csf_actor = actor.contour_from_roi(csf_mask.astype(np.uint8), affine, [0.9, 0.9, 0.9], 0.2)
    brain_matter_actor = actor.contour_from_roi(brain_matter_mask.astype(np.uint8), affine, [0.4, 0.4, 0.4], 0.3)

    # Add the brain structures to the scene
    scene.add(csf_actor)
    scene.add(brain_matter_actor)


def create_obj_file(segmentation_path, labels):
    """
    Creates a .obj file by generating a temporary mask using the given segmentation and labels.

    Args:
        segmentation: NIfTI segmentation image loaded with nibabel.
        labels: Array of labels to create the mask from.
        output_obj: Name of the output .obj file to be generated.

    Returns:
        None
    """
    # Get the data from the segmentation
    segmentation = nib.load(segmentation_path)
    seg_data = segmentation.get_fdata()

    output_obj = os.path.splitext(segmentation_path)[0] + '_surface.obj'

    # Create a mask where the segmentation contains the specified labels
    mask = np.isin(seg_data, labels).astype(np.uint8)

    # Create a temporary file for the mask
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as temp_mask_file:
        temp_mask_file_name = temp_mask_file.name
        # Save the mask as a NIfTI file
        nib.save(nib.Nifti1Image(mask, segmentation.affine), temp_mask_file_name)

    # Run label2mesh to create the .obj file from the temporary mask
    subprocess.run(["label2mesh", temp_mask_file_name, output_obj, "-force"])
    subprocess.run(["meshfilter", output_obj, "smooth", output_obj, "-force"])

    # Clean up the temporary file
    os.remove(temp_mask_file_name)

    return output_obj


def obj_to_nv(obj_file: str):
    """
    Creates an .nv file by reading the .obj file and processing it into an .nv format.
    The .nv file will have the same name as the .obj file, but with a .nv extension.

    Args:
        obj_file: Path to the .obj file.

    Returns:
        None
    """
    # Change the extension from .obj to .nv
    output_nv = os.path.splitext(obj_file)[0] + '.nv'

    # Read the .obj file, skipping the first three lines
    obj_data = pd.read_csv(obj_file, skiprows=3, delim_whitespace=True, header=None, 
                           names=["element", "x", "y", "z", "NA"])

    # Group by 'element' and add a row count for each group
    obj_data_grouped = obj_data.groupby('element').apply(lambda df: df.assign(count=len(df)))

    # Save the .nv file
    obj_data_grouped[['x', 'y', 'z']].to_csv(output_nv, sep=' ', header=False, index=False, na_rep="")
