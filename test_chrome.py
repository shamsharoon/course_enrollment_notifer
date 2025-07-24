"""
Simple Chrome WebDriver test script to diagnose issues
"""

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_chrome_basic():
    """Test basic Chrome setup without any special options"""
    print("🧪 Testing basic Chrome setup...")
    try:
        driver = webdriver.Chrome()
        driver.get("https://www.google.com")
        print(f"✅ Basic Chrome works! Title: {driver.title}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Basic Chrome failed: {e}")
        return False

def test_chrome_headless():
    """Test Chrome in headless mode"""
    print("🧪 Testing headless Chrome...")
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.google.com")
        print(f"✅ Headless Chrome works! Title: {driver.title}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Headless Chrome failed: {e}")
        return False

def test_chrome_with_profile():
    """Test Chrome with user profile"""
    print("🧪 Testing Chrome with profile...")
    try:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        profile_path = "./test_chrome_profile"
        if not os.path.exists(profile_path):
            os.makedirs(profile_path, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_path}")
        
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.google.com")
        print(f"✅ Chrome with profile works! Title: {driver.title}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Chrome with profile failed: {e}")
        return False

def main():
    print("🚀 Chrome WebDriver Diagnostic Test")
    print("=" * 50)
    
    # Test different configurations
    basic_works = test_chrome_basic()
    headless_works = test_chrome_headless()
    profile_works = test_chrome_with_profile()
    
    print("\n📊 Results Summary:")
    print("=" * 50)
    print(f"Basic Chrome: {'✅ PASS' if basic_works else '❌ FAIL'}")
    print(f"Headless Chrome: {'✅ PASS' if headless_works else '❌ FAIL'}")
    print(f"Chrome with Profile: {'✅ PASS' if profile_works else '❌ FAIL'}")
    
    if not any([basic_works, headless_works, profile_works]):
        print("\n🚨 Chrome WebDriver Issues Detected!")
        print("💡 Try these solutions:")
        print("1. Update Chrome: Settings → About Chrome")
        print("2. Install/Update ChromeDriver:")
        print("   - Download from: https://chromedriver.chromium.org/")
        print("   - Or install via: pip install webdriver-manager")
        print("3. Check Chrome installation path")
        print("4. Try running without headless mode")
    elif basic_works:
        print("\n✅ Chrome WebDriver is working!")
        print("The course notifier should work with the updated configuration.")

if __name__ == "__main__":
    main() 