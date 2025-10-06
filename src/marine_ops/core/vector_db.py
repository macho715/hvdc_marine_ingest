# KR: SQLite-vec 벡터 데이터베이스 관리
# EN: SQLite-vec vector database management

import sqlite3
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer

from .schema import MarineTimeseries, MarineDataPoint

class MarineVectorDB:
    """해양 데이터 벡터 데이터베이스 관리자"""
    
    def __init__(self, db_path: str = "marine_vec.db", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = Path(db_path)
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        
        # 벡터 확장 초기화
        self._init_vector_extension()
        self._create_tables()
    
    def _init_vector_extension(self):
        """SQLite 벡터 확장 초기화"""
        # 일단 기본 SQLite만 사용 (sqlite-vec는 설치가 복잡함)
        print("기본 SQLite 사용 (벡터 확장 없음)")
        self.use_vector_extension = False
    
    def _create_tables(self):
        """테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 해양 데이터 원본 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marine_raw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    location TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    UNIQUE(source, location, timestamp)
                )
            """)
            
            # 벡터 임베딩 테이블
            if self.use_vector_extension:
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS marine_vec USING vec0(
                        embedding float[384]
                    )
                """)
            else:
                # 기본 SQLite 테이블 (벡터를 BLOB로 저장)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS marine_vec (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        embedding BLOB
                    )
                """)
            
            # 벡터 메타데이터 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marine_vec_meta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_id INTEGER NOT NULL,
                    text_content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    location TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    embedding_id INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(raw_id) REFERENCES marine_raw(id)
                )
            """)
            
            # 인덱스 생성
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_marine_raw_source_loc ON marine_raw(source, location)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_marine_raw_timestamp ON marine_raw(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vec_meta_source ON marine_vec_meta(source)")
            
            conn.commit()
    
    def store_timeseries(self, timeseries: MarineTimeseries) -> int:
        """시계열 데이터를 벡터 DB에 저장"""
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for data_point in timeseries.data_points:
                try:
                    # 원본 데이터 저장
                    data_json = json.dumps(data_point.__dict__, ensure_ascii=False)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO marine_raw 
                        (source, location, timestamp, data_json, ingested_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        timeseries.source,
                        timeseries.location,
                        data_point.timestamp,
                        data_json,
                        timeseries.ingested_at
                    ))
                    
                    raw_id = cursor.lastrowid
                    
                    # 텍스트 콘텐츠 생성 (임베딩용)
                    text_content = self._create_text_content(data_point, timeseries)
                    
                    # 임베딩 생성
                    embedding = self.model.encode([text_content], normalize_embeddings=True)[0]
                    
                    # 벡터 저장
                    if self.use_vector_extension:
                        cursor.execute("""
                            INSERT INTO marine_vec (embedding) VALUES (?)
                        """, (embedding.tolist(),))
                    else:
                        cursor.execute("""
                            INSERT INTO marine_vec (embedding) VALUES (?)
                        """, (embedding.tobytes(),))
                    
                    embedding_id = cursor.lastrowid
                    
                    # 메타데이터 저장
                    cursor.execute("""
                        INSERT OR REPLACE INTO marine_vec_meta
                        (raw_id, text_content, source, location, timestamp, embedding_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        raw_id,
                        text_content,
                        timeseries.source,
                        timeseries.location,
                        data_point.timestamp,
                        embedding_id,
                        datetime.now().isoformat()
                    ))
                    
                    stored_count += 1
                    
                except Exception as e:
                    print(f"데이터 포인트 저장 실패: {e}")
                    continue
            
            conn.commit()
        
        return stored_count
    
    def _create_text_content(self, data_point: MarineDataPoint, timeseries: MarineTimeseries) -> str:
        """임베딩용 텍스트 콘텐츠 생성"""
        content_parts = [
            f"Location: {timeseries.location}",
            f"Source: {timeseries.source}",
            f"Timestamp: {data_point.timestamp}",
            f"Wind Speed: {data_point.wind_speed} m/s",
            f"Wind Direction: {data_point.wind_direction} degrees",
            f"Wave Height: {data_point.wave_height} m"
        ]
        
        if data_point.wind_gust:
            content_parts.append(f"Wind Gust: {data_point.wind_gust} m/s")
        
        if data_point.wave_period:
            content_parts.append(f"Wave Period: {data_point.wave_period} s")
        
        if data_point.sea_state:
            content_parts.append(f"Sea State: {data_point.sea_state}")
        
        if data_point.visibility:
            content_parts.append(f"Visibility: {data_point.visibility} km")
        
        return " | ".join(content_parts)
    
    def vector_search(self, query: str, top_k: int = 10, location_filter: str = None) -> List[Dict[str, Any]]:
        """벡터 유사도 검색"""
        # 쿼리 임베딩 생성
        query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
        
        results = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if self.use_vector_extension:
                # 벡터 유사도 검색 (sqlite-vec 사용)
                if location_filter:
                    cursor.execute("""
                        SELECT mvm.raw_id, mvm.text_content, mvm.source, mvm.location, 
                               mvm.timestamp, mvm.created_at, v.embedding
                        FROM marine_vec_meta mvm
                        JOIN marine_vec v ON mvm.embedding_id = v.rowid
                        WHERE mvm.location = ?
                        ORDER BY v.embedding <-> ?
                        LIMIT ?
                    """, (location_filter, query_embedding.tolist(), top_k))
                else:
                    cursor.execute("""
                        SELECT mvm.raw_id, mvm.text_content, mvm.source, mvm.location, 
                               mvm.timestamp, mvm.created_at, v.embedding
                        FROM marine_vec_meta mvm
                        JOIN marine_vec v ON mvm.embedding_id = v.rowid
                        ORDER BY v.embedding <-> ?
                        LIMIT ?
                    """, (query_embedding.tolist(), top_k))
            else:
                # 기본 SQLite 검색 (모든 결과 반환 후 Python에서 유사도 계산)
                if location_filter:
                    cursor.execute("""
                        SELECT mvm.raw_id, mvm.text_content, mvm.source, mvm.location, 
                               mvm.timestamp, mvm.created_at, v.embedding
                        FROM marine_vec_meta mvm
                        JOIN marine_vec v ON mvm.embedding_id = v.id
                        WHERE mvm.location = ?
                    """, (location_filter,))
                else:
                    cursor.execute("""
                        SELECT mvm.raw_id, mvm.text_content, mvm.source, mvm.location, 
                               mvm.timestamp, mvm.created_at, v.embedding
                        FROM marine_vec_meta mvm
                        JOIN marine_vec v ON mvm.embedding_id = v.id
                    """)
            
            rows = cursor.fetchall()
            
            # 기본 SQLite 모드에서는 유사도 계산 후 정렬
            if not self.use_vector_extension:
                scored_rows = []
                for row in rows:
                    raw_id, text_content, source, location, timestamp, created_at, embedding_bytes = row
                    
                    # BLOB을 numpy 배열로 변환
                    stored_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                    
                    # 코사인 유사도 계산
                    similarity = float(np.dot(query_embedding, stored_embedding))
                    scored_rows.append((similarity, row))
                
                # 유사도 기준으로 정렬하고 상위 k개 선택
                scored_rows.sort(reverse=True, key=lambda x: x[0])
                rows = [row for _, row in scored_rows[:top_k]]
            
            for row in rows:
                raw_id, text_content, source, location, timestamp, created_at, embedding = row
                
                # 원본 데이터 조회
                cursor.execute("SELECT data_json FROM marine_raw WHERE id = ?", (raw_id,))
                raw_data = cursor.fetchone()
                
                if raw_data:
                    try:
                        data_json = json.loads(raw_data[0])
                        
                        result = {
                            'raw_id': raw_id,
                            'source': source,
                            'location': location,
                            'timestamp': timestamp,
                            'text_content': text_content,
                            'data': data_json,
                            'created_at': created_at
                        }
                        results.append(result)
                        
                    except json.JSONDecodeError:
                        continue
        
        return results
    
    def get_recent_data(self, hours: int = 24, location: str = None) -> List[Dict[str, Any]]:
        """최근 데이터 조회"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if location:
                cursor.execute("""
                    SELECT data_json, source, location, timestamp, ingested_at
                    FROM marine_raw
                    WHERE timestamp >= ? AND location = ?
                    ORDER BY timestamp DESC
                """, (cutoff_iso, location))
            else:
                cursor.execute("""
                    SELECT data_json, source, location, timestamp, ingested_at
                    FROM marine_raw
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_iso,))
            
            rows = cursor.fetchall()
            results = []
            
            for row in rows:
                data_json, source, location, timestamp, ingested_at = row
                try:
                    data = json.loads(data_json)
                    results.append({
                        'source': source,
                        'location': location,
                        'timestamp': timestamp,
                        'data': data,
                        'ingested_at': ingested_at
                    })
                except json.JSONDecodeError:
                    continue
            
            return results
    
    def get_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 총 레코드 수
            cursor.execute("SELECT COUNT(*) FROM marine_raw")
            total_records = cursor.fetchone()[0]
            
            # 소스별 통계
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM marine_raw
                GROUP BY source
                ORDER BY count DESC
            """)
            source_stats = dict(cursor.fetchall())
            
            # 지역별 통계
            cursor.execute("""
                SELECT location, COUNT(*) as count
                FROM marine_raw
                GROUP BY location
                ORDER BY count DESC
            """)
            location_stats = dict(cursor.fetchall())
            
            # 최신 데이터 시간
            cursor.execute("SELECT MAX(timestamp) FROM marine_raw")
            latest_timestamp = cursor.fetchone()[0]
            
            # 벡터 테이블 통계
            cursor.execute("SELECT COUNT(*) FROM marine_vec")
            vector_count = cursor.fetchone()[0]
            
            return {
                'total_records': total_records,
                'vector_embeddings': vector_count,
                'source_stats': source_stats,
                'location_stats': location_stats,
                'latest_timestamp': latest_timestamp,
                'database_path': str(self.db_path)
            }

def save_timeseries_to_vector_db(timeseries_list: List[MarineTimeseries], db_path: str = "marine_vec.db") -> Dict[str, int]:
    """시계열 데이터를 벡터 DB에 일괄 저장"""
    vector_db = MarineVectorDB(db_path)
    results = {}
    
    for timeseries in timeseries_list:
        stored_count = vector_db.store_timeseries(timeseries)
        results[f"{timeseries.source}_{timeseries.location}"] = stored_count
        print(f"저장됨: {timeseries.source} {timeseries.location} - {stored_count}개 데이터 포인트")
    
    return results
