#!/usr/bin/env python3
"""
FEDI Testing Commands

This module:
1. Generates synthetic NIfTI MRI test data with fixed parameters
2. Automatically tests all FEDI command-line tools and verifies outputs

Test data is saved to ~/.fedi_test_data/ (user's home directory, not in repository)

Usage:
    python -m FEDI.scripts.fedi_testing_commands
    or
    fedi_testing
"""

import os
import sys
import subprocess
import tempfile
import shutil
import numpy as np
from pathlib import Path
from scipy.io import savemat

# Add parent directory to path to import FEDI modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import nibabel as nib
from scipy.ndimage import gaussian_filter


# ============================================================================
# PART 1: GENERATE TEST DATA
# ============================================================================

def _generate_uniform_directions(n):
    """
    Generate n uniformly distributed directions on a sphere.
    
    Uses the golden spiral method for uniform distribution.
    """
    directions = []
    golden_angle = np.pi * (3 - np.sqrt(5))  # Golden angle in radians
    
    for i in range(n):
        y = 1 - (i / float(n - 1)) * 2  # y goes from 1 to -1
        radius = np.sqrt(1 - y * y)  # radius at y
        theta = golden_angle * i  # golden angle increment
        
        x = np.cos(theta) * radius
        z = np.sin(theta) * radius
        
        directions.append([x, y, z])
    
    return np.array(directions)


def generate_test_data(output_dir=None):
    """
    Generate synthetic 4D diffusion MRI data with fixed parameters.
    
    Fixed parameters:
    - shape: (64, 64, 30, 100)
    - n_b0: 10
    - b_values: [400, 1000, 2600]
    - n_directions_per_shell: [30, 30, 30]
    - snr: 20.0
    
    Parameters
    ----------
    output_dir : str, optional
        Output directory. If None, uses ~/.fedi_test_data/
        
    Returns
    -------
    dict : Dictionary with paths to generated files
    """
    # Fixed parameters
    shape = (64, 64, 30, 100)
    n_b0 = 10
    b_values = [400, 1000, 2600]
    n_directions_per_shell = [30, 30, 30]
    snr = 20.0
    
    # Set output directory
    if output_dir is None:
        home_dir = os.path.expanduser("~")
        output_dir = os.path.join(home_dir, '.fedi_test_data')
    
    os.makedirs(output_dir, exist_ok=True)
    
    x, y, z, n_volumes = shape
    
    print(f"Generating test data in: {output_dir}")
    print(f"  Shape: {shape}")
    print(f"  b-values: b=0 (x{n_b0}), {b_values}")
    print(f"  Directions per shell: {n_directions_per_shell}")
    print(f"  SNR: {snr}")
    
    # Create a simple brain-like mask (ellipsoid)
    center = np.array([x//2, y//2, z//2])
    radii = np.array([x*0.3, y*0.3, z*0.4])
    
    xx, yy, zz = np.meshgrid(np.arange(x), np.arange(y), np.arange(z), indexing='ij')
    mask = ((xx - center[0])**2 / radii[0]**2 + 
            (yy - center[1])**2 / radii[1]**2 + 
            (zz - center[2])**2 / radii[2]**2) <= 1.0
    
    # Generate b-values and b-vectors
    bvals = []
    bvecs = []
    
    # Add b=0 volumes
    for i in range(n_b0):
        bvals.append(0)
        bvecs.append([0, 0, 0])
    
    # Add diffusion-weighted volumes
    for bval, n_dir in zip(b_values, n_directions_per_shell):
        # Generate uniformly distributed gradient directions
        directions = _generate_uniform_directions(n_dir)
        for direction in directions:
            bvals.append(bval)
            bvecs.append(direction)
    
    bvals = np.array(bvals)
    bvecs = np.array(bvecs)
    
    # Normalize b-vectors
    norms = np.linalg.norm(bvecs, axis=1)
    bvecs[norms > 0] = bvecs[norms > 0] / norms[norms > 0, np.newaxis]
    
    # Ensure we have the right number of volumes
    if len(bvals) != n_volumes:
        # Adjust to match requested volumes
        if len(bvals) < n_volumes:
            # Add more b=0 volumes
            n_add = n_volumes - len(bvals)
            bvals = np.concatenate([bvals, np.zeros(n_add)])
            bvecs = np.concatenate([bvecs, np.zeros((n_add, 3))])
        else:
            # Truncate
            bvals = bvals[:n_volumes]
            bvecs = bvecs[:n_volumes]
    
    # Create synthetic dMRI data
    dmri_data = np.zeros(shape, dtype=np.float32)
    
    # Base signal intensity
    S0 = 1000.0
    
    # Create ADC map (simplified - higher in center, lower at edges)
    adc_map = np.ones((x, y, z)) * 0.8e-3  # mm²/s
    adc_map[mask] = 1.0e-3
    
    # Add some structure (white matter has lower ADC)
    wm_center = center
    wm_radius = radii * 0.5
    wm_mask = ((xx - wm_center[0])**2 / wm_radius[0]**2 + 
               (yy - wm_center[1])**2 / wm_radius[1]**2 + 
               (zz - wm_center[2])**2 / wm_radius[2]**2) <= 1.0
    adc_map[wm_mask] = 0.6e-3
    
    # Generate signal for each volume
    print("  Generating dMRI volumes...")
    for vol_idx in range(n_volumes):
        bval = bvals[vol_idx]
        bvec = bvecs[vol_idx]
        
        if bval == 0:
            # b=0 image
            signal = S0 * np.ones((x, y, z))
        else:
            # Diffusion-weighted image
            # Simple model: S = S0 * exp(-b * ADC * (1 - FA * (g·n)²))
            # where n is the principal diffusion direction
            principal_dir = np.array([1, 0, 0])  # Simplified principal direction
            dot_product = np.abs(np.dot(bvec, principal_dir))
            fa = 0.7  # Fractional anisotropy
            
            # ADC along gradient direction
            adc_effective = adc_map * (1 - fa * dot_product**2)
            
            signal = S0 * np.exp(-bval * adc_effective)
        
        # Apply mask
        signal[~mask] = 0
        
        # Add noise
        noise = np.random.normal(0, S0 / snr, (x, y, z))
        signal = signal + noise
        signal[signal < 0] = 0  # Ensure non-negative
        
        dmri_data[:, :, :, vol_idx] = signal
    
    # Create affine matrix (standard orientation)
    affine = np.eye(4)
    affine[0, 0] = -2.0  # x voxel size
    affine[1, 1] = 2.0  # y voxel size
    affine[2, 2] = 2.0  # z voxel size
    
    # Save dMRI NIfTI file
    print("  Saving files...")
    dmri_img = nib.Nifti1Image(dmri_data, affine)
    dmri_path = os.path.join(output_dir, 'dmri.nii.gz')
    nib.save(dmri_img, dmri_path)
    
    # Save bvals and bvecs (FSL format)
    bval_path = os.path.join(output_dir, 'dmri.bval')
    bvec_path = os.path.join(output_dir, 'dmri.bvec')
    
    # bvals: 1D array, space-delimited, saved as row
    np.savetxt(bval_path, bvals.reshape(1, -1), delimiter=" ", fmt='%.0f')
    
    # bvecs: 3 x N format (3 rows, N columns) - ensure correct shape
    if bvecs.shape[0] != 3:
        bvecs_save = bvecs.T
    else:
        bvecs_save = bvecs
    np.savetxt(bvec_path, bvecs_save, delimiter=" ", fmt='%.6f')
    
    # Save mask
    mask_data = mask.astype(np.uint8)
    mask_img = nib.Nifti1Image(mask_data, affine)
    mask_path = os.path.join(output_dir, 'mask.nii.gz')
    nib.save(mask_img, mask_path)
    
    # Create a simple predicted/reconstructed data (spred)
    # This is a smoothed version of the original data
    spred_data = np.zeros_like(dmri_data)
    for vol_idx in range(n_volumes):
        spred_data[:, :, :, vol_idx] = gaussian_filter(
            dmri_data[:, :, :, vol_idx], sigma=1.0
        )
    spred_img = nib.Nifti1Image(spred_data, affine)
    spred_path = os.path.join(output_dir, 'spred.nii.gz')
    nib.save(spred_img, spred_path)
    
    print(f"✓ Test data generated successfully!")
    print(f"  - dMRI: {dmri_path}")
    print(f"  - bvals: {bval_path}")
    print(f"  - bvecs: {bvec_path}")
    print(f"  - mask: {mask_path}")
    print(f"  - spred: {spred_path}")
    
    return {
        'dmri': dmri_path,
        'bval': bval_path,
        'bvec': bvec_path,
        'mask': mask_path,
        'spred': spred_path,
        'output_dir': output_dir
    }


# ============================================================================
# PART 2: AUTOMATED TESTING
# ============================================================================

class FEDITestingCommands:
    """Testing suite for FEDI toolbox scripts."""
    
    def __init__(self, test_files, verbose=True):
        """
        Initialize test suite.
        
        Parameters
        ----------
        test_files : dict
            Dictionary with paths to test data files
        verbose : bool
            Print detailed output
        """
        self.verbose = verbose
        self.test_files = test_files
        self.test_results = {}
        
    def log(self, message):
        """Print log message if verbose."""
        if self.verbose:
            print(f"[TEST] {message}")
    
    def run_command(self, cmd, expected_exit_code=0, check_outputs=None):
        """
        Run a command and check exit code and output files.
        
        Parameters
        ----------
        cmd : list
            Command to run as list of strings (will be converted to Python module call if needed)
        expected_exit_code : int
            Expected exit code (0 for success)
        check_outputs : list, optional
            List of output file paths to verify exist
            
        Returns
        -------
        bool : True if command succeeded and outputs exist
        """
        # Always use Python module calls for FEDI commands to test source code
        # This ensures we're testing the current source, not the installed package
        if cmd[0].startswith('fedi_'):
            # Convert 'fedi_dmri_snr' to 'python -m FEDI.scripts.fedi_dmri_snr'
            module_name = cmd[0].replace('fedi_', 'FEDI.scripts.fedi_')
            cmd = [sys.executable, '-m', module_name] + cmd[1:]
        
        self.log(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = True
            
            if result.returncode != expected_exit_code:
                self.log(f"✗ Command failed (exit code: {result.returncode}, expected: {expected_exit_code})")
                if result.stderr:
                    self.log(f"  STDERR: {result.stderr[:500]}")
                success = False
            else:
                self.log(f"✓ Command succeeded (exit code: {result.returncode})")
            
            # Check output files
            if check_outputs:
                for output_file in check_outputs:
                    if os.path.exists(output_file):
                        file_size = os.path.getsize(output_file)
                        self.log(f"  ✓ Output file exists: {output_file} ({file_size} bytes)")
                    else:
                        self.log(f"  ✗ Output file missing: {output_file}")
                        success = False
            
            if not success and result.stdout:
                self.log(f"  STDOUT: {result.stdout[:500]}")
            
            return success
                
        except subprocess.TimeoutExpired:
            self.log("✗ Command timed out (>5 minutes)")
            return False
        except Exception as e:
            self.log(f"✗ Command error: {e}")
            return False
    
    def test_fedi_dmri_snr(self):
        """Test fedi_dmri_snr script."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_snr")
        self.log("="*60)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                'fedi_dmri_snr',
                '-d', self.test_files['dmri'],
                '-a', self.test_files['bval'],
                '-m', self.test_files['mask']
            ]
            # This command prints to stdout, no file output expected
            return self.run_command(cmd, expected_exit_code=0)
    
    def test_fedi_dmri_outliers(self):
        """Test fedi_dmri_outliers script."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_outliers")
        self.log("="*60)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create output files
            fsliceweights_mzscore = os.path.join(tmpdir, 'sliceweights_mzscore.txt')
            fsliceweights_angle = os.path.join(tmpdir, 'sliceweights_angle.txt')
            fsliceweights_corr = os.path.join(tmpdir, 'sliceweights_corr.txt')
            
            cmd = [
                'fedi_dmri_outliers',
                '-d', self.test_files['dmri'],
                '-b', self.test_files['dmri'],  # dmrigmm (same file for testing)
                '-a', self.test_files['bval'],
                '-e', self.test_files['bvec'],
                '-o', tmpdir,
                '-s', self.test_files['spred'],  # spred
                '-m', self.test_files['mask'],  # mask
                '-z', fsliceweights_mzscore,
                '-n', fsliceweights_angle,
                '-y', fsliceweights_corr
            ]
            
            expected_outputs = [
                fsliceweights_mzscore,
                fsliceweights_angle,
                fsliceweights_corr,
                fsliceweights_mzscore.replace('.txt', '.png'),
                fsliceweights_corr.replace('.txt', '.png')
            ]
            
            return self.run_command(cmd, expected_exit_code=0, check_outputs=expected_outputs)
    
    def test_fedi_dmri_recon(self):
        """Test fedi_dmri_recon script."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_recon")
        self.log("="*60)
        
        # Check if required dependency is available
        try:
            from FEDI.utils.FEDI_shore import BrainSuiteShoreModel
        except ImportError as e:
            self.log("⚠ Skipping test: FEDI.utils.FEDI_shore not available")
            self.log(f"  Import error: {e}")
            self.log("  This test requires FEDI_shore module in FEDI/utils/")
            return None  # Return None to indicate skipped test
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create weights file
            weights_file = os.path.join(tmpdir, 'weights.txt')
            # Create simple weights (slice x volume)
            n_slices = 30
            n_volumes = 100
            weights = np.ones((n_slices, n_volumes)) * 0.8
            np.savetxt(weights_file, weights, delimiter=',', fmt='%.6f')
            
            # Create output bvec (same as input for testing)
            output_bvec = os.path.join(tmpdir, 'bvec_out.bvec')
            shutil.copy(self.test_files['bvec'], output_bvec)
            
            spred_output = os.path.join(tmpdir, 'spred_output.nii.gz')
            
            cmd = [
                'fedi_dmri_recon',
                '-d', self.test_files['dmri'],
                '-a', self.test_files['bval'],
                '-e', self.test_files['bvec'],  # bvec_in
                '-u', output_bvec,  # bvec_out
                '-w', weights_file,
                '-s', spred_output,
                '-m', self.test_files['mask']
            ]
            
            return self.run_command(cmd, expected_exit_code=0, check_outputs=[spred_output])
    
    def test_fedi_dmri_rotate_bvecs(self):
        """Test fedi_dmri_rotate_bvecs script using provided .mat files."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_rotate_bvecs")
        self.log("="*60)
        
        # Path to testing directory with .mat files
        testing_dir = '/home/ch244310/software/FEDI/testing'
        
        # Check if example .mat files exist
        example_mat_files = [
            'example_Transform_v1_0GenericAffine.mat',
            'example_Transform_v2_0GenericAffine.mat',
            'example_Transform_v3_0GenericAffine.mat'
        ]
        
        for mat_file in example_mat_files:
            mat_path = os.path.join(testing_dir, mat_file)
            if not os.path.exists(mat_path):
                self.log(f"⚠ Skipping test: Required .mat file not found: {mat_path}")
                return None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create transformation matrices directory
            mat_dir = os.path.join(tmpdir, 'transforms')
            os.makedirs(mat_dir, exist_ok=True)
            
            # Load original bvecs
            bvecs = np.loadtxt(self.test_files['bvec'])
            if bvecs.shape[0] == 3:
                # bvecs is in 3xN format (FSL format) - transpose to Nx3 for indexing
                bvecs_T = bvecs.T
                n_volumes_original = bvecs.shape[1]
            else:
                # bvecs is in Nx3 format
                bvecs_T = bvecs
                n_volumes_original = bvecs.shape[0]
            
            # Extract volumes 1, 2, 3 (0-indexed: 1, 2, 3)
            # The script expects Transform_v0, Transform_v1, Transform_v2 for 3 volumes
            volume_indices = [1, 2, 3]
            if any(idx >= n_volumes_original for idx in volume_indices):
                self.log(f"⚠ Skipping test: Volume indices {volume_indices} exceed available volumes ({n_volumes_original})")
                return None
            
            # Create subset bvecs with only volumes 1, 2, 3
            subset_bvecs = bvecs_T[volume_indices].T  # Back to 3xN format
            subset_bvec_file = os.path.join(tmpdir, 'bvec_subset.bvec')
            np.savetxt(subset_bvec_file, subset_bvecs, fmt='%.6f')
            
            self.log(f"  Using {len(volume_indices)} example transformation matrices from testing directory")
            self.log(f"  Volumes: {volume_indices}")
            
            # Copy and rename example .mat files to match expected naming (Transform_v0, Transform_v1, Transform_v2)
            prefix = "Transform_v"
            suffix = "_0GenericAffine.mat"
            
            for i, orig_vol_idx in enumerate([1, 2, 3], start=1):
                orig_mat = os.path.join(testing_dir, f'example_Transform_v{orig_vol_idx}_0GenericAffine.mat')
                new_mat = os.path.join(mat_dir, f'{prefix}{i-1}{suffix}')  # i-1 because we want 0, 1, 2
                shutil.copy2(orig_mat, new_mat)
                self.log(f"    Copied: example_Transform_v{orig_vol_idx} -> Transform_v{i-1}")
            
            output_bvec = os.path.join(tmpdir, 'bvec_rotated.bvec')
            
            cmd = [
                'fedi_dmri_rotate_bvecs',
                '-e', subset_bvec_file,  # Use subset bvecs
                '-n', output_bvec,
                '-m', mat_dir,
                '-s', prefix,  # Specify prefix
                '-d', suffix   # Specify suffix
            ]
            
            return self.run_command(cmd, expected_exit_code=0, check_outputs=[output_bvec])
    
    def test_fedi_dmri_qweights(self):
        """Test fedi_dmri_qweights script."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_qweights")
        self.log("="*60)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use the gradient table file from testing directory
            gradient_file = '/home/ch244310/software/FEDI/testing/gradient_table_example.txt'
            
            if not os.path.exists(gradient_file):
                self.log(f"⚠ Skipping test: Gradient table file not found: {gradient_file}")
                return None
            
            # Output files
            siemens_scheme = os.path.join(tmpdir, 'siemens_scheme.dvs')
            debug_file = os.path.join(tmpdir, 'debug.txt')
            
            # b-values: 500 and 1000 (matching shells 1 and 2 in the gradient file)
            cmd = [
                'fedi_dmri_qweights',
                '-i', gradient_file,
                '-o', siemens_scheme,
                '-b', '500', '1000',  # Two b-values for two shells
                '-d', debug_file
                # -n is optional with default=0, so we don't need to specify it
            ]
            
            expected_outputs = [siemens_scheme, debug_file]
            
            return self.run_command(cmd, expected_exit_code=0, check_outputs=expected_outputs)
    
    def test_fedi_dmri_reg(self):
        """Test fedi_dmri_reg script with a subset of volumes."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_reg")
        self.log("="*60)
        
        # Check for required dependencies
        required_tools = ['mrinfo', 'mrconvert', 'mrcat', 'antsRegistration']
        missing_tools = []
        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            self.log(f"⚠ Skipping test: Required tools not found: {', '.join(missing_tools)}")
            self.log("  This test requires MRtrix3 and ANTs to be installed and in PATH")
            return None
        
        # Use ~/.fedi_test_data/ for test outputs
        test_data_dir = os.path.expanduser('~/.fedi_test_data')
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Create subset with only 3 volumes (volumes 0, 1, 2) for faster testing
        import nibabel as nib
        self.log("  Creating subset with 3 volumes for faster testing...")
        
        # Load original data
        dmri_img = nib.load(self.test_files['dmri'])
        spred_img = nib.load(self.test_files['spred'])
        
        dmri_data = dmri_img.get_fdata()
        spred_data = spred_img.get_fdata()
        
        # Extract first 3 volumes
        n_volumes_subset = 3
        dmri_subset = dmri_data[:, :, :, :n_volumes_subset]
        spred_subset = spred_data[:, :, :, :n_volumes_subset]
        
        # Save subset files
        dmri_subset_file = os.path.join(test_data_dir, 'dmri_subset.nii.gz')
        spred_subset_file = os.path.join(test_data_dir, 'spred_subset.nii.gz')
        
        dmri_subset_img = nib.Nifti1Image(dmri_subset, dmri_img.affine, dmri_img.header)
        spred_subset_img = nib.Nifti1Image(spred_subset, spred_img.affine, spred_img.header)
        
        nib.save(dmri_subset_img, dmri_subset_file)
        nib.save(spred_subset_img, spred_subset_file)
        
        self.log(f"  Created subset files with {n_volumes_subset} volumes")
        
        # Use test_data_dir for outputs
        output_dir = os.path.join(test_data_dir, 'reg_output')
        output_dmri = os.path.join(test_data_dir, 'dmri_registered.nii.gz')
        
        # Remove existing output file if it exists (to avoid mrcat error)
        if os.path.exists(output_dmri):
            os.remove(output_dmri)
            self.log("  Removed existing output file")
        
        cmd = [
            'fedi_dmri_reg',
            '--input_dmri', dmri_subset_file,
            '--target_dmri', spred_subset_file,
            '--output_dir', output_dir,
            '--output_dmri', output_dmri
        ]
        
        # Check that the output file is created
        expected_outputs = [output_dmri]
        
        return self.run_command(cmd, expected_exit_code=0, check_outputs=expected_outputs)
    
    def test_fedi_apply_transform(self):
        """Test fedi_apply_transform script."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_apply_transform")
        self.log("="*60)
        
        # Check for required dependency
        if not shutil.which('antsApplyTransforms'):
            self.log("⚠ Skipping test: antsApplyTransforms not found")
            self.log("  This test requires ANTs to be installed and in PATH")
            return None
        
        # Use ~/.fedi_test_data/ for test files
        test_data_dir = os.path.expanduser('~/.fedi_test_data')
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Use the subset files and transform from fedi_dmri_reg test
        # If reg_output exists, use transforms from there, otherwise create a simple test
        reg_output_dir = os.path.join(test_data_dir, 'reg_output')
        dmri_subset = os.path.join(test_data_dir, 'dmri_subset.nii.gz')
        
        # Check if we have transform files from the reg test
        transform_file = None
        if os.path.exists(reg_output_dir):
            # Look for a transform file (usually Transform_v0_0GenericAffine.mat or similar)
            for vol_idx in range(3):  # We know we have 3 volumes
                potential_transform = os.path.join(reg_output_dir, f'Transform_v{vol_idx}_0GenericAffine.mat')
                if os.path.exists(potential_transform):
                    transform_file = potential_transform
                    self.log(f"  Using transform file from reg test: {os.path.basename(transform_file)}")
                    break
        
        # If no transform from reg test, use example transform from testing directory
        if not transform_file:
            testing_dir = '/home/ch244310/software/FEDI/testing'
            example_transform = os.path.join(testing_dir, 'example_Transform_v1_0GenericAffine.mat')
            if os.path.exists(example_transform):
                transform_file = example_transform
                self.log(f"  Using example transform file: {os.path.basename(transform_file)}")
            else:
                self.log("⚠ Skipping test: No transform file found")
                self.log("  Run fedi_dmri_reg test first, or ensure example transform files exist")
                return None
        
        # antsApplyTransforms works on 3D volumes, so extract first volume from subset
        # Use dmri_subset if it exists, otherwise use full dmri
        if not os.path.exists(dmri_subset):
            # Create subset if it doesn't exist
            import nibabel as nib
            dmri_img = nib.load(self.test_files['dmri'])
            dmri_data = dmri_img.get_fdata()
            dmri_subset_data = dmri_data[:, :, :, :3]  # First 3 volumes
            dmri_subset_img = nib.Nifti1Image(dmri_subset_data, dmri_img.affine, dmri_img.header)
            nib.save(dmri_subset_img, dmri_subset)
            self.log("  Created dMRI subset file")
        else:
            self.log("  Using dMRI subset file")
        
        # Extract first volume (3D) for transformation
        import nibabel as nib
        dmri_subset_img = nib.load(dmri_subset)
        dmri_subset_data = dmri_subset_img.get_fdata()
        dmri_single_vol = dmri_subset_data[:, :, :, 0]  # First volume only
        dmri_single_file = os.path.join(test_data_dir, 'dmri_single_vol.nii.gz')
        dmri_single_img = nib.Nifti1Image(dmri_single_vol, dmri_subset_img.affine, dmri_subset_img.header)
        nib.save(dmri_single_img, dmri_single_file)
        self.log("  Extracted single volume for transformation")
        
        # Output file
        output_file = os.path.join(test_data_dir, 'dmri_transformed.nii.gz')
        
        # Use the same file as reference (extract first volume from spred_subset)
        reference_file = os.path.join(test_data_dir, 'spred_subset.nii.gz')
        if not os.path.exists(reference_file):
            reference_file = self.test_files['spred']
        
        # Extract first volume from reference as well
        spred_img = nib.load(reference_file)
        spred_data = spred_img.get_fdata()
        if spred_data.ndim == 4:
            spred_single_vol = spred_data[:, :, :, 0]
            spred_single_file = os.path.join(test_data_dir, 'spred_single_vol.nii.gz')
            spred_single_img = nib.Nifti1Image(spred_single_vol, spred_img.affine, spred_img.header)
            nib.save(spred_single_img, spred_single_file)
            reference_file = spred_single_file
            self.log("  Extracted single volume from reference")
        
        cmd = [
            'fedi_apply_transform',
            '-i', dmri_single_file,  # Use single volume (3D)
            '-o', output_file,
            '-t', transform_file,
            '-r', reference_file  # Use single volume reference (3D)
        ]
        
        expected_outputs = [output_file]
        
        return self.run_command(cmd, expected_exit_code=0, check_outputs=expected_outputs)
    
    def test_fedi_dmri_moco(self):
        """Test fedi_dmri_moco script (motion correction pipeline)."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_moco")
        self.log("="*60)
        
        # Check if required dependencies are available
        try:
            from FEDI.utils.FEDI_shore import BrainSuiteShoreModel
        except ImportError as e:
            self.log("⚠ Skipping test: FEDI.utils.FEDI_shore not available")
            self.log(f"  Import error: {e}")
            self.log("  This test requires FEDI_shore module")
            return None
        
        # Check for required external tools
        required_tools = ['mrinfo', 'mrconvert', 'mrcat', 'antsRegistration']
        missing_tools = []
        for tool in required_tools:
            if shutil.which(tool) is None:
                missing_tools.append(tool)
        if missing_tools:
            self.log(f"⚠ Skipping test: Required tools not available: {', '.join(missing_tools)}")
            self.log("  This test requires MRtrix3 and ANTs to be installed")
            return None
        
        # Use ~/.fedi_test_data/ for test outputs
        test_data_dir = os.path.expanduser('~/.fedi_test_data')
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Create a small 5x5x5 region from the center for faster testing (keep all 100 volumes)
        import nibabel as nib
        self.log("  Creating 5x5x5 subset from center (keeping all volumes) for faster testing...")
        
        # Load original data
        dmri_img = nib.load(self.test_files['dmri'])
        mask_img = nib.load(self.test_files['mask'])
        
        dmri_data = dmri_img.get_fdata()
        mask_data = mask_img.get_fdata()
        
        # Extract 5x5x5 region from the center, keep all volumes
        x_size, y_size, z_size, n_volumes = dmri_data.shape
        crop_size = 5
        
        # Calculate center indices
        x_center = x_size // 2
        y_center = y_size // 2
        z_center = z_size // 2
        
        # Calculate crop boundaries
        x_start = x_center - crop_size // 2
        x_end = x_start + crop_size
        y_start = y_center - crop_size // 2
        y_end = y_start + crop_size
        z_start = z_center - crop_size // 2
        z_end = z_start + crop_size
        
        # Extract 5x5x5 region from center, keep all volumes
        dmri_subset = dmri_data[x_start:x_end, y_start:y_end, z_start:z_end, :]
        mask_subset = mask_data[x_start:x_end, y_start:y_end, z_start:z_end]
        
        # Update affine to reflect the cropped region
        affine_subset = dmri_img.affine.copy()
        # Adjust translation to account for the crop
        crop_offset = np.array([x_start, y_start, z_start, 0])
        affine_subset[:3, 3] += affine_subset[:3, :3] @ crop_offset[:3]
        
        # Save subset files
        dmri_subset_file = os.path.join(test_data_dir, 'dmri_moco_subset.nii.gz')
        mask_subset_file = os.path.join(test_data_dir, 'mask_moco_subset.nii.gz')
        
        dmri_subset_img = nib.Nifti1Image(dmri_subset, affine_subset, dmri_img.header)
        mask_subset_img = nib.Nifti1Image(mask_subset, affine_subset, mask_img.header)
        
        nib.save(dmri_subset_img, dmri_subset_file)
        nib.save(mask_subset_img, mask_subset_file)
        
        # Keep all bvals and bvecs (100 volumes)
        bval_subset_file = os.path.join(test_data_dir, 'dmri_moco_subset.bval')
        bvec_subset_file = os.path.join(test_data_dir, 'dmri_moco_subset.bvec')
        
        # Copy original bvals and bvecs (all volumes)
        shutil.copy(self.test_files['bval'], bval_subset_file)
        shutil.copy(self.test_files['bvec'], bvec_subset_file)
        
        self.log(f"  Created subset files: 5x5x5 region from center (from {x_size}x{y_size}x{z_size}), keeping all {n_volumes} volumes")
        
        # Set up output directory (clean it first to avoid conflicts)
        output_dir = os.path.join(test_data_dir, 'moco_output')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        self.log("  Note: This test runs the motion correction pipeline (3 epochs) on a subset of data")
        self.log("  Note: This may still take a few minutes due to the iterative nature of the pipeline")
        
        cmd = [
            'fedi_dmri_moco',
            '-d', dmri_subset_file,
            '-a', bval_subset_file,
            '-e', bvec_subset_file,
            '-o', output_dir,
            '-m', mask_subset_file,
            '--epochs', '3'  # Use 3 epochs for faster testing
        ]
        
        # Expected outputs after completion (after 3 epochs)
        expected_outputs = [
            os.path.join(output_dir, 'spred2.nii.gz'),  # Final spred after 3 iterations (0-2)
            os.path.join(output_dir, 'fsliceweights_mzscore_0.txt'),  # Initial weights
            os.path.join(output_dir, 'fsliceweights_gmmodel_1.txt'),  # GMM weights from iteration 1
        ]
        
        # Run the command with increased timeout (20 minutes for full pipeline with reorientation)
        # Convert command to Python module call
        module_cmd = [sys.executable, '-m', 'FEDI.scripts.fedi_dmri_moco'] + cmd[1:]
        self.log(f"Running: {' '.join(module_cmd)}")
        try:
            result = subprocess.run(
                module_cmd,
                capture_output=True,
                text=True,
                timeout=1200  # 20 minutes timeout (reorientation adds processing time)
            )
            
            success = True
            
            if result.returncode != 0:
                self.log(f"✗ Command failed (exit code: {result.returncode})")
                if result.stderr:
                    # Filter out mrtransform warnings which are just progress indicators
                    stderr_filtered = result.stderr
                    # Show last 1000 chars if there's actual error content
                    if len(stderr_filtered) > 500:
                        # Look for actual errors (not just warnings)
                        error_lines = [line for line in stderr_filtered.split('\n') 
                                      if any(keyword in line.lower() for keyword in ['error', 'traceback', 'exception', 'failed'])]
                        if error_lines:
                            self.log(f"  STDERR (errors): {chr(10).join(error_lines[-10:])}")
                        else:
                            self.log(f"  STDERR (last 500 chars): {stderr_filtered[-500:]}")
                    else:
                        self.log(f"  STDERR: {stderr_filtered}")
                success = False
            else:
                self.log(f"✓ Command succeeded (exit code: {result.returncode})")
            
            # Check output files
            for output_file in expected_outputs:
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    self.log(f"  ✓ Output file exists: {output_file} ({file_size} bytes)")
                else:
                    self.log(f"  ✗ Output file missing: {output_file}")
                    success = False
            
            # Also check that working_updated files exist if registration ran
            if success:
                working_updated_0 = os.path.join(output_dir, 'working_updated0.nii.gz')
                if os.path.exists(working_updated_0):
                    self.log(f"  ✓ Registration output exists: working_updated0.nii.gz")
                else:
                    self.log(f"  ⚠ Registration output not found (this may be normal if registration didn't run)")
            
            if not success and result.stdout:
                self.log(f"  STDOUT: {result.stdout[:500]}")
            
            return success
                
        except subprocess.TimeoutExpired:
            self.log("✗ Command timed out (>20 minutes)")
            return False
        except Exception as e:
            self.log(f"✗ Command error: {e}")
            return False
    
    def test_fedi_dmri_fod(self):
        """Test fedi_dmri_fod script."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_fod")
        self.log("="*60)
        
        # Check for required dependencies
        try:
            import torch
            from huggingface_hub import hf_hub_download
        except ImportError as e:
            self.log(f"⚠ Skipping test: Required dependency not found: {e}")
            self.log("  This test requires PyTorch and huggingface_hub to be installed")
            return None
        
        # Use ~/.fedi_test_data/ for test outputs
        test_data_dir = os.path.expanduser('~/.fedi_test_data')
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Output file
        output_fod = os.path.join(test_data_dir, 'fod.nii.gz')
        
        # Remove existing output if it exists
        if os.path.exists(output_fod):
            os.remove(output_fod)
            self.log("  Removed existing output file")
        
        # The script expects b-values [400, 1000, 2600] which matches our test data!
        cmd = [
            'fedi_dmri_fod',
            '-d', self.test_files['dmri'],
            '-a', self.test_files['bval'],
            '-e', self.test_files['bvec'],
            '-o', output_fod,
            '-m', self.test_files['mask']  # Use mask for faster processing
        ]
        
        # Note: This test may take a while as it downloads a model from Hugging Face Hub
        # and processes all voxels with a neural network
        expected_outputs = [output_fod]
        
        return self.run_command(cmd, expected_exit_code=0, check_outputs=expected_outputs)
    
    def run_all_tests(self):
        """Run all available tests."""
        self.log("\n" + "="*60)
        self.log("FEDI Testing Commands - Automated Test Suite")
        self.log("="*60)
        
        # Run tests
        tests = [
            ('fedi_dmri_snr', self.test_fedi_dmri_snr),
            ('fedi_dmri_outliers', self.test_fedi_dmri_outliers),
            ('fedi_dmri_recon', self.test_fedi_dmri_recon),
            ('fedi_dmri_rotate_bvecs', self.test_fedi_dmri_rotate_bvecs),
            ('fedi_dmri_qweights', self.test_fedi_dmri_qweights),
            ('fedi_dmri_reg', self.test_fedi_dmri_reg),
            ('fedi_apply_transform', self.test_fedi_apply_transform),
            ('fedi_dmri_fod', self.test_fedi_dmri_fod),
            ('fedi_dmri_moco', self.test_fedi_dmri_moco),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result is None:
                    # Test was skipped
                    results[test_name] = None
                else:
                    results[test_name] = result
            except Exception as e:
                self.log(f"✗ Test {test_name} raised exception: {e}")
                import traceback
                self.log(traceback.format_exc())
                results[test_name] = False
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results):
        """Print test summary."""
        self.log("\n" + "="*60)
        self.log("TEST SUMMARY")
        self.log("="*60)
        
        passed = sum(1 for v in results.values() if v is True)
        skipped = sum(1 for v in results.values() if v is None)
        failed = sum(1 for v in results.values() if v is False)
        total = len(results)
        
        for test_name, result in results.items():
            if result is True:
                status = "✓ PASSED"
            elif result is None:
                status = "⚠ SKIPPED"
            else:
                status = "✗ FAILED"
            self.log(f"{test_name:30s} {status}")
        
        self.log("-" * 60)
        if skipped > 0:
            self.log(f"Total: {passed}/{total} tests passed ({skipped} skipped)")
        else:
            self.log(f"Total: {passed}/{total} tests passed")
        
        if passed == (total - skipped):
            self.log("="*60)
            self.log("✓ ALL AVAILABLE TESTS PASSED!")
            if skipped > 0:
                self.log(f"  ({skipped} test(s) skipped due to missing dependencies)")
            self.log("="*60)
        else:
            self.log("="*60)
            self.log(f"✗ {failed} TEST(S) FAILED - Please review errors above")
            if skipped > 0:
                self.log(f"  ({skipped} test(s) skipped due to missing dependencies)")
            self.log("="*60)


def main():
    """Main function to generate test data and run tests."""
    print("="*60)
    print("FEDI Testing Commands")
    print("="*60)
    
    # Part 1: Generate test data
    print("\n[PART 1] Generating test data...")
    print("-" * 60)
    
    test_files = generate_test_data()
    
    # Part 2: Run automated tests
    print("\n[PART 2] Running automated tests...")
    print("-" * 60)
    
    suite = FEDITestingCommands(test_files, verbose=True)
    results = suite.run_all_tests()
    
    # Exit with error code if any test failed
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
