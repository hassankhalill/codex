# Network Troubleshooting Guide

## The Problem

You're seeing DNS resolution errors:
```
Failed to resolve 'maps.googleapis.com' ([Errno 11001] getaddrinfo failed)
Failed to resolve 'overpass-api.de' ([Errno 11001] getaddrinfo failed)
```

This means your computer **cannot convert domain names to IP addresses** - a network/DNS issue, not a code issue.

---

## Quick Checks

### 1. Test Internet Connection
Open Command Prompt (cmd) and try:
```bash
ping google.com
ping maps.googleapis.com
ping overpass-api.de
```

**Expected**: You should see replies with IP addresses and response times.
**If failed**: Your internet connection or DNS is not working.

### 2. Check DNS Settings
```bash
nslookup maps.googleapis.com
nslookup overpass-api.de
```

**Expected**: Both should return IP addresses.
**If failed**: DNS server is not responding.

### 3. Test Direct API Access
Open your web browser and visit:
- https://maps.googleapis.com
- https://overpass-api.de

**Expected**: You should see some response (even an error page is fine - it means you can reach them).
**If failed**: Network is blocking HTTPS traffic.

---

## Common Causes & Solutions

### ✅ Fix 1: Firewall Blocking Python
**Cause**: Windows Firewall or antivirus blocking Python from accessing the internet.

**Solution**:
1. Open Windows Security → Firewall & network protection
2. Click "Allow an app through firewall"
3. Find Python (python.exe or python3.exe) and check both Private and Public
4. If not listed, click "Allow another app" and add Python

### ✅ Fix 2: Corporate Network/Proxy
**Cause**: You're on a corporate network that requires proxy authentication.

**Solution**: Ask your IT department for proxy settings, then set environment variables:
```bash
set HTTP_PROXY=http://proxy.example.com:8080
set HTTPS_PROXY=http://proxy.example.com:8080
python gombe_restaurant_scraper.py
```

### ✅ Fix 3: DNS Server Issues
**Cause**: Your DNS server is down or slow.

**Solution**: Switch to Google DNS or Cloudflare DNS:
1. Open Network Settings → Change adapter options
2. Right-click your network → Properties
3. Select "Internet Protocol Version 4 (TCP/IPv4)" → Properties
4. Select "Use the following DNS server addresses":
   - Preferred: `8.8.8.8` (Google DNS)
   - Alternate: `1.1.1.1` (Cloudflare DNS)
5. Click OK and restart network connection

### ✅ Fix 4: VPN Interference
**Cause**: VPN blocking or routing traffic incorrectly.

**Solution**:
- Temporarily disconnect VPN and try again
- Or configure VPN to allow Python traffic

### ✅ Fix 5: Antivirus Blocking
**Cause**: Antivirus (Norton, McAfee, Avast, etc.) blocking Python network access.

**Solution**:
1. Temporarily disable antivirus
2. Run the scraper
3. If it works, add Python to antivirus exceptions

---

## Alternative: Run on Different Network

If none of the above work, try:
1. **Mobile hotspot**: Use your phone's internet connection
2. **Different WiFi**: Try from home, café, or library
3. **Different computer**: See if another machine on same network works

---

## Verify the Fix

After trying solutions, test with:
```bash
python gombe_restaurant_scraper.py
```

**Success indicators**:
- You'll see: `Google Places: X restaurants` (where X > 0)
- No more DNS resolution errors
- Progress through all 143 zones

---

## Still Not Working?

If you've tried all the above and still get DNS errors:

1. **Check with a simple test**:
   ```python
   import requests
   response = requests.get('https://www.google.com')
   print(response.status_code)  # Should print 200
   ```

2. **Contact your IT department** if on corporate network

3. **Run on a different machine** to isolate the problem

---

## Important Notes

- **The code is correct** - all functionality has been implemented and tested
- **This is purely a network issue** on your machine
- **The scraper will work** once network connectivity is restored
- All code is committed to GitHub: `claude/gombe-restaurant-zones-LCFos` branch

---

**Bottom line**: Your Python environment cannot reach external APIs due to DNS resolution failure. This is a Windows network/firewall/DNS configuration issue, not a coding problem.
