"""
Base downloader class with common functionality for all data downloaders.

Provides:
- Error handling and retry logic
- Rate limiting with exponential backoff  
- Progress tracking and logging
- Data validation and CSV output
- Configuration management
"""

import asyncio
import csv
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Import the configuration function
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))
from basis_strategy_v1.infrastructure.config.settings import get_downloader_settings


class RateLimiter:
    """Rate limiter with exponential backoff."""
    
    def __init__(self, max_requests_per_minute: int = 60, max_requests_per_second: int = None):
        self.max_requests_per_minute = max_requests_per_minute
        # Auto-calculate per-second limit if not provided (be conservative)
        self.max_requests_per_second = max_requests_per_second or max(1, max_requests_per_minute // 60)
        self.requests_this_minute = []
        self.requests_this_second = []
        self.last_request_time = 0
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Clean old requests
        self.requests_this_minute = [t for t in self.requests_this_minute if now - t < 60]
        self.requests_this_second = [t for t in self.requests_this_second if now - t < 1]
        
        # Check per-second limit
        if len(self.requests_this_second) >= self.max_requests_per_second:
            wait_time = 1 - (now - min(self.requests_this_second))
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.time()
        
        # Check per-minute limit  
        if len(self.requests_this_minute) >= self.max_requests_per_minute:
            wait_time = 60 - (now - min(self.requests_this_minute))
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.time()
        
        # Record this request
        self.requests_this_minute.append(now)
        self.requests_this_second.append(now)
        self.last_request_time = now


class BaseDownloader(ABC):
    """
    Base class for all data downloaders.
    
    Provides common functionality:
    - Configuration management
    - HTTP session with retry logic
    - Rate limiting
    - Error handling and logging
    - Data validation
    - CSV output formatting
    """
    
    def __init__(self, name: str, output_dir: str, rate_limit_per_minute: int = 60):
        self.name = name
        self.output_dir = Path(output_dir)
        self.logger = self._setup_logging()
        self.config = get_downloader_settings()
        self.session = self._setup_session()
        # Calculate per-second rate (be conservative: use 80% of theoretical max)
        per_second_rate = max(1, int(rate_limit_per_minute * 0.8 / 60))
        self.rate_limiter = RateLimiter(max_requests_per_minute=rate_limit_per_minute, max_requests_per_second=per_second_rate)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Initialized {self.name} downloader")
        self.logger.info(f"Output directory: {self.output_dir}")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for this downloader."""
        logger = logging.getLogger(f"downloader.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Create console handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_session(self) -> requests.Session:
        """Set up HTTP session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config['download_config']['retry_attempts'],
            backoff_factor=self.config['download_config']['retry_delay'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]  # Updated from method_whitelist
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    async def make_request(self, url: str, params: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request with rate limiting and error handling.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response JSON or None if failed
        """
        await self.rate_limiter.wait_if_needed()
        
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Unexpected status code {response.status_code} for {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error for {url}: {e}")
            return None
    
    def validate_data(self, data: List[Dict], required_fields: List[str]) -> bool:
        """
        Validate data has required fields.
        
        Args:
            data: List of data records
            required_fields: List of required field names
            
        Returns:
            True if valid, False otherwise
        """
        if not data:
            self.logger.error("No data to validate")
            return False
        
        for record in data[:5]:  # Check first 5 records
            for field in required_fields:
                if field not in record:
                    self.logger.error(f"Missing required field: {field}")
                    return False
        
        self.logger.info(f"Data validation passed for {len(data)} records")
        return True
    
    def save_to_csv(self, data: List[Dict], filename: str, 
                   fieldnames: Optional[List[str]] = None) -> Path:
        """
        Save data to CSV file.
        
        Args:
            data: List of data records
            filename: Output filename
            fieldnames: Optional field order, otherwise inferred
            
        Returns:
            Path to saved file
        """
        if not data:
            self.logger.warning(f"No data to save for {filename}")
            return None
        
        filepath = self.output_dir / filename
        
        # Infer fieldnames if not provided
        if fieldnames is None:
            fieldnames = list(data[0].keys())
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"Saved {len(data)} records to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save CSV {filepath}: {e}")
            return None
    
    def create_summary_report(self, downloads: List[Dict]) -> Dict:
        """
        Create summary report of download results.
        
        Args:
            downloads: List of download result dictionaries
            
        Returns:
            Summary report dictionary
        """
        total_records = sum(d.get('record_count', 0) for d in downloads)
        successful_downloads = sum(1 for d in downloads if d.get('success', False))
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'downloader': self.name,
            'total_downloads': len(downloads),
            'successful_downloads': successful_downloads,
            'failed_downloads': len(downloads) - successful_downloads,
            'total_records': total_records,
            'downloads': downloads
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = "download_report.json") -> Path:
        """Save download report to JSON file."""
        import json
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Saved download report to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save report {filepath}: {e}")
            return None
    
    @abstractmethod
    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """
        Abstract method for downloading data.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Download result dictionary
        """
        pass
    
    def get_date_range(self) -> tuple:
        """Get configured date range for downloads."""
        config = self.config['date_range']
        return config['start_date'], config['end_date']
    
    def chunk_date_range(self, start_date: str, end_date: str, chunk_days: int) -> List[tuple]:
        """
        Split date range into chunks.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format  
            chunk_days: Days per chunk
            
        Returns:
            List of (start, end) date tuples
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        chunks = []
        current = start
        
        while current <= end:  # Changed from < to <= to handle same-day ranges
            chunk_end = min(current + timedelta(days=chunk_days), end)
            chunks.append((
                current.strftime('%Y-%m-%d'),
                chunk_end.strftime('%Y-%m-%d')
            ))
            current = chunk_end + timedelta(days=1)
            
            # Break if we've covered the end date
            if chunk_end >= end:
                break
        
        return chunks


class ProgressTracker:
    """Simple progress tracker for downloads."""
    
    def __init__(self, total: int, description: str = "Progress"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.logger = logging.getLogger("progress")
    
    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        
        if self.current % max(1, self.total // 20) == 0 or self.current == self.total:
            elapsed = time.time() - self.start_time
            rate = self.current / elapsed if elapsed > 0 else 0
            eta = (self.total - self.current) / rate if rate > 0 else 0
            
            percentage = (self.current / self.total) * 100
            
            self.logger.info(
                f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%) "
                f"- Rate: {rate:.1f}/s - ETA: {eta:.0f}s"
            )
    
    def finish(self):
        """Mark progress as complete."""
        elapsed = time.time() - self.start_time
        rate = self.total / elapsed if elapsed > 0 else 0
        
        self.logger.info(
            f"{self.description}: Complete! {self.total} items in {elapsed:.1f}s "
            f"(avg {rate:.1f}/s)"
        )
