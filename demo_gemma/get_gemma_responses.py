"""
Enhanced AI Model Hallucination Detection System - Multi-Model Analysis

This module provides an advanced testing framework for evaluating the factual accuracy
of multiple AI language models simultaneously, specifically their tendency to "hallucinate"
or provide incorrect information when asked about historical dates and events.

This enhanced version includes:
- Multi-model testing (gemma3:1b, gemma3:4b, gemma3:27b)
- Extended historical dataset with rich metadata
- Year-only accuracy evaluation (simplified from full date matching)
- Batch processing with progress tracking
- Structured output with detailed event categorization
- Comparative analysis across different model sizes

The system works by:
1. Loading historical events from a structured JSON dataset with rich metadata
2. Generating questions about historical events asking for specific years
3. Querying multiple AI models (Ollama) with these questions
4. Extracting years from model responses using pattern matching
5. Comparing extracted years against ground truth with confidence scoring
6. Generating comparative reports across all tested models

Key Features:
- Multi-model evaluation (1B, 4B, 27B parameter models)
- Rich event metadata (category, violence level, cultural region, historical period)
- Year-focused accuracy evaluation with temporal distance penalties
- Batch processing with progress indicators
- Structured JSON output for each model
- Comparative analysis and ranking
- Configurable test parameters and model selection

Classes:
    HistoricalEvent: Enhanced data structure with rich metadata
    TestResult: Data structure for storing test outcomes with model identification

Main Functions:
    test_model_for_hallucinations(): Core testing function for individual models
    load_historical_events(): Loads events from structured JSON dataset
    calculate_accuracy_score(): Evaluates year accuracy with confidence scoring
    extract_year_from_response(): Extracts years from model responses
    save_results(): Saves structured results to JSON files
    print_summary(): Generates comparative summaries across models

Usage:
    Run the main() function to execute multi-model hallucination tests:
    >>> python serge_run_analysis.py
    
    Or import and use individual components:
    >>> from serge_run_analysis import load_historical_events, test_model_for_hallucinations
    >>> events = load_historical_events("/path/to/dataset")
    >>> results = test_model_for_hallucinations(events, "gemma3:4b", num_tests=50)

Dependencies:
    - requests: For API calls to Ollama
    - datetime: For date parsing and validation
    - re: For regex-based year extraction
    - random: For sampling test cases
    - json: For result serialization
    - dataclasses: For data structures
    - pathlib: For file path handling

Configuration:
    - Ollama base URL: http://localhost:11440 (configurable)
    - Default models: ["gemma3:1b", "gemma3:4b", "gemma3:27b"]
    - Temperature: 0.3 (for consistent responses)
    - Max tokens: 500
    - Default tests per model: 100

Output:
    - Console output with progress tracking and comparative summaries
    - Individual JSON files for each model's results
    - Structured data with event metadata and accuracy metrics
    - Overall comparative analysis across all models

This tool is particularly useful for:
- Comparative model evaluation studies
- Scaling analysis (1B vs 4B vs 27B parameter models)
- Quality assurance across different model sizes
- Research on hallucination patterns across model scales
- Benchmarking historical knowledge capabilities
- Identifying optimal model size for factual accuracy
"""

import requests
import json
import re
import os
import random
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

@dataclass
class HistoricalEvent:
    text: str
    year: int
    date: str
    primary_category: str
    violence_level: str
    cultural_region: str
    historical_period: str

@dataclass
class TestResult:
    event: HistoricalEvent
    question: str
    model_response: str
    extracted_year: Optional[int]
    is_correct: bool
    confidence_score: float = 0.0
    model_name: str = ""

def query_ollama(
    prompt: str,
    model: str = "gemma3:1b",
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 500,
    stream: bool = False,
    base_url: str = "http://localhost:11440"
):
    """Query the Ollama API with the given prompt."""
    url = f"{base_url}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    if system_prompt:
        payload["system"] = system_prompt
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        print(f"Error querying Ollama: {e}")
        return None

def load_historical_events(data_dir: str) -> List[HistoricalEvent]:
    """Load historical events from JSON files in the dataset directory."""
    events = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Data directory {data_dir} does not exist!")
        return events
    
    json_files = list(data_path.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to process")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for item in data:
                if all(key in item for key in ['text', 'year', 'date', 'primary_category', 
                                             'violence_level', 'cultural_region', 'historical_period']):
                    event = HistoricalEvent(
                        text=item['text'],
                        year=item['year'],
                        date=item['date'],
                        primary_category=item['primary_category'],
                        violence_level=item['violence_level'],
                        cultural_region=item['cultural_region'],
                        historical_period=item['historical_period']
                    )
                    events.append(event)
                    
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    print(f"Loaded {len(events)} historical events")
    return events

def generate_question_from_event(event: HistoricalEvent) -> str:
    """Generate a question from a historical event."""
    # Create a simple question asking for the year
    return f"What year did this event occur: {event.text}?"

def extract_year_from_response(response: str) -> Optional[int]:
    """
    Extract a year from the model's response.
    Returns the year as integer if found, None otherwise.
    """
    if not response:
        return None
    
    # Common year patterns
    patterns = [
        # Four digit year
        r'\b(1[5-9]\d{2}|20[0-2]\d)\b',
        # Year in various formats
        r'\b(\d{4})\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response)
        if matches:
            try:
                year = int(matches[0])
                # Filter reasonable years (1500-2024)
                if 1500 <= year <= 2024:
                    return year
            except ValueError:
                continue
    
    return None

def calculate_accuracy_score(extracted_year: int, ground_truth_year: int) -> Tuple[bool, float]:
    """
    Calculate if the extracted year is correct and provide a confidence score.
    Returns (is_correct, confidence_score)
    """
    if extracted_year is None:
        return False, 0.0
    
    # Check if years match exactly
    is_correct = extracted_year == ground_truth_year
    
    if is_correct:
        confidence = 1.0
    else:
        # Calculate penalty based on how far off
        year_diff = abs(extracted_year - ground_truth_year)
        
        if year_diff <= 1:
            confidence = 0.8  # Very close year
        elif year_diff <= 5:
            confidence = 0.6  # Close year
        elif year_diff <= 10:
            confidence = 0.4  # Moderately far year
        elif year_diff <= 50:
            confidence = 0.2  # Far year
        else:
            confidence = 0.1  # Very far year
    
    return is_correct, confidence

def test_model_for_hallucinations(events: List[HistoricalEvent], model_name: str, 
                                 num_tests: int = 100) -> List[TestResult]:
    """
    Test the model for hallucinations using historical events.
    """
    results = []
    
    # Randomly sample events
    selected_events = random.sample(events, min(num_tests, len(events)))
    
    print(f"\n--- Testing Model: {model_name} ---")
    print(f"Testing {len(selected_events)} events...")
    
    for i, event in enumerate(selected_events, 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(selected_events)} events...")
        
        # Generate question
        question = generate_question_from_event(event)
        
        # Query the model
        system_prompt = "You are a helpful assistant. Answer questions accurately and concisely. When asked about years, provide only the specific year as a number."
        response = query_ollama(question, model=model_name, system_prompt=system_prompt, temperature=0.3)
        
        if response is None:
            print(f"Failed to get response for event {i}")
            continue
        
        # Extract year from response
        extracted_year = extract_year_from_response(response)
        
        # Check accuracy
        is_correct, confidence = calculate_accuracy_score(extracted_year, event.year)
        
        result = TestResult(
            event=event,
            question=question,
            model_response=response,
            extracted_year=extracted_year,
            is_correct=is_correct,
            confidence_score=confidence,
            model_name=model_name
        )
        
        results.append(result)
    
    return results

def save_results(results: List[TestResult], output_dir: str, model_name: str):
    """Save test results to JSON file."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Clean model name for filename
    clean_model_name = model_name.replace(":", "_")
    
    output_file = output_path / f"results_{clean_model_name}.json"
    
    results_data = []
    for result in results:
        result_dict = {
            "model_name": result.model_name,
            "event": {
                "text": result.event.text,
                "year": result.event.year,
                "date": result.event.date,
                "primary_category": result.event.primary_category,
                "violence_level": result.event.violence_level,
                "cultural_region": result.event.cultural_region,
                "historical_period": result.event.historical_period
            },
            "question": result.question,
            "model_response": result.model_response,
            "extracted_year": result.extracted_year,
            "is_correct": result.is_correct,
            "confidence_score": result.confidence_score
        }
        results_data.append(result_dict)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {output_file}")

def print_summary(results: List[TestResult]):
    """Print a summary of the test results."""
    if not results:
        print("No results to summarize")
        return
    
    total_tests = len(results)
    correct_answers = sum(1 for r in results if r.is_correct)
    avg_confidence = sum(r.confidence_score for r in results) / total_tests
    
    print(f"\n{'='*60}")
    print(f"HALLUCINATION TEST SUMMARY - {results[0].model_name}")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Correct Answers: {correct_answers}")
    print(f"Accuracy: {correct_answers/total_tests*100:.1f}%")
    print(f"Average Confidence: {avg_confidence:.2f}")

def main():
    """Main function to run the hallucination test for all models."""
    print("Starting Gemma Model Hallucination Test")
    print("="*60)
    
    # Configuration
    data_dir = "/home/ch215616/ww/code/reason/s20250727_hallucinations/dataset-extended/selected-gemma3-4b"
    output_dir = "output"
    models = ["gemma3:1b", "gemma3:4b", "gemma3:27b"]
    num_tests_per_model = 100  # Adjust as needed
    
    # Load historical events
    print("Loading historical events...")
    events = load_historical_events(data_dir)
    
    if not events:
        print("No events loaded. Exiting.")
        return
    
    # Test each model
    all_results = []
    
    for model in models:
        print(f"\n{'='*60}")
        print(f"Testing Model: {model}")
        print(f"{'='*60}")
        
        # Run tests for this model
        results = test_model_for_hallucinations(events, model, num_tests_per_model)
        
        # Print summary
        print_summary(results)
        
        # Save results
        save_results(results, output_dir, model)
        
        all_results.extend(results)
        
        print(f"Completed testing for {model}")
    
    # Overall summary
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    
    for model in models:
        model_results = [r for r in all_results if r.model_name == model]
        if model_results:
            correct = sum(1 for r in model_results if r.is_correct)
            accuracy = correct / len(model_results) * 100
            print(f"{model}: {accuracy:.1f}% accuracy ({correct}/{len(model_results)})")
    
    print(f"\nAll results saved to {output_dir}/ directory")

if __name__ == "__main__":
    main()