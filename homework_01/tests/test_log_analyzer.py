import pytest
import pandas as pd
from unittest.mock import mock_open, patch
from src.log_analyzer import parse_nginx_logs, analyze_response_times

def test_parse_nginx_logs():
    mock_log_data = (
        '127.0.0.1 - - [01/Jan/2023:00:00:01 +0000] "GET / HTTP/1.1" 200 0.123\n'
        '127.0.0.1 - - [01/Jan/2023:00:00:02 +0000] "GET /about HTTP/1.1" 200 0.456\n'
        '127.0.0.1 - - [01/Jan/2023:00:00:03 +0000] "GET /contact HTTP/1.1" 200 0.789\n'
        '127.0.0.1 - - [01/Jan/2023:00:00:04 +0000] "GET /error HTTP/1.1" 500\n'
    )
    
    with patch('builtins.open', mock_open(read_data=mock_log_data)):
        response_times = parse_nginx_logs('dummy_log_file.txt')
        expected_response_times = pd.Series([0.123, 0.456, 0.789])
        pd.testing.assert_series_equal(response_times, expected_response_times)

def test_analyze_response_times():
    response_times = pd.Series([0.123, 0.456, 0.789])
    analysis_results = analyze_response_times(response_times)
    
    assert analysis_results['mean'] == pytest.approx(0.456)
    assert analysis_results['median'] == 0.456
    assert analysis_results['max'] == 0.789
    assert analysis_results['min'] == 0.123