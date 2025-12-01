Fetal and Neonatal Development Imaging
======================================

.. figure:: Focus_FEDI.png

**Fetal and Neonatal Development Imaging (FEDI)** is a comprehensive, free, open-source toolbox that provides a suite of command-line tools dedicated to the processing and analysis of fetal and neonatal MRI data.


.. note::

   **FEDI** is under active development, constantly expanding its functionalities.

Key Features
~~~~~~~~~~~~
While **FEDI** is primarily intended for the processing and analysis of fetal and neonatal MRI data, some tools can be used for any type of MRI data. In summary, **FEDI** features:

- **Gradient and b-vector tools:** Rotation of b-vectors, gradient-scheme conversion, and q-weight utilities.

- **Diffusion MRI preprocessing:** Denoising, Gibbs removal, and bias-field correction.

- **Outlier detection and weighting:** Identification and weighting of outlier volumes, slices, or voxels for robust diffusion MRI processing.

- **Reconstruction:** Reconstruction of the diffusion signal with the integration of outlier weights.

- **Motion correction for dMRI:**  Robust intra- and inter-volume motion correction designed for fetal and neonatal data, but compatible with any population.

- **FOD estimation:** Fiber-orientation distribution estimation using a pretrained spherical CNN model optimized for neonatal dMRI.



Getting Started
~~~~~~~~~~~~~~~
**FEDI** runs on GNU/Linux, and macOS platforms. For most users, the easiest way to install **FEDI** is using pre-compiled packages. Refer to the install section for detailed instructions.  A Docker image for **FEDI** will also be available soon.

**FEDI** provides a set of easy-to-use command-line tools for processing and analyzing MRI data. These tools are all designed to be run from a terminal window using a consistent interface.
This documentation covers many of **FEDI**'s functionalities. To get help with a specific tool, simply type its name followed by the -help option in your terminal. 

.. TIP::

  Some familiarity with the Unix command line is recommended to get the most out of **FEDI**.




Table of Contents
~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1
   :caption: Install

   installation/before_install
   installation/package_install

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   getting_started/starts
   getting_started/assocc_diseases

.. toctree::
   :maxdepth: 1
   :caption: FEDI Modules

   modules/starts

.. toctree::
   :maxdepth: 1
   :caption: FEDI Workflows

   workflows/haitch_starts


.. toctree::
   :maxdepth: 1
   :caption: Developer Section

   developer_section/starts


