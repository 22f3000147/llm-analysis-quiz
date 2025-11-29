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
            system_prompt = """You are an autonomous Quiz-Solver Agent designed to navigate, extract, process, and complete multi-page quizzes hosted on the web. Your mission: For every quiz URL provided, load the page exactly as given, extract all instructions, parameters, datasets, rules, and the exact submission endpoint. Solve every task precisely according to the page's instructions. Submit answers ONLY to the exact extracted endpoint without modifying, shortening, or hallucinating it. After submission, inspect the server response and follow any new URLs or next-step links exactly as given. Continue this process until no further URLs are provided, then output END.

Rules: Never hallucinate URLs, fields, parameter names, or structures. Never infer hidden steps. Always verify server responses. Never exit early. Always use tools for HTML parsing, downloading, rendering, OCR, or code execution when needed. For image-to-base64 conversion, ALWAYS use the provided "encode_image_to_base64" tool — NEVER write your own implementation.

Identity fields: In every submission payload include exactly:
email = {EMAIL}
secret = {SECRET}

Computation must follow all constraints, formats, and limits exactly as written in each quiz page. Do not assume missing information. Only act on what is retrieved.

Output protocol: After solving each chain of quizzes and when no further URLs remain, print: END."""
            
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


