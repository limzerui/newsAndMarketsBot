"""
News Summarizer

This module handles the summarization of financial news using AI models.
It primarily uses OpenAI API.
"""

import json
import openai
from loguru import logger

from config.settings import OPENAI_API_KEY

class Summarizer:
    """Summarizes financial news and identifies potential stock impacts."""
    
    def __init__(self, use_openai=True):
        """
        Initialize the summarizer.
        """
        if not OPENAI_API_KEY:
            raise ValueError("No API key available for OpenAI")
        
        # Set API keys
        self.api_key = OPENAI_API_KEY
        openai.api_key = OPENAI_API_KEY
        logger.info("Using OpenAI for summarization")
    
    def summarize(self, messages):
        """
        Summarize a batch of messages and identify potentially impacted stocks.
        
        Args:
            messages (list): List of message objects with text content
            
        Returns:
            dict: Summary information including affected stocks
        """
        if not messages:
            logger.warning("No messages to summarize")
            return None
        
        # Compile message texts
        message_texts = [msg["text"] for msg in messages]
        combined_text = "\n\n---\n\n".join(message_texts)
        
        prompt = f"""
        You are a financial analyst assistant. Summarize the following financial news updates
        and identify potentially impacted stocks or market sectors.

        Format your response as JSON with the following structure:
        {{
            "summary": "Brief 2-3 sentence summary of key points",
            "potentially_impacted_stocks": ["TICKER1", "TICKER2"],
            "market_sectors": ["Sector1", "Sector2"],
            "sentiment": "bullish/bearish/neutral",
            "key_points": ["Point 1", "Point 2", "Point 3"]
        }}

        News updates to analyze:
        {combined_text}
        """
        
        try:
            return self._openai_summarize(prompt)
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            return {
                "summary": "Error generating summary",
                "potentially_impacted_stocks": [],
                "market_sectors": [],
                "sentiment": "neutral",
                "key_points": ["Failed to analyze news due to an error"]
            }
    
    def _openai_summarize(self, prompt):
        """Use OpenAI to generate a summary."""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        result = response.choices[0].message.content
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from OpenAI response")
            return {
                "summary": result[:200] + "...",
                "potentially_impacted_stocks": [],
                "market_sectors": [],
                "sentiment": "neutral",
                "key_points": ["Error: Unable to parse structured data"]
            } 