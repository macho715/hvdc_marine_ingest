# KR: 크론 자동화 스크립트 - 정기적 해양 데이터 수집 및 알림
# EN: Cron automation script - periodic marine data collection and notifications

import sys
import os
import json
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.vector_db import MarineVectorDB
from scripts.generate_weather_report import MarineWeatherOrchestrator
from query_vec import MarineQueryEngine

class MarineAutomation:
    """해양 데이터 자동화 관리자"""
    
    def __init__(self, config_file: str = "config/automation.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.vector_db = MarineVectorDB()
        self.query_engine = MarineQueryEngine()
        self.orchestrator = MarineWeatherOrchestrator()
        
        # 알림 시스템 초기화
        self.notification_enabled = self.config.get('notifications', {}).get('enabled', False)
        self.telegram_enabled = self.config.get('notifications', {}).get('telegram', {}).get('enabled', False)
        self.email_enabled = self.config.get('notifications', {}).get('email', {}).get('enabled', False)
    
    def _load_config(self) -> Dict[str, Any]:
        """자동화 설정 로드"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본 설정 생성
            default_config = {
                "schedule": {
                    "data_collection": "*/3 * * * *",  # 3시간마다
                    "weather_report": "0 6,18 * * *",  # 06:00, 18:00
                    "health_check": "*/30 * * * *"     # 30분마다
                },
                "locations": ["AGI", "DAS"],
                "notifications": {
                    "enabled": False,
                    "telegram": {
                        "enabled": False,
                        "bot_token": "",
                        "chat_id": ""
                    },
                    "email": {
                        "enabled": False,
                        "smtp_server": "",
                        "smtp_port": 587,
                        "username": "",
                        "password": "",
                        "recipients": []
                    }
                },
                "alerts": {
                    "no_go_threshold": 0.3,  # 30% 이상 NO-GO 시 알림
                    "wind_threshold": 20.0,  # 20 m/s 이상 시 알림
                    "wave_threshold": 2.0    # 2.0m 이상 시 알림
                }
            }
            
            # 설정 파일 저장
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            return default_config
    
    def data_collection_job(self):
        """데이터 수집 작업"""
        print(f"\n=== 데이터 수집 작업 시작 ({datetime.now()}) ===")
        
        try:
            # 통합 보고서 생성
            report = self.orchestrator.generate_report(self.config['locations'])
            
            # 알림 조건 확인
            self._check_alert_conditions(report)
            
            print(f"데이터 수집 완료: {report.report_id}")
            
        except Exception as e:
            print(f"데이터 수집 실패: {e}")
            self._send_alert(f"데이터 수집 실패: {e}", "error")
    
    def weather_report_job(self):
        """날씨 보고서 생성 작업"""
        print(f"\n=== 날씨 보고서 생성 작업 시작 ({datetime.now()}) ===")
        
        try:
            # 상세 보고서 생성
            report = self.orchestrator.generate_report(self.config['locations'])
            
            # 보고서 요약 생성
            summary = self._generate_report_summary(report)
            
            # 알림 전송
            if self.notification_enabled:
                self._send_daily_report(summary)
            
            print(f"날씨 보고서 생성 완료: {report.report_id}")
            
        except Exception as e:
            print(f"날씨 보고서 생성 실패: {e}")
            self._send_alert(f"날씨 보고서 생성 실패: {e}", "error")
    
    def health_check_job(self):
        """헬스 체크 작업"""
        print(f"\n=== 헬스 체크 작업 시작 ({datetime.now()}) ===")
        
        try:
            # DB 통계 확인
            stats = self.vector_db.get_stats()
            
            # 최근 데이터 확인
            recent_data = self.vector_db.get_recent_data(hours=6)
            
            if len(recent_data) == 0:
                self._send_alert("최근 6시간 데이터가 없습니다", "warning")
            
            # 시스템 상태 로그
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "db_records": stats['total_records'],
                "recent_data_count": len(recent_data),
                "status": "healthy" if len(recent_data) > 0 else "warning"
            }
            
            # 헬스 상태 저장
            health_file = Path("logs/health_status.json")
            health_file.parent.mkdir(exist_ok=True)
            
            with open(health_file, 'w', encoding='utf-8') as f:
                json.dump(health_status, f, ensure_ascii=False, indent=2)
            
            print(f"헬스 체크 완료: {health_status['status']}")
            
        except Exception as e:
            print(f"헬스 체크 실패: {e}")
            self._send_alert(f"헬스 체크 실패: {e}", "error")
    
    def _check_alert_conditions(self, report):
        """알림 조건 확인"""
        if not self.notification_enabled:
            return
        
        # NO-GO 비율 확인
        total_decisions = len(report.decisions)
        no_go_count = sum(1 for d in report.decisions if d.decision == "NO-GO")
        
        if total_decisions > 0:
            no_go_ratio = no_go_count / total_decisions
            
            if no_go_ratio >= self.config['alerts']['no_go_threshold']:
                message = f"NO-GO 비율 높음: {no_go_ratio:.1%} ({no_go_count}/{total_decisions})"
                self._send_alert(message, "warning")
        
        # 극한 조건 확인
        for forecast in report.fused_forecasts:
            if forecast.wind_speed_fused >= self.config['alerts']['wind_threshold']:
                message = f"강풍 경고: {forecast.wind_speed_fused:.1f} m/s at {forecast.location}"
                self._send_alert(message, "warning")
            
            if forecast.wave_height_fused >= self.config['alerts']['wave_threshold']:
                message = f"고파고 경고: {forecast.wave_height_fused:.1f} m at {forecast.location}"
                self._send_alert(message, "warning")
    
    def _generate_report_summary(self, report) -> Dict[str, Any]:
        """보고서 요약 생성"""
        # 판정 통계
        decisions_by_location = {}
        for decision in report.decisions:
            location = decision.location
            if location not in decisions_by_location:
                decisions_by_location[location] = {"GO": 0, "CONDITIONAL": 0, "NO-GO": 0}
            decisions_by_location[location][decision.decision] += 1
        
        # 전체 통계
        total_decisions = len(report.decisions)
        go_count = sum(1 for d in report.decisions if d.decision == "GO")
        conditional_count = sum(1 for d in report.decisions if d.decision == "CONDITIONAL")
        no_go_count = sum(1 for d in report.decisions if d.decision == "NO-GO")
        
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "locations": report.locations,
            "total_periods": total_decisions,
            "summary": {
                "GO": go_count,
                "CONDITIONAL": conditional_count,
                "NO-GO": no_go_count,
                "operational_ratio": (go_count + conditional_count) / total_decisions if total_decisions > 0 else 0
            },
            "by_location": decisions_by_location,
            "warnings": report.warnings
        }
    
    def _send_alert(self, message: str, alert_type: str = "info"):
        """알림 전송"""
        if not self.notification_enabled:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {alert_type.upper()}: {message}"
        
        print(f"알림 전송: {full_message}")
        
        # Telegram 알림
        if self.telegram_enabled:
            self._send_telegram_alert(full_message)
        
        # 이메일 알림
        if self.email_enabled:
            self._send_email_alert(full_message, alert_type)
    
    def _send_telegram_alert(self, message: str):
        """Telegram 알림 전송"""
        try:
            import requests
            
            telegram_config = self.config['notifications']['telegram']
            bot_token = telegram_config['bot_token']
            chat_id = telegram_config['chat_id']
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("Telegram 알림 전송 성공")
            else:
                print(f"Telegram 알림 전송 실패: {response.status_code}")
        
        except Exception as e:
            print(f"Telegram 알림 전송 오류: {e}")
    
    def _send_email_alert(self, message: str, alert_type: str):
        """이메일 알림 전송"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            email_config = self.config['notifications']['email']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['Subject'] = f"해양 날씨 알림 - {alert_type.upper()}"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            
            for recipient in email_config['recipients']:
                msg['To'] = recipient
                server.send_message(msg)
            
            server.quit()
            print("이메일 알림 전송 성공")
        
        except Exception as e:
            print(f"이메일 알림 전송 오류: {e}")
    
    def _send_daily_report(self, summary: Dict[str, Any]):
        """일일 보고서 전송"""
        report_text = f"""
🌊 해양 날씨 일일 보고서

📅 생성 시간: {summary['generated_at']}
📍 대상 지역: {', '.join(summary['locations'])}
📊 총 예보 기간: {summary['total_periods']}개

📈 운항 판정 요약:
• GO: {summary['summary']['GO']}개
• CONDITIONAL: {summary['summary']['CONDITIONAL']}개  
• NO-GO: {summary['summary']['NO-GO']}개
• 운항 가능률: {summary['summary']['operational_ratio']:.1%}

⚠️ 경고사항: {len(summary['warnings'])}개
        """
        
        if summary['warnings']:
            report_text += "\n" + "\n".join(summary['warnings'])
        
        self._send_alert(report_text, "report")
    
    def start_scheduler(self):
        """스케줄러 시작"""
        print("=== 해양 데이터 자동화 스케줄러 시작 ===")
        print(f"설정 파일: {self.config_file}")
        
        # 작업 스케줄 등록
        schedule.every(3).hours.do(self.data_collection_job)
        schedule.every().day.at("06:00").do(self.weather_report_job)
        schedule.every().day.at("18:00").do(self.weather_report_job)
        schedule.every(30).minutes.do(self.health_check_job)
        
        print("스케줄 등록 완료:")
        print("- 데이터 수집: 3시간마다")
        print("- 날씨 보고서: 06:00, 18:00")
        print("- 헬스 체크: 30분마다")
        
        # 스케줄러 실행
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
        except KeyboardInterrupt:
            print("\n스케줄러 종료")
    
    def run_once(self):
        """한 번만 실행 (테스트용)"""
        print("=== 한 번 실행 모드 ===")
        
        self.data_collection_job()
        self.health_check_job()

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='해양 데이터 자동화')
    parser.add_argument('--once', action='store_true', help='한 번만 실행')
    parser.add_argument('--config', default='config/automation.json', help='설정 파일 경로')
    
    args = parser.parse_args()
    
    # 자동화 시스템 초기화
    automation = MarineAutomation(args.config)
    
    if args.once:
        automation.run_once()
    else:
        automation.start_scheduler()

if __name__ == "__main__":
    main()
