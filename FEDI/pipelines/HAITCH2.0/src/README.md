# HAITCH 2.0 Source Files

This directory contains utility scripts that are still needed by the HAITCH 2.0 pipeline.

## Files in this directory

### Still Required (used in other pipeline steps):
- `display_name.sh` - Displays toolbox name/logo (STEP 0)
- `create_grad5cls_index.py` - Creates gradient class index files (STEP 0)
- `segm_outliers.py` - Segmentation outlier detection (STEP 4)
- `update_bvecs_bvals.py` - Updates b-values and b-vectors for multi-echo data (STEP 7, STEP 8)
- `segment_fetalbrain.sh` - Fetal brain segmentation script (STEP 4, STEP 9)

### Removed (replaced by fedi_* commands):
- `outlierdetection.py` → **fedi_dmri_outliers**
- `shorerecon.py` → **fedi_dmri_recon**
- `rotate_bvecs_ants.py` → **fedi_dmri_rotate_bvecs**
- `dwiregistration` → **fedi_dmri_reg**
- `applytransform` → **fedi_apply_transform**

## Note

The motion correction pipeline (STEP 8) now uses `fedi_dmri_moco` which internally calls the fedi_* commands above. These old scripts are no longer needed for STEP 8.

