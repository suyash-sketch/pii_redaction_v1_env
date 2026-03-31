"""
Inference Script Example
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    
- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables
"""

from ast import mod
import asyncio
import os
import re
import base64
import textwrap
from io import BytesIO
from typing import List, Optional, Dict
import json
from openai import OpenAI, AsyncOpenAI
import numpy as np
from PIL import Image

from pii_redaction_v1 import PiiRedactionV1Action, PiiRedactionV1Env
from dotenv import load_dotenv
load_dotenv()

# 1. READ THE MANDATORY ENVIRONMENT VARIABLES
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
OPENAI_API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

# 2. INITIALIZE THE OPENAI CLIENT USING THE INJECTED CREDENTIALS
llm_client = AsyncOpenAI(
    # base_url=API_BASE_URL,
    # api_key=OPENAI_API_KEY
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


async def evaluate_task(env : PiiRedactionV1Env, task_name : str):
    """Runs the LLM against a specific task queue."""

    result = await env.reset(task_name=task_name)
    obs = result.observation
    done = result.done
    total_reward = 0.0
    
    print(f"\n--- Starting Task: {task_name.upper()} ---")

    while not done:
        # Construct the prompt using the environment's observation
        prompt = f"""
        You are a Data Privacy Compliance Agent.
        Rules: {obs.active_rules}
        
        Ticket Content:
        {obs.ticket_content}
        
        Currently Applied Redactions: {obs.applied_redactions}
        
        Identify ONE exact string of text to redact based on the rules. 
        If you have found all PII, respond with the command "SubmitTicket" and an empty string.
        Respond ONLY with a valid JSON in this exact format:
        {{"command": "Redact" or "SubmitTicket", "text_to_redact": "exact text here"}}
        """

        try:
            # 1. Call the LLM
            response = await llm_client.chat.completions.create(
                # model=MODEL_NAME,
                model="qwen2.5-coder:7b",
                # model="llama3.2:1b",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            # 2. Extract the text response
            raw_content = response.choices[0].message.content.strip()

            # 3. Clean the response (LLMs sometimes wrap JSON in markdown blocks like ```json )
            if raw_content.startswith("```json"):
                raw_content = raw_content.replace("```json", "").replace("```", "").strip()
            elif raw_content.startswith("```"):
                raw_content = raw_content.replace("```", "").strip()

            # 4. Parse the JSON
            parsed_json = json.loads(raw_content)

            # --- NEW: Sanitize the LLM's command casing ---
            raw_command = str(parsed_json.get("command", "SubmitTicket")).strip().lower()
            
            if raw_command == "redact":
                safe_command = "Redact"
            else:
                safe_command = "SubmitTicket" # Default fallback

            # 5. Create the action using the sanitized command
            action = PiiRedactionV1Action(
                command=safe_command,
                text_to_redact=parsed_json.get("text_to_redact", "")
            )
            
            # 6. STEP THE ENVIRONMENT WITH THE LLM'S ACTION
            result = await env.step(action)
            obs = result.observation
            done = result.done
            
            # Note: We ONLY add the reward when the LLM submits the ticket, 
            # to avoid double-counting intermediate steps.
            if action.command == "SubmitTicket":
                total_reward += result.reward

        except json.JSONDecodeError:
            print(f"Failed to parse JSON from LLM: {raw_content}")
            # Force a submit to prevent infinite loops if the LLM breaks
            result = await env.step(PiiRedactionV1Action(command="SubmitTicket"))
            obs = result.observation
            done = result.done
            total_reward += result.reward
            
        

    print(f"Final score for {task_name} : {total_reward}")


async def main():
    env = PiiRedactionV1Env(base_url="http://localhost:8000")

    try:
        await evaluate_task(env, "hard")
        await evaluate_task(env, "medium")
        await evaluate_task(env, "easy")
    finally:
        await env.close()
    

if __name__ == "__main__":
    asyncio.run(main())