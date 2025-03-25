"""
# SVG Code Generator

This module provides functionality to generate SVG code based on a user's description using the OpenAI API.

## Function

### `generate_svg_code(description: str, api_key: str) -> str`

Generates SVG code based on the provided description.

#### Parameters:
- `description` (str): A description of the SVG graphic to generate.
- `api_key` (str): Your OpenAI API key.

#### Returns:
- `str`: The generated SVG code.

## Example Usage
```python
svg_code = generate_svg_code('A red circle with a blue border', 'your_openai_api_key')
print(svg_code)
```
"""

import os
from typing import Dict, Any, List, Optional
import openai

import openai

def generate_svg_code(description: str, api_key: str) -> str:
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': description}],
        max_tokens=100
    )
    svg_code = response['choices'][0]['message']['content']
    return svg_code

# Example usage:
# svg_code = generate_svg_code('A red circle with a blue border', 'your_openai_api_key')

# Example usage
if __name__ == "__main__":
    # Example usage based on the specification
    print(f"Tool SVG Code Generator loaded successfully")
    
    # Add example usage based on the specification
    example_usage = """svg_code = generate_svg_code('A red circle with a blue border', 'your_openai_api_key')"""
    print(f"Example usage: svg_code = generate_svg_code('A red circle with a blue border', 'your_openai_api_key')")

# Unit Tests
"""
import pytest

class TestSVGCodeGenerator:
    def test_generate_svg_code(self, mocker):
        mock_openai = mocker.patch('openai.ChatCompletion.create')
        mock_openai.return_value = {'choices': [{'message': {'content': '<svg><circle cx="50" cy="50" r="40" stroke="blue" stroke-width="4" fill="red" /></svg>'}}]}
        svg_code = generate_svg_code('A red circle with a blue border', 'fake_api_key')
        assert svg_code == '<svg><circle cx="50" cy="50" r="40" stroke="blue" stroke-width="4" fill="red" /></svg>'
    
    def test_invalid_api_key(self, mocker):
        mock_openai = mocker.patch('openai.ChatCompletion.create', side_effect=Exception('Invalid API key'))
        with pytest.raises(Exception):
            generate_svg_code('A red circle with a blue border', 'invalid_api_key')
"""
