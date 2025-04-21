Fetal and Neonatal Development Imaging
======================================

.. figure:: Focus_FEDI.png

**Fetal and Neonatal Development Imaging (FEDI)** is a comprehensive, free, open-source toolbox that provides a suite of command-line tools dedicated to the processing and analysis of fetal and neonatal MRI data.


.. note::

   **FEDI** is under active development, constantly expanding its functionalities.

Key Features
~~~~~~~~~~~~
While **FEDI** is primarily intended for the processing and analysis of fetal and neonatal MRI data, some tools can be used for any type of MRI data. In summary, **FEDI** features:

- Multiple Q-Shell Sampling
- Diffusion MRI Preprocessing
- Distortion Correction for Diffusion MRI
- Data Weighting and Outlier Detection
- Motion Correction for diffusion MRI


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


