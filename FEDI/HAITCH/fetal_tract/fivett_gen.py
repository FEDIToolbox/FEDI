import sys
import pandas as pd
import nibabel as nib
import numpy as np
import ants
import SimpleITK as sitk
from utils import dilate_image, add_spine_label

# Constants
SPINE = 160
BRAINSTEM = 94

def get_interface_mask(image, label1, label2):
    """Gets interface mask between two labels."""
    mask = (image == label1).astype(np.uint8)
    dilated_label = dilate_image(mask, 1)
    return np.logical_and(dilated_label, image == label2)

def get_optimal_interface(image, label1, label2):
    """Determines the optimal interface mask between two labels."""
    interface_mask_1 = get_interface_mask(image, label1, label2)
    interface_mask_2 = get_interface_mask(image, label2, label1)
    return interface_mask_1 if np.count_nonzero(interface_mask_1) < np.count_nonzero(interface_mask_2) else interface_mask_2

def get_label_id(labelkey_df, label_name):
    """Gets the label id for a given label name."""
    return labelkey_df[labelkey_df["label"] == label_name]["id"].values[0]

def fivett_segmentation(seg_data, md_data, labelkey_path, voxel_size):
    """
    Converts a segmentation image into a 5-tissue-type (5TT) image.

    This function processes a segmentation image, mean diffusivity (MD) data, and a label key CSV file
    to generate a 5TT image for tractography seeding. The 5TT format is used to distinguish between
    cortical gray matter, sub-cortical gray matter, white matter, cerebrospinal fluid (CSF), and 
    other brain tissues, which are essential for diffusion MRI processing and tractography.

    Args:
    -----
    seg_data : NumPy array
        The 3D NumPy array representing the segmentation image where each voxel is assigned a tissue or structure label.
    md_data : NumPy array
        The mean diffusivity (MD) image in NumPy array format, used for CSF detection.
    labelkey_path : str
        The file path to the label key CSV that maps tissue/structure labels to their corresponding IDs in the segmentation.
    voxel_size : float
        The voxel size of the image, used for proper scaling of structures during processing.

    Returns:
    --------
    five_tt_np : NumPy array
        A 4D NumPy array representing the 5-tissue-type (5TT) segmentation. The 5 dimensions correspond to:
        0: cortical gray matter, 1: sub-cortical gray matter, 2: white matter, 3: CSF, 4: pathologica tissue.
    whole_brain_mask : NumPy array
        A binary mask (3D) of the entire brain, excluding non-brain structures like the spine.
    csf_mask : NumPy array
        A binary mask (3D) representing the cerebrospinal fluid (CSF) within the brain.

    Description:
    ------------
    The function performs several steps:
    1. **Mean Diffusivity Scaling**: If the mean value of non-zero voxels in the MD image is less than 1, 
       the MD image is scaled by 1000.
    2. **Spine Label Addition**: The segmentation is updated by adding spine labels based on the provided label key and voxel size.
    3. **Tissue Segmentation**: The segmentation is converted into cortical gray matter, sub-cortical gray matter, 
       white matter, and CSF using the label key.
    4. **CSF Detection**: The CSF mask is enhanced by performing k-means clustering on the MD image and using dilation.
    5. **Interface Optimization**: For certain tissue interfaces (e.g., between thalamus and hippocampus), the optimal 
       boundary is determined and the segmentation is adjusted accordingly.
    6. **Output**: The final output includes a 5TT image and masks for whole-brain and CSF regions.

    Example:
    --------
    Suppose you have a segmentation file 'seg.nii.gz' and an MD file 'md.nii.gz', along with a label key CSV 'labels.csv'. 
    You can run the pipeline as follows:

        five_tt_img, whole_brain_img, csf_mask_img = fivett_segmentation(seg_data, md_data, 'labels.csv', voxel_size=1.0)

    This will return:
    - `five_tt_img`: A 5TT image with the 5 tissue types labeled.
    - `whole_brain_img`: A binary mask of the whole brain.
    - `csf_mask_img`: A binary mask of the cerebrospinal fluid (CSF).

    """
    
    # Get the mean value of non-zero voxels of the MD image
    mean_md = np.mean(md_data[md_data > 0])

    # If the mean value is less than 1, multiply the MD image by 1000
    if mean_md < 1:
        md_data *= 1000

    # Convert md_data back to ANTs image
    md = ants.from_numpy(md_data)

    # Load the label key CSV
    labelkey_df = pd.read_csv(labelkey_path, sep=",")

    # Using get_label_id to simplify label extraction
    label_ids = {label: get_label_id(labelkey_df, label) for label in labelkey_df["label"]}

    seg_data = add_spine_label(seg_data, voxel_size, BRAINSTEM, SPINE)

    # Processing interfaces
    interface_pairs = [
        (label_ids["Thalamus_L"], label_ids["Thalamus_R"], 0),
        (label_ids["Cerebellum_L"], label_ids["Cerebellum_R"], 0),
        (label_ids["Cerebellum_L"], SPINE, label_ids["Brainstem"]),
        (label_ids["Cerebellum_R"], SPINE, label_ids["Brainstem"]),
        (label_ids["Thalamus_L"], label_ids["Hippocampus_L"], 0),
        (label_ids["Thalamus_R"], label_ids["Hippocampus_R"], 0),
        (label_ids["Amygdala_L"], label_ids["Hippocampus_L"], label_ids["White_Matter_L"]),
        (label_ids["Amygdala_R"], label_ids["Hippocampus_R"], label_ids["White_Matter_R"]),
    ]

    for label1, label2, replace in interface_pairs:
        interface = get_optimal_interface(seg_data, label1, label2)
        seg_data[interface] = replace

    ####### Create segmentation for the 5tt #########
    cortical_gm = np.isin(
        seg_data, np.array(labelkey_df[labelkey_df["cortical_grey_matter"] == 1]["id"])
    )
    sub_cortical_gm = np.isin(
        seg_data, np.array(labelkey_df[labelkey_df["sub_cortical_grey_matter"] == 1]["id"])
    )
    wm = np.isin(seg_data, np.array(labelkey_df[labelkey_df["white_matter"] == 1]["id"]))

    # Make k-mean segmentation for CSF detection
    mask = ants.get_mask(md)  # Now passing the ANTs image, not the NumPy array
    new_mask = ants.atropos(md, mask, i="Kmeans[3]", m="[0.2, 1x1x1]")[
        "segmentation"
    ].numpy()

    csf = dilate_image(seg_data, 2)
    csf[new_mask == 3] = 1
    csf[seg_data != 0] = 0
    csf[md_data < 0.5] = 0

    # Join all different tissues in one segmentation
    five_tt_np = np.zeros(np.append(seg_data.shape, 5), np.int8)
    five_tt_np[cortical_gm, 0] = 1
    five_tt_np[sub_cortical_gm, 1] = 1
    five_tt_np[wm, 2] = 1
    five_tt_np[csf.astype(bool), 3] = 1

    # Create masks for seeding streamlines
    whole_brain_mask = seg_data != 0
    whole_brain_mask[seg_data == 160] = 0

    return five_tt_np, whole_brain_mask.astype(np.int8), (new_mask != 0).astype(np.int8)

def main():
    # File paths
    file_name_seg = sys.argv[1]
    file_name_md = sys.argv[2]
    labelkey_path = sys.argv[3]

    # Load the segmentation and MD files
    seg = nib.load(file_name_seg)
    seg_data = seg.get_fdata()

    md = ants.image_read(file_name_md)
    md_data = md.numpy()

    # Process the pipeline and get outputs
    five_tt_img, whole_brain_img, csf_mask_img = fivett_segmentation(
        seg_data, md_data, labelkey_path, voxel_size=seg.affine[0, 0])

    # Save the results as Nifti images
    nib.save(nib.Nifti1Image(five_tt_img, seg.affine), file_name_seg.split(".nii")[0] + "_5tt.nii.gz")
    nib.save(nib.Nifti1Image(whole_brain_img, seg.affine), file_name_seg.split(".nii")[0] + "_whole_brain.nii.gz")
    nib.save(nib.Nifti1Image(csf_mask_img, seg.affine), file_name_seg.split(".nii")[0] + "_mask.nii.gz")

if __name__ == "__main__":
    main()