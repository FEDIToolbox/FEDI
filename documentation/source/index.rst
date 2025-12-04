Fetal and Neonatal Development Imaging
======================================

.. figure:: Focus_FEDI.png

**Fetal and Neonatal Development Imaging (FEDI)** is a free and open-source software that provides a suite of command-line tools for processing and analyzing fetal and neonatal MRI data.


Key Features
~~~~~~~~~~~~
While **FEDI** is primarily designed for fetal and neonatal MRI, several tools are applicable to general MRI processing. In summary, **FEDI** provides:


- **Gradient and b-vector tools:** Rotation of b-vectors, and gradient-scheme conversion.

- **Diffusion MRI preprocessing:** Denoising, Gibbs artifact removal, and bias-field correction.

- **Outlier detection:** Identification and weighting of outlier volumes, slices, or voxels.

- **Reconstruction:** Diffusion signal reconstruction with integrated outlier weighting.

- **Motion correction for diffusion MRI:**  Robust intra- and inter-volume motion correction designed for fetal and neonatal data, but compatible with any population.

- **FOD estimation:** Fiber-orientation distribution estimation using a pretrained spherical CNN model optimized for neonatal diffusion MRI.



.. note::

   **FEDI** is under active development, constantly expanding its functionalities.


Getting Started
~~~~~~~~~~~~~~~

**FEDI** runs on GNU/Linux and macOS. The easiest way to install it is via the pre-compiled packages (see the installation section). A Docker image will be available soon.

All **FEDI** tools share a consistent command-line interface and are executed from a terminal. For help with any tool, type its name followed by ``--help``.


.. TIP::

  Basic familiarity with the Unix command line is required to use **FEDI** effectively.


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
   workflows/fod_starts


.. toctree::
   :maxdepth: 1
   :caption: Developer Section

   developer_section/starts


