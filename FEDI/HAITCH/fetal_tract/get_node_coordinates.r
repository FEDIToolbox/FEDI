library(dplyr)
library(oro.nifti)
library(Gmedian)
library(reshape2)
library(tidyr)

# Function to calculate the geometric median and translate coordinates
get_geometric_median <- function(coords, seg) {
  geom_med <- matrix(Gmedian(coords[, c("x", "y", "z")]), nrow = 3)
  geom_med <- as_tibble(t(translateCoordinate(geom_med, seg)))
  colnames(geom_med) <- c("x", "y", "z")
  round(geom_med, 2)
}

# Main processing function
process_segmentation <- function(seg_path, labelkey_path) {
  # Import data
  labelkey <- read.csv(labelkey_path)
  seg <- readNIfTI(seg_path)
  
  # Get segmentation coordinates and filter by label IDs
  seg_matrix <- reshape2::melt(seg@.Data, value.name = "id", varnames = c("x", "y", "z")) %>%
    filter(id %in% labelkey$id)
  
  # Calculate coordinates and write the output CSV
  seg_matrix %>%
    group_by(id) %>%
    summarise(coords = list(get_geometric_median(across(1:3), seg))) %>%
    unnest_wider(coords) %>%
    mutate(y = y * -1) %>%
    left_join(labelkey, by = "id") %>%
    select(id, label, x, y, z) %>%
    write.csv(gsub(".nii.gz", "_coordinates.csv", seg_path), row.names = FALSE)
}

# Execute with command-line arguments
args <- commandArgs(trailingOnly = TRUE)
process_segmentation_data(args[1], args[2])