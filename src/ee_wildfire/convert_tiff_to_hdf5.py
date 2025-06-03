"""
Author: Kyle Krstulich
convert_tiff_to_hdf5.py

"""
import argparse
import os
import sys
from pathlib import Path
import h5py
from tqdm import tqdm
import numpy as np
import json # For safely storing complex metadata attributes

# --- Import the new dataset class ---
# Adjust the path modification if your project structure is different
try:
    # Assumes the script is run from a location where this relative path works
    # e.g., script is in project_root/scripts/ and dataset class is in project_root/src/dataloader/
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from src.dataloader.HighResFireEventDataset import HighResFireEventDataset
except ImportError as e:
    print(f"Error importing HighResFireEventDataset using relative path: {e}")
    print("Attempting import assuming it's in PYTHONPATH or current/local directory...")
    try:
        # Fallback import
        from HighResFireEventDataset import HighResFireEventDataset
    except ImportError:
         sys.exit("ERROR: Could not import HighResFireEventDataset. Check PYTHONPATH or file location relative to script.")


# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Create HDF5 files from high-resolution fire event data.")
parser.add_argument("--data_dir", type=str,
                    help="Path to the root directory containing the event subdirectories", required=True)
parser.add_argument("--target_dir", type=str,
                    help="Path to directory where the HDF5 files should be stored", required=True)
parser.add_argument("--event_names", nargs='+', required=True,
                    help="List of specific event names (subdirectory names) to process.")
parser.add_argument("--compress", action='store_true',
                    help="Enable gzip compression for the HDF5 data dataset.")

args = parser.parse_args()

# --- Environment Setup ---
# Prevents potential file locking issues, especially on network file systems
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"

# --- Dataset Initialization for Generator ---
print("Initializing dataset loader for HDF5 generation...")
try:
    # Instantiate the dataset class. For the HDF5 generator, we primarily need
    # data_dir and event_names. Other parameters are not used by get_generator_for_hdf5
    # but might be required by __init__ depending on its implementation.
    # We set dummy values where applicable.
    dataset = HighResFireEventDataset(
        data_dir=args.data_dir,
        event_names=args.event_names,
        n_leading_observations=1, # Dummy value, not used by generator method
        is_train=False,           # Dummy value, not used by generator method
        target_type='temperature' # Dummy value, not used by generator method
        # mean_temp, std_temp, crop_side_length etc. are not needed here
    )
    # Get the specific generator method
    data_gen = dataset.get_generator_for_hdf5()
except Exception as e:
    print(f"ERROR: Failed to initialize HighResFireEventDataset or get generator: {e}")
    sys.exit(1)

# --- HDF5 File Creation ---
target_path = Path(args.target_dir)
target_path.mkdir(parents=True, exist_ok=True) # Create target directory if it doesn't exist
print(f"Target directory for HDF5 files: {target_path.resolve()}")

print("\nStarting HDF5 file creation process...")
# Loop through the data yielded by the generator for each event
# Expects: event_name (str), timestamps (List[str]), geo_metadata (Dict), imgs (np.ndarray)
for event_name, timestamps, geo_metadata, imgs in tqdm(data_gen, desc="Creating HDF5 files"):

    h5_filename = f"{event_name}.hdf5"
    h5_path = target_path / h5_filename
    print(f"\nProcessing event: {event_name} -> {h5_path}")

    if h5_path.is_file():
        print(f"  File {h5_path} already exists, skipping...")
        continue

    try:
        print(f"  Creating HDF5 file: {h5_path}")
        with h5py.File(h5_path, "w") as f:
            # Create the main dataset storing the image time series
            print(f"    Creating dataset 'data' with shape {imgs.shape} and dtype {imgs.dtype}")
            compression_opts = "gzip" if args.compress else None
            dset = f.create_dataset("data",
                                    data=imgs,
                                    dtype=imgs.dtype, # Should be float32 from the generator
                                    compression=compression_opts)

            # --- Store metadata as attributes ---
            print("    Storing metadata as attributes...")
            dset.attrs["event_name"] = event_name

            # Store timestamps (convert list of strings to numpy array of variable-length UTF-8 strings)
            if timestamps:
                # Use h5py's special string dtype for variable-length UTF-8 strings
                string_dt = h5py.string_dtype(encoding='utf-8')
                dset.attrs.create("timestamps", data=np.array(timestamps, dtype=string_dt))
                print(f"      Stored {len(timestamps)} timestamps.")
            else:
                print("      Warning: No timestamps provided for this event.")

            # Store geo_metadata dictionary items individually
            if isinstance(geo_metadata, dict):
                print("      Storing geo_metadata...")
                for key, value in geo_metadata.items():
                    try:
                        # Basic type checking/conversion for HDF5 attribute compatibility
                        if value is None:
                             attr_value = "None" # Store None as a string indicator
                        elif isinstance(value, (str, int, float, np.number, bytes)):
                             attr_value = value # Directly storable types
                        elif isinstance(value, (list, tuple)):
                             # Attempt to store lists/tuples if items are simple
                             if all(isinstance(item, (str, int, float, np.number, bytes)) for item in value):
                                 attr_value = np.array(value) # Store as numpy array if possible
                             else:
                                 # Fallback: Store complex lists/tuples as JSON strings
                                 attr_value = json.dumps(value)
                                 print(f"        Warning: Storing geo_metadata['{key}'] as JSON string due to complex list items.")
                        elif isinstance(value, np.ndarray):
                             attr_value = value # Store numpy arrays directly
                        else:
                             # Fallback for other types: Store as string representation
                             attr_value = str(value)
                             print(f"        Warning: Storing geo_metadata['{key}'] as string representation: {attr_value}")

                        dset.attrs[key] = attr_value
                        # print(f"        Stored attribute: {key} = {repr(attr_value)}") # Use repr for clarity

                    except TypeError as te:
                        # If direct storage fails, try storing as a JSON string as a last resort
                        try:
                            attr_value_json = json.dumps(value)
                            dset.attrs[key] = attr_value_json
                            print(f"      Warning: Storing geo_metadata['{key}'] as JSON string due to HDF5 TypeError: {te}")
                        except Exception as json_e:
                            print(f"      ERROR: Could not store attribute '{key}' with value '{value}' (type: {type(value)}). H5py Error: {te}. JSON fallback failed: {json_e}")
                    except Exception as other_e:
                         print(f"      ERROR: Could not store attribute '{key}' with value '{value}' (type: {type(value)}). Error: {other_e}")
            else:
                 print("    Warning: geo_metadata is not a dictionary or is None, skipping detailed geo attributes.")

            print(f"  Successfully created {h5_path}")

    except Exception as e:
        print(f"  ERROR: Failed to create or write to HDF5 file for event {event_name}: {e}")
        # Clean up partially created file if an error occurred during writing
        if h5_path.is_file():
            try:
                os.remove(h5_path)
                print(f"  Removed partially created file: {h5_path}")
            except OSError as oe:
                print(f"  Warning: Could not remove partial file {h5_path}: {oe}")

print("\nFinished creating HDF5 files.")
