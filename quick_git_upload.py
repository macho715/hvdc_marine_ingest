#!/usr/bin/env python3
"""
빠른 Git 업로드 스크립트 - HVDC Marine Ingestion Project
"""

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_command(cmd, cwd=None):
    """명령어 실행"""
    print(f"실행: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"오류: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def main():
    """메인 함수"""
    print("🚀 HVDC Marine Ingestion Project Git 업로드 시작")
    print("=" * 60)
    
    # 현재 디렉터리 확인
    current_dir = Path.cwd()
    print(f"작업 디렉터리: {current_dir}")
    
    # Git 초기화
    if not (current_dir / '.git').exists():
        print("\n📁 Git 저장소 초기화...")
        if not run_command(['git', 'init'], current_dir):
            return False
    
    # 사용자 정보 설정
    print("\n👤 Git 사용자 정보 설정...")
    run_command(['git', 'config', 'user.name', 'MACHO-GPT'])
    run_command(['git', 'config', 'user.email', 'macho@hvdc.com'])
    
    # 원격 저장소 설정
    remote_url = "https://github.com/macho715/hvdc_marine_ingest.git"
    print(f"\n🌐 원격 저장소 설정: {remote_url}")
    
    try:
        run_command(['git', 'remote', 'add', 'origin', remote_url], current_dir)
    except:
        run_command(['git', 'remote', 'set-url', 'origin', remote_url], current_dir)
    
    # 기본 브랜치 설정
    print("\n🌿 기본 브랜치 설정...")
    run_command(['git', 'checkout', '-B', 'main'], current_dir)
    
    # .gitignore 확인
    gitignore_path = current_dir / '.gitignore'
    if not gitignore_path.exists():
        print("\n📝 .gitignore 생성...")
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*.so
.Python
build/
dist/
*.egg-info/

# Virtual environments
.venv/
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.sqlite
*.db

# API keys
.env
*.key
*.pem

# Temporary files
*.tmp
*.bak
*~

# Cache
.cache/
.pytest_cache/
.mypy_cache/

# Marine data
data/raw/
reports/temp/
"""
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✓ .gitignore 생성 완료")
    
    # 파일 추가
    print("\n📦 파일 스테이징...")
    if not run_command(['git', 'add', '-A'], current_dir):
        return False
    
    # 커밋
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"feat: HVDC Marine Weather Ingestion System v2.1 @ {timestamp}"
    
    print(f"\n💾 커밋 생성: {commit_message}")
    if not run_command(['git', 'commit', '-m', commit_message], current_dir):
        print("⚠️ 커밋할 변경사항이 없거나 이미 커밋됨")
    
    # 푸시
    print("\n🚀 원격 저장소에 푸시...")
    if not run_command(['git', 'push', '-u', 'origin', 'main'], current_dir):
        print("❌ 푸시 실패")
        return False
    
    print("\n✅ Git 업로드 완료!")
    print(f"🔗 저장소: {remote_url}")
    print(f"📅 업로드 시간: {timestamp}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
