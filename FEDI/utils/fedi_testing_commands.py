#!/usr/bin/env python3
"""
FEDI Testing Commands

This module:
1. Generates synthetic NIfTI MRI test data with fixed parameters
2. Automatically tests all FEDI command-line tools and verifies outputs

Test data is saved to ~/.fedi_test_data/ (user's home directory, not in repository)

Usage:
    python -m FEDI.utils.fedi_testing_commands
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

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
        # Convert FEDI commands to Python module calls if not in PATH
        if cmd[0].startswith('fedi_') and not shutil.which(cmd[0]):
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
            from dipy.reconst.brainsuite_shore import BrainSuiteShoreModel
        except ImportError:
            self.log("⚠ Skipping test: dipy.reconst.brainsuite_shore not available")
            self.log("  This test requires a custom DIPY installation with BrainSuite SHORE support")
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
        """Test fedi_dmri_rotate_bvecs script."""
        self.log("\n" + "="*60)
        self.log("Testing: fedi_dmri_rotate_bvecs")
        self.log("="*60)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create transformation matrices directory
            mat_dir = os.path.join(tmpdir, 'transforms')
            os.makedirs(mat_dir, exist_ok=True)
            
            # Load bvecs to get number of volumes
            bvecs = np.loadtxt(self.test_files['bvec'])
            if bvecs.shape[0] == 3:
                # bvecs is in 3xN format (FSL format)
                n_volumes = bvecs.shape[1]
            else:
                # bvecs is in Nx3 format
                n_volumes = bvecs.shape[0]
            
            self.log(f"  Creating {n_volumes} transformation matrices...")
            
            # Create transformation matrix files for each volume
            # Using scipy.io.savemat format (MATLAB .mat files)
            # Format: prefix + volume_index + suffix
            # Default: Transform_v{volume_index}_0GenericAffine.mat
            prefix = "Transform_v"
            suffix = "_0GenericAffine.mat"
            
            for v in range(n_volumes):
                # Create identity transform matrix (4x4 for ANTs format)
                # The script expects 'AffineTransform_double_3_3' key
                # Save as column vector (16, 1) so when loaded it's (16, 1)
                # Script will flatten and take [:9] to get 3x3 rotation matrix
                transform_matrix = np.eye(4, dtype=np.float64)
                # Save as column vector - when loaded with loadmat, it will be (16, 1)
                # Script handles this by flattening first
                transform = {
                    'AffineTransform_double_3_3': transform_matrix.flatten().reshape(-1, 1)
                }
                mat_file = os.path.join(mat_dir, f'{prefix}{v}{suffix}')
                savemat(mat_file, transform)
                # Only log first few and last few to avoid clutter
                if v < 5 or v >= n_volumes - 5:
                    self.log(f"    Created: {os.path.basename(mat_file)}")
                elif v == 5:
                    self.log(f"    ... (creating {n_volumes - 10} more matrices) ...")
            
            output_bvec = os.path.join(tmpdir, 'bvec_rotated.bvec')
            
            cmd = [
                'fedi_dmri_rotate_bvecs',
                '-e', self.test_files['bvec'],
                '-n', output_bvec,
                '-m', mat_dir,
                '-s', prefix,  # Specify prefix
                '-d', suffix   # Specify suffix
            ]
            
            return self.run_command(cmd, expected_exit_code=0, check_outputs=[output_bvec])
    
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
