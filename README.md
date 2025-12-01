# FEDI Toolbox

![GitHub issues](https://img.shields.io/github/issues/FEDIToolbox/FEDI)
[![Documentation Status](https://readthedocs.org/projects/fedi/badge/?version=latest)](https://fedi.readthedocs.io/en/latest/)
[![GitHub license](https://img.shields.io/github/license/FEDIToolbox/FEDI)](https://github.com/FEDIToolbox/FEDI/blob/main/LICENSE)

**Fetal and Neonatal Development Imaging (FEDI)** toolbox is a comprehensive, free, open-source toolbox that provides a suite of command-line tools dedicated to the processing and analysis of fetal and neonatal MRI data.

![FEDI_Dreaming](https://github.com/FEDIToolbox/FEDI/assets/20087558/754a9d42-858f-4445-b25c-98354903f34a)


## Key Features

While **FEDI** is primarily designed for fetal and neonatal MRI, several tools are applicable to general MRI processing. In summary, **FEDI** provides:

- **Gradient and b-vector tools:** Rotation of b-vectors, gradient-scheme conversion, and q-weight utilities.

- **Diffusion MRI preprocessing:** Denoising, Gibbs artifact removal, and bias-field correction.

- **Outlier detection and weighting:** Identification and weighting of outlier volumes, slices, or voxels for robust diffusion MRI processing.

- **Reconstruction:** Diffusion signal reconstruction with integrated outlier weighting.

- **Motion correction for diffusion MRI:** Robust intra- and inter-volume motion correction designed for fetal and neonatal data, but compatible with any population.

- **FOD estimation:** Fiber-orientation distribution estimation using a pretrained spherical CNN model optimized for neonatal diffusion MRI.

## Installing FEDI

There are multiple ways to install the FEDI toolbox.

### Installation Methods

#### Option 1: Install via pip

The easiest way to install FEDI is through `pip`. Open a terminal and run:

```bash
pip install fedi
```

#### Option 2: Clone the Repository

To manually install the FEDI toolbox and primarily access its workflows, clone the repository and add the necessary paths to your `.bashrc` file:

```bash
git clone https://github.com/FEDIToolbox/FEDI.git
cd FEDI/FEDI/scripts
FEDI_SCRIPTS=$(pwd)
echo 'export PATH="${FEDI_SCRIPTS}:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

[Workflows](https://github.com/FEDIToolbox/FEDI/tree/main/FEDI/pipelines) such as HAITCH are available in:

```bash
cd FEDI/FEDI/pipelines
```

#### Option 3: Conda Environment (Coming Soon)

We are currently working on providing an installation option via Conda for easier dependency management.

### Verifying Installation

After installing FEDI, we recommend verifying that the installation is working correctly by running the automated test suite:

```bash
fedi_testing
```

This command will:

1. **Generate synthetic test data**: Creates realistic 4D diffusion MRI data with fixed parameters in `~/.fedi_test_data/`
2. **Run automated tests**: Tests all FEDI command-line tools and verifies that they execute correctly and produce expected outputs

The test suite will report which tools passed, failed, or were skipped (due to missing optional dependencies). Some tests may take several minutes to complete, especially `fedi_dmri_moco` and `fedi_dmri_recon`.

For more information about the testing command, see the [documentation](https://fedi.readthedocs.io/en/latest/modules/commands/fedi_testing.html).

### Dependencies

FEDI supports **DICOM, NIfTI, and MIF** image formats and relies on several external dependencies for full functionality.  
We **strongly recommend** using the **Anaconda Python distribution** to manage dependencies efficiently.

#### Required Python Packages

These packages are automatically installed when you install FEDI via pip:

- [NumPy](https://numpy.org/) - Numerical computing
- [SciPy](https://scipy.org/) - Scientific computing
- [NiBabel](https://nipy.org/nibabel/) - Neuroimaging file I/O
- [Matplotlib](https://matplotlib.org/) - Plotting and visualization
- [DIPY](https://dipy.org/) - Diffusion imaging in Python
- [CVXPY](http://www.cvxpy.org/) - Convex optimization
- [Healpy](https://healpy.readthedocs.io/) - Spherical harmonics and HEALPix

#### Required for Specific Features

- [PyTorch](https://pytorch.org/) - Required for [fedi_dmri_fod](https://fedi.readthedocs.io/en/latest/modules/commands/fedi_dmri_fod.html) (FOD estimation)
- [Hugging Face Hub](https://huggingface.co/docs/hub/) - Required for [fedi_dmri_fod](https://fedi.readthedocs.io/en/latest/modules/commands/fedi_dmri_fod.html) (model downloads)

#### Required External Tools

- [MRtrix3](https://www.mrtrix.org/)
- [ANTs](https://github.com/ANTsX/ANTs)

## Getting Help

For questions, issues, or suggestions, please open an issue on [our GitHub repository](https://github.com/FEDIToolbox/FEDI/issues).

## Citation

If you use FEDI in your research, please cite:

**HAITCH Framework:**
Snoussi, Haykel, Davood Karimi, Onur Afacan, Mustafa Utkur, and Ali Gholipour. HAITCH: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI. Imaging Neuroscience 2025.

**FOD Estimation:**
Snoussi, Haykel, and Davood Karimi. Equivariant Spherical CNNs for Accurate Fiber Orientation Distribution Estimation in Neonatal Diffusion MRI with Reduced Acquisition Time. Frontiers in Neuroscience 2025.
