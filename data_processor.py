"""Data processing utilities."""
import pandas as pd
import numpy as np
import json
import base64
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import pdfplumber
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config import Config

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.temp_dir = Path(Config.TEMP_DIR)
        self.temp_dir.mkdir(exist_ok=True)
    
    def download_file(self, url, filename=None):
        try:
            logger.info(f"Downloading file from: {url}")
            response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            if not filename:
                if 'Content-Disposition' in response.headers:
                    filename = response.headers['Content-Disposition'].split('filename=')[1].strip('"')
                else:
                    filename = url.split('/')[-1].split('?')[0] or 'downloaded_file'
            
            file_path = self.temp_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"File downloaded to: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise
    
    def read_pdf(self, file_path):
        try:
            result = {'text': {}, 'tables': {}}
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    result['text'][f'page_{i}'] = page.extract_text()
                    tables = page.extract_tables()
                    if tables:
                        result['tables'][f'page_{i}'] = []
                        for table in tables:
                            if table:
                                df = pd.DataFrame(table[1:], columns=table[0])
                                result['tables'][f'page_{i}'].append(df)
            logger.info(f"Extracted {len(result['text'])} pages from PDF")
            return result
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            raise
    
    def read_csv(self, file_path):
        df = pd.read_csv(file_path)
        logger.info(f"Read CSV with shape: {df.shape}")
        return df
    
    def read_excel(self, file_path):
        excel_data = pd.read_excel(file_path, sheet_name=None)
        logger.info(f"Read {len(excel_data)} sheets from Excel")
        return excel_data
    
    def analyze_dataframe(self, df, question):
        info = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'describe': df.describe().to_dict(),
            'head': df.head().to_dict(),
            'sum': {col: df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else None for col in df.columns}
        }
        return info
