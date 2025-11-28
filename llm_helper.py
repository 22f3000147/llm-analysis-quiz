"""LLM helper using OpenAI API."""
from openai import OpenAI
import logging
import json
import base64
from config import Config

logger = logging.getLogger(__name__)

class LLMHelper:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def analyze_quiz_question(self, question_text, context=None):
        try:
            system_prompt = """You are an expert data analyst and quiz solver. 
Analyze the given quiz question and provide:
1. The type of task (scraping, API call, data processing, analysis, visualization)
2. Required steps to solve it
3. Any URLs, file paths, or data sources mentioned
4. The expected answer format (boolean, number, string, base64, JSON)

Respond in JSON format with keys: task_type, steps, sources, answer_format, reasoning"""
            
            user_prompt = f"Question: {question_text}\n\n{f'Context: {context}' if context else ''}\n\nAnalyze this question and provide a structured plan to solve it."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"Quiz analysis: {analysis.get('task_type', 'unknown')}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing quiz: {str(e)}")
            raise
    
    def solve_with_data(self, question, data, data_description=""):
        try:
            system_prompt = """You are an expert data analyst. Given a question and data, provide the exact answer. Be precise and follow the required format."""
            user_prompt = f"Question: {question}\n\nData Description: {data_description}\n\nData:\n{str(data)[:5000]}\n\nProvide the exact answer to the question based on this data. Respond with ONLY the answer value, nothing else."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"LLM provided answer: {answer[:100]}")
            return answer
        except Exception as e:
            logger.error(f"Error solving with data: {str(e)}")
            raise
