# KR: 단위 변환 유틸리티
# EN: Unit conversion utilities

from typing import Dict, Any

def kt_to_ms(knots: float) -> float:
    """노트를 m/s로 변환"""
    return knots * 0.514444

def ms_to_kt(ms: float) -> float:
    """m/s를 노트로 변환"""
    return ms / 0.514444

def ft_to_m(feet: float) -> float:
    """피트를 미터로 변환"""
    return feet * 0.3048

def m_to_ft(meters: float) -> float:
    """미터를 피트로 변환"""
    return meters / 0.3048

def mph_to_ms(mph: float) -> float:
    """마일/시를 m/s로 변환"""
    return mph * 0.44704

def celsius_to_fahrenheit(c: float) -> float:
    """섭씨를 화씨로 변환"""
    return (c * 9/5) + 32

def fahrenheit_to_celsius(f: float) -> float:
    """화씨를 섭씨로 변환"""
    return (f - 32) * 5/9

def normalize_to_si(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """데이터를 SI 단위로 정규화"""
    normalized = data.copy()
    
    # 풍속 변환
    if 'wind_speed' in normalized and normalized['wind_speed'] is not None:
        wind_unit = data.get('wind_unit', 'ms')  # 기본값: m/s
        if wind_unit == 'kt':
            normalized['wind_speed'] = kt_to_ms(normalized['wind_speed'])
        elif wind_unit == 'mph':
            normalized['wind_speed'] = mph_to_ms(normalized['wind_speed'])
        # wind_unit이 'ms'이거나 없으면 그대로 유지
    
    # 돌풍 변환
    if 'wind_gust' in normalized and normalized['wind_gust'] is not None:
        wind_unit = data.get('wind_unit', 'ms')
        if wind_unit == 'kt':
            normalized['wind_gust'] = kt_to_ms(normalized['wind_gust'])
        elif wind_unit == 'mph':
            normalized['wind_gust'] = mph_to_ms(normalized['wind_gust'])
    
    # 파고 변환
    if 'wave_height' in normalized and normalized['wave_height'] is not None:
        wave_unit = data.get('wave_unit', 'm')  # 기본값: 미터
        if wave_unit == 'ft':
            normalized['wave_height'] = ft_to_m(normalized['wave_height'])
    
    # 온도 변환
    if 'temperature' in normalized and normalized['temperature'] is not None:
        temp_unit = data.get('temp_unit', 'c')
        if temp_unit == 'f':
            normalized['temperature'] = fahrenheit_to_celsius(normalized['temperature'])
    
    # 단위 정보 제거
    normalized.pop('wind_unit', None)
    normalized.pop('wave_unit', None)
    normalized.pop('temp_unit', None)
    
    return normalized

def convert_wind_direction(degrees: float) -> str:
    """풍향을 방향명으로 변환"""
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    index = round(degrees / 22.5) % 16
    return directions[index]

def calculate_sea_state(wave_height: float) -> str:
    """파고를 바다 상태로 변환 (Douglas Sea Scale)"""
    if wave_height < 0.1:
        return "Calm (Glassy)"
    elif wave_height < 0.5:
        return "Calm (Ripples)"
    elif wave_height < 1.0:
        return "Smooth"
    elif wave_height < 1.5:
        return "Slight"
    elif wave_height < 2.5:
        return "Moderate"
    elif wave_height < 4.0:
        return "Rough"
    elif wave_height < 6.0:
        return "Very Rough"
    elif wave_height < 9.0:
        return "High"
    else:
        return "Very High"
