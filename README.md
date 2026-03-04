# CatastroJSON

A Python tool for processing Spanish cadastral data from multi-part ZIP archives into individual GeoJSON files for each municipality.

## Overview

This tool extracts and converts Spanish cadastral shapefiles (from the Spanish National Cadastre) into GeoJSON format. It processes multi-part ZIP archives containing municipal cadastral data and outputs individual GeoJSON files for each municipality.

## Features

- Extracts multi-part ZIP archives using 7-Zip
- Processes multiple data types: PARCELA, CONSTRU, MASA, SUBPARCE, MAPA, LIMITES, CARVIA, EJES
- Converts shapefiles to GeoJSON format with WGS84 coordinate system (EPSG:4326)
- Creates individual GeoJSON files per municipality
- Handles coordinate system transformations automatically
- Adds municipality metadata to each feature

## Prerequisites

### System Dependencies
- **7-Zip**: Required for extracting multi-part ZIP archives
  ```bash
  # Ubuntu/Debian
  sudo apt-get install p7zip-full
  
  # Fedora/CentOS
  sudo dnf install p7zip
  
  # macOS (with Homebrew)
  brew install p7zip
  ```

### Python Dependencies
- Python 3.7+
- geopandas
- pathlib (included in Python 3.4+)

Install Python dependencies:
```bash
pip install geopandas
```

## Usage

0. **Download the data**
   - Download the date from https://www.sedecatastro.gob.es/Accesos/SECAccDescargaDatos.aspx (Descarga de cartografía vectorial por provincia (formato Shapefile)) and unzip the files.

1. **Prepare Input Data**
   - Place your multi-part Spanish cadastral ZIP files in the `input/` directory
   - The main ZIP file should be named like `XX_UA_YYYYMMDD_SHP.zip`
   - Include all parts (`.z01`, `.z02`, etc.) in the same directory

2. **Run the Script**
   ```bash
   python main.py
   ```

3. **Output**
   - Individual GeoJSON files will be created in the `output/` directory
   - Each file represents one municipality's cadastral data
   - Files are named: `{municipality_code}_{municipality_name}_{data_type}.geojson`

## Data Types

The tool supports processing different types of cadastral data:

- **PARCELA**: Land parcels (default)
- **CONSTRU**: Buildings/constructions
- **MASA**: Building masses
- **SUBPARCE**: Sub-parcels
- **MAPA**: Maps
- **LIMITES**: Administrative boundaries
- **CARVIA**: Roads/pathways
- **EJES**: Axes/centerlines

Currently, the script is configured to process PARCELA (land parcels) data by default.

## Output Format

Each GeoJSON file contains:
- Geographic features in WGS84 coordinate system (EPSG:4326)
- Original cadastral attributes
- Added municipality metadata:
  - `municipality`: Full municipality name
  - `municipality_code`: Municipality code

## Example Output

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "REFCAT": "08001A00100001",
        "municipality": "08001uA 8027 ABRERA",
        "municipality_code": "08001uA",
        ...
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[2.104..., 41.515...], ...]]
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **7-Zip not found**
   - Install p7zip-full package
   - Ensure `7z` command is available in PATH

2. **Missing dependencies**
   ```bash
   pip install geopandas pandas shapely fiona pyproj
   ```

3. **Coordinate system warnings**
   - The tool assumes EPSG:25831 (ETRS89 / UTM zone 31N) if no CRS is specified
   - All output is automatically converted to WGS84 (EPSG:4326)

4. **Memory issues with large datasets**
   - The tool processes municipalities individually to minimize memory usage
   - Consider processing subsets of data if memory constraints occur

### File Permissions
Ensure the script has write permissions for the `extracted/` and `output/` directories.

## Data Source

This tool is designed to work with Spanish cadastral data available from:
- Spanish National Cadastre (Catastro Nacional)
- Typically provided in multi-part ZIP format for provinces or regions

## License

This project processes public Spanish cadastral data. Please ensure compliance with the Spanish National Cadastre's terms of use for the source data.