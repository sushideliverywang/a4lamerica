#!/usr/bin/env python3
"""
Address Validator using Google Maps API
This script validates addresses using Google Maps Geocoding API
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Tuple

class AddressValidator:
    def __init__(self, api_key: str):
        """
        Initialize the address validator with Google Maps API key
        
        Args:
            api_key (str): Google Maps API key
        """
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
    def validate_address(self, address: str) -> Dict:
        """
        Validate an address using Google Maps Geocoding API
        
        Args:
            address (str): The address to validate
            
        Returns:
            Dict: Validation result with status and details
        """
        try:
            # Prepare request parameters
            params = {
                'address': address,
                'key': self.api_key
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check API response status
            if data['status'] == 'OK':
                return self._parse_successful_response(data, address)
            else:
                return self._parse_error_response(data, address)
                
        except requests.exceptions.RequestException as e:
            return {
                'valid': False,
                'error': f'Network error: {str(e)}',
                'address': address,
                'suggestions': []
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Unexpected error: {str(e)}',
                'address': address,
                'suggestions': []
            }
    
    def _parse_successful_response(self, data: Dict, original_address: str) -> Dict:
        """
        Parse successful API response
        
        Args:
            data (Dict): API response data
            original_address (str): Original address that was validated
            
        Returns:
            Dict: Parsed validation result
        """
        results = data['results']
        
        if not results:
            return {
                'valid': False,
                'error': 'No results found',
                'address': original_address,
                'suggestions': []
            }
        
        # Get the best match (first result)
        best_result = results[0]
        
        # Extract address components
        formatted_address = best_result['formatted_address']
        location = best_result['geometry']['location']
        place_id = best_result['place_id']
        
        # Check if the result is exact match
        is_exact_match = formatted_address.lower() == original_address.lower()
        
        # Extract address components for detailed analysis
        address_components = self._extract_address_components(best_result['address_components'])
        
        # Generate suggestions if not exact match
        suggestions = []
        if not is_exact_match and len(results) > 1:
            suggestions = [result['formatted_address'] for result in results[1:4]]  # Top 3 alternatives
        
        return {
            'valid': True,
            'address': original_address,
            'formatted_address': formatted_address,
            'is_exact_match': is_exact_match,
            'location': {
                'lat': location['lat'],
                'lng': location['lng']
            },
            'place_id': place_id,
            'address_components': address_components,
            'suggestions': suggestions,
            'confidence': self._calculate_confidence(best_result)
        }
    
    def _parse_error_response(self, data: Dict, address: str) -> Dict:
        """
        Parse error API response
        
        Args:
            data (Dict): API response data
            address (str): Original address
            
        Returns:
            Dict: Error result
        """
        error_messages = {
            'ZERO_RESULTS': 'No results found for this address',
            'OVER_QUERY_LIMIT': 'API quota exceeded',
            'REQUEST_DENIED': 'API request denied - check API key',
            'INVALID_REQUEST': 'Invalid request parameters',
            'UNKNOWN_ERROR': 'Unknown error occurred'
        }
        
        error_msg = error_messages.get(data['status'], f'API error: {data["status"]}')
        
        return {
            'valid': False,
            'error': error_msg,
            'address': address,
            'suggestions': []
        }
    
    def _extract_address_components(self, components: List[Dict]) -> Dict:
        """
        Extract and organize address components
        
        Args:
            components (List[Dict]): Address components from API
            
        Returns:
            Dict: Organized address components
        """
        extracted = {}
        
        for component in components:
            types = component['types']
            long_name = component['long_name']
            short_name = component['short_name']
            
            if 'street_number' in types:
                extracted['street_number'] = long_name
            elif 'route' in types:
                extracted['street_name'] = long_name
            elif 'locality' in types:
                extracted['city'] = long_name
            elif 'administrative_area_level_1' in types:
                extracted['state'] = long_name
                extracted['state_code'] = short_name
            elif 'postal_code' in types:
                extracted['postal_code'] = long_name
            elif 'country' in types:
                extracted['country'] = long_name
                extracted['country_code'] = short_name
        
        return extracted
    
    def _calculate_confidence(self, result: Dict) -> str:
        """
        Calculate confidence level based on API result
        
        Args:
            result (Dict): API result
            
        Returns:
            str: Confidence level (high, medium, low)
        """
        # Check if result is exact match
        if result.get('partial_match', False):
            return 'low'
        
        # Check geometry type
        geometry_type = result['geometry']['location_type']
        if geometry_type == 'ROOFTOP':
            return 'high'
        elif geometry_type == 'RANGE_INTERPOLATED':
            return 'medium'
        else:
            return 'low'
    
    def batch_validate(self, addresses: List[str], delay: float = 0.1) -> List[Dict]:
        """
        Validate multiple addresses with rate limiting
        
        Args:
            addresses (List[str]): List of addresses to validate
            delay (float): Delay between requests in seconds
            
        Returns:
            List[Dict]: List of validation results
        """
        results = []
        
        for i, address in enumerate(addresses):
            print(f"Validating address {i+1}/{len(addresses)}: {address}")
            
            result = self.validate_address(address)
            results.append(result)
            
            # Add delay to avoid hitting rate limits
            if i < len(addresses) - 1:  # Don't delay after last request
                time.sleep(delay)
        
        return results

    def validate_address_legacy(self, address_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Legacy method for compatibility with existing code
        Returns (is_valid, standardized_address, error_message)
        
        Args:
            address_data (Dict): Address data with street_address, city, state, zip_code, country
            
        Returns:
            Tuple[bool, Dict, str]: (is_valid, standardized_address, error_message)
        """
        # Construct full address string
        address_parts = [
            address_data.get('street_address', ''),
            address_data.get('apartment_suite', ''),
            address_data.get('city', ''),
            address_data.get('state', ''),
            address_data.get('zip_code', ''),
            address_data.get('country', 'US')
        ]
        full_address = ', '.join([part for part in address_parts if part])
        
        # Validate using Google Maps API
        result = self.validate_address(full_address)
        
        if not result['valid']:
            return False, {}, result['error']
        
        # Extract address components
        components = result['address_components']
        
        # Build standardized address dict
        # Use state_code (2-letter) instead of state (full name) for database compatibility
        standardized_address = {
            'street_address': components.get('street_number', '') + ' ' + components.get('street_name', ''),
            'city': components.get('city', ''),
            'state': components.get('state_code', ''),  # Use 2-letter state code
            'zip_code': components.get('postal_code', ''),
            'country': components.get('country_code', 'US'),  # Use 2-letter country code
            'formatted_address': result['formatted_address'],
            'latitude': result['location']['lat'],
            'longitude': result['location']['lng']
        }
        
        return True, standardized_address, ""


def main():
    """
    Main function for testing the address validator
    """
    # Get API key from environment variable or use hardcoded one
    # Set environment variable: export GOOGLE_MAPS_API_KEY="your_api_key_here"
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if API_KEY == None:
        print("⚠️  Warning: Please set your Google Maps API key!")
        print("You can either:")
        print("1. Set environment variable: export GOOGLE_MAPS_API_KEY='your_key_here'")
        print("2. Or edit this file and replace 'YOUR_GOOGLE_MAPS_API_KEY_HERE' with your actual key")
        print("\nTo get an API key:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Geocoding API")
        print("4. Create credentials (API key)")
        return
    
    # Test addresses
    test_addresses = [
        "1600 Amphitheatre Parkway, Mountain View, CA",
        "123 Main Street, New York, NY",
        "Invalid Address That Should Fail",
        "1 Infinite Loop, Cupertino, CA"
    ]
    
    # Initialize validator
    validator = AddressValidator(API_KEY)
    
    print("=== Address Validation Test ===\n")
    
    # Test single address
    print("Testing single address validation:")
    result = validator.validate_address(test_addresses[0])
    print(json.dumps(result, indent=2))
    print("\n" + "="*50 + "\n")
    
    # Test batch validation
    print("Testing batch address validation:")
    results = validator.batch_validate(test_addresses[:2], delay=0.5)
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Address: {result['address']}")
        print(f"Valid: {result['valid']}")
        if result['valid']:
            print(f"Formatted: {result['formatted_address']}")
            print(f"Confidence: {result['confidence']}")
        else:
            print(f"Error: {result['error']}")
        print("-" * 30)


if __name__ == "__main__":
    main() 