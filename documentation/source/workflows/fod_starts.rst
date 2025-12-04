.. _fod_estimation:

Fiber Orientation Estimation with sCNN
===================================

**Fiber Orientation Distribution (FOD) Estimation** enables accurate white matter tractography and microstructural characterization. The ``fedi_dmri_fod`` tool implements a rotationally equivariant Spherical Convolutional Neural Network (sCNN) framework optimized for neonatal dMRI data.

For full methodological and validation details, refer to:

`Snoussi and Karimi, 2025 – Equivariant spherical CNNs for accurate fiber orientation distribution estimation in neonatal diffusion MRI with reduced acquisition time <https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2025.1604545/full>`__


Key Features
------------

- **Reduced Acquisition Time**: Accurate FOD estimation using only 30% of the full gradient direction protocol
- **Rotational Equivariance**: Respects the rotational symmetry of diffusion signals
- **Neonatal-Optimized**: Trained on 43 neonatal dMRI datasets from the Developing Human Connectome Project (dHCP)
- **Pretrained Model**: Automatically downloaded from Hugging Face Hub
- **Multi-Shell Support**: Works with multi-shell dMRI data (b-values: 400, 1000, 2600 s/mm²)


Results and Visualizations
---------------------------

.. only:: html

   .. image:: fod_figures/Figure1.jpg
      :width: 100%
      :align: center

   **Figure 1.** Representative FODs from a test subject. (Left column) FODs estimated by the MLP using the full dHCP dataset. (Middle column) FODs estimated by the sCNN using 30% of the diffusion directions. (Right column) Ground truth FODs estimated using Hybrid-CSD with the full dHCP dataset. The sCNN produces FODs that are visually much more similar to the ground truth than the MLP.

.. only:: latex

   \begin{figure}[htbp]
   \centering
   \includegraphics[width=\textwidth]{fod_figures/Figure1.jpg}
   \caption{Representative FODs from a test subject. (Left column) FODs estimated by the MLP using the full dHCP dataset. (Middle column) FODs estimated by the sCNN using 30\% of the diffusion directions. (Right column) Ground truth FODs estimated using Hybrid-CSD with the full dHCP dataset. The sCNN produces FODs that are visually much more similar to the ground truth than the MLP.}
   \end{figure}

.. only:: html

   .. image:: fod_figures/Figure2.jpg
      :width: 100%
      :align: center

   **Figure 2.** Representative tractography results. (Left) Tractogram generated using MLP-predicted FODs. (Middle) Tractogram generated using sCNN-predicted FODs. (Right) Tractogram generated using ground truth FODs (Hybrid-CSD).

.. only:: latex

   \begin{figure}[htbp]
   \centering
   \includegraphics[width=\textwidth]{fod_figures/Figure2.jpg}
   \caption{Representative tractography results. (Left) Tractogram generated using MLP-predicted FODs. (Middle) Tractogram generated using sCNN-predicted FODs. (Right) Tractogram generated using ground truth FODs (Hybrid-CSD).}
   \end{figure}

Accessing the FOD Estimation Code
----------------------------------

The FOD estimation functionality is implemented in ``fedi_dmri_fod`` (see :ref:`fedi_dmri_fod`), with the model in ``FEDI/models/pytorch/models.py`` (``SphericalCNN_FOD_Neonatal`` class). The pretrained model is automatically downloaded from Hugging Face Hub (``feditoolbox/scnn_neonatal_fod_estimation``).

Integration with HAITCH Pipeline
----------------------------------

The ``fedi_dmri_fod`` tool can be used as part of the HAITCH pipeline (STEP 10) to estimate FOD after motion and distortion correction. For more information, see :ref:`haitch_starts`.
