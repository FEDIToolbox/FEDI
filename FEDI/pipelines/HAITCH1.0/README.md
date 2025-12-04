# HAITCH 1.0 - Original Pipeline Version

This is the cleaned and stable version of the HAITCH pipeline that uses the original Python scripts from the `src/` directory.

## Features

- **Original Implementation**: Uses the original Python scripts (`outlierdetection.py`, `shorerecon.py`, `rotate_bvecs_ants.py`, `dwiregistration`, `applytransform`)
- **Manual Iteration Loop**: Implements the motion correction pipeline with a manual bash loop (6 epochs)
- **Stable and Tested**: This version has been tested and works without issues

## Usage

```bash
bash dMRI_HAITCH.sh <config_file>
```

## Structure

- `dMRI_HAITCH.sh` - Main pipeline script
- `dMRI_HAITCH_local-config.sh` - Local configuration template
- `dMRI_HAITCH_browser.sh` - Browser interface
- `src/` - Original Python scripts and utilities
- `refs/` - Reference files

## Pipeline Steps

1. DWI Denoising using GSVS
2. MRdegibbs Ringing Artifacts
3. Rician Bias Correction
4. Fetal Brain Extraction
5. Split Crop Skull Data Mask
6. Slice Correct Distortion
7. B1 Field Bias Correction
8. **3D SHORE Reconstruction** (motion correction with manual iteration loop)
9. Registration to T2W Atlas
10. TSOR Response FOD Tractography

## Notes

- All merge conflicts have been resolved (keeping HEAD version)
- This version maintains backward compatibility with existing workflows
- The pipeline is fully functional and tested

