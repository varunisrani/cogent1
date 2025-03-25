"""
# OpenWeatherFetcher

## Description
A tool that integrates with the OpenWeather API to fetch current weather data based on city name or geographic coordinates.

## Usage
To use the `OpenWeatherFetcher`, create an instance by providing a location and your OpenWeather API key:

```python
weather_data = OpenWeatherFetcher(location='London', api_key='your_api_key')
```

Call the `fetch_weather` method to get the current weather data:

```python
current_weather = weather_data.fetch_weather()
print(current_weather)
```

## Dependencies
- `requests`: For making HTTP requests to the OpenWeather API.
- `cachetools`: For caching responses to reduce API calls.

## Caching
The `fetch_weather` method uses caching to store results for 5 minutes to improve performance and reduce the number of requests made to the OpenWeather API.
"""

import os
from typing import Dict, Any, List, Optional
import requests
import cachetools
import time

import requests
from cachetools import TTLCache, cached

class OpenWeatherFetcher:
    def __init__(self, location: str, api_key: str):
        self.location = location
        self.api_key = api_key
        self.cache = TTLCache(maxsize=100, ttl=300)  # Cache with a TTL of 5 minutes

    @cached(cache)
    def fetch_weather(self) -> dict:
        base_url = 'http://api.openweathermap.org/data/2.5/weather'
        params = {'q': self.location, 'appid': self.api_key, 'units': 'metric'}
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'conditions': data['weather'][0]['description']
            }
        else:
            error_message = ''
            if response.status_code == 404:
                error_message = 'City not found.'
            elif response.status_code == 401:
                error_message = 'Invalid API key.'
            else:
                error_message = 'An error occurred while fetching weather data.'
            raise Exception(error_message)

# Example usage
if __name__ == "__main__":
    # Example usage based on the specification
    print(f"Tool OpenWeatherFetcher loaded successfully")
    
    # Add example usage based on the specification
    example_usage = """weather_data = OpenWeatherFetcher(location='London', api_key='your_api_key').fetch_weather()"""
    print(f"Example usage: weather_data = OpenWeatherFetcher(location='London', api_key='your_api_key').fetch_weather()")

# Unit Tests
"""
import pytest
from unittest.mock import patch, MagicMock

class TestOpenWeatherFetcher:
    @patch('requests.get')
    def test_fetch_weather_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'weather': [{'description': 'clear sky'}], 'main': {'temp': 20, 'humidity': 70}}
        fetcher = OpenWeatherFetcher(location='London', api_key='dummy_key')
        weather_data = fetcher.fetch_weather()
        assert weather_data['conditions'] == 'clear sky'
        assert weather_data['temperature'] == 20
        assert weather_data['humidity'] == 70

    @patch('requests.get')
    def test_fetch_weather_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        fetcher = OpenWeatherFetcher(location='InvalidCity', api_key='dummy_key')
        with pytest.raises(Exception):
            fetcher.fetch_weather()
"""
