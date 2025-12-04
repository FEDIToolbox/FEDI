HAITCH: Motion Correction
======

**HAITCH** is a robust framework for **distortion and motion correction** in fetal multi-shell diffusion-weighted MRI. It is an integral part of the **FEDI** toolbox, enabling high-quality preprocessing of challenging fetal dMRI datasets, and facilitating accurate downstream analyses such as tractography and microstructural modeling.

For full methodological and validation details, refer to the following publication:

`Snoussi et al., 2025 – HAITCH: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI <https://direct.mit.edu/imag/article/doi/10.1162/imag_a_00490/127881>`__

HAITCH Pipeline Steps
---------------------

The HAITCH pipeline consists of 10 main processing steps that progressively correct for noise, artifacts, distortion, and motion in fetal dMRI data:

1. **DWI Denoising (GSVS)**: Removes noise using the Generalized Spatially Varying Smoothing (GSVS) estimator
2. **Gibbs Ringing Artifact Removal**: Eliminates Gibbs ringing artifacts using the method by Kellner et al. (2016)
3. **Rician Bias Correction**: Corrects Rician noise bias, particularly important for low SNR fetal data
4. **Fetal Brain Extraction**: Segments the fetal brain from surrounding maternal tissue using deep learning methods
5. **Split, Crop, and Skull Stripping**: Processes the segmented brain data and creates masks
6. **Slice-wise Distortion Correction**: Corrects for slice-specific distortions
7. **B1 Field Bias Correction**: Corrects for B1 field inhomogeneities
8. **Motion Correction**: Iterative process using 3D-SHORE modeling. This step includes:
   - Outlier detection (slice-wise and voxel-wise weighting)
   - SHORE-based signal prediction
   - Volume-to-volume registration
   - B-vector rotation
   - Iterative refinement (typically 6 epochs)
9. **Registration to T2W Atlas**: Registers the motion-corrected dMRI data to T2-weighted anatomical space and fetal brain atlas
10. **Tensor/FOD Estimation and Tractography**: Estimates diffusion tensors or fiber orientation distributions (FODs) and performs tractography

Accessing the HAITCH Pipeline Code
-----------------------------------

The HAITCH pipeline is available in two versions:

**HAITCH 1.0** (Original Version)
   - Location: ``FEDI/pipelines/HAITCH1.0/``
   - Uses original Python scripts from the ``src/`` directory
   - Manual iteration loop for motion correction
   - Fully tested and stable

**HAITCH 2.0** (Updated Version)
   - Location: ``FEDI/pipelines/HAITCH2.0/``
   - Uses the new ``fedi_*`` command-line tools
   - Simplified STEP 8 using ``fedi_dmri_moco`` (single command instead of manual loop)
   - Cleaner implementation with better maintainability

Both versions produce identical results and can be used interchangeably. The main pipeline script is ``dMRI_HAITCH.sh``, which requires a configuration file as input.

For detailed usage instructions and configuration options, see the ``README.md`` files in each pipeline directory.

Sampling Schemes
----------------

The diffusion-weighted MRI sampling schemes used in the HAITCH validation study are available in the ``FEDI/sampling_scheme/`` directory. These include:

- ``HAITCH_scheme_dual_echo_sequence.dvs`` - Dual-echo sequence sampling scheme
- ``HAITCH_scheme_siemens_product_sequence.dvs`` - Siemens product sequence sampling scheme


Results and Visualizations
--------------------------

The following figures illustrate the effectiveness of HAITCH in real fetal diffusion MRI datasets.

.. only:: html

   .. image:: haitch_figures/Figure5.png
      :width: 100%
      :align: center

   **Figure 1.** Two examples fetal dMRI scans before and after motion correction.  

.. only:: latex

   \begin{figure}[htbp]
   \centering
   \includegraphics[width=\textwidth]{Figures/Figure5.pdf}
   \caption{Example fetal dMRI scans before and after motion correction. The left two columns display axial, coronal, and sagittal views of the raw data (Subject A) and corresponding motion-corrected data. The right two columns show corrected data for Subject B. Each row represents selected volume indices.}
   \end{figure}

.. only:: html

   .. image:: haitch_figures/Figure6.png
      :width: 80%
      :align: center

   **Figure 2.** Estimated motion parameters and slice weights for Subject B. Peaks in motion correlate with low slice weights.

.. only:: latex

   \begin{figure}[htbp]
   \centering
   \includegraphics[width=0.8\textwidth, trim={1cm 0cm 0cm 0cm}, clip]{Figures/Figure6.pdf}
   \caption{Estimated motion parameters over time and slice weights for Subject B. The top panels show translation and rotation parameters; the bottom panel shows slice-wise weights, where low values indicate motion-related outliers.}
   \end{figure}

.. only:: html

   .. image:: haitch_figures/Figure9.png
      :width: 100%
      :align: center

   **Figure 3.** Impact of HAITCH on the quality of NODDI parameter maps.  

.. only:: latex

   \begin{figure}[htbp]
   \centering
   \includegraphics[width=\textwidth]{Figures/Figure9.pdf}
   \caption{Comparison of NODDI parameter maps before and after applying HAITCH correction. The top row shows maps from uncorrected data; the bottom row shows maps after motion and distortion correction. From left to right: ODI, NDI (ICVF), and FISO.}
   \end{figure}
