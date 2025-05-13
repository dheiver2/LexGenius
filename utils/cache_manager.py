from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, app=None):
        self.cache = Cache(config={
            'CACHE_TYPE': Config.CACHE_TYPE,
            'CACHE_DEFAULT_TIMEOUT': Config.CACHE_DEFAULT_TIMEOUT
        })
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[Config.RATELIMIT_DEFAULT],
            storage_uri=Config.RATELIMIT_STORAGE_URL
        )
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the cache and limiter with the Flask app"""
        self.cache.init_app(app)
        self.limiter.init_app(app)
        logger.info("Cache and rate limiter initialized")

    def cache_document(self, case_type, parties, facts, legal_grounds, requests, document):
        """Cache a document with its parameters"""
        cache_key = f"doc_{hash(f'{case_type}{parties}{facts}{legal_grounds}{requests}')}"
        self.cache.set(cache_key, document)
        logger.debug(f"Document cached with key: {cache_key}")
        return cache_key

    def get_cached_document(self, case_type, parties, facts, legal_grounds, requests):
        """Retrieve a cached document"""
        cache_key = f"doc_{hash(f'{case_type}{parties}{facts}{legal_grounds}{requests}')}"
        document = self.cache.get(cache_key)
        if document:
            logger.debug(f"Document retrieved from cache: {cache_key}")
        return document

    def clear_cache(self):
        """Clear all cached documents"""
        self.cache.clear()
        logger.info("Document cache cleared")

# Create global instances
cache_manager = CacheManager()
cache = cache_manager.cache
limiter = cache_manager.limiter

def init_cache(app):
    """Initialize cache with Flask app"""
    cache_manager.init_app(app)

def cache_document(case_type, parties, facts, legal_grounds, requests, document):
    """Cache a document"""
    return cache_manager.cache_document(case_type, parties, facts, legal_grounds, requests, document)

def get_cached_document(case_type, parties, facts, legal_grounds, requests):
    """Get a cached document"""
    return cache_manager.get_cached_document(case_type, parties, facts, legal_grounds, requests)

def clear_document_cache():
    """Clear document cache"""
    cache_manager.clear_cache() 