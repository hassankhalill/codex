#!/usr/bin/env python3
"""
Gombe Business Zone Scraper
Divides Gombe commune into 500m hexagonal zones and scrapes business data
Supports: Restaurants, Pharmacies, Grocery Stores, Supermarkets, Delivery Companies, Moto Taxis
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
OUTPUT_EXCEL = "gombe_businesses.xlsx"
OUTPUT_ZONES = "gombe_zones.geojson"

# Business type configurations
BUSINESS_TYPES = {
    'restaurants': {
        'google_type': 'restaurant',
        'osm_query': 'amenity=restaurant',
        'name': 'Restaurants'
    },
    'pharmacies': {
        'google_type': 'pharmacy',
        'osm_query': 'amenity=pharmacy',
        'name': 'Pharmacies'
    },
    'grocery_stores': {
        'google_type': 'grocery_or_supermarket',
        'osm_query': 'shop=convenience',
        'name': 'Grocery Stores'
    },
    'supermarkets': {
        'google_type': 'supermarket',
        'osm_query': 'shop=supermarket',
        'name': 'Supermarkets'
    },
    'delivery_companies': {
        'google_type': None,  # No specific Google type, will use keyword search
        'google_keyword': 'delivery service',
        'osm_query': 'shop=courier or office=courier',
        'name': 'Delivery Companies'
    },
    'moto_taxis': {
        'google_type': None,  # No specific Google type
        'google_keyword': 'moto taxi OR motorcycle taxi',
        'osm_query': 'amenity=motorcycle_taxi or amenity=taxi',
        'name': 'Moto Taxis'
    }
}


class GombeBusinessScraper:
    def __init__(self):
        self.zones = []
        self.businesses = {key: [] for key in BUSINESS_TYPES.keys()}
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

            # Fallback: use exact Gombe commune boundary coordinates
            print("Using exact Gombe commune boundary...")
            self.gombe_boundary = Polygon([
                (15.27984918931836, -4.301048471090325),
                (15.27627583152506, -4.302865274255328),
                (15.27201970350358, -4.308769949363948),
                (15.26547687243528, -4.315710288633783),
                (15.26199377309104, -4.322047518006186),
                (15.25850626035386, -4.327518392192644),
                (15.26401704242657, -4.333232640256546),
                (15.27454344264567, -4.327421032233625),
                (15.28654882166330, -4.320915141232931),
                (15.30020674038804, -4.316404321048534),
                (15.32580430159864, -4.313019075934860),
                (15.32458181483468, -4.303211787948333),
                (15.31979617646593, -4.297482603324646),
                (15.31013733370281, -4.296698817119354),
                (15.29637980785769, -4.301915322959200),
                (15.28924507894354, -4.304864625615211),
                (15.27984918931836, -4.301048471090325),
            ])
            print("✓ Using exact Gombe commune boundary (17 points)")
            return True

        except Exception as e:
            print(f"Error fetching boundary: {e}")
            print("Using exact Gombe commune boundary...")
            self.gombe_boundary = Polygon([
                (15.27984918931836, -4.301048471090325),
                (15.27627583152506, -4.302865274255328),
                (15.27201970350358, -4.308769949363948),
                (15.26547687243528, -4.315710288633783),
                (15.26199377309104, -4.322047518006186),
                (15.25850626035386, -4.327518392192644),
                (15.26401704242657, -4.333232640256546),
                (15.27454344264567, -4.327421032233625),
                (15.28654882166330, -4.320915141232931),
                (15.30020674038804, -4.316404321048534),
                (15.32580430159864, -4.313019075934860),
                (15.32458181483468, -4.303211787948333),
                (15.31979617646593, -4.297482603324646),
                (15.31013733370281, -4.296698817119354),
                (15.29637980785769, -4.301915322959200),
                (15.28924507894354, -4.304864625615211),
                (15.27984918931836, -4.301048471090325),
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

        # Convert H3 hexagons to zone data
        print(f"Found {len(h3_hexagons)} unique hexagonal zones")

        for idx, h3_hex in enumerate(sorted(h3_hexagons), 1):
            # Get hexagon boundary (h3 v4 API)
            boundary = h3.cell_to_boundary(h3_hex)

            # Get center point (h3 v4 API)
            center = h3.cell_to_latlng(h3_hex)

            zone = {
                'zone_id': f'GOMBE-{idx:03d}',
                'h3_cell': h3_hex,
                'center_lat': center[0],
                'center_lon': center[1],
                'boundary': boundary
            }
            self.zones.append(zone)

        print(f"✓ Generated {len(self.zones)} hexagonal zones")
        return True

    def save_zones_to_geojson(self):
        """Save zones to GeoJSON file for visualization"""
        print(f"\nSaving zones to {OUTPUT_ZONES}...")

        features = []
        for zone in self.zones:
            # Convert boundary to GeoJSON polygon format
            coords = [[lon, lat] for lat, lon in zone['boundary']]
            coords.append(coords[0])  # Close the polygon

            feature = {
                'type': 'Feature',
                'properties': {
                    'zone_id': zone['zone_id'],
                    'h3_cell': zone['h3_cell'],
                    'center_lat': zone['center_lat'],
                    'center_lon': zone['center_lon']
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coords]
                }
            }
            features.append(feature)

        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }

        with open(OUTPUT_ZONES, 'w') as f:
            json.dump(geojson, f, indent=2)

        print(f"✓ Zones saved to {OUTPUT_ZONES}")
        return True

    def get_place_details(self, place_id):
        """Fetch detailed information for a place including phone number and website"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"

        params = {
            'place_id': place_id,
            'fields': 'formatted_phone_number,international_phone_number,website',
            'key': GOOGLE_API_KEY
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data['status'] == 'OK':
                result = data.get('result', {})
                return {
                    'phone': result.get('formatted_phone_number') or result.get('international_phone_number'),
                    'website': result.get('website')
                }
            else:
                return {'phone': None, 'website': None}

        except Exception as e:
            print(f"    Error fetching place details: {e}")
            return {'phone': None, 'website': None}

    def scrape_google_places(self, zone, business_type_key):
        """Scrape businesses from Google Places API for a zone"""
        businesses = []
        config = BUSINESS_TYPES[business_type_key]

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

        # Build params based on whether we have a type or keyword
        params = {
            'location': f"{zone['center_lat']},{zone['center_lon']}",
            'radius': 500,  # 500 meters
            'key': GOOGLE_API_KEY
        }

        if config.get('google_type'):
            params['type'] = config['google_type']
        elif config.get('google_keyword'):
            params['keyword'] = config['google_keyword']
        else:
            return []  # No search criteria

        try:
            # First request
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data['status'] == 'OK':
                # Process first page of results
                for place in data['results']:
                    # Get additional details including phone number
                    place_id = place.get('place_id', '')
                    details = self.get_place_details(place_id) if place_id else {'phone': None, 'website': None}

                    # Small delay to respect API rate limits
                    time.sleep(0.05)

                    business = {
                        'zone_id': zone['zone_id'],
                        'name': place.get('name', ''),
                        'address': place.get('vicinity', ''),
                        'lat': place['geometry']['location']['lat'],
                        'lon': place['geometry']['location']['lng'],
                        'phone': details['phone'],
                        'email': None,  # Email not available from Google Places API
                        'rating': place.get('rating', None),
                        'user_ratings_total': place.get('user_ratings_total', None),
                        'place_id': place_id,
                        'types': ', '.join(place.get('types', [])),
                        'source': 'Google Places'
                    }
                    businesses.append(business)

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
                            # Get additional details including phone number
                            place_id = place.get('place_id', '')
                            details = self.get_place_details(place_id) if place_id else {'phone': None, 'website': None}

                            # Small delay to respect API rate limits
                            time.sleep(0.05)

                            business = {
                                'zone_id': zone['zone_id'],
                                'name': place.get('name', ''),
                                'address': place.get('vicinity', ''),
                                'lat': place['geometry']['location']['lat'],
                                'lon': place['geometry']['location']['lng'],
                                'phone': details['phone'],
                                'email': None,  # Email not available from Google Places API
                                'rating': place.get('rating', None),
                                'user_ratings_total': place.get('user_ratings_total', None),
                                'place_id': place_id,
                                'types': ', '.join(place.get('types', [])),
                                'source': 'Google Places'
                            }
                            businesses.append(business)
                    else:
                        break

            elif data['status'] == 'ZERO_RESULTS':
                pass  # No businesses in this zone
            else:
                print(f"  Warning: Google API returned status {data['status']} for zone {zone['zone_id']}")

            # Respect API rate limits
            time.sleep(0.1)

        except requests.Timeout:
            print(f"  Timeout scraping Google Places for zone {zone['zone_id']}")
        except Exception as e:
            print(f"  Error scraping Google Places for zone {zone['zone_id']}: {e}")

        return businesses

    def scrape_openstreetmap(self, zone, business_type_key):
        """Scrape businesses from OpenStreetMap for a zone"""
        businesses = []
        config = BUSINESS_TYPES[business_type_key]

        # Build Overpass query
        overpass_url = "https://overpass-api.de/api/interpreter"

        # Calculate bounding box (expand by ~600m to ensure coverage)
        lat_offset = 0.006
        lon_offset = 0.006

        south = zone['center_lat'] - lat_offset
        north = zone['center_lat'] + lat_offset
        west = zone['center_lon'] - lon_offset
        east = zone['center_lon'] + lon_offset

        osm_query_condition = config.get('osm_query', '')
        if not osm_query_condition:
            return []  # No OSM query defined

        overpass_query = f"""
        [out:json][timeout:25];
        (
          node[{osm_query_condition}]({south},{west},{north},{east});
          way[{osm_query_condition}]({south},{west},{north},{east});
        );
        out center tags;
        """

        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            try:
                response = requests.post(overpass_url, data={'data': overpass_query}, timeout=30)

                # Check if response is empty
                if not response.text or len(response.text) < 10:
                    if retry_count < max_retries:
                        retry_count += 1
                        print(f"  Empty response from OSM, retrying ({retry_count}/{max_retries})...")
                        time.sleep(5)
                        continue
                    else:
                        print(f"  Empty response from OSM for zone {zone['zone_id']}")
                        break

                data = response.json()

                for element in data.get('elements', []):
                    tags = element.get('tags', {})
                    name = tags.get('name', '')

                    if not name:
                        continue

                    # Get coordinates
                    if element['type'] == 'node':
                        lat = element['lat']
                        lon = element['lon']
                    elif 'center' in element:
                        lat = element['center']['lat']
                        lon = element['center']['lon']
                    else:
                        continue

                    # Extract phone and email
                    phone = tags.get('phone') or tags.get('contact:phone') or tags.get('phone:mobile')
                    email = tags.get('email') or tags.get('contact:email')

                    business = {
                        'zone_id': zone['zone_id'],
                        'name': name,
                        'address': tags.get('addr:street', ''),
                        'lat': lat,
                        'lon': lon,
                        'phone': phone,
                        'email': email,
                        'rating': None,
                        'user_ratings_total': None,
                        'place_id': None,
                        'types': osm_query_condition,
                        'source': 'OpenStreetMap'
                    }
                    businesses.append(business)

                # Wait between requests to respect OSM rate limits
                time.sleep(3)
                break

            except requests.Timeout:
                if retry_count < max_retries:
                    retry_count += 1
                    print(f"  Timeout from OSM, retrying ({retry_count}/{max_retries})...")
                    time.sleep(5)
                else:
                    print(f"  Timeout scraping OSM for zone {zone['zone_id']}")
                    break
            except ValueError as e:
                # JSON parsing error
                if retry_count < max_retries:
                    retry_count += 1
                    print(f"  Invalid response from OSM, retrying ({retry_count}/{max_retries})...")
                    time.sleep(5)
                else:
                    print(f"  Invalid JSON from OSM for zone {zone['zone_id']}")
                    break
            except Exception as e:
                print(f"  Error scraping OSM for zone {zone['zone_id']}: {e}")
                break

        return businesses

    def scrape_all_zones(self):
        """Scrape businesses from all zones using multiple sources"""
        print(f"\nScraping businesses from {len(self.zones)} zones...")
        print("This may take several minutes...\n")

        for business_type_key in BUSINESS_TYPES.keys():
            print(f"\n{'='*60}")
            print(f"SCRAPING: {BUSINESS_TYPES[business_type_key]['name']}")
            print(f"{'='*60}\n")

            all_businesses = []

            for i, zone in enumerate(self.zones, 1):
                print(f"Processing zone {i}/{len(self.zones)}: {zone['zone_id']}")

                # Scrape from Google Places
                google_businesses = self.scrape_google_places(zone, business_type_key)
                print(f"  Google Places: {len(google_businesses)} businesses")
                all_businesses.extend(google_businesses)

                # Scrape from OpenStreetMap
                osm_businesses = self.scrape_openstreetmap(zone, business_type_key)
                print(f"  OpenStreetMap: {len(osm_businesses)} businesses")
                all_businesses.extend(osm_businesses)

            self.businesses[business_type_key] = all_businesses
            print(f"\n✓ Total {BUSINESS_TYPES[business_type_key]['name']} scraped (before deduplication): {len(all_businesses)}")

        return True

    def deduplicate_businesses(self):
        """Remove duplicate businesses based on name and location proximity"""
        print("\n" + "="*60)
        print("DEDUPLICATING BUSINESSES")
        print("="*60 + "\n")

        for business_type_key in BUSINESS_TYPES.keys():
            print(f"Deduplicating {BUSINESS_TYPES[business_type_key]['name']}...")

            if not self.businesses[business_type_key]:
                print(f"  No {BUSINESS_TYPES[business_type_key]['name']} to deduplicate")
                continue

            df = pd.DataFrame(self.businesses[business_type_key])
            initial_count = len(df)

            # Sort by source priority (Google Places first as it typically has more complete data)
            df['source_priority'] = df['source'].map({'Google Places': 1, 'OpenStreetMap': 2})
            df = df.sort_values('source_priority')

            unique_businesses = []
            seen_locations = []

            for _, business in df.iterrows():
                is_duplicate = False
                current_loc = (business['lat'], business['lon'])

                # Check if this business is too close to an already seen one with similar name
                for seen_idx, seen_loc in enumerate(seen_locations):
                    distance = geodesic(current_loc, seen_loc).meters

                    # If within 50 meters and similar name, consider duplicate
                    if distance < 50:
                        seen_business = unique_businesses[seen_idx]

                        # Compare names (simple similarity check)
                        current_name = str(business['name']).lower()
                        seen_name = str(seen_business['name']).lower()

                        # Check if names are similar (one contains the other or exact match)
                        if (current_name in seen_name or seen_name in current_name or
                            current_name == seen_name):
                            is_duplicate = True
                            break

                if not is_duplicate:
                    # Convert to dict and remove source_priority column
                    business_dict = business.to_dict()
                    business_dict.pop('source_priority', None)
                    unique_businesses.append(business_dict)
                    seen_locations.append(current_loc)

            self.businesses[business_type_key] = unique_businesses
            final_count = len(unique_businesses)
            duplicates_removed = initial_count - final_count

            print(f"  ✓ Initial: {initial_count} | Duplicates removed: {duplicates_removed} | Final: {final_count} unique")

        return True

    def export_to_excel(self):
        """Export results to Excel file with separate sheets for each business type"""
        print(f"\n{'='*60}")
        print(f"EXPORTING TO EXCEL: {OUTPUT_EXCEL}")
        print(f"{'='*60}\n")

        # Create Excel writer
        with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:

            # Create a sheet for each business type
            for business_type_key in BUSINESS_TYPES.keys():
                businesses = self.businesses[business_type_key]

                if not businesses:
                    print(f"  No {BUSINESS_TYPES[business_type_key]['name']} to export")
                    continue

                df = pd.DataFrame(businesses)

                # Ensure source_priority column is removed if it exists
                if 'source_priority' in df.columns:
                    df = df.drop('source_priority', axis=1)

                # Reorder columns for better readability
                columns = ['zone_id', 'name', 'address', 'phone', 'email', 'lat', 'lon', 'rating',
                           'user_ratings_total', 'types', 'source', 'place_id']
                # Only select columns that exist in the dataframe
                columns = [col for col in columns if col in df.columns]
                df = df[columns]

                # Write to sheet
                sheet_name = BUSINESS_TYPES[business_type_key]['name']
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Format the worksheet
                worksheet = writer.sheets[sheet_name]
                worksheet.column_dimensions['A'].width = 15  # zone_id
                worksheet.column_dimensions['B'].width = 35  # name
                worksheet.column_dimensions['C'].width = 40  # address
                worksheet.column_dimensions['D'].width = 18  # phone
                worksheet.column_dimensions['E'].width = 30  # email
                worksheet.column_dimensions['F'].width = 12  # lat
                worksheet.column_dimensions['G'].width = 12  # lon
                worksheet.column_dimensions['H'].width = 10  # rating
                worksheet.column_dimensions['I'].width = 18  # user_ratings_total
                worksheet.column_dimensions['J'].width = 30  # types
                worksheet.column_dimensions['K'].width = 18  # source
                worksheet.column_dimensions['L'].width = 25  # place_id

                print(f"  ✓ {sheet_name}: {len(df)} businesses exported")

            # Create a summary sheet
            summary_data = []
            for business_type_key in BUSINESS_TYPES.keys():
                count = len(self.businesses[business_type_key])
                summary_data.append({
                    'Business Type': BUSINESS_TYPES[business_type_key]['name'],
                    'Total Count': count,
                    'Google Places': len([b for b in self.businesses[business_type_key] if b['source'] == 'Google Places']),
                    'OpenStreetMap': len([b for b in self.businesses[business_type_key] if b['source'] == 'OpenStreetMap']),
                    'With Phone': len([b for b in self.businesses[business_type_key] if b.get('phone')]),
                    'With Email': len([b for b in self.businesses[business_type_key] if b.get('email')])
                })

            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Format summary sheet
            worksheet = writer.sheets['Summary']
            worksheet.column_dimensions['A'].width = 25
            worksheet.column_dimensions['B'].width = 15
            worksheet.column_dimensions['C'].width = 18
            worksheet.column_dimensions['D'].width = 18
            worksheet.column_dimensions['E'].width = 15
            worksheet.column_dimensions['F'].width = 15

        print(f"\n✓ All data exported to {OUTPUT_EXCEL}")
        return True

    def run(self):
        """Main execution flow"""
        print("="*60)
        print("GOMBE BUSINESS ZONE SCRAPER")
        print("="*60)

        # Step 1: Get boundary
        if not self.get_gombe_boundary():
            print("Failed to get Gombe boundary")
            return False

        # Step 2: Generate zones
        if not self.generate_h3_zones():
            print("Failed to generate zones")
            return False

        # Step 3: Save zones
        if not self.save_zones_to_geojson():
            print("Failed to save zones")
            return False

        # Step 4: Scrape businesses
        if not self.scrape_all_zones():
            print("Failed to scrape businesses")
            return False

        # Step 5: Deduplicate
        if not self.deduplicate_businesses():
            print("Failed to deduplicate businesses")
            return False

        # Step 6: Export to Excel
        if not self.export_to_excel():
            print("Failed to export to Excel")
            return False

        print("\n" + "="*60)
        print("SCRAPING COMPLETE!")
        print("="*60)
        print(f"✓ Zones saved to: {OUTPUT_ZONES}")
        print(f"✓ Businesses saved to: {OUTPUT_EXCEL}")
        print("\nTo visualize zones, run: python visualize_zones.py")

        return True


if __name__ == "__main__":
    scraper = GombeBusinessScraper()
    scraper.run()
