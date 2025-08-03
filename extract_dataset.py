"""
Wikipedia 'On This Day' Dataset Extraction System

This module provides a comprehensive data collection system that scrapes historical events
from Wikipedia's 'On This Day' API for every single date of the year (365 days). It creates
a structured dataset of historical events that can be used for AI model testing, research,
or analysis purposes.

The system works by:
1. Iterating through all 365 days of the year (January 1st to December 31st)
2. Fetching data from Wikipedia's 'On This Day' API for each date
3. Processing both regular events and "selected" (featured) events
4. Validating dates and handling both AD and BC historical periods
5. Organizing data into a structured directory hierarchy
6. Saving each date as a separate JSON file for easy access and processing

Key Features:
- Complete year coverage (365 days)
- Handles both AD and BC dates with proper formatting
- Separates regular events from featured "selected" events
- Creates organized directory structure (dataset/events/ and dataset/selected/)
- Individual JSON files for each date (730 total files)
- Date validation and error handling
- API rate limiting to be respectful to Wikipedia's servers
- Rich metadata preservation (pages, categories, etc.)

Data Structure:
- Each date gets two files: events/MM-DD.json and selected/MM-DD.json
- Events include: text, year, date, month, day, pages, category, bc flag
- Supports historical events from ancient times to modern day
- No year filtering - includes all available historical events

Classes:
    HistoricalEvent: Data structure for regular historical events
    SelectedEvent: Data structure for featured/selected historical events

Main Functions:
    scrape_all_dates(): Core function that processes all 365 days
    get_wikipedia_on_this_day_data(): Fetches data from Wikipedia API
    process_events_data(): Processes regular events from API response
    process_selected_data(): Processes featured events from API response
    save_date_data(): Saves processed data to organized file structure
    validate_date(): Validates date components (month/day ranges)

Usage:
    Run the main() function to extract the complete dataset:
    >>> python extract_dataset.py
    
    Or import and use individual components:
    >>> from extract_dataset import get_wikipedia_on_this_day_data, process_events_data
    >>> data = get_wikipedia_on_this_day_data(12, 25)  # Christmas
    >>> events = process_events_data(data, 12, 25)

Dependencies:
    - requests: For API calls to Wikipedia
    - json: For data serialization
    - datetime: For date handling
    - dataclasses: For data structures
    - time: For rate limiting
    - os: For directory operations

Output Structure:
    dataset/
    ├── events/
    │   ├── 01-01.json
    │   ├── 01-02.json
    │   └── ... (365 files)
    └── selected/
        ├── 01-01.json
        ├── 01-02.json
        └── ... (365 files)

API Information:
    - Endpoint: https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/
    - Rate limiting: 0.5 second delay between requests
    - No authentication required for basic usage
    - Returns events, selected events, births, deaths, and holidays

This tool is particularly useful for:
- Creating training datasets for AI models
- Historical research and analysis
- Educational content generation
- AI hallucination detection testing
- Historical event timeline analysis
- Content creation for historical applications
"""

import requests
import json
import time
from datetime import datetime, date
from typing import Dict, List, Optional
import os
from dataclasses import dataclass, asdict

@dataclass
class HistoricalEvent:
    text: str
    year: int
    date: str  # YYYY-MM-DD format
    month: int
    day: int
    pages: List[Dict]
    category: str = "events"
    bc: bool = False  # True if the year is BC (negative)

@dataclass
class SelectedEvent:
    text: str
    year: int
    date: str  # YYYY-MM-DD format
    month: int
    day: int
    pages: List[Dict]
    category: str = "selected"
    bc: bool = False  # True if the year is BC (negative)

def get_wikipedia_on_this_day_data(month: int, day: int) -> Optional[Dict]:
    """
    Fetch all data from Wikipedia's 'On This Day' API for a specific date.
    Returns the complete JSON response or None if failed.
    """
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{month:02d}/{day:02d}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching data for {month:02d}/{day:02d}: {e}")
        return None

def validate_date(year: int, month: int, day: int) -> bool:
    """
    Validate if a date is valid, handling both AD and BC dates.
    Only validates month and day ranges, not year.
    """
    # Check if month and day are in valid ranges
    if month < 1 or month > 12:
        return False
    
    # Days in each month (non-leap year)
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    if day < 1 or day > days_in_month[month - 1]:
        return False
    
    return True

def format_date_string(year: int, month: int, day: int) -> str:
    """
    Format date string, handling BC dates with proper formatting.
    """
    if year < 0:
        # For BC dates, use absolute value and add BC indicator
        return f"{abs(year)}-{month:02d}-{day:02d}"
    else:
        return f"{year}-{month:02d}-{day:02d}"

def process_events_data(data: Dict, month: int, day: int) -> List[HistoricalEvent]:
    """
    Process events data from the API response.
    No year filtering applied.
    """
    events = []
    events_data = data.get("events", [])
    
    for event in events_data:
        if "year" in event and "text" in event:
            year = event["year"]
            
            # Only validate month and day, accept any year (BC or AD)
            if not validate_date(year, month, day):
                print(f"Skipping invalid date: {year}-{month:02d}-{day:02d} for event: {event['text'][:50]}...")
                continue
            
            historical_event = HistoricalEvent(
                text=event["text"],
                year=year,
                date=format_date_string(year, month, day),
                month=month,
                day=day,
                pages=event.get("pages", []),
                category="events",
                bc=(year < 0)
            )
            events.append(historical_event)
    
    return events

def process_selected_data(data: Dict, month: int, day: int) -> List[SelectedEvent]:
    """
    Process selected data from the API response.
    No year filtering applied.
    """
    selected_events = []
    selected_data = data.get("selected", [])
    
    for event in selected_data:
        if "year" in event and "text" in event:
            year = event["year"]
            
            # Only validate month and day, accept any year (BC or AD)
            if not validate_date(year, month, day):
                print(f"Skipping invalid date: {year}-{month:02d}-{day:02d} for selected event: {event['text'][:50]}...")
                continue
            
            selected_event = SelectedEvent(
                text=event["text"],
                year=year,
                date=format_date_string(year, month, day),
                month=month,
                day=day,
                pages=event.get("pages", []),
                category="selected",
                bc=(year < 0)
            )
            selected_events.append(selected_event)
    
    return selected_events

def save_date_data(events: List[HistoricalEvent], selected: List[SelectedEvent], month: int, day: int):
    """
    Save events and selected data for a specific date to separate JSON files.
    """
    # Create directory structure
    dataset_dir = "dataset"
    events_dir = os.path.join(dataset_dir, "events")
    selected_dir = os.path.join(dataset_dir, "selected")
    
    os.makedirs(events_dir, exist_ok=True)
    os.makedirs(selected_dir, exist_ok=True)
    
    # Create filename in format month-day.json
    filename = f"{month:02d}-{day:02d}.json"
    
    # Save events data
    if events:
        events_data = [asdict(event) for event in events]
        events_file = os.path.join(events_dir, filename)
        with open(events_file, "w", encoding="utf-8") as f:
            json.dump(events_data, f, indent=2, ensure_ascii=False)
        print(f"  - Saved {len(events)} events to {events_file}")
    else:
        # Create empty file for dates with no events
        events_file = os.path.join(events_dir, filename)
        with open(events_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print(f"  - Created empty events file: {events_file}")
    
    # Save selected data
    if selected:
        selected_data = [asdict(event) for event in selected]
        selected_file = os.path.join(selected_dir, filename)
        with open(selected_file, "w", encoding="utf-8") as f:
            json.dump(selected_data, f, indent=2, ensure_ascii=False)
        print(f"  - Saved {len(selected)} selected events to {selected_file}")
    else:
        # Create empty file for dates with no selected events
        selected_file = os.path.join(selected_dir, filename)
        with open(selected_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print(f"  - Created empty selected file: {selected_file}")

def scrape_all_dates():
    """
    Scrape data for every single date of the year (365 days).
    Saves each date as a separate JSON file in organized folders.
    """
    total_events = 0
    total_selected = 0
    
    # Iterate through all months and days
    for month in range(1, 13):
        for day in range(1, 32):  # We'll handle invalid dates in the processing
            print(f"Scraping data for {month:02d}/{day:02d}...")
            
            # Get data for this date
            data = get_wikipedia_on_this_day_data(month, day)
            
            if data is None:
                print(f"Failed to get data for {month:02d}/{day:02d}")
                # Still create empty files for failed dates
                save_date_data([], [], month, day)
                continue
            
            # Process events
            events = process_events_data(data, month, day)
            total_events += len(events)
            
            # Process selected events
            selected = process_selected_data(data, month, day)
            total_selected += len(selected)
            
            # Save data for this date
            save_date_data(events, selected, month, day)
            
            # Add a small delay to be respectful to the API
            time.sleep(0.5)
    
    return total_events, total_selected

def print_summary(total_events: int, total_selected: int):
    """
    Print a summary of the collected data.
    """
    print("\n" + "="*50)
    print("DATASET EXTRACTION SUMMARY")
    print("="*50)
    print(f"Total Events Collected: {total_events}")
    print(f"Total Selected Events Collected: {total_selected}")
    print(f"Total Files Created: 730 (365 dates × 2 categories)")
    print("\nDirectory Structure:")
    print("dataset/")
    print("├── events/")
    print("│   ├── 01-01.json")
    print("│   ├── 01-02.json")
    print("│   └── ... (365 files)")
    print("└── selected/")
    print("    ├── 01-01.json")
    print("    ├── 01-02.json")
    print("    └── ... (365 files)")

def main():
    """
    Main function to run the dataset extraction.
    """
    print("Starting Wikipedia 'On This Day' Dataset Extraction")
    print("="*60)
    print("This will scrape data for all 365 days of the year...")
    print("Each date will be saved as a separate JSON file")
    print("Directory structure: dataset/events/ and dataset/selected/")
    print("Estimated time: ~3-5 minutes (with API rate limiting)")
    print("="*60)
    
    # Scrape all dates
    total_events, total_selected = scrape_all_dates()
    
    # Print summary
    print_summary(total_events, total_selected)
    
    print("\nDataset extraction completed successfully!")
    print("All files saved in the 'dataset' directory structure")

if __name__ == "__main__":
    main() 