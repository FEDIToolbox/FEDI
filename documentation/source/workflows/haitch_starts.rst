HAITCH
======

**HAITCH** is a robust framework for **distortion and motion correction** in fetal multi-shell diffusion-weighted MRI. It is an integral part of the **FEDI** toolbox, enabling high-quality preprocessing of challenging fetal dMRI datasets, and facilitating accurate downstream analyses such as tractography and microstructural modeling.

For full methodological and validation details, refer to the following publication:

`Snoussi et al., 2025 – HAITCH: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI <https://direct.mit.edu/imag/article/doi/10.1162/imag_a_00490/127881>`__



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
