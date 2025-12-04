======================================================
Fetal and Neonatal MRI and FEDI Toolbox Overview
======================================================

Fetal and Neonatal Magnetic Resonance Imaging (MRI) are **advanced diagnostic tools** used to assess prenatal and early postnatal development, especially when ultrasound is inconclusive. MRI provides **unparalleled soft-tissue contrast** and high-resolution 3D insights for precise evaluation of complex anatomy and pathology.

.. note::
   MRI is helpful for all of the following conditions mainly by better characterizing brain structure, detecting additional lesions, and improving prognostication compared with ultrasound or clinical exam alone. [1]_ [2]_ [3]_ [4]_ [5]_ [6]_

-------------------------------------------------
I. Introduction to Fetal and Neonatal MRI
-------------------------------------------------

Key Applications
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Modality
     - When Performed
     - Primary Use
   * - **Fetal MRI**
     - Typically after 18 weeks of gestation.
     - Provides **superior visualization** of the developing **brain, lungs, and abdomen**. Essential for assessing congenital anomalies and placental health.
   * - **Neonatal MRI**
     - Shortly after birth, often for critically ill newborns.
     - Crucial for diagnosing **brain injuries** (like Hypoxic-Ischemic Encephalopathy (HIE)) and monitoring neurodevelopmental outcomes.

Imaging Challenges
^^^^^^^^^^^^^^^^^^

Both modalities face specific processing challenges due to the patient population:

* **Fetal MRI:** Primarily motion artifacts from fetal movement and limited spatial resolution.
* **Neonatal MRI:** High sensitivity to patient movement and lower tissue contrast in immature organs.

The FEDI Toolbox Solution
^^^^^^^^^^^^^^^^^^^^^^^^^

The **FEDI toolbox** streamlines the **processing and analysis** of fetal and neonatal MRI data. It directly addresses the primary imaging challenges via core capabilities like **motion correction, segmentation, and brain tractography**.

-------------------------------------------------
II. Fetal and Neonatal Brain Conditions
-------------------------------------------------

**T2-weighted (T2w)** and **Diffusion MRI (dMRI)** are crucial for investigating a wide range of fetal and neonatal brain conditions. Here are key examples of conditions assessed by MRI.

Fetal Conditions
^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 40 35
   :header-rows: 1

   * - Condition
     - T2w (Structural)
     - dMRI (Microstructural)
   * - **Ventriculomegaly & Hydrocephalus**
     - Assesses ventricular size and underlying causes. (Most common indication for Fetal MRI [3]_ [4]_)
     - Investigational use in detecting associated white matter injuries.
   * - **Congenital Brain Malformations**
     - Detects structural abnormalities such as Neural tube defects and Agenesis of the corpus callosum. [3]_
     - Used in research to assess white matter tract development (e.g., in callosal agenesis).
   * - **Twin Complications (TTTS)**
     - Identifies brain injury (atrophy, hemorrhage) in donor/recipient twin. [5]_ [6]_
     - May reveal acute ischemia (restricted diffusion).

Neonatal Conditions
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 40 35
   :header-rows: 1

   * - Condition
     - T2w (Structural/Chronic)
     - dMRI (Acute Injury)
   * - **Hypoxic-Ischemic Encephalopathy (HIE)**
     - Shows later-phase changes (edema, atrophy, and cystic changes).
     - Detects early injury (restricted diffusion in basal ganglia, thalamus, and white matter). (Most common clinically important injury [6]_)
   * - **IVH & Periventricular Leukomalacia (PVL)**
     - Depicts hemorrhage, ventricular enlargement, and cystic changes (in chronic PVL).
     - Used for early detection of white matter injury in preterm infants.
   * - **Neonatal Stroke**
     - Maps infarct territory and excludes hemorrhage.
     - Identifies acute infarcts (bright DWI, dark ADC).

.. rubric:: References (Most Recent)

.. [1] https://www.sciencedirect.com/science/article/abs/pii/S2173510725001569 (2025)
.. [2] https://link.springer.com/chapter/10.1007/978-3-031-73260-7_4 (2024 - **Requested**)
.. [3] https://pmc.ncbi.nlm.nih.gov/articles/PMC10687196/ (2023)
.. [4] https://pmc.ncbi.nlm.nih.gov/articles/PMC10378043/ (2023)
.. [5] https://pmc.ncbi.nlm.nih.gov/articles/PMC8947742/ (2022)
.. [6] https://pmc.ncbi.nlm.nih.gov/articles/PMC8013256/ (2021)
