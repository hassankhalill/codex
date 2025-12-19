# Gombe Restaurant Zone Scraper

## Overview
This project divides Gombe commune (Kinshasa) into 75 hexagonal zones with ~500m radius and scrapes restaurant data from multiple sources.

## What Has Been Created

### Files Generated:
1. **gombe_zones.geojson** - 75 hexagonal zones covering Gombe with unique Zone IDs (GOMBE-001 to GOMBE-075)
2. **gombe_restaurant_scraper.py** - Main scraping script
3. **requirements.txt** - Python dependencies

### Zone Details:
- **Method**: H3 Hexagonal Grid (industry standard used by Uber)
- **Resolution**: H3 level 9 (~500m edge-to-edge hexagons)
- **Total Zones**: 75 zones covering Gombe commune
- **Zone IDs**: GOMBE-001 through GOMBE-075

## Running the Scraper

### Prerequisites:
1. Python 3.8 or higher
2. Internet connection (for API calls)
3. Google Places API key (you already have: AIzaSyDu3_NeaMxaCAx4b2jMX5RRTb-khH7VoZU)

### Installation:

```bash
# Install dependencies
pip install -r requirements.txt
```

### Usage:

```bash
# Run the scraper
python3 gombe_restaurant_scraper.py
```

### Expected Output:
- **gombe_restaurants.xlsx** - Excel file with 3 sheets:
  - **All Restaurants**: Complete list with Zone ID, name, address, coordinates, rating, source
  - **Zone Summary**: Restaurant count and average rating per zone
  - **Source Summary**: Restaurant count by data source

### Important Notes:

**Network Issue in Current Environment:**
The scraper encountered network restrictions (proxy 403 errors) in the current environment. To run successfully:
1. Download all files to your local machine
2. Ensure you have internet access
3. Run the script locally

**API Key Security:**
- Your Google API key is embedded in the script
- Consider using environment variables for production:
  ```python
  GOOGLE_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY')
  ```

## Data Sources:
1. **Google Places API** - Primary source (most comprehensive)
2. **OpenStreetMap/Overpass API** - Secondary source (free, community-maintained)

## Deduplication:
- Restaurants within 50 meters with similar names are considered duplicates
- Google Places data is prioritized (more complete information)

## Viewing the Zones:
You can visualize the zones by:
1. Opening `gombe_zones.geojson` in QGIS, or
2. Using https://geojson.io and uploading the file
3. Using the visualization script (create one if needed)
