"""
Historical Facts Classification System

This module provides an AI-powered classification system that enriches historical facts
with detailed metadata using a local Ollama language model. It takes raw historical events
from the dataset and adds comprehensive categorization across multiple dimensions.

The system works by:
1. Loading historical facts from JSON files in the dataset directory
2. Using an AI model (gemma3:4b) to classify each fact across multiple dimensions
3. Adding rich metadata including primary categories, geographic classification,
   temporal classification, and impact assessment
4. Creating extended fact objects with comprehensive categorization
5. Saving enriched data to a new dataset structure for further analysis

Key Features:
- Multi-dimensional classification (12 different classification axes)
- AI-powered categorization using local Ollama models
- Comprehensive metadata enrichment
- Geographic and temporal classification
- Violence level and human impact assessment
- Cultural and developmental classification
- Batch processing with progress tracking
- Resume capability (skips already processed files)

Classification Dimensions:
- Primary Category: Military & Warfare, Politics & Government, Science & Technology, etc.
- Violence Level: peaceful, violent, catastrophic
- Scale: local, national, international, global
- Human Impact: individual, small group, mass population
- Geographic: continental regions, cultural regions, development status
- Temporal: century, decade, seasonal, historical period

Classes:
    ExtendedFact: Enhanced data structure with comprehensive classification metadata

Main Functions:
    classify_fact(): Classifies a single historical fact using AI
    create_classification_prompt(): Generates structured prompts for the AI model
    process_file(): Processes individual JSON files with batch classification
    create_extended_fact(): Creates enriched fact objects with classifications
    query_ollama(): Interfaces with local Ollama API for AI classification

Usage:
    Run the main() function to process all files in the dataset:
    >>> python classify_facts.py
    
    Or import and use individual components:
    >>> from classify_facts import classify_fact, create_extended_fact
    >>> classification = classify_fact(fact_dict, model="gemma3:4b")
    >>> extended_fact = create_extended_fact(fact_dict, classification)

Dependencies:
    - requests: For API calls to Ollama
    - json: For data serialization and parsing
    - dataclasses: For data structures
    - time: For rate limiting
    - os: For file operations

Configuration:
    - Ollama base URL: http://localhost:11441 (configurable)
    - Default model: gemma3:4b
    - Temperature: 0.1 (for consistent classifications)
    - Input directory: dataset/
    - Output directory: dataset-extended/

Input Structure:
    dataset/
    ├── events/          # Raw historical events
    └── selected/        # Raw selected events

Output Structure:
    dataset-extended/
    ├── events-gemma3-4b/    # Classified events
    └── selected-gemma3-4b/  # Classified selected events

Classification Categories:
    Primary Categories: Military & Warfare, Politics & Government, Science & Technology,
                       Arts & Culture, Disasters & Accidents, Sports & Recreation,
                       Economics & Business, Religion & Philosophy
    
    Geographic: North America, South America, Europe, Asia, Africa, Oceania
    Cultural: Western, Eastern, Middle Eastern, African, Latin American
    Temporal: Pre-1500, 1500-1699, 1700-1799, 1800-1899, 1900-1999, 2000+
    Impact: peaceful/violent/catastrophic, local/national/international/global

This tool is particularly useful for:
- Enriching historical datasets with structured metadata
- Creating categorized training data for AI models
- Historical research and analysis with detailed classification
- AI hallucination detection with rich context
- Educational content organization and filtering
- Historical pattern analysis across different dimensions
- Creating specialized datasets for specific research domains
"""

import json
import os
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import time

@dataclass
class ExtendedFact:
    text: str
    year: int
    date: str
    month: int
    day: int
    pages: List[Dict]
    category: str
    
    # Primary Categories
    primary_category: str
    
    # Secondary Tags
    violence_level: str
    scale: str
    human_impact: str
    
    # Geographic Classification
    continental: str
    cultural_region: str
    development_status: str
    colonial_status: str
    
    # Temporal Classification
    century: str
    decade: str
    seasonal: str
    historical_period: str

def query_ollama(prompt: str, model: str = "gemma3:4b", temperature: float = 0.1) -> Optional[str]:
    """
    Query the local Ollama model for classification.
    """
    url = "http://localhost:11441/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None

def create_classification_prompt(fact_text: str, fact_year: int) -> str:
    """
    Create a prompt for the LLM to classify the historical fact.
    """
    prompt = f"""Classify the following historical fact using ONLY the specified categories. Return ONLY a valid JSON object with the exact keys shown below.

Historical Fact: "{fact_text}" (Year: {fact_year})

Return a JSON object with these exact keys and values from the specified categories:

{{
    "primary_category": "Military & Warfare" | "Politics & Government" | "Science & Technology" | "Arts & Culture" | "Disasters & Accidents" | "Sports & Recreation" | "Economics & Business" | "Religion & Philosophy",
    "violence_level": "peaceful" | "violent" | "catastrophic",
    "scale": "local" | "national" | "international" | "global",
    "human_impact": "individual" | "small group" | "mass population",
    "continental": "North America" | "South America" | "Europe" | "Asia" | "Africa" | "Oceania",
    "cultural_region": "Western" | "Eastern" | "Middle Eastern" | "African" | "Latin American",
    "development_status": "developed" | "developing",
    "colonial_status": "colonial" | "independent",
    "century": "Pre-1500" | "1500-1699" | "1700-1799" | "1800-1899" | "1900-1999" | "2000+",
    "decade": "1500s" | "1510s" | "1520s" | "1530s" | "1540s" | "1550s" | "1560s" | "1570s" | "1580s" | "1590s" | "1600s" | "1610s" | "1620s" | "1630s" | "1640s" | "1650s" | "1660s" | "1670s" | "1680s" | "1690s" | "1700s" | "1710s" | "1720s" | "1730s" | "1740s" | "1750s" | "1760s" | "1770s" | "1780s" | "1790s" | "1800s" | "1810s" | "1820s" | "1830s" | "1840s" | "1850s" | "1860s" | "1870s" | "1880s" | "1890s" | "1900s" | "1910s" | "1920s" | "1930s" | "1940s" | "1950s" | "1960s" | "1970s" | "1980s" | "1990s" | "2000s" | "2010s" | "2020s",
    "seasonal": "Winter" | "Spring" | "Summer" | "Fall",
    "historical_period": "Ancient" | "Medieval" | "Renaissance" | "Industrial" | "Modern" | "Contemporary"
}}

Choose the most appropriate category for each field based on the historical fact. Return ONLY the JSON object, no additional text."""
    
    return prompt

def classify_fact(fact: Dict, model: str = "gemma3:4b") -> Optional[Dict]:
    """
    Classify a single fact using the Ollama model.
    """
    fact_text = fact["text"]
    fact_year = fact["year"]
    
    prompt = create_classification_prompt(fact_text, fact_year)
    response = query_ollama(prompt, model)
    
    if not response:
        return None
    
    try:
        # Clean the response to extract JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        classification = json.loads(response)
        
        # Validate that all required keys are present
        required_keys = [
            "primary_category", "violence_level", "scale", "human_impact",
            "continental", "cultural_region", "development_status", "colonial_status",
            "century", "decade", "seasonal", "historical_period"
        ]
        
        for key in required_keys:
            if key not in classification:
                print(f"Missing key {key} in classification for fact: {fact_text[:50]}...")
                return None
        
        return classification
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response for fact: {fact_text[:50]}...")
        print(f"Response: {response}")
        return None

def create_extended_fact(fact: Dict, classification: Dict) -> ExtendedFact:
    """
    Create an ExtendedFact object from the original fact and classification.
    """
    return ExtendedFact(
        text=fact["text"],
        year=fact["year"],
        date=fact["date"],
        month=fact["month"],
        day=fact["day"],
        pages=fact["pages"],
        category=fact["category"],
        primary_category=classification["primary_category"],
        violence_level=classification["violence_level"],
        scale=classification["scale"],
        human_impact=classification["human_impact"],
        continental=classification["continental"],
        cultural_region=classification["cultural_region"],
        development_status=classification["development_status"],
        colonial_status=classification["colonial_status"],
        century=classification["century"],
        decade=classification["decade"],
        seasonal=classification["seasonal"],
        historical_period=classification["historical_period"]
    )

def process_file(input_file: str, output_file: str, model: str = "gemma3:4b"):
    """
    Process a single JSON file and create its extended version.
    """
    # Check if output file already exists and is not empty
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        print(f"Skipping {input_file} - output already exists")
        return
    
    print(f"Processing {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            facts = json.load(f)
        
        if not facts:
            print(f"Empty file: {input_file}")
            return
        
        extended_facts = []
        
        for i, fact in enumerate(facts):
            print(f"  Classifying fact {i+1}/{len(facts)}: {fact['text'][:50]}...")
            
            classification = classify_fact(fact, model)
            if classification:
                extended_fact = create_extended_fact(fact, classification)
                extended_facts.append(asdict(extended_fact))
            else:
                print(f"    Failed to classify fact {i+1}")
            
            # Add delay between requests
            time.sleep(0.0)
        
        # Save extended facts
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extended_facts, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved {len(extended_facts)} extended facts to {output_file}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {e}")

def main():
    """
    Main function to process all files in the dataset.
    """
    print("Starting Historical Facts Classification")
    print("="*50)
    
    # Configuration
    model = "gemma3:4b"  # Change this to your available model
    input_base_dir = "dataset"
    output_base_dir = "dataset-extended"
    
    input('events categorization is temporarily disabled. proceed?')
    # # Process events
    # events_input_dir = os.path.join(input_base_dir, "events")
    # events_output_dir = os.path.join(output_base_dir, "events-gemma3-4b")
    
    # if os.path.exists(events_input_dir):
    #     print(f"Processing events from {events_input_dir}")
    #     for filename in os.listdir(events_input_dir):
    #         if filename.endswith('.json'):
    #             input_file = os.path.join(events_input_dir, filename)
    #             output_file = os.path.join(events_output_dir, filename)
    #             process_file(input_file, output_file, model)
    
    # Process selected
    selected_input_dir = os.path.join(input_base_dir, "selected")
    selected_output_dir = os.path.join(output_base_dir, "selected-gemma3-4b")
    
    if os.path.exists(selected_input_dir):
        print(f"Processing selected from {selected_input_dir}")
        for filename in os.listdir(selected_input_dir):
            if filename.endswith('.json'):
                input_file = os.path.join(selected_input_dir, filename)
                output_file = os.path.join(selected_output_dir, filename)
                process_file(input_file, output_file, model)
    
    print("\nClassification completed!")

if __name__ == "__main__":
    main() 