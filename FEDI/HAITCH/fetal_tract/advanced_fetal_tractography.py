#!/usr/bin/env python
# coding: utf-8

import os
import nibabel as nib
import subprocess
import argparse
from tensor2odf import compute_fod_sh
from fivett_gen import fivett_segmentation
from adjust_parcellation import adjust_parcellation
from create_ctx_wm import parcellation_ctx_wm
from get_max_min_streamline import calculate_streamline_lengths
from dipy.io.streamline import load_tractogram, save_tractogram
from extract_labels import extract_individual_labels

# ------------------------
# Argument Parser
# ------------------------
parser = argparse.ArgumentParser(description="Run diffusion pipeline with optional custom filenames.")

parser.add_argument('--basename', type=str, default='GA23', help='Base name for input/output files (default: GA23)')
parser.add_argument('--subject_dir', type=str, default='example', help='Subject directory (default: example)')
parser.add_argument('--work_dir', type=str, default=os.getcwd(), help='Working directory (default: current dir)')

parser.add_argument('--tensor_path', type=str, default=None, help='Path to DTI input')
parser.add_argument('--md_path', type=str, default=None, help='Path to MD map')
parser.add_argument('--tissue_path', type=str, default=None, help='Path to tissue segmentation (e.g., GA23_tissue.nii.gz)')
parser.add_argument('--fivett_key_path', type=str, default='5tt_key.csv', help='Path to 5TT key CSV')
parser.add_argument('--parcellation_path', type=str, default=None, help='Path to parcellation (e.g., GA23_regional.nii.gz)')

args = parser.parse_args()

# ------------------------
# Set Paths
# ------------------------
basename = args.basename
subject_dir = args.subject_dir
work_dir = args.work_dir

# Inputs
tensor_path = args.tensor_path or os.path.join(work_dir, subject_dir, f'{basename}.nii.gz')
md_path = args.md_path or os.path.join(work_dir, subject_dir, f'{basename}_md.nii.gz')
tissue_path = args.tissue_path or os.path.join(work_dir, subject_dir, f'{basename}_tissue.nii.gz')
fivett_key_path = args.fivett_key_path
parcellation_path = args.parcellation_path or os.path.join(work_dir, subject_dir, f'{basename}_regional.nii.gz')

# Outputs
fod_path = os.path.join(work_dir, subject_dir, f'{basename}_odf.nii.gz')
_5tt_img_path = os.path.join(work_dir, subject_dir, f'{basename}_5tt.nii.gz')
parcellation_adjusted_path = os.path.join(work_dir, subject_dir, f'{basename}_regional_adjusted.nii.gz')
ctx_wm_parcellation_path = os.path.join(work_dir, subject_dir, f'{basename}_ctx_wm.nii.gz')
gmwmi_img_path = os.path.join(work_dir, subject_dir, f'{basename}_gmwmi.nii.gz')
tractography_output = os.path.join(work_dir, subject_dir, f'{basename}.tck')
tract_extraction_output = os.path.join(work_dir, subject_dir, 'tract_extraction', basename)
query_file = os.path.join(work_dir, 'crl_fetal_parcellation_ACT.qry')
labelkey_path = os.path.join(work_dir, 'labelkey.csv')
structure_output_dir = os.path.join(work_dir, subject_dir, 'structure_extraction')

# ------------------------
# Step 1: Convert Tensor to ODF
# ------------------------
tensor = nib.load(tensor_path)
tensor_data = tensor.get_fdata()
fod_data = compute_fod_sh(tensor_data)
fod_img = nib.Nifti1Image(fod_data, tensor.affine)
nib.save(fod_img, fod_path)

# ------------------------
# Step 2: Tissue Segmentation and Parcellation
# ------------------------
tissue = nib.load(tissue_path)
tissue_data = tissue.get_fdata()
md = nib.load(md_path)
md_data = md.get_fdata()

five_tt_img_data, whole_brain_data, csf_mask_data = fivett_segmentation(tissue_data, md_data, fivett_key_path, tissue.header.get_zooms()[0])
five_tt_img = nib.Nifti1Image(five_tt_img_data, tissue.affine)
nib.save(five_tt_img, _5tt_img_path)

# ------------------------
# Step 4: Adjust Parcellation
# ------------------------
parcellation = nib.load(parcellation_path)
parcellation_data = parcellation.get_fdata()
parcellation_adjusted_data = adjust_parcellation(tissue_data, parcellation_data)
parcellation_adjusted_img = nib.Nifti1Image(parcellation_adjusted_data, parcellation.affine)
nib.save(parcellation_adjusted_img, parcellation_adjusted_path)

# ------------------------
# Step 5: Separate Gray and White Matter
# ------------------------
voxel_size = tissue.header.get_zooms()[0]
ctx_wm_parcellation_data = parcellation_adjusted_data.copy()
ctx_wm_parcellation_data = parcellation_ctx_wm(tissue_data, ctx_wm_parcellation_data, voxel_size)
ctx_wm_parcellation_img = nib.Nifti1Image(ctx_wm_parcellation_data, tissue.affine)
nib.save(ctx_wm_parcellation_img, ctx_wm_parcellation_path)

# ------------------------
# Step 6: Generate GMWMI
# ------------------------
subprocess.run(['5tt2gmwmi', _5tt_img_path, gmwmi_img_path, '-force'], check=True)

# ------------------------
# Step 7: Min/Max Streamline Length
# ------------------------
streamline_lengths = calculate_streamline_lengths(whole_brain_data, tissue.header.get_zooms(), 'tract')
minlength, maxlength = streamline_lengths
print(f'Minimum streamline length: {minlength}')
print(f'Maximum streamline length: {maxlength}')

# ------------------------
# Step 8: Tractography
# ------------------------
subprocess.run([
    'tckgen', fod_path, tractography_output,
    '-act', _5tt_img_path,
    '-seed_gmwmi', gmwmi_img_path,
    '-cutoff', '0.001',
    '-select', '10000',
    '-power', '10',
    '-angle', '15',
    '-minlength', str(minlength),
    '-maxlength', str(maxlength),
    '-force'
], check=True)

# ------------------------
# Step 9: Convert TCK to TRK
# ------------------------
def tck2trk(tck_file, anatomy_ref):
    whole_brain = load_tractogram(tck_file, anatomy_ref)
    trk_file = tck_file.replace(".tck", ".trk")
    save_tractogram(whole_brain, trk_file)
    return trk_file

trk_file_path = tck2trk(tractography_output, md)

# ------------------------
# Step 10: Extract Tracts
# ------------------------
subprocess.run(
    f"tract_querier -t {trk_file_path} -a {ctx_wm_parcellation_path} -q {ctx_wm_parcellation_path} -o {tract_extraction_output}",
    shell=True
)

# ------------------------
# Step 11: Extract Brain Structures
# ------------------------
extract_individual_labels(
    parcellation_adjusted_data, parcellation_adjusted_img.affine,
    labelkey_path, structure_output_dir, base_name=basename
)
