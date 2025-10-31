#!/usr/bin/env python3
"""
Quick test script to verify backend endpoints are working
Run with: python test_endpoints.py
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", json_data=None):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=json_data, timeout=5)

        status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
        print(f"{status} - {name}")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                # Show first few keys
                keys = list(data.keys())[:5]
                print(f"  Response keys: {keys}")
                if "data" in data and isinstance(data["data"], list):
                    print(f"  Data length: {len(data['data'])}")
            return True
        else:
            print(f"  Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ ERROR - {name}")
        print(f"  Exception: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("SIGMA ANALYST - Backend API Test")
    print("=" * 60)
    print()

    tests = [
        ("Health Check", f"{BASE_URL}/health"),
        ("Ready Check", f"{BASE_URL}/ready"),
        ("Ops Ping", f"{BASE_URL}/api/ops/ping"),
        ("Data OHLCV", f"{BASE_URL}/api/data/ohlcv?symbol=BTCUSDT&timeframe=1H&limit=10"),
        ("Data Symbols", f"{BASE_URL}/api/data/symbols"),
        ("Data Timeframes", f"{BASE_URL}/api/data/timeframes"),
    ]

    results = []
    for name, url in tests:
        passed = test_endpoint(name, url)
        results.append(passed)
        print()

    # Summary
    print("=" * 60)
    passed_count = sum(results)
    total_count = len(results)
    print(f"SUMMARY: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("✅ All endpoints are working!")
        sys.exit(0)
    else:
        print("❌ Some endpoints failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
