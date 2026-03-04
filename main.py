import os
import zipfile
import subprocess
import geopandas as gpd
from pathlib import Path
import glob


def find_catastro_zip_file(input_dir):
    """Find the catastro ZIP file automatically in the input directory."""
    # Look for ZIP files matching the pattern XX_UA_XXXXXXXX_SHP.zip
    pattern = os.path.join(input_dir, "*_UA_*_SHP.zip")
    zip_files = glob.glob(pattern)
    
    if not zip_files:
        raise FileNotFoundError(f"No catastro ZIP file found in {input_dir}. Looking for pattern *_UA_*_SHP.zip")
    
    if len(zip_files) > 1:
        print(f"Multiple ZIP files found: {zip_files}")
        print(f"Using the first one: {zip_files[0]}")
    
    zip_file = zip_files[0]
    
    # Extract the base name for the extracted directory
    zip_basename = os.path.basename(zip_file)
    extracted_dir_name = zip_basename.replace('.zip', '')
    
    print(f"Found ZIP file: {zip_file}")
    print(f"Expected extracted directory: {extracted_dir_name}")
    
    return zip_file, extracted_dir_name


def extract_multipart_zip_with_7z(zip_path, extract_to):
    """Extract a multi-part ZIP archive using 7-Zip."""
    print(f"Extracting {zip_path} using 7-Zip to {extract_to}...")
    
    # Create extraction directory if it doesn't exist
    os.makedirs(extract_to, exist_ok=True)
    
    # Use 7z to extract the multi-part archive
    cmd = ["7z", "x", zip_path, f"-o{extract_to}", "-y"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Extraction completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"7z extraction failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def extract_nested_zips(base_dir, data_type="PARCELA"):
    """Extract nested ZIP files for a specific data type from all municipalities."""
    print(f"Looking for {data_type} files in all municipalities...")
    
    municipalities = []
    shapefiles = []
    
    for municipality_dir in Path(base_dir).iterdir():
        if municipality_dir.is_dir():
            municipality_name = municipality_dir.name
            
            # Look for the specific data type ZIP file
            zip_files = list(municipality_dir.glob(f"*_{data_type}.ZIP"))
            
            if zip_files:
                zip_file = zip_files[0]
                print(f"  Processing {municipality_name}...")
                
                # Create a temporary directory for this municipality
                temp_dir = municipality_dir / "temp_extracted"
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    # Extract the ZIP file
                    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Find the .shp file (try both lowercase and uppercase)
                    shp_files = list(temp_dir.glob("*.shp")) + list(temp_dir.glob("*.SHP"))
                    if shp_files:
                        municipalities.append(municipality_name)
                        shapefiles.append(str(shp_files[0]))
                    else:
                        print(f"    No shapefile found in {municipality_name}")
                    
                except Exception as e:
                    print(f"    Error processing {municipality_name}: {e}")
    
    print(f"Found {len(shapefiles)} {data_type} shapefiles from {len(municipalities)} municipalities")
    return shapefiles, municipalities


def convert_individual_shapefiles_to_geojson(shapefile_paths, municipalities, output_dir, data_type):
    """Convert each shapefile to an individual GeoJSON file."""
    print(f"Converting {len(shapefile_paths)} shapefiles to individual GeoJSON files...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    successful_conversions = 0
    
    for i, shp_path in enumerate(shapefile_paths):
        try:
            municipality_name = municipalities[i]
            municipality_code = municipality_name.split()[0] if ' ' in municipality_name else municipality_name
            
            # Clean municipality name for filename (remove special characters)
            clean_name = "".join(c for c in municipality_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_name = clean_name.replace(' ', '_')
            
            output_filename = f"{municipality_code}_{clean_name}_{data_type.lower()}.geojson"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"  Converting {municipality_name}...")
            
            # Read the shapefile
            gdf = gpd.read_file(shp_path)
            
            # Check current CRS and transform to WGS84 if needed
            if gdf.crs is None:
                print(f"    Warning: No CRS found for {municipality_name}, assuming EPSG:25831 (ETRS89 / UTM zone 31N)")
                gdf.set_crs('EPSG:25831', inplace=True)
            
            # Transform to WGS84 (EPSG:4326) if not already in that CRS
            if gdf.crs.to_string() != 'EPSG:4326':
                print(f"    Transforming from {gdf.crs} to WGS84 (EPSG:4326)...")
                gdf = gdf.to_crs('EPSG:4326')
            
            # Add municipality information
            gdf['municipality'] = municipality_name
            gdf['municipality_code'] = municipality_code
            
            # Convert to GeoJSON with WGS84 and ensure proper coordinate order (longitude, latitude)
            # The to_file method with driver='GeoJSON' automatically follows RFC 7946 standard
            # which specifies WGS84 and longitude-latitude order with right-hand rule
            gdf.to_file(output_path, driver='GeoJSON')
            
            successful_conversions += 1
            
            # Print some stats for this municipality
            file_size_mb = os.path.getsize(output_path) / 1024 / 1024
            print(f"    ✅ {len(gdf)} features, {file_size_mb:.1f} MB, CRS: {gdf.crs}")
            
        except Exception as e:
            print(f"    ❌ Error converting {municipality_name}: {e}")
    
    return successful_conversions


def main():
    # Define paths
    input_dir = "input"
    extract_dir = "extracted"
    output_dir = "output"
    
    # Available data types
    data_types = ["PARCELA", "CONSTRU", "MASA", "SUBPARCE", "MAPA", "LIMITES", "CARVIA", "EJES"]
    
    print("Available data types:")
    for i, dt in enumerate(data_types):
        print(f"  {i+1}. {dt}")
    
    # Default to PARCELA (parcels) - most commonly requested
    selected_type = "PARCELA"
    
    print(f"\nUsing data type: {selected_type}")
    print(f"Output directory: {output_dir}/")
    
    try:
        # Find the ZIP file dynamically
        zip_file, extracted_dir_name = find_catastro_zip_file(input_dir)
        shapefile_dir = os.path.join(extract_dir, extracted_dir_name)
        
        # Check if already extracted
        if not os.path.exists(shapefile_dir):
            # Extract using 7-Zip
            if not os.path.exists(zip_file):
                raise FileNotFoundError(f"ZIP file not found: {zip_file}")
            
            success = extract_multipart_zip_with_7z(zip_file, extract_dir)
            if not success:
                raise Exception("Failed to extract the archive")
        else:
            print("Archive already extracted, proceeding with conversion...")
        
        # Extract nested ZIPs and get shapefiles
        shapefiles, municipalities = extract_nested_zips(shapefile_dir, selected_type)
        
        if not shapefiles:
            print(f"No {selected_type} files found!")
            print("Available data types in first municipality:")
            first_muni = next(Path(shapefile_dir).iterdir())
            for zip_file in first_muni.glob("*.ZIP"):
                data_type = zip_file.stem.split('_')[-1]
                print(f"  - {data_type}")
            return
        
        # Convert each shapefile to individual GeoJSON files
        successful_conversions = convert_individual_shapefiles_to_geojson(
            shapefiles, municipalities, output_dir, selected_type
        )
        
        print(f"\n✅ Successfully converted {successful_conversions}/{len(municipalities)} municipalities!")

        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()


