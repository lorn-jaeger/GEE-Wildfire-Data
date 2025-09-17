# Pipeline Refactor Plan

## Goals
- Replace the current CLI/argparse heavy workflow with a configuration-first pipeline.
- Minimize interactive prompts; a single YAML file defines credentials, storage paths, and dataset schema.
- Make dataset acquisition modular via a registry so new sources can be added without modifying the core pipeline.
- Execute the pipeline in ordered stages: index → Earth Engine → earthaccess → custom.

## Configuration File
All user interaction flows through a YAML file. Proposed top-level keys:

```yaml
credentials:
  earthengine_service_account: /abs/path/to/ee.json
  earthaccess_netrc: /abs/path/to/earthaccess.netrc
paths:
  raw_data: /abs/path/to/raw
  processed_data: /abs/path/to/processed
  scratch: /abs/path/to/tmp
schema:
  index:
    dataset: globfire
    options:
      start_date: 2021-01-01
      end_date: 2021-12-31
      min_size: 10000000
  earthengine:
    - dataset: firepred_daily
      options:
        buffer_days: 4
        utm_zone: 32610
  earthaccess:
    - dataset: modis_burned_area
      options:
        collection: MCD64A1
        bands: ["BurnDate"]
  custom:
    - dataset: local_annotations
      function: local_annotations.load_shapefile
      options:
        path: data/annotations.geojson
```

### Notes
- `dataset` references a registered name within `raster_builder.datasets`.
- `function` is optional and only required for `custom` entries that are not pre-registered.
- Each options block is passed verbatim to the dataset fetch function.
- Pipeline stages are optional; if a section is omitted it is skipped.

## Module Layout

```
raster_builder/
├── config.py            # Data classes + YAML loader
├── pipeline.py          # Stage orchestrator
├── context.py           # Execution context/shared state (index results, paths)
├── datasets/
│   ├── __init__.py      # Registry management helpers
│   ├── registry.py      # Registry + decorators
│   ├── earthengine.py   # Built-in EE dataset fetchers (e.g., firepred_daily)
│   ├── earthaccess.py   # Built-in earthaccess fetchers (placeholder now)
│   ├── custom.py        # Utility helpers for custom/local datasets
│   └── index.py         # Globfire index dataset implementation
└── io/
    ├── auth.py          # Credential loading/authentication helpers
    └── storage.py       # Directory preparation + file helpers
```

## Pipeline Execution Flow
1. Load YAML config into `Config` dataclass; validate file paths and create root directories.
2. Initialize execution context (credentials, output directories, logs).
3. `index` stage: run the registered index dataset to produce the driving table; store outputs in raw directory.
4. `earthengine` stage: iterate through dataset entries, running each fetcher with the context and index information.
5. `earthaccess` stage: same pattern using Earthdata credentials via earthaccess API.
6. `custom` stage: call either registered helper functions or user-provided import paths.
7. Each stage returns metadata for potential caching—future work can extend with caching.

## Next Steps
- Implement config loader and registry scaffolding (Step 3 of overall plan).
- Port existing GlobFire logic into the new `datasets.index` module.
- Provide a minimal pipeline runner that logs progress without the old `ConsoleUI` dependency.
```
