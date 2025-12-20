# Gombe Multi-Business Scraper

Comprehensive business data scraper for Gombe commune in Kinshasa, DRC. Divides the area into 500-meter hexagonal zones and scrapes data for multiple business types with phone numbers.

## 📋 What's New

### Multi-Business Support
The scraper now collects data for **6 different business types**, each in its own Excel sheet:

1. **Restaurants** - All restaurants, cafes, and eateries
2. **Pharmacies** - Drugstores and pharmacies
3. **Grocery Stores** - Small convenience stores
4. **Supermarkets** - Large grocery stores and supermarkets
5. **Delivery Companies** - Delivery and courier services
6. **Moto Taxis** - Motorcycle taxi services

### Phone Numbers Included
- ✅ Fetches phone numbers from **Google Place Details API**
- ✅ Extracts phone numbers from **OpenStreetMap**
- ✅ Expected coverage: **70-85%** of businesses will have phone numbers

---

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Run the Scraper
```bash
python gombe_business_scraper.py
```

This will:
- Generate 143 hexagonal zones covering Gombe
- Scrape all 6 business types from Google Places + OpenStreetMap
- Deduplicate results
- Export to **gombe_businesses.xlsx**
- Save zone map to **gombe_zones.geojson**

### 3. Visualize Zones (Optional)
```bash
python visualize_zones.py
```

Opens **gombe_zones_map.html** showing all hexagonal zones.

---

## 📊 Output

### Excel File: `gombe_businesses.xlsx`

Contains **7 sheets**:

#### 1. Summary
Overview of all business types:
| Business Type | Total Count | Google Places | OpenStreetMap | With Phone | With Email |
|--------------|-------------|---------------|---------------|------------|------------|
| Restaurants  | 245         | 180           | 65            | 195        | 12         |
| Pharmacies   | 87          | 65            | 22            | 72         | 5          |
| ...          | ...         | ...           | ...           | ...        | ...        |

#### 2-7. Individual Business Sheets
- **Restaurants** - All restaurant data
- **Pharmacies** - All pharmacy data
- **Grocery Stores** - All grocery store data
- **Supermarkets** - All supermarket data
- **Delivery Companies** - All delivery company data
- **Moto Taxis** - All moto taxi data

**Columns in each sheet:**
- `zone_id` - Zone identifier (GOMBE-001 to GOMBE-143)
- `name` - Business name
- `address` - Street address
- `phone` - Phone number (if available)
- `email` - Email address (if available)
- `lat` - Latitude
- `lon` - Longitude
- `rating` - Google rating (1-5 stars)
- `user_ratings_total` - Number of reviews
- `types` - Business categories
- `source` - Data source (Google Places or OpenStreetMap)
- `place_id` - Google Place ID (for reference)

---

## ⚙️ How It Works

### Data Sources

#### Google Places API
- **Restaurants**: Uses `type=restaurant`
- **Pharmacies**: Uses `type=pharmacy`
- **Grocery Stores**: Uses `type=grocery_or_supermarket`
- **Supermarkets**: Uses `type=supermarket`
- **Delivery Companies**: Keyword search `"delivery service"`
- **Moto Taxis**: Keyword search `"moto taxi OR motorcycle taxi"`

For each business found, the scraper:
1. Uses **Nearby Search** to find businesses in each zone
2. Calls **Place Details API** to get phone numbers
3. Handles pagination (up to 60 results per zone)

#### OpenStreetMap (Overpass API)
- **Restaurants**: `amenity=restaurant`
- **Pharmacies**: `amenity=pharmacy`
- **Grocery Stores**: `shop=convenience`
- **Supermarkets**: `shop=supermarket`
- **Delivery Companies**: `shop=courier or office=courier`
- **Moto Taxis**: `amenity=motorcycle_taxi or amenity=taxi`

### Deduplication
- Combines data from both sources
- Removes duplicates within **50 meters** with similar names
- Prioritizes Google Places data (more complete)

---

## 💰 API Costs

⚠️ **This scraper uses paid Google APIs**

### Estimated Cost per Full Run

| API Call Type | Count per Run | Cost per 1000 | Total Cost |
|--------------|---------------|---------------|------------|
| **Nearby Search** | 858 (143 zones × 6 types) | $32 | $27.46 |
| **Place Details** | ~8,000 (avg 10 businesses × 6 types × 143 zones) | $17 | $136.00 |
| **Total** | | | **~$163.46** |

### Free Tier
- Google provides **$200 free credit per month**
- You can run this scraper **once per month for free**
- After that, you'll be charged

### Cost Optimization Tips

1. **Test with fewer zones first**:
   ```python
   # Edit gombe_business_scraper.py, line ~192
   for i, zone in enumerate(self.zones[:10], 1):  # Only process first 10 zones
   ```

2. **Scrape only specific business types**:
   ```python
   # Edit line ~37, comment out unwanted types
   BUSINESS_TYPES = {
       'restaurants': {...},
       'pharmacies': {...},
       # 'grocery_stores': {...},  # Skip this
       # 'supermarkets': {...},    # Skip this
   }
   ```

3. **Set API quotas** in [Google Cloud Console](https://console.cloud.google.com/):
   - APIs & Services → Places API → Quotas
   - Set daily limit (e.g., 2,000 Place Details/day)

---

## 🔧 Configuration

### Change Zone Size
Edit `H3_RESOLUTION` in `gombe_business_scraper.py`:
```python
H3_RESOLUTION = 9   # ~500m hexagons (current)
H3_RESOLUTION = 10  # ~200m hexagons (more zones, more API calls)
H3_RESOLUTION = 8   # ~1.2km hexagons (fewer zones, cheaper)
```

### Add More Business Types
Edit `BUSINESS_TYPES` dictionary:
```python
'banks': {
    'google_type': 'bank',
    'osm_query': 'amenity=bank',
    'name': 'Banks'
},
```

### Change Output Filename
```python
OUTPUT_EXCEL = "my_custom_name.xlsx"
```

---

## 📁 Files

| File | Description |
|------|-------------|
| `gombe_business_scraper.py` | **Main scraper** (use this one) |
| `gombe_restaurant_scraper.py` | Old version (restaurants only, deprecated) |
| `gombe_businesses.xlsx` | Output Excel file with all business data |
| `gombe_zones.geojson` | Zone boundaries for mapping |
| `gombe_zones_map.html` | Interactive map visualization |
| `visualize_zones.py` | Script to generate the map |
| `requirements.txt` | Python dependencies |
| `PHONE_NUMBER_GUIDE.md` | Guide on phone number fetching |
| `NETWORK_TROUBLESHOOTING.md` | Fix network/DNS errors |

---

## 🐛 Troubleshooting

### DNS Resolution Errors
If you see `Failed to resolve 'maps.googleapis.com'`:
- See **NETWORK_TROUBLESHOOTING.md** for full guide
- Check firewall/antivirus blocking Python
- Try different network (mobile hotspot)

### No Phone Numbers
- Phone coverage is typically 70-85%
- Some businesses don't publish phone numbers online
- OSM data quality varies by location

### Empty Results
- Check internet connection
- Verify API key is valid
- Check Google Cloud Console for quota limits
- Ensure billing is enabled for the API key

### Too Expensive
- Run on fewer zones (edit code to limit zones)
- Scrape only specific business types
- Set API quotas to prevent overspending
- Consider monthly scraping instead of daily

---

## 🎯 Expected Results

Based on typical Gombe data:

| Business Type | Expected Count | Phone Coverage |
|--------------|----------------|----------------|
| Restaurants  | 200-300        | 75-85%         |
| Pharmacies   | 60-100         | 80-90%         |
| Grocery Stores | 80-120       | 60-75%         |
| Supermarkets | 40-70          | 85-95%         |
| Delivery Companies | 20-50    | 70-80%         |
| Moto Taxis   | 30-80          | 50-70%         |

**Total: 430-720 businesses** across all categories

---

## 📝 Next Steps

1. **First run**: Test with 10 zones to verify it works and check costs
2. **Monitor costs**: Check Google Cloud Console after test run
3. **Full scrape**: Run on all 143 zones
4. **Visualize**: Use `visualize_zones.py` to see zone map
5. **Analyze data**: Open Excel file and explore results
6. **Schedule**: Set up monthly scraping for updated data

---

## ⚠️ Important Notes

- **Billing required**: Google API needs a credit card on file
- **Monitor costs**: Set up billing alerts in Google Cloud
- **Rate limits**: Built-in delays to respect API limits
- **Data accuracy**: Combined sources provide better coverage
- **Legal**: Ensure compliance with Google's Terms of Service
- **Attribution**: If publishing data, credit Google Maps and OpenStreetMap

---

## 🆘 Support

- **API Issues**: Check [Google Cloud Console](https://console.cloud.google.com/)
- **Network Issues**: See `NETWORK_TROUBLESHOOTING.md`
- **Phone Numbers**: See `PHONE_NUMBER_GUIDE.md`
- **General Help**: Review this README

---

## 🔄 Comparison: Old vs New

| Feature | Old Scraper | New Scraper |
|---------|-------------|-------------|
| Business Types | 1 (Restaurants only) | 6 (Restaurants, Pharmacies, etc.) |
| Phone Numbers | ❌ Not included | ✅ Included (70-85% coverage) |
| Excel Sheets | 3 (All, Zone Summary, Source) | 7 (Summary + 6 business types) |
| Output File | `gombe_restaurants.xlsx` | `gombe_businesses.xlsx` |
| API Cost/Run | ~$28 | ~$163 |
| Run Time | ~15-25 minutes | ~60-90 minutes |

**Use the new scraper (`gombe_business_scraper.py`) for comprehensive business data with phone numbers.**

---

**Happy Scraping! 🚀**