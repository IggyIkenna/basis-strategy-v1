"""
Download Ethena Historical Data from DeFiLlama CSV Export (MANUAL/FUTURE USE)

CURRENT STATUS: Manual download preferred
- Download CSV manually from: https://defillama.com/yields/pool/66985a81-9c51-46ca-9977-42b4fe7bc6df
- Process with: scripts/processing/process_ethena_benchmark.py

FUTURE: This script contains Selenium automation code for potential future use
Uses Selenium to automate the CSV download from DeFiLlama's web interface.
"""

import asyncio
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EthenaHistoricalDownloader:
    """Download Ethena historical data from DeFiLlama CSV export."""
    
    def __init__(self, output_dir: str = "data/manual_sources/benchmark_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # DeFiLlama credentials and URL
        self.email = "ikenna@odum-research.com"
        self.password = "crypto123"
        self.ethena_url = "https://defillama.com/yields/pool/66985a81-9c51-46ca-9977-42b4fe7bc6df"
        
        logger.info("Ethena Historical Downloader initialized")
    
    def setup_selenium(self):
        """Set up Selenium WebDriver."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Store imports for later use
            self.By = By
            self.EC = EC
            
            # Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Set download directory
            download_dir = str(self.output_dir.absolute())
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Initialize driver
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 20)
            
            logger.info("✅ Selenium WebDriver initialized")
            return driver, wait
            
        except ImportError:
            logger.error("❌ Selenium not installed. Run: pip install selenium")
            return None, None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Selenium: {e}")
            return None, None
    
    def download_ethena_csv(self):
        """Download Ethena historical CSV from DeFiLlama."""
        logger.info("🚀 Starting Ethena CSV download from DeFiLlama...")
        
        driver, wait = self.setup_selenium()
        if not driver:
            return False
        
        try:
            # Navigate to Ethena page
            logger.info(f"📡 Navigating to: {self.ethena_url}")
            driver.get(self.ethena_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Look for CSV download button
            logger.info("🔍 Looking for CSV download button...")
            
            # Try different selectors for CSV button
            csv_selectors = [
                "//button[contains(text(), 'csv')]",
                "//button[contains(text(), 'CSV')]", 
                "//a[contains(text(), 'csv')]",
                "//a[contains(text(), 'CSV')]",
                "//button[contains(@class, 'csv')]",
                "//div[contains(text(), 'csv')]//parent::button",
                "//*[contains(text(), 'Download') and contains(text(), 'CSV')]"
            ]
            
            csv_button = None
            for selector in csv_selectors:
                try:
                    csv_button = wait.until(self.EC.element_to_be_clickable((self.By.XPATH, selector)))
                    logger.info(f"✅ Found CSV button with selector: {selector}")
                    break
                except:
                    continue
            
            if not csv_button:
                # Try to find any download-related button
                logger.info("🔍 Looking for any download button...")
                download_buttons = driver.find_elements(self.By.XPATH, "//*[contains(text(), 'Download') or contains(text(), 'download') or contains(text(), 'CSV') or contains(text(), 'csv')]")
                
                if download_buttons:
                    csv_button = download_buttons[0]
                    logger.info(f"✅ Found download button: {csv_button.text}")
                else:
                    logger.error("❌ No CSV download button found")
                    return False
            
            # Click the CSV button
            logger.info("📥 Clicking CSV download button...")
            driver.execute_script("arguments[0].click();", csv_button)
            
            # Wait for download to complete
            logger.info("⏳ Waiting for download to complete...")
            time.sleep(5)
            
            # Check for downloaded file
            downloaded_files = list(self.output_dir.glob("*.csv"))
            new_files = [f for f in downloaded_files if (datetime.now().timestamp() - f.stat().st_mtime) < 60]  # Files modified in last minute
            
            if new_files:
                downloaded_file = new_files[0]
                logger.info(f"✅ Download successful: {downloaded_file.name}")
                
                # Rename to standard format
                new_name = f"ethena_susde_historical_{datetime.now().strftime('%Y%m%d')}.csv"
                final_path = self.output_dir / new_name
                downloaded_file.rename(final_path)
                
                logger.info(f"📄 Renamed to: {new_name}")
                
                # Verify data quality
                try:
                    df = pd.read_csv(final_path)
                    logger.info(f"📊 Data verification:")
                    logger.info(f"   Records: {len(df):,}")
                    logger.info(f"   Columns: {list(df.columns)}")
                    
                    if 'apy' in df.columns or 'APY' in df.columns:
                        apy_col = 'apy' if 'apy' in df.columns else 'APY'
                        logger.info(f"   APY range: {df[apy_col].min():.2f}% - {df[apy_col].max():.2f}%")
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Data verification failed: {e}")
                    return False
            else:
                logger.error("❌ No new files found - download may have failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return False
            
        finally:
            driver.quit()
            logger.info("🔄 Browser closed")
    
    def download_with_manual_instructions(self):
        """Provide manual download instructions if automation fails."""
        logger.info("📋 MANUAL DOWNLOAD INSTRUCTIONS:")
        logger.info("=" * 50)
        logger.info(f"1. Go to: {self.ethena_url}")
        logger.info(f"2. Look for CSV download button on the page")
        logger.info(f"3. Click the CSV button to download")
        logger.info(f"4. Save the file to: {self.output_dir}")
        logger.info(f"5. Rename to: ethena_susde_historical_YYYYMMDD.csv")
        logger.info("=" * 50)

async def main():
    """Main function to download Ethena historical data."""
    try:
        downloader = EthenaHistoricalDownloader()
        
        print("🎯 Downloading Ethena historical data from DeFiLlama...")
        print("📊 This will provide complete historical APY data for benchmarking")
        
        # Try automated download
        success = downloader.download_ethena_csv()
        
        if success:
            print("\\n🎉 SUCCESS! Ethena historical data downloaded")
            print("📈 Data available for strategy benchmarking")
        else:
            print("\\n⚠️  Automated download failed")
            print("📋 Manual download instructions provided")
            downloader.download_with_manual_instructions()
        
        return 0
        
    except Exception as e:
        print(f"\\n💥 ERROR: {e}")
        return 1

if __name__ == "__main__":
    import sys
    
    # Check if selenium is available
    try:
        import selenium
        print("✅ Selenium available - attempting automated download")
    except ImportError:
        print("⚠️  Selenium not installed")
        print("📦 Install with: pip install selenium")
        print("📦 Also need ChromeDriver: brew install chromedriver")
        sys.exit(1)
    
    sys.exit(asyncio.run(main()))
