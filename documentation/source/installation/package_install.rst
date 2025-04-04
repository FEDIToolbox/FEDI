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

Dependencies
------------

FEDI supports **DICOM, NIfTI, and MIF** image formats and relies on several external dependencies for full functionality.  
We **strongly recommend** using the **Anaconda Python distribution** to manage dependencies efficiently.

**Required Dependencies:**
^^^^^^^^^^^^^^^^^^^^^^^^^^

- `DIPY <https://dipy.org/>`__
- `CVXPY <http://www.cvxpy.org/>`__
- `MRtrix3 <https://www.mrtrix.org/>`__
- `FSL <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation>`__
- `ANTs <https://github.com/ANTsX/ANTs>`__
- `NumPy <https://numpy.org/>`__
- `SciPy <https://scipy.org/>`__
- `NiBabel <https://nipy.org/nibabel/>`__
- `Matplotlib <https://matplotlib.org/>`__

Getting Help
------------

For questions, issues, or suggestions, please open an issue on `our GitHub repository <https://github.com/FEDIToolbox/FEDI/issues>`__.
