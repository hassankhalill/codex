#!/usr/bin/env python3
"""
Gombe Restaurant Zone Scraper
Divides Gombe commune into 500m hexagonal zones and scrapes restaurant data
"""

import h3
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import requests
import json
import time
from typing import List, Dict, Tuple
import os
from geopy.distance import geodesic

# Configuration
GOOGLE_API_KEY = "AIzaSyDu3_NeaMxaCAx4b2jMX5RRTb-khH7VoZU"
H3_RESOLUTION = 9  # ~500m hexagons
OUTPUT_EXCEL = "gombe_restaurants.xlsx"
OUTPUT_ZONES = "gombe_zones.geojson"


class GombeZoneScraper:
    def __init__(self):
        self.zones = []
        self.restaurants = []
        self.gombe_boundary = None

    def get_gombe_boundary(self):
        """Fetch Gombe commune boundary from OpenStreetMap"""
        print("Fetching Gombe commune boundary from OpenStreetMap...")

        # Overpass API query for Gombe commune
        overpass_url = "https://overpass-api.de/api/interpreter"
        overpass_query = """
        [out:json][timeout:25];
        area["name"="Kinshasa"]["admin_level"="4"]->.a;
        (
          relation["name"="Gombe"]["admin_level"="6"](area.a);
        );
        out geom;
        """

        try:
            response = requests.post(overpass_url, data={'data': overpass_query}, timeout=30)
            data = response.json()

            if data['elements']:
                # Extract coordinates from the relation
                element = data['elements'][0]
                if 'members' in element:
                    coords = []
                    for member in element['members']:
                        if member['type'] == 'way' and 'geometry' in member:
                            for node in member['geometry']:
                                coords.append((node['lon'], node['lat']))

                    if coords:
                        polygon = Polygon(coords)
                        self.gombe_boundary = polygon
                        print(f"✓ Gombe boundary loaded: {len(coords)} points")
                        return True

            # Fallback: use more accurate approximate coordinates for Gombe
            print("Using approximate Gombe boundary...")
            self.gombe_boundary = Polygon([
                (15.2950, -4.3200),  # Southwest
                (15.3400, -4.3200),  # Southeast
                (15.3400, -4.2800),  # Northeast
                (15.2950, -4.2800),  # Northwest
                (15.2950, -4.3200)   # Close polygon
            ])
            print("✓ Using approximate boundary")
            return True

        except Exception as e:
            print(f"Error fetching boundary: {e}")
            print("Using approximate Gombe boundary...")
            self.gombe_boundary = Polygon([
                (15.2950, -4.3200),
                (15.3400, -4.3200),
                (15.3400, -4.2800),
                (15.2950, -4.2800),
                (15.2950, -4.3200)
            ])
            return True

    def generate_h3_zones(self):
        """Generate H3 hexagonal zones covering Gombe"""
        print(f"\nGenerating H3 hexagonal zones (resolution {H3_RESOLUTION})...")

        # Get bounding box
        bounds = self.gombe_boundary.bounds  # (minx, miny, maxx, maxy)

        # Create a set to store unique H3 hexagons
        h3_hexagons = set()

        # Sample points within the boundary and get their H3 hexagons
        minx, miny, maxx, maxy = bounds

        # Create a grid of points to sample
        lat_step = 0.001  # ~100m
        lon_step = 0.001

        lat = miny
        while lat <= maxy:
            lon = minx
            while lon <= maxx:
                point = Point(lon, lat)
                if self.gombe_boundary.contains(point):
                    # Get H3 hexagon for this point (h3 v4 API)
                    h3_hex = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)
                    h3_hexagons.add(h3_hex)
                lon += lon_step
            lat += lat_step

        # Convert H3 hexagons to polygons
        zone_id = 1
        for h3_hex in h3_hexagons:
            # h3 v4 API
            boundary = h3.cell_to_boundary(h3_hex)
            # Convert to GeoJSON format (list of [lon, lat] pairs)
            boundary_geojson = [(lon, lat) for lat, lon in boundary]
            polygon = Polygon(boundary_geojson)

            # Get center point (h3 v4 API)
            center = h3.cell_to_latlng(h3_hex)

            self.zones.append({
                'zone_id': f'GOMBE-{zone_id:03d}',
                'h3_id': h3_hex,
                'center_lat': center[0],
                'center_lon': center[1],
                'geometry': polygon
            })
            zone_id += 1

        print(f"✓ Generated {len(self.zones)} hexagonal zones")
        return True

    def save_zones(self):
        """Save zones to GeoJSON file"""
        print(f"\nSaving zones to {OUTPUT_ZONES}...")

        gdf = gpd.GeoDataFrame(self.zones, crs='EPSG:4326')
        gdf.to_file(OUTPUT_ZONES, driver='GeoJSON')

        print(f"✓ Zones saved to {OUTPUT_ZONES}")
        return True

    def scrape_google_places(self, zone):
        """Scrape restaurants from Google Places API for a zone"""
        restaurants = []

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

        params = {
            'location': f"{zone['center_lat']},{zone['center_lon']}",
            'radius': 500,  # 500 meters
            'type': 'restaurant',
            'key': GOOGLE_API_KEY
        }

        try:
            # First request
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data['status'] == 'OK':
                # Process first page of results
                for place in data['results']:
                    restaurant = {
                        'zone_id': zone['zone_id'],
                        'name': place.get('name', ''),
                        'address': place.get('vicinity', ''),
                        'lat': place['geometry']['location']['lat'],
                        'lon': place['geometry']['location']['lng'],
                        'rating': place.get('rating', None),
                        'user_ratings_total': place.get('user_ratings_total', None),
                        'place_id': place.get('place_id', ''),
                        'types': ', '.join(place.get('types', [])),
                        'source': 'Google Places'
                    }
                    restaurants.append(restaurant)

                # Handle pagination if there are more results
                while 'next_page_token' in data:
                    # Wait for token to become valid (Google requirement)
                    time.sleep(2)

                    next_params = {
                        'pagetoken': data['next_page_token'],
                        'key': GOOGLE_API_KEY
                    }

                    response = requests.get(url, params=next_params, timeout=10)
                    data = response.json()

                    if data['status'] == 'OK':
                        for place in data['results']:
                            restaurant = {
                                'zone_id': zone['zone_id'],
                                'name': place.get('name', ''),
                                'address': place.get('vicinity', ''),
                                'lat': place['geometry']['location']['lat'],
                                'lon': place['geometry']['location']['lng'],
                                'rating': place.get('rating', None),
                                'user_ratings_total': place.get('user_ratings_total', None),
                                'place_id': place.get('place_id', ''),
                                'types': ', '.join(place.get('types', [])),
                                'source': 'Google Places'
                            }
                            restaurants.append(restaurant)
                    else:
                        break

            elif data['status'] == 'ZERO_RESULTS':
                pass  # No restaurants in this zone
            else:
                print(f"  Warning: Google API returned status {data['status']} for zone {zone['zone_id']}")

            # Respect API rate limits
            time.sleep(0.1)

        except requests.Timeout:
            print(f"  Timeout scraping Google Places for zone {zone['zone_id']}")
        except Exception as e:
            print(f"  Error scraping Google Places for zone {zone['zone_id']}: {e}")

        return restaurants

    def scrape_openstreetmap(self, zone):
        """Scrape restaurants from OpenStreetMap for a zone"""
        restaurants = []

        # Overpass API query
        overpass_url = "https://overpass-api.de/api/interpreter"

        # Calculate bounding box around center point
        lat, lon = zone['center_lat'], zone['center_lon']

        # ~500m in degrees (rough approximation)
        delta = 0.0045  # ~500m at equator

        bbox = f"{lat-delta},{lon-delta},{lat+delta},{lon+delta}"

        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="restaurant"]({bbox});
          way["amenity"="restaurant"]({bbox});
          node["amenity"="cafe"]({bbox});
          way["amenity"="cafe"]({bbox});
          node["amenity"="fast_food"]({bbox});
          way["amenity"="fast_food"]({bbox});
          node["amenity"="bar"]({bbox});
          way["amenity"="bar"]({bbox});
          node["amenity"="pub"]({bbox});
          way["amenity"="pub"]({bbox});
        );
        out center;
        """

        try:
            response = requests.post(overpass_url, data={'data': overpass_query}, timeout=30)
            data = response.json()

            for element in data.get('elements', []):
                # Get coordinates
                if 'lat' in element and 'lon' in element:
                    elem_lat = element['lat']
                    elem_lon = element['lon']
                elif 'center' in element:
                    elem_lat = element['center']['lat']
                    elem_lon = element['center']['lon']
                else:
                    continue

                tags = element.get('tags', {})

                restaurant = {
                    'zone_id': zone['zone_id'],
                    'name': tags.get('name', 'Unnamed'),
                    'address': tags.get('addr:street', ''),
                    'lat': elem_lat,
                    'lon': elem_lon,
                    'rating': None,
                    'user_ratings_total': None,
                    'place_id': f"osm-{element['type']}-{element['id']}",
                    'types': tags.get('amenity', ''),
                    'source': 'OpenStreetMap'
                }
                restaurants.append(restaurant)

            # Respect API rate limits
            time.sleep(1)

        except requests.Timeout:
            print(f"  Timeout scraping OSM for zone {zone['zone_id']}")
        except Exception as e:
            print(f"  Error scraping OSM for zone {zone['zone_id']}: {e}")

        return restaurants

    def scrape_all_zones(self):
        """Scrape restaurants from all zones using multiple sources"""
        print(f"\nScraping restaurants from {len(self.zones)} zones...")
        print("This may take several minutes...\n")

        all_restaurants = []

        for i, zone in enumerate(self.zones, 1):
            print(f"Processing zone {i}/{len(self.zones)}: {zone['zone_id']}")

            # Scrape from Google Places
            google_restaurants = self.scrape_google_places(zone)
            print(f"  Google Places: {len(google_restaurants)} restaurants")
            all_restaurants.extend(google_restaurants)

            # Scrape from OpenStreetMap
            osm_restaurants = self.scrape_openstreetmap(zone)
            print(f"  OpenStreetMap: {len(osm_restaurants)} restaurants")
            all_restaurants.extend(osm_restaurants)

        self.restaurants = all_restaurants
        print(f"\n✓ Total restaurants scraped (before deduplication): {len(self.restaurants)}")
        return True

    def deduplicate_restaurants(self):
        """Remove duplicate restaurants based on name and location proximity"""
        print("\nDeduplicating restaurants...")

        if not self.restaurants:
            print("No restaurants to deduplicate")
            return True

        df = pd.DataFrame(self.restaurants)
        initial_count = len(df)

        # Sort by source priority (Google Places first as it typically has more complete data)
        df['source_priority'] = df['source'].map({'Google Places': 1, 'OpenStreetMap': 2})
        df = df.sort_values('source_priority')

        unique_restaurants = []
        seen_locations = []

        for _, restaurant in df.iterrows():
            is_duplicate = False
            current_loc = (restaurant['lat'], restaurant['lon'])

            # Check if this restaurant is too close to an already seen one with similar name
            for seen_idx, seen_loc in enumerate(seen_locations):
                distance = geodesic(current_loc, seen_loc).meters

                # If within 50 meters and similar name, consider duplicate
                if distance < 50:
                    seen_restaurant = unique_restaurants[seen_idx]

                    # Compare names (simple similarity check)
                    current_name = str(restaurant['name']).lower()
                    seen_name = str(seen_restaurant['name']).lower()

                    # Check if names are similar (one contains the other or exact match)
                    if (current_name in seen_name or seen_name in current_name or
                        current_name == seen_name):
                        is_duplicate = True
                        break

            if not is_duplicate:
                # Convert to dict and remove source_priority column
                rest_dict = restaurant.to_dict()
                rest_dict.pop('source_priority', None)
                unique_restaurants.append(rest_dict)
                seen_locations.append(current_loc)

        self.restaurants = unique_restaurants
        final_count = len(self.restaurants)
        duplicates_removed = initial_count - final_count

        print(f"✓ Deduplication complete:")
        print(f"  Initial: {initial_count} restaurants")
        print(f"  Duplicates removed: {duplicates_removed}")
        print(f"  Final: {final_count} unique restaurants")

        return True

    def export_to_excel(self):
        """Export results to Excel file"""
        print(f"\nExporting results to {OUTPUT_EXCEL}...")

        if not self.restaurants:
            print("No restaurants to export")
            return False

        df = pd.DataFrame(self.restaurants)

        # Ensure source_priority column is removed if it exists
        if 'source_priority' in df.columns:
            df = df.drop('source_priority', axis=1)

        # Reorder columns for better readability
        columns = ['zone_id', 'name', 'address', 'lat', 'lon', 'rating',
                   'user_ratings_total', 'types', 'source', 'place_id']
        # Only select columns that exist in the dataframe
        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Create Excel writer
        with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
            # Main sheet with all restaurants
            df.to_excel(writer, sheet_name='All Restaurants', index=False)

            # Summary sheet by zone
            zone_summary = df.groupby('zone_id').agg({
                'name': 'count',
                'rating': 'mean'
            }).rename(columns={'name': 'restaurant_count', 'rating': 'avg_rating'})
            zone_summary = zone_summary.sort_values('restaurant_count', ascending=False)
            zone_summary.to_excel(writer, sheet_name='Zone Summary')

            # Summary by source
            source_summary = df.groupby('source').agg({
                'name': 'count'
            }).rename(columns={'name': 'restaurant_count'})
            source_summary.to_excel(writer, sheet_name='Source Summary')

            # Format the worksheets
            workbook = writer.book

            # Format All Restaurants sheet
            worksheet = writer.sheets['All Restaurants']
            worksheet.column_dimensions['A'].width = 15  # zone_id
            worksheet.column_dimensions['B'].width = 35  # name
            worksheet.column_dimensions['C'].width = 40  # address
            worksheet.column_dimensions['D'].width = 12  # lat
            worksheet.column_dimensions['E'].width = 12  # lon
            worksheet.column_dimensions['F'].width = 10  # rating
            worksheet.column_dimensions['G'].width = 18  # user_ratings_total
            worksheet.column_dimensions['H'].width = 30  # types
            worksheet.column_dimensions['I'].width = 18  # source
            worksheet.column_dimensions['J'].width = 25  # place_id

            # Format Zone Summary sheet
            worksheet = writer.sheets['Zone Summary']
            worksheet.column_dimensions['A'].width = 15
            worksheet.column_dimensions['B'].width = 20
            worksheet.column_dimensions['C'].width = 15

            # Format Source Summary sheet
            worksheet = writer.sheets['Source Summary']
            worksheet.column_dimensions['A'].width = 20
            worksheet.column_dimensions['B'].width = 20

        print(f"✓ Excel file created: {OUTPUT_EXCEL}")
        print(f"  Sheets: All Restaurants, Zone Summary, Source Summary")
        print(f"  Total restaurants exported: {len(df)}")

        return True

    def run(self):
        """Run the complete scraping pipeline"""
        print("=" * 60)
        print("GOMBE RESTAURANT ZONE SCRAPER")
        print("=" * 60)

        # Step 1: Get boundary
        if not self.get_gombe_boundary():
            print("Failed to get Gombe boundary")
            return False

        # Step 2: Generate zones
        if not self.generate_h3_zones():
            print("Failed to generate zones")
            return False

        # Step 3: Save zones
        if not self.save_zones():
            print("Failed to save zones")
            return False

        # Step 4: Scrape restaurants
        if not self.scrape_all_zones():
            print("Failed to scrape restaurants")
            return False

        # Step 5: Deduplicate
        if not self.deduplicate_restaurants():
            print("Failed to deduplicate")
            return False

        # Step 6: Export to Excel
        if not self.export_to_excel():
            print("Failed to export to Excel")
            return False

        print("\n" + "=" * 60)
        print("✓ COMPLETE!")
        print("=" * 60)
        print(f"\nOutput files:")
        print(f"  - {OUTPUT_ZONES} (Zone boundaries in GeoJSON format)")
        print(f"  - {OUTPUT_EXCEL} (Restaurant data)")
        print(f"\nTotal zones: {len(self.zones)}")
        print(f"Total unique restaurants: {len(self.restaurants)}")

        return True


if __name__ == "__main__":
    scraper = GombeZoneScraper()
    scraper.run()
