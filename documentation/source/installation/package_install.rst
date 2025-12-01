Installing FEDI
===============

There are multiple ways to install the FEDI toolbox.

Installation Methods
--------------------

**Option 1: Install via pip**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The easiest way to install FEDI is through `pip`. Open a terminal and run:

.. code-block:: bash

   pip install fedi

**Option 2: Clone the Repository**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To manually install the FEDI toolbox and primarily access its workflows, clone the repository and add the necessary paths to your `.bashrc` file:

.. code-block:: bash

   git clone https://github.com/FEDIToolbox/FEDI.git
   cd FEDI/FEDI/scripts
   FEDI_SCRIPTS=$(pwd)
   echo 'export PATH="${FEDI_SCRIPTS}:$PATH"' >> ~/.bashrc
   source ~/.bashrc

`Workflows <https://github.com/FEDIToolbox/FEDI/tree/main/FEDI/pipelines>`__ such as HAITCH are available in:

.. code-block:: bash

   cd FEDI/FEDI/pipelines


**Option 3: Conda Environment (Coming Soon)**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We are currently working on providing an installation option via Conda for easier dependency management.

Verifying Installation
----------------------

After installing FEDI, we recommend verifying that the installation is working correctly by running the automated test suite:

.. code-block:: bash

   fedi_testing

This command will:

1. **Generate synthetic test data**: Creates realistic 4D diffusion MRI data with fixed parameters in ``~/.fedi_test_data/``
2. **Run automated tests**: Tests all FEDI command-line tools and verifies that they execute correctly and produce expected outputs

The test suite will report which tools passed, failed, or were skipped (due to missing optional dependencies). This helps ensure that:

- All FEDI commands are properly installed and accessible
- Required dependencies are correctly configured
- Optional dependencies (MRtrix3, ANTs, PyTorch) are available if you plan to use features that require them

**Note**: Some tests may take several minutes to complete, especially ``fedi_dmri_moco`` which runs the full motion correction pipeline.

For more information about the testing command, see :ref:`fedi_testing`.

Dependencies
------------

FEDI supports **DICOM, NIfTI, and MIF** image formats and relies on several external dependencies for full functionality.  
We **strongly recommend** using the **Anaconda Python distribution** to manage dependencies efficiently.

**Required Python Packages:**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These packages are automatically installed when you install FEDI via pip:

- `NumPy <https://numpy.org/>`__ - Numerical computing
- `SciPy <https://scipy.org/>`__ - Scientific computing
- `NiBabel <https://nipy.org/nibabel/>`__ - Neuroimaging file I/O
- `Matplotlib <https://matplotlib.org/>`__ - Plotting and visualization
- `DIPY <https://dipy.org/>`__ - Diffusion imaging in Python
- `CVXPY <http://www.cvxpy.org/>`__ - Convex optimization
- `Healpy <https://healpy.readthedocs.io/>`__ - Spherical harmonics and HEALPix

**Required for Specific Features:**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- `PyTorch <https://pytorch.org/>`__ - Required for :ref:`fedi_dmri_fod` (FOD estimation)
- `Hugging Face Hub <https://huggingface.co/docs/hub/>`__ - Required for :ref:`fedi_dmri_fod` (model downloads)

**Required External Tools:**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are command-line tools that must be installed separately and available in your PATH:

- `MRtrix3 <https://www.mrtrix.org/>`__ 
- `ANTs <https://github.com/ANTsX/ANTs>`__ 

Getting Help
------------

For questions, issues, or suggestions, please open an issue on `our GitHub repository <https://github.com/FEDIToolbox/FEDI/issues>`__.
