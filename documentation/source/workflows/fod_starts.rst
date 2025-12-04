.. _fod_estimation:

FOD Estimation with Spherical CNNs
===================================

**Fiber Orientation Distribution (FOD) Estimation** is a critical step in diffusion MRI analysis that enables accurate white matter tractography and microstructural characterization. The ``fedi_dmri_fod`` tool implements a rotationally equivariant Spherical Convolutional Neural Network (sCNN) framework specifically optimized for neonatal dMRI data.

For full methodological and validation details, refer to the following publication:

`Snoussi and Karimi, 2025 – Equivariant spherical CNNs for accurate fiber orientation distribution estimation in neonatal diffusion MRI with reduced acquisition time <https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2025.1604545/full>`__

Overview
--------

The ``fedi_dmri_fod`` tool addresses a key challenge in neonatal dMRI: accurately estimating FODs from data acquired with reduced gradient directions (30% of full protocol), enabling faster and more cost-effective acquisitions while maintaining high-quality results.

Key Features
------------

- **Reduced Acquisition Time**: Achieves accurate FOD estimation using only 30% of the full gradient direction protocol
- **Rotational Equivariance**: The spherical CNN architecture respects the rotational symmetry of diffusion signals
- **Neonatal-Optimized**: Trained and validated on 43 neonatal dMRI datasets from the Developing Human Connectome Project (dHCP)
- **Pretrained Model**: Uses a pretrained model automatically downloaded from Hugging Face Hub
- **Multi-Shell Support**: Works with multi-shell dMRI data (typically b-values: 400, 1000, 2600 s/mm²)

Methodology
-----------

The tool implements a spherical CNN that converts multi-shell dMRI signals to spherical harmonic (SH) coefficients, applies rotationally equivariant convolutions on the sphere, and outputs SH coefficients representing the FOD. The model architecture leverages the rotational symmetry of diffusion signals, ensuring that rotations of the input signal result in corresponding rotations of the predicted FOD.


Performance and Validation
---------------------------

The spherical CNN approach has been validated against Multi-Layer Perceptron (MLP) baseline and Hybrid-CSD ground truth. The sCNN significantly outperforms MLP and produces FODs and tractography that are quantitatively comparable and qualitatively highly similar to Hybrid-CSD, despite using only 30% of the full acquisition data.

Results and Visualizations
---------------------------

The following figures from the publication demonstrate the effectiveness of the spherical CNN approach for FOD estimation in neonatal dMRI.

.. note::

   Figures from Snoussi and Karimi (2025) will be added to the ``fod_figures/`` directory.

Example figure structure (to be added):

.. only:: html

   .. image:: fod_figures/FigureX.png
      :width: 100%
      :align: center

   **Figure 1.** [Description of FOD estimation results]

.. only:: latex

   \begin{figure}[htbp]
   \centering
   \includegraphics[width=\textwidth]{fod_figures/FigureX.pdf}
   \caption{[Description of FOD estimation results]}
   \end{figure}

Accessing the FOD Estimation Code
----------------------------------

The FOD estimation functionality is implemented in ``fedi_dmri_fod`` (see :ref:`fedi_dmri_fod`), with the model implementation in ``FEDI/models/pytorch/models.py`` (``SphericalCNN_FOD_Neonatal`` class). The pretrained model is automatically downloaded from Hugging Face Hub (``feditoolbox/scnn_neonatal_fod_estimation``) on first use.

Integration with HAITCH Pipeline
----------------------------------

The ``fedi_dmri_fod`` tool can be used as part of the HAITCH pipeline (STEP 10) for FOD estimation after motion and distortion correction. For more information about the HAITCH pipeline, see :ref:`haitch_starts`.
