import os

KG_RESEARCH_NUM_RETRIEVED_DOCS: int = int(
    os.environ.get("KG_RESEARCH_NUM_RETRIEVED_DOCS", "25")
)


KG_SIMPLE_ANSWER_MAX_DISPLAYED_SOURCES: int = int(
    os.environ.get("KG_SIMPLE_ANSWER_MAX_DISPLAYED_SOURCES", "10")
)


KG_ENTITY_EXTRACTION_TIMEOUT: int = int(
    os.environ.get("KG_ENTITY_EXTRACTION_TIMEOUT", "15")
)

KG_RELATIONSHIP_EXTRACTION_TIMEOUT: int = int(
    os.environ.get("KG_RELATIONSHIP_EXTRACTION_TIMEOUT", "15")
)

KG_STRATEGY_GENERATION_TIMEOUT: int = int(
    os.environ.get("KG_STRATEGY_GENERATION_TIMEOUT", "20")
)

KG_SQL_GENERATION_TIMEOUT: int = int(os.environ.get("KG_SQL_GENERATION_TIMEOUT", "40"))

KG_SQL_GENERATION_TIMEOUT_OVERRIDE: int = int(
    os.environ.get("KG_SQL_GENERATION_TIMEOUT_OVERRIDE", "40")
)

KG_SQL_GENERATION_MAX_TOKENS: int = int(
    os.environ.get("KG_SQL_GENERATION_MAX_TOKENS", "1500")
)

KG_TEMP_ALLOWED_DOCS_VIEW_NAME_PREFIX: str = os.environ.get(
    "KG_TEMP_ALLOWED_DOCS_VIEW_NAME_PREFIX", "allowed_docs"
)

KG_TEMP_KG_RELATIONSHIPS_VIEW_NAME_PREFIX: str = os.environ.get(
    "KG_TEMP_KG_RELATIONSHIPS_VIEW_NAME_PREFIX", "kg_relationships_with_access"
)

KG_TEMP_KG_ENTITIES_VIEW_NAME_PREFIX: str = os.environ.get(
    "KG_TEMP_KG_ENTITIES_VIEW_NAME_PREFIX", "kg_entities_with_access"
)


KG_FILTER_CONSTRUCTION_TIMEOUT: int = int(
    os.environ.get("KG_FILTER_CONSTRUCTION_TIMEOUT", "15")
)


KG_NORMALIZATION_RETRIEVE_ENTITIES_LIMIT: int = int(
    os.environ.get("KG_NORMALIZATION_RETRIEVE_ENTITIES_LIMIT", "100")
)

KG_FILTERED_SEARCH_TIMEOUT: int = int(
    os.environ.get("KG_FILTERED_SEARCH_TIMEOUT", "30")
)


KG_OBJECT_SOURCE_RESEARCH_TIMEOUT: int = int(
    os.environ.get("KG_OBJECT_SOURCE_RESEARCH_TIMEOUT", "30")
)

KG_TIMEOUT_LLM_INITIAL_ANSWER_GENERATION: int = int(
    os.environ.get("KG_TIMEOUT_LLM_INITIAL_ANSWER_GENERATION", "45")
)


# When content classification rules a file-connector document NOT_CV (e.g. a
# tender / procurement / contract document mistakenly tagged as a CV), skip
# KG extraction for it entirely rather than running GENERAL_CHUNK_PREPROCESSING
# over content that wasn't intended for this pipeline. Default is True for the
# CV-focused FOSS deployment; set to "false" to restore general extraction.
KG_SKIP_EXTRACTION_FOR_NON_CV_FILES: bool = (
    os.environ.get("KG_SKIP_EXTRACTION_FOR_NON_CV_FILES", "true").lower() == "true"
)

KG_TIMEOUT_CONNECT_LLM_INITIAL_ANSWER_GENERATION: int = int(
    os.environ.get("KG_TIMEOUT_CONNECT_LLM_INITIAL_ANSWER_GENERATION", "15")
)

KG_MAX_TOKENS_ANSWER_GENERATION: int = int(
    os.environ.get("KG_MAX_TOKENS_ANSWER_GENERATION", "1024")
)

KG_MAX_DEEP_SEARCH_RESULTS: int = int(
    os.environ.get("KG_MAX_DEEP_SEARCH_RESULTS", "30")
)


KG_METADATA_TRACKING_THRESHOLD: int = int(
    os.environ.get("KG_METADATA_TRACKING_THRESHOLD", "10")
)


KG_DEFAULT_MAX_PARENT_RECURSION_DEPTH: int = int(
    os.environ.get("KG_DEFAULT_MAX_PARENT_RECURSION_DEPTH", "2")
)


_KG_NORMALIZATION_RERANK_UNIGRAM_WEIGHT: float = max(
    1e-3,
    min(1, float(os.environ.get("KG_NORMALIZATION_RERANK_UNIGRAM_WEIGHT", "0.25"))),
)
_KG_NORMALIZATION_RERANK_BIGRAM_WEIGHT: float = max(
    1e-3,
    min(1, float(os.environ.get("KG_NORMALIZATION_RERANK_BIGRAM_WEIGHT", "0.25"))),
)
_KG_NORMALIZATION_RERANK_TRIGRAM_WEIGHT: float = max(
    1e-3,
    min(1, float(os.environ.get("KG_NORMALIZATION_RERANK_TRIGRAM_WEIGHT", "0.5"))),
)
_KG_NORMALIZATION_RERANK_NGRAM_SUMS: float = (
    _KG_NORMALIZATION_RERANK_UNIGRAM_WEIGHT
    + _KG_NORMALIZATION_RERANK_BIGRAM_WEIGHT
    + _KG_NORMALIZATION_RERANK_TRIGRAM_WEIGHT
)

KG_NORMALIZATION_RERANK_NGRAM_WEIGHTS: tuple[float, float, float] = (
    _KG_NORMALIZATION_RERANK_UNIGRAM_WEIGHT / _KG_NORMALIZATION_RERANK_NGRAM_SUMS,
    _KG_NORMALIZATION_RERANK_BIGRAM_WEIGHT / _KG_NORMALIZATION_RERANK_NGRAM_SUMS,
    _KG_NORMALIZATION_RERANK_TRIGRAM_WEIGHT / _KG_NORMALIZATION_RERANK_NGRAM_SUMS,
)


KG_NORMALIZATION_RERANK_LEVENSHTEIN_WEIGHT: float = max(
    0,
    min(1, float(os.environ.get("KG_NORMALIZATION_RERANK_LEVENSHTEIN_WEIGHT", "0.25"))),
)


KG_NORMALIZATION_RERANK_THRESHOLD: float = float(
    os.environ.get("KG_NORMALIZATION_RERANK_THRESHOLD", "0.3")
)


KG_CLUSTERING_RETRIEVE_THRESHOLD: float = float(
    os.environ.get("KG_CLUSTERING_RETRIEVE_THRESHOLD", "0.6")
)


KG_CLUSTERING_THRESHOLD: float = float(
    os.environ.get("KG_CLUSTERING_THRESHOLD", "0.96")
)

KG_MAX_SEARCH_DOCUMENTS: int = int(os.environ.get("KG_MAX_SEARCH_DOCUMENTS", "15"))

KG_MAX_DECOMPOSITION_SEGMENTS: int = int(
    os.environ.get("KG_MAX_DECOMPOSITION_SEGMENTS", "10")
)
KG_BETA_ASSISTANT_DESCRIPTION = (
    "The KG Beta assistant uses the Onyx Knowledge Graph (beta) structure \
to answer questions"
)

# Neo4j configuration for the graph query backend
NEO4J_URI: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER: str = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD: str = os.environ.get("NEO4J_PASSWORD", "neo4jpassword")
NEO4J_DATABASE: str = os.environ.get("NEO4J_DATABASE", "neo4j")

# "postgres" = current SQL self-join backend, "neo4j" = Cypher traversal backend
KG_QUERY_BACKEND: str = os.environ.get("KG_QUERY_BACKEND", "postgres")
