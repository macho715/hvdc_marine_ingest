#!/usr/bin/env python3
"""
3-Day GO/NO-GO Marine Operations Formatter
Telegram 및 Email용 Impact-Based Forecast 포맷
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
import json


class ThreeDayFormatter:
    """3일치 해양 운항 판정 포맷터"""
    
    # WMO Sea State + NOAA Small Craft Advisory 기반 임계값
    THRESHOLDS = {
        'GO': {'hs_m': 1.50, 'wind_kt': 20},
        'CONDITIONAL': {'hs_m': 2.50, 'wind_kt': 23},
        'NO_GO': {'hs_m': 2.51, 'wind_kt': 24}
    }
    
    MIN_WINDOW_HOURS = 2  # 최소 윈도우 지속시간
    
    ICONS = {
        'GO': '🟢',
        'CONDITIONAL': '🟡',
        'NO_GO': '🔴',
        'TBD': '〰️',
        'CHECK': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌'
    }
    
    def __init__(self, location: str = "AGI"):
        self.location = location
        self.location_full = "Al Ghallan Island" if location == "AGI" else location
    
    def classify_point(self, hs_m: float, wind_kt: float) -> str:
        """단일 데이터 포인트 분류"""
        if hs_m <= self.THRESHOLDS['GO']['hs_m'] and wind_kt <= self.THRESHOLDS['GO']['wind_kt']:
            return 'GO'
        elif hs_m <= self.THRESHOLDS['CONDITIONAL']['hs_m'] and wind_kt <= self.THRESHOLDS['CONDITIONAL']['wind_kt']:
            return 'CONDITIONAL'
        else:
            return 'NO_GO'
    
    def detect_windows(self, timeseries: List[Dict], day_offset: int = 0) -> List[Dict]:
        """
        연속된 GO/CONDITIONAL 윈도우 탐지
        
        Args:
            timeseries: 시계열 데이터
            day_offset: 0=D0(오늘), 1=D+1(내일), 2=D+2(모레)
        
        Returns:
            윈도우 목록 [{'start': datetime, 'end': datetime, 'status': str, 'duration_hours': float}]
        """
        windows = []
        current_window = None
        
        for point in timeseries:
            # UTC+4 변환 (GST)
            point_time = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
            point_time_gst = point_time.astimezone(timezone(timedelta(hours=4)))
            
            # 날짜 필터링
            if point_time_gst.date() != (datetime.now(timezone(timedelta(hours=4))).date() + timedelta(days=day_offset)):
                continue
            
            hs_m = point.get('wave_height_m', 0)
            wind_ms = point.get('wind_speed_ms', 0)
            wind_kt = wind_ms * 1.94384  # m/s to knots
            
            status = self.classify_point(hs_m, wind_kt)
            
            if status in ['GO', 'CONDITIONAL']:
                if current_window is None:
                    # 새 윈도우 시작
                    current_window = {
                        'start': point_time_gst,
                        'end': point_time_gst,
                        'status': status,
                        'count': 1
                    }
                elif current_window['status'] == status:
                    # 같은 상태 계속
                    current_window['end'] = point_time_gst
                    current_window['count'] += 1
                else:
                    # 상태 변경 - 이전 윈도우 저장
                    if current_window['count'] >= self.MIN_WINDOW_HOURS:
                        duration = (current_window['end'] - current_window['start']).total_seconds() / 3600
                        windows.append({
                            'start': current_window['start'],
                            'end': current_window['end'],
                            'status': current_window['status'],
                            'duration_hours': duration
                        })
                    # 새 윈도우 시작
                    current_window = {
                        'start': point_time_gst,
                        'end': point_time_gst,
                        'status': status,
                        'count': 1
                    }
            else:
                # NO_GO - 윈도우 종료
                if current_window and current_window['count'] >= self.MIN_WINDOW_HOURS:
                    duration = (current_window['end'] - current_window['start']).total_seconds() / 3600
                    windows.append({
                        'start': current_window['start'],
                        'end': current_window['end'],
                        'status': current_window['status'],
                        'duration_hours': duration
                    })
                current_window = None
        
        # 마지막 윈도우 처리
        if current_window and current_window['count'] >= self.MIN_WINDOW_HOURS:
            duration = (current_window['end'] - current_window['start']).total_seconds() / 3600
            windows.append({
                'start': current_window['start'],
                'end': current_window['end'],
                'status': current_window['status'],
                'duration_hours': duration
            })
        
        return windows
    
    def generate_day_headline(self, windows: List[Dict], day_offset: int) -> Tuple[str, str]:
        """
        일자별 헤드라인 생성
        
        Returns:
            (icon, headline_text)
        """
        if not windows:
            return self.ICONS['NO_GO'], "창 없음 (대체 일정 탐색)"
        
        # 가장 긴 윈도우 찾기
        best_window = max(windows, key=lambda w: (w['status'] == 'GO', w['duration_hours']))
        
        start_time = best_window['start'].strftime('%H:%M')
        end_time = best_window['end'].strftime('%H:%M')
        
        if best_window['status'] == 'GO':
            return self.ICONS['GO'], f"운항 권장, {start_time}–{end_time}"
        else:
            return self.ICONS['CONDITIONAL'], f"조건부, 완화조치 필요, {start_time}–{end_time}"
    
    def format_windows_line(self, windows: List[Dict]) -> str:
        """윈도우 목록을 한 줄로 포맷"""
        if not windows:
            return "—"
        
        parts = []
        for w in windows:
            start = w['start'].strftime('%H:%M')
            end = w['end'].strftime('%H:%M')
            icon = self.ICONS[w['status']]
            parts.append(f"{icon} {start}–{end}")
        
        return " | ".join(parts)
    
    def calculate_confidence(self, api_status: Dict) -> Tuple[float, str]:
        """
        신뢰도 계산 (실데이터만 포함)
        
        Returns:
            (confidence_value, confidence_tier)
        """
        confidences = []
        
        for api_name, status in api_status.items():
            if '✅' in status.get('status', ''):
                conf = status.get('confidence', 0)
                if conf > 0:
                    confidences.append(conf)
        
        if not confidences:
            return 0.0, 'LOW'
        
        avg_conf = sum(confidences) / len(confidences)
        
        if avg_conf < 0.60:
            tier = 'LOW'
        elif avg_conf <= 0.80:
            tier = 'MED'
        else:
            tier = 'HIGH'
        
        return avg_conf, tier
    
    def generate_telegram_message(self, summary_data: Dict, timeseries: List[Dict]) -> str:
        """
        Telegram용 3-Day GO/NO-GO 메시지 생성
        
        Args:
            summary_data: weather_job.py의 summary JSON
            timeseries: 융합된 시계열 데이터
        """
        build_utc = datetime.now(timezone.utc)
        build_gst = build_utc.astimezone(timezone(timedelta(hours=4)))
        
        # 각 날짜별 윈도우 탐지
        d0_windows = self.detect_windows(timeseries, 0)
        d1_windows = self.detect_windows(timeseries, 1)
        d2_windows = self.detect_windows(timeseries, 2)
        
        # 헤드라인 생성
        d0_icon, d0_headline = self.generate_day_headline(d0_windows, 0)
        d1_icon, d1_headline = ("〰️", "데이터 대기") if not d1_windows else self.generate_day_headline(d1_windows, 1)
        d2_icon, d2_headline = ("〰️", "데이터 대기") if not d2_windows else self.generate_day_headline(d2_windows, 2)
        
        # Best window 표시
        best_badge = ""
        if d2_windows and any(w['status'] == 'GO' for w in d2_windows):
            best_badge = " ← Best Window"
        
        # 평균 계산
        analysis = summary_data.get('analysis', {})
        avg_hs = analysis.get('averages', {}).get('wave_height_m', 0)
        avg_wind_ms = analysis.get('averages', {}).get('wind_speed_ms', 0)
        avg_wind_kt = avg_wind_ms * 1.94384
        eri = analysis.get('averages', {}).get('eri', 0)
        
        # 판정 편향
        decisions = analysis.get('decisions', {})
        go_count = decisions.get('GO', 0)
        cond_count = decisions.get('CONDITIONAL', 0)
        no_count = decisions.get('NO-GO', 0)
        
        if no_count > go_count:
            daily_bias = f"NO-GO>GO ({no_count}/{go_count})"
        else:
            daily_bias = f"GO>NO-GO ({go_count}/{no_count})"
        
        # Notes 생성
        notes_list = []
        api_status = summary_data.get('api_status', {})
        
        if '❌' in api_status.get('STORMGLASS', {}).get('status', ''):
            notes_list.append("Stormglass 실패")
        if '⚠️' in api_status.get('WORLDTIDES', {}).get('status', ''):
            notes_list.append("Tides 크레딧 부족")
        
        if notes_list:
            notes_list.append("보수적 해석")
        
        notes_line = ", ".join(notes_list) if notes_list else "정상"
        
        # 신뢰도
        conf_val, conf_tier = self.calculate_confidence(api_status)
        
        # API 아이콘
        om_icon = self.ICONS['CHECK'] if '✅' in api_status.get('OPEN_METEO', {}).get('status', '') else self.ICONS['ERROR']
        ncm_icon = self.ICONS['CHECK'] if '✅' in api_status.get('NCM_SELENIUM', {}).get('status', '') else self.ICONS['ERROR']
        sg_icon = self.ICONS['CHECK'] if '✅' in api_status.get('STORMGLASS', {}).get('status', '') else self.ICONS['ERROR']
        tide_icon = self.ICONS['CHECK'] if '✅' in api_status.get('WORLDTIDES', {}).get('status', '') else self.ICONS['WARNING']
        
        # 최적 윈도우 추천
        plan_day = "D+2" if d2_windows and any(w['status'] == 'GO' for w in d2_windows) else "TBD"
        plan_window = ""
        if plan_day != "TBD":
            best_win = max((w for w in d2_windows if w['status'] == 'GO'), key=lambda w: w['duration_hours'])
            plan_window = f"{best_win['start'].strftime('%H:%M')}-{best_win['end'].strftime('%H:%M')}"
        
        # 최종 메시지
        message = f"""🌊 {self.location} Marine Ops — 3-Day GO/NO-GO

🗓 Build: {build_utc.strftime('%Y-%m-%d %H:%M')} UTC  |  {build_gst.strftime('%Y-%m-%d %H:%M')} (UTC+4)
📍 Spot: {self.location} ({self.location_full})

🔎 3-Day Overview (UTC+4)
D0 오늘:     {d0_icon}  {d0_headline}
D+1 내일:    {d1_icon}  {d1_headline}
D+2 모레:    {d2_icon}  {d2_headline}{best_badge}

🪟 Windows (UTC+4)
• D0: {self.format_windows_line(d0_windows)}
• D+1: {self.format_windows_line(d1_windows)}
• D+2: {self.format_windows_line(d2_windows)}

Why (요약)
• Hs/Wind (avg): {avg_hs:.2f} m / {avg_wind_kt:.0f} kt
• ERI(mean): {eri:.2f}  | Bias: {daily_bias}
• Notes: {notes_line}

Confidence: {conf_tier} ({conf_val:.2f})
Data: OPEN-METEO {om_icon}  NCM {ncm_icon}  STORMGLASS {sg_icon}  TIDES {tide_icon}

/actions  ➜  /plan {plan_day} {plan_window}   /brief crew   /share mws
"""
        
        return message
    
    def generate_telegram_buttons(self, d2_windows: List[Dict]) -> Dict:
        """Telegram 인라인 버튼 생성"""
        
        # 최적 윈도우 찾기
        plan_window = "06:00-10:00"
        if d2_windows and any(w['status'] == 'GO' for w in d2_windows):
            best_win = max((w for w in d2_windows if w['status'] == 'GO'), key=lambda w: w['duration_hours'])
            plan_window = f"{best_win['start'].strftime('%H:%M')}-{best_win['end'].strftime('%H:%M')}"
        
        return {
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": f"📅 Plan D+2 {plan_window}", "callback_data": f"plan:D2:{plan_window}"},
                        {"text": "🧭 Crew Brief", "callback_data": "brief:crew"}
                    ],
                    [
                        {"text": "📝 Share to MWS", "callback_data": "share:mws"},
                        {"text": "🔁 Recompute (3d)", "callback_data": "recalc:3d"}
                    ]
                ]
            }
        }
    
    def generate_email_html(self, summary_data: Dict, timeseries: List[Dict]) -> str:
        """
        Email용 HTML 보고서 생성
        """
        telegram_message = self.generate_telegram_message(summary_data, timeseries)
        
        # Telegram 메시지를 HTML로 변환
        html_lines = telegram_message.split('\n')
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Courier New', monospace;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            max-width: 800px;
            margin: 0 auto;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        pre {
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.6;
            font-size: 14px;
        }
        h1 {
            color: #0066cc;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌊 Marine Operations — 3-Day Forecast</h1>
        <pre>"""
        
        html_content += telegram_message
        
        html_content += """</pre>
        <div class="footer">
            <p><strong>References:</strong></p>
            <ul>
                <li>WMO Sea State / Code 3700: Slight(≤1.25m), Moderate(1.25-2.5m), Rough(≥2.5m)</li>
                <li>Beaufort Scale: Bft 5-6 ≈ 17-27 kt</li>
                <li>NOAA Small Craft Advisory: 22-33 kt</li>
                <li>WMO IBFWS: Impact-Based Forecast and Warning Services</li>
            </ul>
            <p><em>Generated by HVDC Marine Weather System v2.5</em></p>
        </div>
    </div>
</body>
</html>"""
        
        return html_content


if __name__ == "__main__":
    # 테스트
    formatter = ThreeDayFormatter("AGI")
    
    # 샘플 데이터
    summary_data = {
        "api_status": {
            "OPEN_METEO": {"status": "✅ 실제 데이터", "confidence": 0.75},
            "NCM_SELENIUM": {"status": "✅ 실제 데이터", "confidence": 0.70},
            "STORMGLASS": {"status": "❌ 실패", "confidence": 0},
            "WORLDTIDES": {"status": "⚠️ 폴백 데이터", "confidence": 0.30}
        },
        "analysis": {
            "averages": {
                "wave_height_m": 0.64,
                "wind_speed_ms": 10.8,
                "eri": 0.27
            },
            "decisions": {
                "GO": 41,
                "CONDITIONAL": 33,
                "NO-GO": 47
            }
        }
    }
    
    timeseries = []  # 실제 데이터 필요
    
    message = formatter.generate_telegram_message(summary_data, timeseries)
    print(message)

