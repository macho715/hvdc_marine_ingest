# KR: 데이터 캐시 관리
# EN: Data cache management

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class MarineDataCache:
    """해양 데이터 캐시 관리자"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 3):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600
    
    def _get_cache_path(self, key: str) -> Path:
        """캐시 파일 경로 생성"""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 조회"""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # TTL 확인
            cached_at = datetime.fromisoformat(data['cached_at'])
            if datetime.now() - cached_at > timedelta(seconds=self.ttl_seconds):
                cache_path.unlink()  # 만료된 캐시 삭제
                return None
            
            return data['payload']
        
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            cache_path.unlink()  # 손상된 캐시 삭제
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """캐시에 데이터 저장"""
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'ttl_hours': self.ttl_seconds // 3600,
            'payload': data
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    def invalidate(self, key: str) -> None:
        """특정 캐시 무효화"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
    
    def clear_all(self) -> None:
        """모든 캐시 삭제"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        active_caches = 0
        expired_caches = 0
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cached_at = datetime.fromisoformat(data['cached_at'])
                if datetime.now() - cached_at <= timedelta(seconds=self.ttl_seconds):
                    active_caches += 1
                else:
                    expired_caches += 1
            except:
                expired_caches += 1
        
        return {
            'total_files': len(cache_files),
            'active_caches': active_caches,
            'expired_caches': expired_caches,
            'total_size_bytes': total_size,
            'cache_dir': str(self.cache_dir)
        }
