import nibabel as nib
import numpy as np
import pandas as pd
import os
import sys

def extract_individual_labels(nifti_data, affine, file_name_key, output_dir, base_name):
    """
    Extracts individual labels from a NIfTI segmentation and creates a corresponding NIfTI file 
    for each label. The labels and their corresponding IDs are provided in a CSV file.

    Parameters:
    -----------
    nifti_data : numpy.ndarray
        The 3D numpy array representing the NIfTI segmentation data where each voxel 
        is assigned a label ID.
    affine : numpy.ndarray
        The affine transformation matrix associated with the NIfTI file.
    file_name_key : str
        Path to the CSV file that contains the mapping of label names to label IDs. The CSV 
        file must have two columns: 'label' (label name) and 'id' (corresponding label ID).
    output_dir : str
        Directory where the individual label NIfTI files will be saved.
    base_name : str
        Base name for the output NIfTI files. Each file will be saved as 
        'base_name_label_name.nii.gz'.

    Description:
    ------------
    This function takes a segmentation NIfTI file and a CSV file that maps label names to 
    label IDs. For each label in the CSV file, the function checks if the label ID is present 
    in the segmentation. If the label ID is found, it creates a binary mask for that label, 
    generates a new NIfTI image with this mask, and saves it as a separate NIfTI file in the 
    specified output directory. The filename of each output NIfTI file is of the format:
    'base_name_label_name.nii.gz'.

    Example:
    --------
    Given a segmentation file 'brain_seg.nii.gz' and a CSV file 'labels.csv' with the following
    contents:

        label,id
        White_Matter,1
        Gray_Matter,2
        Cerebellum,3

    The function will create the following files if the corresponding labels are found in the 
    segmentation:

        - brain_seg_White_Matter.nii.gz
        - brain_seg_Gray_Matter.nii.gz
        - brain_seg_Cerebellum.nii.gz
    """
    # Load the CSV file inside the function
    csv_data = pd.read_csv(file_name_key)

    # Get the unique labels in the NIfTI segmentation
    unique_labels = np.unique(nifti_data)

    # Loop through each label in the CSV file
    for label in csv_data['label']:
        label_id = csv_data[csv_data["label"] == label]["id"].values[0]

        # Check if the label is present in the NIfTI segmentation
        if label_id in unique_labels:
            # Create a mask for the current label
            label_mask = (nifti_data == label_id).astype(np.uint8)

            # Create a new NIfTI image for the current label
            label_img = nib.Nifti1Image(label_mask, affine)

            # Save the NIfTI image with the label name in the "structures" folder
            label_filename = os.path.join(output_dir, f"{base_name}_{label}.nii.gz")
            nib.save(label_img, label_filename)

            print(f"Segmentation file created for: {label}")

def main():
    # Load the input NIfTI file
    file_name_seg = sys.argv[1]
    file_name_key = sys.argv[2]

    # Load the NIfTI file
    nifti_file = nib.load(file_name_seg)
    nifti_data = nifti_file.get_fdata()

    # Create a folder named "structures" in the same directory as the NIfTI file
    output_dir = os.path.join(os.path.dirname(file_name_seg), "structures")
    os.makedirs(output_dir, exist_ok=True)

    # Get the base name of the NIfTI file without the ".nii" extension
    base_name = os.path.basename(file_name_seg).split(".nii")[0]

    # Call the processing function
    extract_individual_labels(nifti_data, nifti_file.affine, file_name_key, output_dir, base_name)

if __name__ == "__main__":
    main()