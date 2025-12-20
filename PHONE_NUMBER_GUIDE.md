# Getting Phone Numbers for Restaurants

## What Changed

I've updated the scraper to **automatically fetch phone numbers** from Google Places API using the **Place Details** endpoint.

### Before (Original):
- Only used **Nearby Search** API
- Did NOT return phone numbers
- Phone field was always `None` for Google Places results

### After (Current):
- Uses **Nearby Search** to find restaurants
- Then calls **Place Details** for EACH restaurant to get phone number
- Phone numbers now populated when available

---

## How It Works

```python
def get_place_details(self, place_id):
    """Fetch phone number and website for a specific place"""
    # Calls: https://maps.googleapis.com/maps/api/place/details/json
    # Returns: formatted_phone_number, website
```

For each restaurant found:
1. **Nearby Search** finds the restaurant (returns name, address, rating, etc.)
2. **Place Details** fetches additional info using `place_id` (returns phone number, website)
3. Combines both into final restaurant record

---

## API Cost Implications

⚠️ **IMPORTANT**: This significantly increases API usage and costs!

### Google Places API Pricing (as of 2024):
- **Nearby Search**: $32 per 1000 requests
- **Place Details** (Basic Data - phone): $17 per 1000 requests

### Example Cost Calculation:

**Scenario**: Scraping Gombe with 143 zones, averaging 10 restaurants per zone

**Without Place Details** (Original):
- 143 Nearby Search requests
- **Cost**: 143 × $0.032 = **$4.58**

**With Place Details** (Current):
- 143 Nearby Search requests
- ~1,430 Place Details requests (10 restaurants × 143 zones)
- **Cost**: (143 × $0.032) + (1,430 × $0.017) = **$4.58 + $24.31 = $28.89**

**6x more expensive!**

### Free Tier:
- Google gives **$200 free credit per month**
- This is enough for ~7,000 Place Details calls
- You can scrape Gombe ~5 times per month on free tier

---

## Alternative Approaches

### Option 1: Use Current Implementation (Recommended)
✅ **Best phone number coverage**
✅ Most accurate data
❌ Higher API costs
❌ Slower (more API calls)

### Option 2: Only Use OpenStreetMap Phone Numbers
Modify code to skip Place Details and rely only on OSM data:
```python
# Don't call get_place_details()
# Only use phone numbers from OpenStreetMap results
```
✅ **Free** (no API costs)
✅ Faster
❌ **Much lower coverage** (OSM has fewer phone numbers)
❌ Less reliable data

### Option 3: Hybrid Approach (Conditional Fetching)
Only fetch Place Details if OSM didn't find a phone number:
```python
# After deduplication, check if phone is missing
# Only call Place Details for restaurants without phones
```
✅ Lower API costs than Option 1
✅ Better coverage than Option 2
⚠️ More complex logic

### Option 4: Manual Web Scraping
For restaurants missing phone numbers, scrape their websites:
```python
# Use 'website' field from Place Details
# Scrape contact page for phone number
```
✅ Can find phone numbers not in Google/OSM
❌ **Very slow** and unreliable
❌ Legal/ethical concerns
❌ Websites block scrapers

---

## What Phone Numbers Look Like

### From Google Places:
```python
{
    'name': 'Restaurant Le Cercle',
    'phone': '+243 81 234 5678',  # International format
    'source': 'Google Places'
}
```

### From OpenStreetMap:
```python
{
    'name': 'Chez Ntemba',
    'phone': '0812345678',  # Local format (varies)
    'source': 'OpenStreetMap'
}
```

### Missing:
```python
{
    'name': 'Small Local Eatery',
    'phone': None,  # Not available in either source
}
```

---

## Expected Coverage

Based on typical data availability:

| Source | Phone Coverage |
|--------|---------------|
| **Google Places** | 60-80% |
| **OpenStreetMap** | 20-40% |
| **Combined** | 70-85% |

**You'll still have 15-30% of restaurants without phone numbers** - this is normal as many small businesses don't list contact info online.

---

## How to Check API Usage

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to: **APIs & Services** → **Dashboard**
4. Click on **Places API**
5. View usage metrics and costs

---

## Recommendations

### For Testing:
- Use a **small test area** first (e.g., 10 zones instead of 143)
- Check phone number quality before running full scrape
- Monitor API costs in real-time

### For Production:
- **Current implementation is good** - phone numbers are valuable
- Set up **billing alerts** in Google Cloud ($10, $20, $50 thresholds)
- Consider running scraper **once per month** to update data
- Cache results and only re-scrape periodically

### To Reduce Costs:
- Implement **Option 3** (hybrid approach) - only call Place Details for restaurants without OSM phones
- Filter by rating (only get phones for 4+ star restaurants)
- Only scrape high-density zones (skip zones with 0-2 restaurants)

---

## What If I Run Out of Free Credits?

Google charges your credit card automatically. To prevent surprise bills:

### Set Budget Alerts:
1. Google Cloud Console → **Billing** → **Budgets & alerts**
2. Create budget: $10, $20, $50
3. Get email alerts at 50%, 90%, 100%

### Set Usage Quotas:
1. **APIs & Services** → **Places API** → **Quotas**
2. Limit requests per day (e.g., 2,000 Place Details/day)
3. This prevents runaway costs

### Disable Billing:
- If you hit your limit, Google will stop making API calls
- Scraper will continue but won't fetch new data
- You can re-enable when ready

---

## Summary

✅ **Updated scraper now fetches phone numbers automatically**
✅ Uses Google Place Details API (costs ~$17 per 1,000 phones)
✅ Combined with OpenStreetMap for maximum coverage
✅ Expect 70-85% phone number coverage
⚠️ Monitor API costs - set billing alerts
⚠️ ~6x more expensive than original implementation
💡 Free tier ($200/month) is enough for ~5 full Gombe scrapes

**The current implementation is the best balance of data quality and cost.**
