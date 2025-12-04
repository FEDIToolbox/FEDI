# HAITCH 2.0 - Updated Pipeline Version

This is the updated version of the HAITCH pipeline that uses the new `fedi_*` command-line tools.

## Features

- **Modern Implementation**: Uses the new FEDI command-line tools (`fedi_dmri_moco`, `fedi_dmri_outliers`, `fedi_dmri_recon`, etc.)
- **Simplified STEP 8**: Replaces the manual iteration loop with a single `fedi_dmri_moco` command
- **Better Maintainability**: Cleaner code with fewer lines and better error handling
- **Consistent Interface**: All tools use the same command-line interface pattern

## Key Changes from HAITCH 1.0

### STEP 8: Motion Correction

**HAITCH 1.0** (Original):
- Manual bash loop with 6 epochs
- Calls individual Python scripts: `outlierdetection.py`, `shorerecon.py`, `rotate_bvecs_ants.py`, `dwiregistration`, `applytransform`
- ~150 lines of iteration logic

**HAITCH 2.0** (Updated):
- Single command: `fedi_dmri_moco`
- Handles all iterations internally
- ~20 lines of setup and call
- Same functionality, cleaner implementation

### Command Mapping

| HAITCH 1.0 (Old) | HAITCH 2.0 (New) |
|------------------|------------------|
| `outlierdetection.py` | `fedi_dmri_outliers` |
| `shorerecon.py` | `fedi_dmri_recon` |
| `rotate_bvecs_ants.py` | `fedi_dmri_rotate_bvecs` |
| `dwiregistration` | `fedi_dmri_reg` |
| `applytransform` | `fedi_apply_transform` |
| Manual iteration loop | `fedi_dmri_moco` (single command) |

## Usage

```bash
bash dMRI_HAITCH.sh <config_file>
```

## Structure

- `dMRI_HAITCH.sh` - Main pipeline script (updated to use fedi_* commands)
- `dMRI_HAITCH_local-config.sh` - Local configuration template
- `dMRI_HAITCH_browser.sh` - Browser interface
- `src/` - Legacy scripts (kept for reference, not used in STEP 8)
- `refs/` - Reference files

## Pipeline Steps

1. DWI Denoising using GSVS
2. MRdegibbs Ringing Artifacts
3. Rician Bias Correction
4. Fetal Brain Extraction
5. Split Crop Skull Data Mask
6. Slice Correct Distortion
7. B1 Field Bias Correction
8. **3D SHORE Reconstruction** (using `fedi_dmri_moco`)
9. Registration to T2W Atlas
10. TSOR Response FOD Tractography

## Requirements

- FEDI package installed (`pip install fedi`)
- All `fedi_*` commands available in PATH
- MRtrix3, ANTs, and other dependencies (same as HAITCH 1.0)

## Migration from HAITCH 1.0

The output structure and file names remain the same, so HAITCH 2.0 is a drop-in replacement for HAITCH 1.0. The main difference is the internal implementation of STEP 8.

## Notes

- All merge conflicts resolved
- Backward compatible output structure
- Improved error handling and logging
- Easier to maintain and extend

