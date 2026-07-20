import hashlib
import time
import threading
from typing import Any, Dict, Optional, Tuple

class ComputationCache:
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, Optional[float]]] = {}  # key -> (value, expiry_timestamp)
        self._lock = threading.Lock()
        
        # Metrics
        self._hits = 0
        self._misses = 0
        self._llm_avoided = 0
        self._total_lookup_time = 0.0
        self._total_generation_time = 0.0
        self._lookups_count = 0
        self._generations_count = 0
        
    def generate_cache_key(self, namespace: str, version: str, identifier: str) -> str:
        return f"{namespace}:{version}:{identifier}"
        
    def get(self, key: str) -> Optional[Any]:
        start = time.perf_counter()
        with self._lock:
            self._lookups_count += 1
            if key in self._cache:
                val, expiry = self._cache[key]
                if expiry is None or expiry > time.time():
                    self._hits += 1
                    self._llm_avoided += 1
                    elapsed = time.perf_counter() - start
                    self._total_lookup_time += elapsed
                    return val
                else:
                    # Expired
                    del self._cache[key]
            
            self._misses += 1
            elapsed = time.perf_counter() - start
            self._total_lookup_time += elapsed
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        expiry = time.time() + ttl if ttl is not None else None
        with self._lock:
            self._cache[key] = (value, expiry)
            
    def invalidate(self, key: str):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                
    def collect_metrics(self) -> Dict[str, Any]:
        with self._lock:
            avg_lookup = (self._total_lookup_time / self._lookups_count) if self._lookups_count > 0 else 0.0
            avg_generation = (self._total_generation_time / self._generations_count) if self._generations_count > 0 else 0.0
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100.0) if total_requests > 0 else 0.0
            
            return {
                "memory_cache_hit_rate_percent": round(hit_rate, 2),
                "cache_hits": self._hits,
                "cache_misses": self._misses,
                "llm_calls_avoided": self._llm_avoided,
                "avg_lookup_time_seconds": round(avg_lookup, 6),
                "avg_generation_time_seconds": round(avg_generation, 4),
                "total_cached_items": len(self._cache)
            }

    def record_generation_time(self, duration: float):
        with self._lock:
            self._total_generation_time += duration
            self._generations_count += 1

# Global cache instance
comp_cache = ComputationCache()

def hash_text(text: str) -> str:
    if not text:
        return "empty"
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
