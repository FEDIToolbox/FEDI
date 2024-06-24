
![try](https://github.com/H-Snoussi/HAITCH/assets/20087558/4c6f39b9-72f0-4b45-818f-d39bddbd736f)

## HAITCH : High Angular resolution diffusion Imaging reconsTruction and Correction approacH

HAITCH is a novel framework designed to address the challenges of fetal diffusion MRI (dMRI) by overcoming limitations caused by fetal motion and geometric distortion. It achieves this through optimized acquisition and reconstruction strategies, enabling more accurate analysis of the developing fetal brain.

## Features
- **Optimized Scheme:** Optimizing the gradient table to enhance the dMRI data's tolerance to fetal motion.
- **Motion Correction:** Mitigates the effects of fetal motion on dMRI images.
- **Dynamic Distortion Correction:** Corrects distortions caused by magnetic field inhomogeneities.
- **Post-Processing:** Spatial Normalization, Diffusion Model Estimation and Tractography.

## Installation
```bash
git clone https://github.com/H-Snoussi/HAITCH.git
cd HAITCH
```

## Dependencies
Recommended to use Anaconda Python distribution.
- [DIPY](https://dipy.org/)
- [CVXPY](http://www.cvxpy.org/)
- [MRtrix3](https://www.mrtrix.org/)
- [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation)
- [ANTs](https://github.com/ANTsX/ANTs).
- Numpy, Scipy, Nibabel, Matplotlib

## Contact
For questions, issues, or suggestions, please open an issue on GitHub.

