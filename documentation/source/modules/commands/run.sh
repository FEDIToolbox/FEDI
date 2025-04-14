#!/bin/bash

# List of section titles to replace
sections=("Synopsis" "Usage" "Options" "References")

# Loop through all .rst files in the current directory
for file in *.rst; do
  echo "Processing $file"
  for section in "${sections[@]}"; do
    # Use awk to process the file and replace underlined headers with .. rubric::
    awk -v section="$section" '
      BEGIN { skip = 0 }
      skip {
        skip = 0
        next
      }
      $0 == section {
        getline next_line
        if (match(next_line, "^[-=^~\"#*+`'']+$")) {
          print ".. rubric:: " section
          skip = 1
          next
        } else {
          print $0
          print next_line
          next
        }
      }
      { print }
    ' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
  done
done
