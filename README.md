# raster-builder

`raster-builder` is a configuration-first pipeline for assembling wildfire-oriented raster datasets. A
single YAML file defines credentials, working directories, and the datasets to materialise. The
pipeline then executes deterministic stages—index → Earth Engine → earthaccess → custom—so new data
sources can be added without rewriting orchestration code.

## Features
- YAML-only user interface; no interactive prompts
- Dataset registry so data sources are defined once and reused across projects
- Built-in GlobFire index stage that prepares fire start locations and timelines
- Extensible stages for Google Earth Engine, NASA earthaccess, and custom/local datasets

## Installation
Clone the repository and install in editable mode:

```bash
git clone https://github.com/lorn-jaeger/raster-builder.git
cd raster-builder
pip install -e .
```

## Configuration
A configuration file controls the entire pipeline. Key sections:

```yaml
credentials:
  earthengine_service_account: ./credentials/service_account.json
  earthaccess_netrc: ~/.netrc
paths:
  raw_data: ./data/raw
  processed_data: ./data/processed
schema:
  index:
    dataset: globfire
    options:
      start_date: 2021-01-01
      end_date: 2021-03-01
      min_size: 1.0e7
  earthengine:
    - dataset: firepred_daily
      options:
        buffer_days: 4
        utm_zone: 32610
  earthaccess:
    - dataset: example
      options:
        short_name: MYD11A2
  custom: []
```

- `credentials`: absolute or config-relative paths to authentication material.
- `paths`: directories created on demand for pipeline outputs.
- `schema`: ordered dataset declarations. Each entry names a registered dataset and forwards `options`
  to its loader. The `index` dataset seeds downstream stages.

A working example lives at `docs/examples/pipeline.example.yml`.

## Usage
Run the pipeline by pointing to your YAML file:

```bash
python -m raster_builder path/to/pipeline.yml
# or, after installation with entry points
raster-builder path/to/pipeline.yml
```

The command authenticates Google Earth Engine using the configured service account, loads the index
stage, then executes Earth Engine, earthaccess, and custom stages in order. Outputs land in the
configured directories (e.g., `data/raw/index/globfire/index.csv`).

## Pipeline Stages
- **index** – Produces the core table of fire events (currently GlobFire).
- **earthengine** – Pulls imagery or rasters from Google Earth Engine for each indexed event.
- **earthaccess** – Adds NASA Earthdata products (placeholder implementations supplied).
- **custom** – Invokes user-provided callables for arbitrary enrichment.

Each stage is optional; omit the section from the schema to skip it. Custom datasets can reference any
`module:function` path available on the Python path.

## Development
- Python 3.10+
- Earth Engine API access with a linked Google Cloud project
- Optional: NASA Earthdata credentials for `earthaccess`

Design notes for the ongoing refactor are tracked in `docs/pipeline_design.md`.
