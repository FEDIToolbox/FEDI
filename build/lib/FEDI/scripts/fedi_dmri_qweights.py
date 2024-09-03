#!/usr/bin/env python

# inspired from https://github.com/mandorra/multishell-qspace-gradients

import argparse
import csv
import numpy as np

from FEDI.utils.common import FEDI_ArgumentParser, Metavar



def intersperse_qspace_with_b0(input_dirs, num_b0_volumes):
    """
    Intersperse b-value=0 volumes among the directions.

    Parameters
    ----------
    input_dirs : list of str
        List of direction vectors as strings.
    num_b0_volumes : int
        Number of b-value=0 volumes to intersperse.

    Returns
    -------
    list of str
        List of directions with interspersed b-value=0 volumes.
    """
    num_directions = len(input_dirs)
    directions_per_block = num_directions // num_b0_volumes

    output_dirs = [None] * (num_directions + num_b0_volumes)
    output_index = 0
    input_index = 0

    for _ in range(num_b0_volumes):
        output_dirs[output_index:output_index + directions_per_block] = input_dirs[input_index:input_index + directions_per_block]
        output_index += directions_per_block
        input_index += directions_per_block
        output_dirs[output_index] = '( 0.000, 0.000, 0.000 )'
        output_index += 1

    # Add remaining directions
    for remaining_index in range(num_directions - input_index):
        output_dirs[output_index] = input_dirs[input_index]
        output_index += 1
        input_index += 1

    return output_dirs

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m \n\n    "
            "Process diffusion MRI scheme and generate Siemens scanner compatible output.\n"
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2024. "
            "Haitch: A framework for distortion and motion correction in fetal multi-shell "
            "diffusion-weighted MRI. arXiv preprint arXiv:2406.20042."
        ),
        formatter_class=FEDI_ArgumentParser
    )

    mandatory = parser.add_argument_group('\033[1mMANDATORY OPTIONS\033[0m')

    mandatory.add_argument(
        "-i", "--unitary_scheme",
        required=True,
        metavar=Metavar.file,
        help="Path to the input scheme file from http://www.emmanuelcaruyer.com/q-space-sampling.php containing unitary directions and b-values. Example: Sample.txt"
    )
    mandatory.add_argument(
        "-o", "--siemens_scheme",
        required=True,
        metavar=Metavar.file,
        help="Path to the output file where directions will be saved in Siemens scanner format (*.dvs)."
    )
    mandatory.add_argument(
        "-b", "--bvalues",
        required=True,
        nargs="+",
        metavar=Metavar.int,
        help="List of b-values corresponding to each shell in the input scheme (e.g., 1000 2000 3000)."
    )
    mandatory.add_argument(
        "-d", "--debug_file",
        required=True,
        metavar=Metavar.file,
        help="Path to the debug file where detailed information about the directions and weights will be logged."
    )

    optional = parser.add_argument_group('\033[1mOPTINAL OPTIONS\033[0m')


    optional.add_argument(
        "--interspersed",
        action="store_true",
        help="Specify whether to intersperse b-value=0 volumes among the directions (default: False)."
    )
    optional.add_argument(
        "-n", "--num_b0_volumes",
        required=False,
        metavar=Metavar.int,
        help="Number of b-value=0 volumes to include, if --interspersed was chosen."
    )
    optional.add_argument(
        "--b0_at_beginning",
        action="store_true",
        help="Include b-value=0 volume at the beginning of the acquisition."
    )
    optional.add_argument(
        "--b0_at_end",
        action="store_true",
        help="Include b-value=0 volume at the end of the acquisition."
    )


    return parser.parse_args()

def main():
    args = parse_arguments()

    bvalues = np.array(args.bvalues, dtype=np.int64)
    num_b0_volumes = int(args.num_b0_volumes) or 0
    interspersed = args.interspersed
    b0_at_beginning = args.b0_at_beginning
    b0_at_end = args.b0_at_end

    scheme = []
    output = []

    try:
        with open(args.unitary_scheme) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t', quotechar='|')
            start = False
            for row in reader:
                if start:
                    try:
                        unit_vector = np.array(row, dtype=np.float64)
                        scheme.append(unit_vector)
                    except ValueError:
                        print(f"Skipping invalid row: {row}")
                        continue

                if row[0] == "#shell":
                    start = True
    except FileNotFoundError:
        print(f"File {args.unitary_scheme} not found.")
        return

    # Check number of shells in input scheme
    input_nshells = int(max(item[0] for item in scheme))
    given_bvalues = len(bvalues)

    if input_nshells != given_bvalues:
        print(f"ERROR: The number of provided b-values ({given_bvalues}) does not match the number of shells in the input scheme ({input_nshells}).")
        return

    max_bvalue = max(bvalues)

    try:
        with open(args.debug_file, 'w') as debug_fd:
            debug_fd.write(f"Maximum B-Value (MRI scanner should acquire all the time with this value): {max_bvalue} s/mm^2\n")
            debug_fd.write(f"B-values: {bvalues} s/mm^2\n\n\n")

            for idx, direction in enumerate(scheme):
                bvalue = bvalues[int(direction[0] - 1)]
                weight = np.sqrt(float(bvalue) / float(max_bvalue))
                unit_vector = direction[1:4]
                weighted_vector = unit_vector * weight
                output.append(f"( {weighted_vector[0]:.6f}, {weighted_vector[1]:.6f}, {weighted_vector[2]:.6f} )")

                # Write debug information
                debug_fd.write(f"Direction #{idx}:\n------------\n")
                debug_fd.write(f"Assigned B-Value: {bvalue}\n")
                debug_fd.write(f"Unitary direction vector: {unit_vector}\n")
                debug_fd.write(f"Unitary direction vector norm: {np.linalg.norm(unit_vector)}\n")
                debug_fd.write(f"Assigned weight: {weight}\n")
                debug_fd.write(f"Weighted direction vector: {weighted_vector}\n")
                debug_fd.write(f"Weighted direction vector norm: {np.linalg.norm(weighted_vector)}\n")
                debug_fd.write(f"True B-value (proportional to G^2): {max_bvalue * np.square(np.linalg.norm(weighted_vector))}\n\n")

    except IOError as e:
        print(f"Error writing to debug file: {e}")
        return

    try:
        with open(args.siemens_scheme, 'w') as siemens_fd:
            total_directions = len(output)
            if interspersed:
                output = intersperse_qspace_with_b0(output, num_b0_volumes)
                total_directions = len(output)
            if b0_at_beginning:
                total_directions += 1
                output = ['( 0.000, 0.000, 0.000 )'] + output
            if b0_at_end:
                total_directions += 1
                output += ['( 0.000, 0.000, 0.000 )']

            siemens_fd.write(f"[directions={total_directions}]\n")
            siemens_fd.write("CoordinateSystem = xyz\n")
            siemens_fd.write("Normalisation = none\n")

            for idx, direction in enumerate(output):
                siemens_fd.write(f"Vector[{idx}] = {direction}\n")

    except IOError as e:
        print(f"Error writing to Siemens scheme file: {e}")

if __name__ == '__main__':
    main()
