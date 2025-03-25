"""
# CrewAI Search and Scrape Tool

## Description
This tool integrates with the Serper API to retrieve search results and the Webscraper API to scrape content from those results, then generates a PDF file containing the scraped content.

## Parameters
- **search_query** (str): The query string to search for.
- **num_results** (int): The number of search results to retrieve.
- **scrape_config** (dict): The configuration for scraping the content from each result.
- **output_file_path** (str): The file path where the output PDF will be saved.

## Returns
- Returns the file path of the generated PDF as a string.

## Example Usage
```python
results = crewai_search_and_scrape_tool(search_query='OpenAI', num_results=5, scrape_config=my_scrape_config, output_file_path='output.pdf')
```
"""

import os
from typing import Dict, Any, List, Optional
import requests
import pdfkit
import json

import requests
import pdfkit
import json

def crewai_search_and_scrape_tool(search_query: str, num_results: int, scrape_config: dict, output_file_path: str) -> str:
    # Step 1: Search using Serper API
    serper_api_url = 'https://api.serper.dev/search'
    serper_api_key = 'YOUR_SERPER_API_KEY'
    headers = {'Authorization': f'Bearer {serper_api_key}'}
    params = {'q': search_query, 'num_results': num_results}
    response = requests.get(serper_api_url, headers=headers, params=params)
    search_results = response.json().get('results', [])

    # Step 2: Scrape each result using Webscraper API
    webscraper_api_url = 'https://api.webscraper.io/scrape'
    scraped_contents = []
    for result in search_results:
        scrape_response = requests.post(webscraper_api_url, json={
            'url': result['link'],
            'config': scrape_config
        })
        scraped_contents.append(scrape_response.json())

    # Step 3: Generate PDF from scraped contents
    pdf_content = '\n'.join([json.dumps(content, indent=4) for content in scraped_contents])
    pdfkit.from_string(pdf_content, output_file_path)

    return output_file_path


# Example usage
if __name__ == "__main__":
    # Example usage based on the specification
    print(f"Tool CrewAI Search and Scrape Tool loaded successfully")
    
    # Add example usage based on the specification
    example_usage = """results = crewai_search_and_scrape_tool(search_query='OpenAI', num_results=5, scrape_config=my_scrape_config, output_file_path='output.pdf')"""
    print(f"Example usage: results = crewai_search_and_scrape_tool(search_query='OpenAI', num_results=5, scrape_config=my_scrape_config, output_file_path='output.pdf')")

# Unit Tests
"""
import pytest
from your_module import crewai_search_and_scrape_tool

@pytest.fixture
def mock_requests(mocker):
    mock_search_response = {'results': [{'link': 'http://example.com'}]}
    mock_scrape_response = {'data': 'scraped content'}
    mocker.patch('requests.get', return_value=mocker.Mock(json=lambda: mock_search_response))
    mocker.patch('requests.post', return_value=mocker.Mock(json=lambda: mock_scrape_response))

def test_crewai_search_and_scrape_tool(mock_requests):
    search_query = 'OpenAI'
    num_results = 1
    scrape_config = {'selector': 'div.content'}
    output_file_path = 'output.pdf'
    result = crewai_search_and_scrape_tool(search_query, num_results, scrape_config, output_file_path)
    assert result == output_file_path
"""
