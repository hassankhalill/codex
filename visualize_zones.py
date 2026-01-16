#!/usr/bin/env python3
"""
Visualization script for Gombe zones
Creates an interactive HTML map showing all zones
"""

import folium
from shapely.geometry import shape
import json

def create_zone_map():
    """Create an interactive map of the zones"""
    print("Creating interactive map of Gombe zones...")

    # Load zones from GeoJSON
    with open('gombe_zones.geojson', 'r') as f:
        geojson_data = json.load(f)

    zones = geojson_data['features']

    # Calculate center of all zones
    all_lats = [zone['properties']['center_lat'] for zone in zones]
    all_lons = [zone['properties']['center_lon'] for zone in zones]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )

    # Add zones to map
    for zone in zones:
        props = zone['properties']
        geom = zone['geometry']

        # Create popup with zone info
        popup_html = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{props['zone_id']}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>H3 ID:</b></td><td>{props['h3_id'][:10]}...</td></tr>
                <tr><td><b>Center:</b></td><td>{props['center_lat']:.4f}, {props['center_lon']:.4f}</td></tr>
            </table>
        </div>
        """

        # Add polygon to map
        folium.GeoJson(
            geom,
            style_function=lambda x: {
                'fillColor': '#3186cc',
                'color': '#0047AB',
                'weight': 2,
                'fillOpacity': 0.3
            },
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)

        # Add zone ID label at center
        folium.Marker(
            location=[props['center_lat'], props['center_lon']],
            icon=folium.DivIcon(html=f"""
                <div style="
                    font-size: 10px;
                    font-weight: bold;
                    color: #0047AB;
                    text-align: center;
                    white-space: nowrap;
                ">
                    {props['zone_id']}
                </div>
            """)
        ).add_to(m)

    # Add title
    title_html = '''
    <div style="position: fixed;
                top: 10px; left: 50px; width: 300px; height: 90px;
                background-color: white; border:2px solid grey;
                z-index:9999; font-size:14px; padding: 10px">
        <h4 style="margin: 0;">Gombe Restaurant Zones</h4>
        <p style="margin: 5px 0 0 0;">
            <b>Total Zones:</b> {}<br>
            <b>Zone Radius:</b> ~500 meters<br>
            <b>Grid Type:</b> H3 Hexagonal
        </p>
    </div>
    '''.format(len(zones))

    m.get_root().html.add_child(folium.Element(title_html))

    # Save map
    output_file = 'gombe_zones_map.html'
    m.save(output_file)

    print(f"✓ Interactive map created: {output_file}")
    print(f"  Open this file in a web browser to view the zones")
    return output_file

if __name__ == "__main__":
    create_zone_map()
