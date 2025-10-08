#!/usr/bin/env python3
"""
통합 실행 스크립트: 해양 데이터 수집 + GIS 시각화
기존 weather_job.py 데이터를 VIZ 모듈로 시각화
"""
import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def extract_marine_data_to_csv(summary_json_path: str, output_csv: str):
    """
    weather_job.py의 summary JSON에서 해양 데이터를 추출하여 CSV로 변환
    """
    print(f"📊 데이터 추출 중: {summary_json_path}")
    
    with open(summary_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # AGI 좌표 (기본값)
    AGI_LAT = 24.843833
    AGI_LON = 53.655306
    
    rows = []
    
    # 분석 결과에서 평균값 추출
    analysis = data.get('analysis', {})
    averages = analysis.get('averages', {})
    
    # 현재 시간
    now = datetime.now().isoformat(timespec="seconds") + "Z"
    
    # 단일 데이터 포인트 생성 (평균값 기반)
    wind_speed_ms = averages.get('wind_speed_ms', 8.0)
    wave_height_m = averages.get('wave_height_m', 0.6)
    
    # 풍향은 남서풍 가정 (225도)
    wind_dir_deg = 225.0
    
    row = {
        'lat': AGI_LAT,
        'lon': AGI_LON,
        'time_iso': now,
        'wind_speed_ms': round(wind_speed_ms, 2),
        'wind_dir_deg': wind_dir_deg,
        'wave_height_m': round(wave_height_m, 2)
    }
    rows.append(row)
    
    # 주변 격자점 생성 (샘플링)
    import math
    for i in range(1, 9):
        r_km = i * 6.0
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            dlat = (r_km / 111.0) * math.cos(rad)
            dlon = (r_km / (111.0 * math.cos(math.radians(AGI_LAT)))) * math.sin(rad)
            
            lat = AGI_LAT + dlat
            lon = AGI_LON + dlon
            
            # 거리에 따라 값 변화
            factor = max(0.2, 1.0 - i / 9)
            spd = wind_speed_ms * factor
            hs = wave_height_m * factor
            wdir = (wind_dir_deg + deg) % 360
            
            rows.append({
                'lat': round(lat, 6),
                'lon': round(lon, 6),
                'time_iso': now,
                'wind_speed_ms': round(spd, 2),
                'wind_dir_deg': round(wdir, 1),
                'wave_height_m': round(hs, 2)
            })
    
    # CSV 저장
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['lat', 'lon', 'time_iso', 'wind_speed_ms', 'wind_dir_deg', 'wave_height_m'])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ CSV 생성 완료: {output_csv} ({len(rows)}개 포인트)")
    return output_csv


def main():
    import argparse
    import subprocess
    
    parser = argparse.ArgumentParser(description="통합 실행: 데이터 수집 + GIS 시각화")
    parser.add_argument("--location", default="AGI", help="위치 코드")
    parser.add_argument("--hours", type=int, default=24, help="예보 시간")
    parser.add_argument("--mode", default="auto", choices=['auto', 'online', 'offline'], help="실행 모드")
    parser.add_argument("--skip-collection", action="store_true", help="데이터 수집 건너뛰기 (기존 데이터 사용)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌊 통합 실행: 해양 데이터 수집 + GIS 시각화")
    print("=" * 60)
    
    # 1. 데이터 수집 (weather_job.py)
    if not args.skip_collection:
        print("\n📡 1단계: 해양 데이터 수집 중...")
        result = subprocess.run([
            sys.executable,
            "scripts/weather_job.py",
            "--location", args.location,
            "--hours", str(args.hours),
            "--mode", args.mode,
            "--out", "out"
        ], check=True)
        print("✅ 데이터 수집 완료")
    else:
        print("\n⏭️ 1단계: 데이터 수집 건너뜀 (기존 데이터 사용)")
    
    # 2. 최신 summary.json 찾기
    print("\n🔍 2단계: 최신 데이터 파일 검색 중...")
    out_dir = Path("out")
    summary_files = list(out_dir.glob("summary_*.json"))
    
    if not summary_files:
        print("❌ summary JSON 파일을 찾을 수 없습니다")
        return False
    
    latest_summary = max(summary_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ 최신 파일 발견: {latest_summary.name}")
    
    # 3. CSV 변환
    print("\n📊 3단계: CSV 형식으로 변환 중...")
    csv_path = "out/marine_data.csv"
    extract_marine_data_to_csv(str(latest_summary), csv_path)
    
    # 4. GeoJSON 생성 (Open-Meteo API 실시간 호출)
    print("\n🗺️ 4단계: GeoJSON 생성 중 (실시간 API)...")
    subprocess.run([
        sys.executable,
        "VIZ/src/marine_ops/viz/adapter.py",
        "--out", "out/wind_uv.geojson",
        "--site", args.location,
        "--hours", "72",
        "--radius_km", "30"
    ], check=True)
    
    # 5. Leaflet 지도 생성
    print("\n🌐 5단계: Leaflet 지도 HTML 생성 중...")
    subprocess.run([
        sys.executable,
        "VIZ/src/marine_ops/viz/map_leaflet.py",
        "--geo", "out/wind_uv.geojson",
        "--out", "out/map_leaflet.html",
        "--site", args.location
    ], check=True)
    
    # 6. 스크린샷 생성 (Playwright 설치 확인)
    print("\n📸 6단계: 지도 스크린샷 생성 시도...")
    try:
        subprocess.run([
            sys.executable,
            "VIZ/src/marine_ops/viz/screenshot.py",
            "--html", "out/map_leaflet.html",
            "--png", "out/map_leaflet.png"
        ], check=True)
        print("✅ 스크린샷 생성 완료")
    except subprocess.CalledProcessError:
        print("⚠️ 스크린샷 생성 실패 (Playwright 미설치 가능)")
        print("   설치: python -m playwright install chromium")
    
    # 7. 결과 요약
    print("\n" + "=" * 60)
    print("🎉 통합 실행 완료!")
    print("=" * 60)
    print(f"\n📁 출력 파일:")
    print(f"  - 데이터: out/{latest_summary.name}")
    print(f"  - CSV: {csv_path}")
    print(f"  - GeoJSON: out/wind_uv.geojson")
    print(f"  - 지도: out/map_leaflet.html")
    if Path("out/map_leaflet.png").exists():
        print(f"  - 스크린샷: out/map_leaflet.png")
    
    print(f"\n🌐 브라우저에서 열기:")
    print(f"  start out/map_leaflet.html")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

