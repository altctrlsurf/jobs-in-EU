from base.utils import auto_map_countries


test_mapping_input_output = [[[{
    "country": "Remote-US",
    "city": "San Francisco",
    "state": "California",
    "is_remote": False}], 
    [{
    "country": "United States",
    "city": "San Francisco",
    "state": "California",
    "is_remote": False}]]]

@auto_map_countries
def call_mapping(data):
    return data

def test_mapping():
    for input, output in test_mapping_input_output:
        assert call_mapping(input) == output