# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "numpy",
#   "matplotlib",
#   "seaborn",
#   "openai==0.28",
#   "chardet"
# ]
# ///

import os
import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import openai
import chardet

# Setup OpenAI API Key
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"
openai.api_key = os.getenv("AIPROXY_TOKEN")

def detect_and_convert_to_utf8(file_path):
    """Detects encoding and converts the file to UTF-8."""
    try:
        # Detect encoding
        with open(file_path, "rb") as file:
            result = chardet.detect(file.read())
        encoding = result['encoding']
        print(f"Detected encoding: {encoding}")
        
        # Read the file with detected encoding
        df = pd.read_csv(file_path, encoding=encoding)
        
        # Define new UTF-8 output file path
        base, ext = os.path.splitext(file_path)
        utf8_file_path = f"{base}_utf8{ext}"
        
        # Save the file in UTF-8 encoding
        df.to_csv(utf8_file_path, index=False, encoding="utf-8")
        print(f"File converted to UTF-8: {utf8_file_path}")
        return utf8_file_path
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        sys.exit(1)

def load_dataset(file_path):
    """Load the dataset after converting it to UTF-8."""
    try:
        # Convert file to UTF-8 if necessary
        utf8_file_path = detect_and_convert_to_utf8(file_path)
        return pd.read_csv(utf8_file_path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

def analyze_data(df):
    """Perform generic analysis on the dataset."""
    numeric_df = df.select_dtypes(include=[np.number])

    analysis = {
        "shape": df.shape,
        "columns": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary": df.describe(include="all").to_dict(),
        "correlation_matrix": numeric_df.corr().to_dict() if not numeric_df.select_dtypes(include=[np.number]).empty else {}
    }
    return analysis

def generate_visualizations(df, output_dir):
    """Create visualizations and save as PNG files."""
    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists
    files = []

    # Filter only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        # Correlation heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", cbar=True)
        plt.title("Correlation Heatmap")
        heatmap_file = os.path.join(output_dir, "correlation_heatmap.png")
        plt.savefig(heatmap_file)
        plt.close()
        files.append(heatmap_file)
    else:
        print("No numeric data available for creating a correlation heatmap.")

    return files

def ask_llm(prompt):
    """Ask GPT-4o-Mini for insights."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"Error interacting with LLM: {e}")
        sys.exit(1)

def write_readme(output_dir, analysis, insights, visualization_files):
    """Write the README.md file with results."""
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write("# Analysis Report\n\n")
        f.write("## Dataset Overview\n")
        f.write(f"**Shape:** {analysis['shape']}\n\n")
        f.write("**Columns and Data Types:**\n")
        for col, dtype in analysis['columns'].items():
            f.write(f"- {col}: {dtype}\n")
        f.write("\n## Missing Values\n")
        for col, missing in analysis['missing_values'].items():
            f.write(f"- {col}: {missing}\n")
        f.write("\n## Summary Statistics\n")
        f.write("```text\n")
        f.write(str(pd.DataFrame(analysis['summary'])))
        f.write("\n```\n\n")
        f.write("## Insights from LLM\n")
        f.write(insights + "\n\n")
        if visualization_files:
            f.write("## Visualizations\n")
            for file in visualization_files:
                f.write(f"![Visualization]({file})\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    file_path = sys.argv[1]
    output_dir = os.path.splitext(file_path)[0]

    # Load dataset
    df = load_dataset(file_path)

    # Analyze dataset
    analysis = analyze_data(df)

    # Prompt LLM for insights
    prompt = (
        f"Analyze the dataset with shape {analysis['shape']} and columns {list(analysis['columns'].keys())}. "
        "Provide an overview, insights, and possible actions."
    )
    insights = ask_llm(prompt)

    # Generate visualizations
    visualizations = generate_visualizations(df, output_dir)

    # Write README.md
    write_readme(output_dir, analysis, insights, visualizations)

    print(f"Analysis completed. Results saved in {output_dir}")

if __name__ == "__main__":
    main()
