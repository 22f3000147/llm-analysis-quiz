"""Core quiz solving logic."""
import logging
import re
import json
import requests
from time import time, sleep
import traceback

from config import Config
from browser_helper import BrowserHelper
from llm_helper import LLMHelper
from data_processor import DataProcessor

logger = logging.getLogger(__name__)

class QuizSolver:
    def __init__(self):
        self.llm = LLMHelper()
        self.data_processor = DataProcessor()
        self.start_time = None
    
    def solve_quiz_chain(self, initial_url, email, secret):
        self.start_time = time()
        current_url = initial_url
        attempt = 1
        
        logger.info(f"Starting quiz chain from: {initial_url}")
        
        while current_url:
            elapsed = time() - self.start_time
            remaining = Config.QUIZ_TIMEOUT - elapsed
            
            if remaining <= 0:
                logger.warning("Quiz timeout reached")
                break
            
            logger.info(f"Attempt {attempt} - Time remaining: {remaining:.1f}s")
            
            try:
                result = self.solve_single_quiz(current_url, email, secret)
                
                if result and result.get('correct'):
                    logger.info("✓ Correct answer!")
                    current_url = result.get('url')
                    if not current_url:
                        logger.info("Quiz chain completed!")
                        break
                else:
                    logger.warning(f"✗ Incorrect: {result.get('reason', 'Unknown')}")
                    next_url = result.get('url')
                    if next_url and next_url != current_url:
                        current_url = next_url
                    else:
                        sleep(1)
                
                attempt += 1
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                break
        
        logger.info(f"Total time: {time() - self.start_time:.2f}s")
    
    def solve_single_quiz(self, quiz_url, email, secret):
        try:
            with BrowserHelper() as browser:
                page_content = browser.get_rendered_content(quiz_url)
            
            question_text = page_content['text']
            logger.info(f"Question: {question_text[:300]}")
            
            analysis = self.llm.analyze_quiz_question(question_text)
            submit_url = self.extract_submit_url(question_text)
            
            if not submit_url:
                logger.error("No submission URL found")
                return None
            
            answer = self.process_task(question_text, analysis, page_content)
            logger.info(f"Answer: {answer}")
            
            return self.submit_answer(submit_url, email, secret, quiz_url, answer)
        except Exception as e:
            logger.error(f"Error solving quiz: {str(e)}")
            return None
    
    def extract_submit_url(self, text):
        patterns = [
            r'https?://[^\s<>"]+/submit[^\s<>"]*',
            r'Post your answer to ([https?://[^\s]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if 'Post' in pattern else match.group(0)
        return None
    
    def extract_file_url(self, text):
        patterns = [
            r'href=["\'"]([^"\'>]+\.(?:pdf|csv|xlsx?|json|txt))["\'"]',
            r'https?://[^\s<>"]+\.(?:pdf|csv|xlsx?|json|txt)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if 'href' in pattern else match.group(0)
        return None
    
    def process_task(self, question_text, analysis, page_content):
        file_url = self.extract_file_url(question_text)
        
        if file_url:
            return self.handle_file_task(file_url, question_text)
        else:
            return self.llm.solve_with_data(question_text, analysis, "Question analysis")
    
    def handle_file_task(self, file_url, question_text):
        try:
            file_path = self.data_processor.download_file(file_url)
            
            if file_path.endswith('.pdf'):
                data = self.data_processor.read_pdf(file_path)
                return self.llm.solve_with_data(question_text, data, "PDF content")
            elif file_path.endswith('.csv'):
                df = self.data_processor.read_csv(file_path)
                data_info = self.data_processor.analyze_dataframe(df, question_text)
                return self.llm.solve_with_data(question_text, data_info, f"CSV: {df.shape}")
            elif file_path.endswith(('.xlsx', '.xls')):
                sheets = self.data_processor.read_excel(file_path)
                data_info = {s: self.data_processor.analyze_dataframe(df, question_text) for s, df in sheets.items()}
                return self.llm.solve_with_data(question_text, data_info, "Excel")
            else:
                with open(file_path, 'r') as f:
                    data = f.read()
                return self.llm.solve_with_data(question_text, data, "File content")
        except Exception as e:
            logger.error(f"Error handling file: {str(e)}")
            raise
    
    def submit_answer(self, submit_url, email, secret, quiz_url, answer):
        try:
            payload = {
                'email': email,
                'secret': secret,
                'url': quiz_url,
                'answer': self.format_answer(answer)
            }
            
            logger.info(f"Submitting to: {submit_url}")
            response = requests.post(submit_url, json=payload, timeout=Config.REQUEST_TIMEOUT, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error submitting: {str(e)}")
            raise
    
    def format_answer(self, answer):
        if isinstance(answer, str):
            try:
                if '.' in answer:
                    return float(answer)
                return int(answer)
            except ValueError:
                pass
            if answer.lower() in ['true', 'false']:
                return answer.lower() == 'true'
            try:
                return json.loads(answer)
            except:
                pass
        return answer
