import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

# Set style for better looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_results(output_dir: str) -> List[Dict]:
    """Load all result files from the output directory."""
    results = []
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"Output directory {output_dir} does not exist!")
        return results
    
    json_files = list(output_path.glob("results_*.json"))
    print(f"Found {len(json_files)} result files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.extend(data)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    print(f"Loaded {len(results)} total results")
    return results

def create_dataframe(results: List[Dict]) -> pd.DataFrame:
    """Convert results to a pandas DataFrame for analysis."""
    df_data = []
    
    for result in results:
        df_data.append({
            'model_name': result['model_name'],
            'text': result['event']['text'],
            'true_year': result['event']['year'],
            'extracted_year': result['extracted_year'],
            'is_correct': result['is_correct'],
            'confidence_score': result['confidence_score'],
            'primary_category': result['event']['primary_category'],
            'violence_level': result['event']['violence_level'],
            'cultural_region': result['event']['cultural_region'],
            'historical_period': result['event']['historical_period'],
            'year_error': abs(result['extracted_year'] - result['event']['year']) if result['extracted_year'] else None
        })
    
    return pd.DataFrame(df_data)

def calculate_accuracy_by_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """Calculate accuracy for each category."""
    accuracy_data = []
    
    for model in df['model_name'].unique():
        model_df = df[df['model_name'] == model]
        
        for cat_value in model_df[category].unique():
            cat_df = model_df[model_df[category] == cat_value]
            
            if len(cat_df) > 0:
                accuracy = cat_df['is_correct'].mean() * 100
                count = len(cat_df)
                avg_confidence = cat_df['confidence_score'].mean()
                avg_error = cat_df['year_error'].mean() if 'year_error' in cat_df.columns else None
                
                accuracy_data.append({
                    'model_name': model,
                    'category': cat_value,
                    'accuracy': accuracy,
                    'count': count,
                    'avg_confidence': avg_confidence,
                    'avg_error': avg_error
                })
    
    return pd.DataFrame(accuracy_data)

def plot_model_comparison(df: pd.DataFrame, output_dir: str):
    """Plot overall accuracy comparison between models."""
    plt.figure(figsize=(12, 8))
    
    # Overall accuracy by model
    model_accuracy = df.groupby('model_name')['is_correct'].agg(['mean', 'count']).reset_index()
    model_accuracy['accuracy_pct'] = model_accuracy['mean'] * 100
    
    # Define the correct order for models
    model_order = ['gemma3:1b', 'gemma3:4b', 'gemma3:27b']
    
    # Sort the dataframe by the defined order
    model_accuracy['model_name'] = pd.Categorical(model_accuracy['model_name'], categories=model_order, ordered=True)
    model_accuracy = model_accuracy.sort_values('model_name')
    
    # Create bar plot
    bars = plt.bar(model_accuracy['model_name'], model_accuracy['accuracy_pct'], 
                   color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    
    # Add value labels on bars
    for bar, acc, count in zip(bars, model_accuracy['accuracy_pct'], model_accuracy['count']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{acc:.1f}%\n(n={count})', ha='center', va='bottom', fontweight='bold')
    
    plt.title('Overall Accuracy by Model', fontsize=16, fontweight='bold')
    plt.ylabel('Accuracy (%)', fontsize=12)
    plt.xlabel('Model', fontsize=12)
    plt.ylim(0, 100)
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/model_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_category_analysis(df: pd.DataFrame, category: str, output_dir: str):
    """Plot accuracy analysis for a specific category."""
    accuracy_df = calculate_accuracy_by_category(df, category)
    
    if accuracy_df.empty:
        print(f"No data for category: {category}")
        return
    
    # Filter categories with sufficient data
    min_count = 5
    accuracy_df = accuracy_df[accuracy_df['count'] >= min_count]
    
    if accuracy_df.empty:
        print(f"No categories with sufficient data (min {min_count}) for: {category}")
        return
    
    # Define the correct order for models
    model_order = ['gemma3:1b', 'gemma3:4b', 'gemma3:27b']
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Plot 1: Accuracy by category and model
    pivot_df = accuracy_df.pivot(index='category', columns='model_name', values='accuracy')
    
    # Reorder columns to match the desired model order
    available_models = [model for model in model_order if model in pivot_df.columns]
    pivot_df = pivot_df[available_models]
    
    # Sort by average accuracy
    pivot_df['avg'] = pivot_df.mean(axis=1)
    pivot_df = pivot_df.sort_values('avg', ascending=False)
    pivot_df = pivot_df.drop('avg', axis=1)
    
    pivot_df.plot(kind='bar', ax=ax1, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    ax1.set_title(f'Accuracy by {category.replace("_", " ").title()} and Model', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Accuracy (%)', fontsize=12)
    ax1.set_xlabel(category.replace('_', ' ').title(), fontsize=12)
    ax1.legend(title='Model')
    ax1.grid(axis='y', alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Sample size by category
    count_df = accuracy_df.groupby('category')['count'].sum().reset_index()
    count_df = count_df.sort_values('count', ascending=False)
    
    bars = ax2.bar(count_df['category'], count_df['count'], color='#95E1D3')
    ax2.set_title(f'Sample Size by {category.replace("_", " ").title()}', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Number of Events', fontsize=12)
    ax2.set_xlabel(category.replace('_', ' ').title(), fontsize=12)
    ax2.grid(axis='y', alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Add count labels on bars
    for bar, count in zip(bars, count_df['count']):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/accuracy_by_{category}.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_error_analysis(df: pd.DataFrame, output_dir: str):
    """Plot error analysis showing how far off the predictions are."""
    # Filter out None values
    error_df = df[df['year_error'].notna()].copy()
    
    if error_df.empty:
        print("No error data available")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Error distribution by model
    for model in error_df['model_name'].unique():
        model_data = error_df[error_df['model_name'] == model]['year_error']
        ax1.hist(model_data, alpha=0.7, label=model, bins=20)
    
    ax1.set_title('Year Error Distribution by Model', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Absolute Year Error', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Plot 2: Box plot of errors by model
    error_df.boxplot(column='year_error', by='model_name', ax=ax2)
    ax2.set_title('Year Error Distribution by Model', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Model', fontsize=12)
    ax2.set_ylabel('Absolute Year Error', fontsize=12)
    ax2.grid(alpha=0.3)
    
    # Plot 3: Error vs confidence
    for model in error_df['model_name'].unique():
        model_data = error_df[error_df['model_name'] == model]
        ax3.scatter(model_data['confidence_score'], model_data['year_error'], 
                   alpha=0.6, label=model, s=30)
    
    ax3.set_title('Error vs Confidence Score', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Confidence Score', fontsize=12)
    ax3.set_ylabel('Absolute Year Error', fontsize=12)
    ax3.legend()
    ax3.grid(alpha=0.3)
    
    # Plot 4: Error by historical period
    period_error = error_df.groupby('historical_period')['year_error'].mean().sort_values()
    period_error.plot(kind='bar', ax=ax4, color='#FFB6C1')
    ax4.set_title('Average Error by Historical Period', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Historical Period', fontsize=12)
    ax4.set_ylabel('Average Absolute Year Error', fontsize=12)
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/error_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_confidence_analysis(df: pd.DataFrame, output_dir: str):
    """Plot confidence score analysis."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Confidence distribution by model
    for model in df['model_name'].unique():
        model_data = df[df['model_name'] == model]['confidence_score']
        ax1.hist(model_data, alpha=0.7, label=model, bins=20)
    
    ax1.set_title('Confidence Score Distribution by Model', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Confidence Score', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Plot 2: Confidence vs accuracy
    for model in df['model_name'].unique():
        model_data = df[df['model_name'] == model]
        correct_data = model_data[model_data['is_correct'] == True]['confidence_score']
        incorrect_data = model_data[model_data['is_correct'] == False]['confidence_score']
        
        ax2.hist(correct_data, alpha=0.7, label=f'{model} (Correct)', bins=15)
        ax2.hist(incorrect_data, alpha=0.7, label=f'{model} (Incorrect)', bins=15)
    
    ax2.set_title('Confidence Score: Correct vs Incorrect', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Confidence Score', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    # Plot 3: Average confidence by category
    category_confidence = df.groupby('primary_category')['confidence_score'].mean().sort_values(ascending=False)
    category_confidence.plot(kind='bar', ax=ax3, color='#98D8C8')
    ax3.set_title('Average Confidence by Primary Category', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Primary Category', fontsize=12)
    ax3.set_ylabel('Average Confidence Score', fontsize=12)
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(axis='y', alpha=0.3)
    
    # Plot 4: Confidence by violence level
    violence_confidence = df.groupby('violence_level')['confidence_score'].mean().sort_values(ascending=False)
    violence_confidence.plot(kind='bar', ax=ax4, color='#F7DC6F')
    ax4.set_title('Average Confidence by Violence Level', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Violence Level', fontsize=12)
    ax4.set_ylabel('Average Confidence Score', fontsize=12)
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/confidence_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_summary_table(df: pd.DataFrame, output_dir: str):
    """Create a summary table of all results."""
    summary_data = []
    
    for model in df['model_name'].unique():
        model_df = df[df['model_name'] == model]
        
        # Overall stats
        total = len(model_df)
        correct = model_df['is_correct'].sum()
        accuracy = correct / total * 100
        avg_confidence = model_df['confidence_score'].mean()
        
        # Error stats
        error_df = model_df[model_df['year_error'].notna()]
        avg_error = error_df['year_error'].mean() if not error_df.empty else None
        median_error = error_df['year_error'].median() if not error_df.empty else None
        
        summary_data.append({
            'Model': model,
            'Total Events': total,
            'Correct Predictions': correct,
            'Accuracy (%)': f"{accuracy:.1f}%",
            'Avg Confidence': f"{avg_confidence:.3f}",
            'Avg Year Error': f"{avg_error:.1f}" if avg_error else "N/A",
            'Median Year Error': f"{median_error:.1f}" if median_error else "N/A"
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Save to CSV
    summary_df.to_csv(f'{output_dir}/summary_table.csv', index=False)
    
    # Display as formatted table
    print("\n" + "="*80)
    print("SUMMARY TABLE")
    print("="*80)
    print(summary_df.to_string(index=False))
    
    return summary_df

def main():
    """Main function to create all plots and analysis."""
    print("Starting Results Analysis and Plotting")
    print("="*60)
    
    # Configuration
    output_dir = "output"
    
    # Load results
    results = load_results(output_dir)
    
    if not results:
        print("No results found. Please run serge_run_analysis.py first.")
        return
    
    # Convert to DataFrame
    df = create_dataframe(results)
    
    print(f"Loaded {len(df)} results from {df['model_name'].nunique()} models")
    
    # Create output directory for plots
    plots_dir = f"{output_dir}/plots"
    Path(plots_dir).mkdir(exist_ok=True)
    
    # Generate all plots and analysis
    print("\nGenerating plots and analysis...")
    
    # 1. Model comparison
    print("1. Creating model comparison plot...")
    plot_model_comparison(df, plots_dir)
    
    # 2. Category analysis
    categories = ['primary_category', 'violence_level', 'cultural_region', 'historical_period']
    for category in categories:
        print(f"2. Creating {category} analysis...")
        plot_category_analysis(df, category, plots_dir)
    
    # 3. Error analysis
    print("3. Creating error analysis...")
    plot_error_analysis(df, plots_dir)
    
    # 4. Confidence analysis
    print("4. Creating confidence analysis...")
    plot_confidence_analysis(df, plots_dir)
    
    # 5. Summary table
    print("5. Creating summary table...")
    summary_df = create_summary_table(df, output_dir)
    
    print(f"\nAll plots saved to {plots_dir}/")
    print(f"Summary table saved to {output_dir}/summary_table.csv")
    
    # Print some key insights
    print("\n" + "="*60)
    print("KEY INSIGHTS")
    print("="*60)
    
    # Best performing model
    best_model = summary_df.loc[summary_df['Accuracy (%)'].str.rstrip('%').astype(float).idxmax()]
    print(f"Best performing model: {best_model['Model']} ({best_model['Accuracy (%)']})")
    
    # Category with highest accuracy
    for category in categories:
        accuracy_df = calculate_accuracy_by_category(df, category)
        if not accuracy_df.empty:
            best_category = accuracy_df.loc[accuracy_df['accuracy'].idxmax()]
            print(f"Best {category}: {best_category['category']} ({best_category['accuracy']:.1f}%)")
    
    # Model with highest confidence
    model_confidence = df.groupby('model_name')['confidence_score'].mean().sort_values(ascending=False)
    most_confident = model_confidence.index[0]
    print(f"Most confident model: {most_confident} ({model_confidence.iloc[0]:.3f})")

if __name__ == "__main__":
    main()