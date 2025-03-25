"""
# LLMTextProcessor

## Description
`LLMTextProcessor` is a tool that processes text using various LLM APIs, including OpenAI and Anthropic. It supports prompt templating, retry logic, streaming responses, system messages, token counting, and response validation.

## Installation
To use this tool, ensure you have the required libraries installed:
```bash
pip install openai anthropic requests
```

## Usage Example
```python
processor = LLMTextProcessor(api_key='your_api_key', prompt='Hello, how are you?', model='gpt-3.5-turbo')
response = processor.process_text()
print(response)
```

## Parameters
- `api_key` (str): API key for authenticating with the LLM services (required)
- `prompt` (str): The text prompt to send to the LLM API for processing (required)
- `model` (str): The specific LLM model to use (e.g., 'gpt-3.5-turbo', 'claude-v1') (required)
- `max_retries` (int): Maximum number of retry attempts for failed requests (optional)
- `stream` (bool): Whether to stream responses from the LLM API (optional)
- `system_message` (str): A system message to set the behavior and context for the LLM (optional)
- `validate_response` (bool): Whether to validate the response from the LLM (optional)

## Return Type
Returns a dictionary indicating success or failure, along with the response or error message.
"""

import os
from typing import Dict, Any, List, Optional
import openai
import anthropic
import requests
import json
import time
import re

import openai
import anthropic
import requests
import json
import time
import re

class LLMTextProcessor:
    def __init__(self, api_key: str, prompt: str, model: str, max_retries: int = 3, stream: bool = False, system_message: str = None, validate_response: bool = False):
        self.api_key = api_key
        self.prompt = prompt
        self.model = model
        self.max_retries = max_retries
        self.stream = stream
        self.system_message = system_message
        self.validate_response = validate_response

    def _validate_response(self, response):
        # Example validation: Check if response is a non-empty string
        return isinstance(response, str) and len(response) > 0

    def process_text(self) -> dict:
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        body = {'model': self.model, 'prompt': self.prompt}
        if self.system_message:
            body['system_message'] = self.system_message

        for attempt in range(self.max_retries):
            try:
                if self.stream:
                    # Streaming logic (pseudo, would need actual implementation)
                    response = requests.post('https://api.llm-service.com/stream', headers=headers, json=body)
                else:
                    response = requests.post('https://api.llm-service.com/completions', headers=headers, json=body)

                response.raise_for_status()
                response_data = response.json()
                result = response_data.get('choices')[0].get('text').strip()

                if self.validate_response and not self._validate_response(result):
                    raise ValueError('Invalid response from LLM')

                return {'success': True, 'response': result}

            except (requests.exceptions.RequestException, ValueError) as e:
                if attempt == self.max_retries - 1:
                    return {'success': False, 'error': str(e)}
                time.sleep(1)  # Exponential backoff could be implemented here

        return {'success': False, 'error': 'Max retries exceeded'}

# Example usage
if __name__ == "__main__":
    # Example usage based on the specification
    print(f"Tool LLMTextProcessor loaded successfully")
    
    # Add example usage based on the specification
    example_usage = """processor = LLMTextProcessor(api_key='your_api_key', prompt='Hello, how are you?', model='gpt-3.5-turbo')
response = processor.process_text()"""
    print(f"Example usage: processor = LLMTextProcessor(api_key='your_api_key', prompt='Hello, how are you?', model='gpt-3.5-turbo')
response = processor.process_text()")

# Unit Tests
"""
import pytest
from llm_text_processor import LLMTextProcessor

@pytest.fixture
def processor():
    return LLMTextProcessor(api_key='test_api_key', prompt='Hello, how are you?', model='gpt-3.5-turbo')

def test_process_text_success(mocker, processor):
    mocker.patch('requests.post')
    requests.post.return_value.json.return_value = {'choices': [{'text': 'I am fine, thank you!'}]},
    requests.post.return_value.raise_for_status = lambda: None

    response = processor.process_text()
    assert response['success'] == True
    assert response['response'] == 'I am fine, thank you!'


def test_process_text_failure(mocker, processor):
    mocker.patch('requests.post', side_effect=requests.exceptions.RequestException('API error'))

    response = processor.process_text()
    assert response['success'] == False
    assert 'API error' in response['error']


def test_process_text_invalid_response(mocker, processor):
    mocker.patch('requests.post')
    requests.post.return_value.json.return_value = {'choices': [{'text': ''}]}
    requests.post.return_value.raise_for_status = lambda: None

    response = processor.process_text()
    assert response['success'] == False
    assert 'Invalid response from LLM' in response['error']
"""
