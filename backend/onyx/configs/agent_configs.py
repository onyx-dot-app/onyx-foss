import os

AGENT_DEFAULT_RETRIEVAL_HITS = 25
AGENT_DEFAULT_RERANKING_HITS = 15
AGENT_DEFAULT_SUB_QUESTION_MAX_CONTEXT_HITS = 8
AGENT_DEFAULT_NUM_DOCS_FOR_INITIAL_DECOMPOSITION = 3
AGENT_DEFAULT_NUM_DOCS_FOR_REFINED_DECOMPOSITION = 5
AGENT_DEFAULT_EXPLORATORY_SEARCH_RESULTS = 3
AGENT_DEFAULT_MIN_ORIG_QUESTION_DOCS = 5
AGENT_DEFAULT_MAX_ANSWER_CONTEXT_DOCS = 10
AGENT_DEFAULT_MAX_STATIC_HISTORY_CHAR_LENGTH = 10000

#####
# Agent Configs
#####

agent_retrieval_stats_os: bool | str | None = os.environ.get(
    "AGENT_RETRIEVAL_STATS", False
)

AGENT_RETRIEVAL_STATS: bool = False
if isinstance(agent_retrieval_stats_os, str) and agent_retrieval_stats_os == "True":
    AGENT_RETRIEVAL_STATS = True
elif isinstance(agent_retrieval_stats_os, bool) and agent_retrieval_stats_os:
    AGENT_RETRIEVAL_STATS = True

agent_max_query_retrieval_results_os: int | str = os.environ.get(
    "AGENT_MAX_QUERY_RETRIEVAL_RESULTS", AGENT_DEFAULT_RETRIEVAL_HITS
)

AGENT_MAX_QUERY_RETRIEVAL_RESULTS: int = AGENT_DEFAULT_RETRIEVAL_HITS
try:
    atmqrr = int(agent_max_query_retrieval_results_os)
    AGENT_MAX_QUERY_RETRIEVAL_RESULTS = atmqrr
except ValueError:
    raise ValueError(
        f"MAX_AGENT_QUERY_RETRIEVAL_RESULTS must be an integer, got {AGENT_MAX_QUERY_RETRIEVAL_RESULTS}"
    )


# Reranking agent configs
# Reranking stats - no influence on flow outside of stats collection
agent_reranking_stats_os: bool | str | None = os.environ.get(
    "AGENT_RERANKING_TEST", False
)
AGENT_RERANKING_STATS: bool = False
if isinstance(agent_reranking_stats_os, str) and agent_reranking_stats_os == "True":
    AGENT_RERANKING_STATS = True
elif isinstance(agent_reranking_stats_os, bool) and agent_reranking_stats_os:
    AGENT_RERANKING_STATS = True


agent_reranking_max_query_retrieval_results_os: int | str = os.environ.get(
    "AGENT_RERANKING_MAX_QUERY_RETRIEVAL_RESULTS", AGENT_DEFAULT_RERANKING_HITS
)

AGENT_RERANKING_MAX_QUERY_RETRIEVAL_RESULTS: int = AGENT_DEFAULT_RERANKING_HITS

GRAPH_VERSION_NAME: str = "a"

try:
    atmqrr = int(agent_reranking_max_query_retrieval_results_os)
    AGENT_RERANKING_MAX_QUERY_RETRIEVAL_RESULTS = atmqrr
except ValueError:
    raise ValueError(
        f"AGENT_RERANKING_MAX_QUERY_RETRIEVAL_RESULTS must be an integer, got {AGENT_RERANKING_MAX_QUERY_RETRIEVAL_RESULTS}"
    )

AGENT_NUM_DOCS_FOR_DECOMPOSITION_OS: int | str = os.environ.get(
    "AGENT_NUM_DOCS_FOR_DECOMPOSITION", AGENT_DEFAULT_NUM_DOCS_FOR_INITIAL_DECOMPOSITION
)

try:
    AGENT_NUM_DOCS_FOR_DECOMPOSITION = int(AGENT_NUM_DOCS_FOR_DECOMPOSITION_OS)
except ValueError:
    raise ValueError(
        f"AGENT_NUM_DOCS_FOR_DECOMPOSITION must be an integer, got {AGENT_NUM_DOCS_FOR_DECOMPOSITION_OS}"
    )

AGENT_NUM_DOCS_FOR_REFINED_DECOMPOSITION_OS: int | str = os.environ.get(
    "AGENT_NUM_DOCS_FOR_REFINED_DECOMPOSITION",
    AGENT_DEFAULT_NUM_DOCS_FOR_REFINED_DECOMPOSITION,
)

try:
    AGENT_NUM_DOCS_FOR_REFINED_DECOMPOSITION = int(
        AGENT_NUM_DOCS_FOR_REFINED_DECOMPOSITION_OS
    )
except ValueError:
    raise ValueError(
        f"AGENT_NUM_DOCS_FOR_REFINED_DECOMPOSITION must be an integer, got {AGENT_NUM_DOCS_FOR_REFINED_DECOMPOSITION_OS}"
    )

AGENT_EXPLORATORY_SEARCH_RESULTS_OS: int | str = os.environ.get(
    "AGENT_EXPLORATORY_SEARCH_RESULTS", AGENT_DEFAULT_EXPLORATORY_SEARCH_RESULTS
)

try:
    AGENT_EXPLORATORY_SEARCH_RESULTS = int(AGENT_EXPLORATORY_SEARCH_RESULTS_OS)
except ValueError:
    raise ValueError(
        f"AGENT_EXPLORATORY_SEARCH_RESULTS must be an integer, got {AGENT_EXPLORATORY_SEARCH_RESULTS_OS}"
    )

AGENT_MIN_ORIG_QUESTION_DOCS_OS: int | str = os.environ.get(
    "AGENT_MIN_ORIG_QUESTION_DOCS", AGENT_DEFAULT_MIN_ORIG_QUESTION_DOCS
)

try:
    AGENT_MIN_ORIG_QUESTION_DOCS = int(AGENT_MIN_ORIG_QUESTION_DOCS_OS)
except ValueError:
    raise ValueError(
        f"AGENT_MIN_ORIG_QUESTION_DOCS must be an integer, got {AGENT_MIN_ORIG_QUESTION_DOCS_OS}"
    )

AGENT_MAX_ANSWER_CONTEXT_DOCS_OS: int | str = os.environ.get(
    "AGENT_MAX_ANSWER_CONTEXT_DOCS", AGENT_DEFAULT_SUB_QUESTION_MAX_CONTEXT_HITS
)

try:
    AGENT_MAX_ANSWER_CONTEXT_DOCS = int(AGENT_MAX_ANSWER_CONTEXT_DOCS_OS)
except ValueError:
    raise ValueError(
        f"AGENT_MAX_ANSWER_CONTEXT_DOCS must be an integer, got {AGENT_MAX_ANSWER_CONTEXT_DOCS_OS}"
    )

AGENT_MAX_STATIC_HISTORY_CHAR_LENGTH_OS: int | str = os.environ.get(
    "AGENT_MAX_STATIC_HISTORY_CHAR_LENGTH_OS",
    AGENT_DEFAULT_MAX_STATIC_HISTORY_CHAR_LENGTH,
)

try:
    AGENT_MAX_STATIC_HISTORY_CHAR_LENGTH = int(AGENT_MAX_STATIC_HISTORY_CHAR_LENGTH_OS)
except ValueError:
    raise ValueError(
        f"AGENT_MAX_STATIC_HISTORY_CHAR_LENGTH must be an integer, got {AGENT_MAX_STATIC_HISTORY_CHAR_LENGTH_OS}"
    )
