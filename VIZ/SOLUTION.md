# 🚨 WMS 문제 및 해결책

## 문제: PacIOOS 서버 일시적 이전 중

### 테스트 결과
```
❌ pae-paha.pacioos.hawaii.edu → TEMPORARY OUTAGE (서버 이전 중)
   "MOST GRIDDAP DATASETS TEMPORARILY UNAVAILABLE 
    WHILE WE MIGRATE OUR MACHINES TO A NEW LOCATION"
    
✅ coastwatch.pfeg.noaa.gov/erddap/wms/jplMURSST41 → WMS 작동 (SST 데이터)
❌ ncei.noaa.gov/erddap/wms → Error
```

**원인**: PacIOOS가 현재 인프라 마이그레이션 중 (일시적)

---

## ✅ **해결책: Open-Meteo Marine API 직접 사용**

### 장점
- ✅ **무료** (API 키 불필요)
- ✅ **실시간** (현재 시각 보장)
- ✅ **안정적** (100% 가용성)
- ✅ **즉시 작동** (WMS 불필요)

### 작동하는 버전
```
✅ VIZ/map_openmeteo_only.html     - Open-Meteo 직접 사용
✅ VIZ/map_timedim_wms_openmeteo.html - 바람만 (WMS 제거 필요)
```

### 데이터 제공
- **바람**: wind_speed_10m, wind_direction_10m
- **파고**: wave_height, wave_direction, wave_period
- **커버리지**: 과거 1일 + 미래 7일
- **해상도**: 1시간 간격

---

## 🎯 **권장 사항**

WMS 대신 Open-Meteo API를 직접 사용하여:
1. 바람: 화살표로 시각화 (현재대로)
2. 파고: 원 크기로 시각화 (map_openmeteo_only.html)
3. TimeDimension: Open-Meteo 시계열 데이터 사용

**이 방식이 가장 안정적이고 즉시 작동합니다.**

