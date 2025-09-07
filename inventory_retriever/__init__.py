"""
Inventory Retriever Package for Warehouse Operational Assistant

This package provides comprehensive retrieval capabilities including:
- Structured SQL retrieval for precise data queries
- Vector search with enhanced RAG capabilities
- Hybrid retrieval combining SQL and vector search
- Query preprocessing and post-processing
- Intelligent routing and optimization
- Redis caching with configurable TTL and eviction policies
- Cache warming and monitoring
- Performance analytics and health checks
"""

from .structured.sql_retriever import SQLRetriever
from .vector.milvus_retriever import MilvusRetriever
from .vector.embedding_service import EmbeddingService
from .vector.enhanced_retriever import EnhancedVectorRetriever
from .enhanced_hybrid_retriever import EnhancedHybridRetriever
from .query_preprocessing import QueryPreprocessor, PreprocessedQuery, QueryIntent
from .structured.sql_query_router import SQLQueryRouter, QueryType, QueryComplexity
from .result_postprocessing import ResultPostProcessor, ProcessedResult, ResultType, DataQuality
from .integrated_query_processor import IntegratedQueryProcessor, QueryProcessingResult

# Caching imports
from .caching import (
    RedisCacheService, CacheType, CacheConfig, CacheMetrics,
    CacheManager, CachePolicy, CacheWarmingRule, EvictionStrategy,
    CachedQueryProcessor, CacheIntegrationConfig,
    get_cache_service, get_cache_manager, get_cached_query_processor
)

__all__ = [
    # Core retrievers
    'SQLRetriever',
    'MilvusRetriever', 
    'EmbeddingService',
    'EnhancedVectorRetriever',
    'EnhancedHybridRetriever',
    
    # Query processing
    'QueryPreprocessor',
    'PreprocessedQuery',
    'QueryIntent',
    
    # SQL routing
    'SQLQueryRouter',
    'QueryType',
    'QueryComplexity',
    
    # Result processing
    'ResultPostProcessor',
    'ProcessedResult',
    'ResultType',
    'DataQuality',
    
    # Integrated processing
    'IntegratedQueryProcessor',
    'QueryProcessingResult',
    
    # Caching
    'RedisCacheService',
    'CacheType',
    'CacheConfig',
    'CacheMetrics',
    'CacheManager',
    'CachePolicy',
    'CacheWarmingRule',
    'EvictionStrategy',
    'CachedQueryProcessor',
    'CacheIntegrationConfig',
    'get_cache_service',
    'get_cache_manager',
    'get_cached_query_processor'
]

__version__ = "1.0.0"
__author__ = "Warehouse Operational Assistant Team"
__description__ = "Advanced retrieval system with SQL path optimization, hybrid RAG, and intelligent Redis caching"
