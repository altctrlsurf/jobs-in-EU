import os
import importlib
import concurrent.futures
from base.config import logger
import sys

import os
import glob
import pandas as pd
from xml.sax.saxutils import escape

def execute_scraper(module_path):
    """Dynamically imports and runs the 'run' function of a scraper module."""
    try:
        logger.info(f"Loading module: {module_path}")
        module = importlib.import_module(module_path)
        
        if hasattr(module, 'run'):
            module.run()
        else:
            logger.error(f"No 'run()' function found in {module_path}")
            
    except Exception as e:
        logger.error(f"Critical error executing {module_path}: {e}")

def main(run_folder = None):
    logger.info("--- Starting Global Scraper Orchestrator ---")
    
    companies_dir = 'companies'
    scraper_modules = []

    # 1. Dynamically discover all scrapers
    for folder_name in os.listdir(companies_dir):

        if run_folder and folder_name != run_folder:
            continue

        folder_path = os.path.join(companies_dir, folder_name)
        
        # Ignore __pycache__, __init__.py, etc.
        if os.path.isdir(folder_path) and not folder_name.startswith('__'):
            scrape_file = os.path.join(folder_path, 'scrape.py')
            
            if os.path.exists(scrape_file):
                # Convert path to Python module syntax (e.g., companies.Greenhouse.scrape)
                module_path = f"{companies_dir}.{folder_name}.scrape"
                scraper_modules.append(module_path)

    logger.info(f"Found {len(scraper_modules)} scrapers to run.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(execute_scraper, scraper_modules)

    logger.info("--- All scraping tasks completed ---")


def process_csv_to_xml():
    # Define base directories
    base_dir = os.getcwd()
    output_dir = os.path.join(base_dir, 'output')
    latest_output_dir = os.path.join(base_dir, 'latest_output')

    # 1. Check if output folder exists
    if not os.path.exists(output_dir):
        logger.info(f"Error: The folder '{output_dir}' does not exist.")
        return

    # 2. Find the latest created folder inside 'output'
    subfolders = [f.path for f in os.scandir(output_dir) if f.is_dir()]
    if not subfolders:
        logger.info(f"No subfolders found inside '{output_dir}'.")
        return
    
    # Get the latest folder based on modification/creation time
    latest_folder = max(subfolders, key=os.path.getmtime)
    logger.info(f"Latest folder found: {latest_folder}")

    # 3. Find all .csv files inside every folder of the latest_folder
    # Pattern: latest_folder/*/*.csv
    csv_pattern = os.path.join(latest_folder, '*', '*.csv')
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        logger.info(f"No CSV files found in the subdirectories of '{latest_folder}'.")
        return

    # 4. Merge all CSV files
    logger.info(f"Found {len(csv_files)} CSV files. Merging...")
    df_list = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df_list.append(df)
        except Exception as e:
            logger.info(f"Could not read {file}: {e}")

    if not df_list:
        logger.info("No valid data could be extracted from the CSV files.")
        return

    df = pd.concat(df_list, ignore_index=True)
    df_filtered = df[~df['job_title'].str.contains('apply for future', case=False, na=False)]

    # 5. Create 'latest_output' folder if it doesn't exist
    os.makedirs(latest_output_dir, exist_ok=True)

    # 6. Save merged CSV as latest.csv
    csv_output_path = os.path.join(latest_output_dir, 'latest.csv')
    df_filtered.to_csv(csv_output_path, index=False)
    logger.info(f"Merged CSV saved to: {csv_output_path}")

    # 7. Convert to XML with CDATA for 'job_description'
    xml_output_path = os.path.join(latest_output_dir, 'latest.xml')
    
    logger.info("Converting to XML...")
    with open(xml_output_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        folder_name = os.path.basename(latest_folder)
        xml_file.write(f'<jobs file_date={folder_name}>\n')
        
        # Iterate through dataframe rows
        for _, row in df_filtered.iterrows():
            xml_file.write('  <job>\n')
            
            for col_name in df_filtered.columns:
                # Sanitize column name for XML tag (replace spaces with underscores)
                safe_col_name = str(col_name).strip().replace(' ', '_').replace('&', 'and')
                
                # Get value, handle NaN/Null values
                val = row[col_name]
                val = "" if pd.isna(val) else str(val)
                
                # Apply CDATA specifically to job_description
                if col_name == 'job_description':
                    # Ensure we don't break CDATA if the text itself contains ']]>'
                    val = val.replace(']]>', ']]]]><![CDATA[>')
                    xml_file.write(f'    <{safe_col_name}><![CDATA[{val}]]></{safe_col_name}>\n')
                else:
                    # Escape standard XML characters (<, >, &) for normal columns
                    safe_val = escape(val)
                    xml_file.write(f'    <{safe_col_name}>{safe_val}</{safe_col_name}>\n')
                    
            xml_file.write('  </job>\n')
            
        xml_file.write('</jobs>\n')

    logger.info(f"XML file successfully saved to: {xml_output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
    try:
        process_csv_to_xml()
    except Exception as e:
        logger.exception(f'{e}')