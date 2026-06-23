import time

class ExplanationCache:
    """
    A simple in-memory cache to store LLM explanations with a 5-minute (300 seconds) TTL.
    """
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    def _get_key(self, symbol: str, timeframe: str, signal: str) -> tuple:
        return (symbol.upper().strip(), timeframe.lower().strip(), signal.upper().strip())

    def get(self, symbol: str, timeframe: str, signal: str) -> str:
        """
        Retrieves the cached explanation if it exists and has not expired.
        """
        key = self._get_key(symbol, timeframe, signal)
        if key in self.cache:
            explanation, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return explanation
            else:
                # Evict expired entry
                del self.cache[key]
        return None

    def set(self, symbol: str, timeframe: str, signal: str, explanation: str):
        """
        Stores an explanation in the cache with the current timestamp.
        """
        key = self._get_key(symbol, timeframe, signal)
        self.cache[key] = (explanation, time.time())

    def clear(self):
        """
        Clears all cache entries.
        """
        self.cache.clear()
