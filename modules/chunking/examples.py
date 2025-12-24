"""
Parent-Child Chunking Examples
==============================
Demonstrates hierarchical chunking with unique IDs and semantic ranking.
"""

import asyncio
import json
from parent_child_chunker import (
    ParentChildChunker,
    ChunkingConfig,
    SplitStrategy,
    SemanticRanker,
    create_search_index_schema
)


# =============================================================================
# SAMPLE DOCUMENTS
# =============================================================================

SAMPLE_DOCUMENT_1 = """
Azure AI Search Overview

Azure AI Search (formerly Azure Cognitive Search) is a cloud search service that gives developers APIs and tools for building rich search experiences. It provides full-text search, vector search, and semantic ranking capabilities.

Key Features:
- Full-text search with linguistic analysis
- Vector search for AI-powered similarity matching
- Semantic ranking for relevance tuning
- Integrated AI enrichment with Azure AI services

Architecture:
The service consists of an indexing pipeline that ingests data from various sources, an index that stores searchable content, and a query engine that processes search requests. Indexes can be configured with multiple fields, analyzers, and scoring profiles.

Indexing Pipeline:
Data flows from source systems through optional AI enrichment skills into the search index. Skills can extract entities, detect language, translate text, and generate embeddings for vector search.

Query Processing:
Queries are analyzed, matched against the index, and results are ranked. Semantic ranking uses machine learning to understand query intent and improve relevance.
"""

SAMPLE_DOCUMENT_2 = """
Machine Learning Model Deployment Best Practices

Deploying machine learning models to production requires careful planning. This guide covers essential considerations for successful deployments.

1. Model Versioning
Always version your models using semantic versioning. Track model lineage including training data, hyperparameters, and evaluation metrics. Use a model registry to manage versions.

2. Infrastructure Setup
Choose appropriate compute resources based on inference requirements. Consider CPU vs GPU trade-offs. Set up auto-scaling to handle variable loads.

3. Monitoring and Observability
Implement logging for all predictions. Track model drift by comparing production distributions to training data. Set up alerts for anomalies.

4. Security Considerations
Encrypt models at rest and in transit. Implement authentication for API endpoints. Follow principle of least privilege for access control.

5. Testing Strategy
Unit test preprocessing logic. Integration test the full pipeline. Load test to verify performance under peak conditions.
"""


# =============================================================================
# EXAMPLE 1: Basic Parent-Child Chunking
# =============================================================================

def example_basic_chunking():
    """Basic document chunking with default settings."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Parent-Child Chunking")
    print("=" * 60)

    chunker = ParentChildChunker()

    hierarchy = chunker.chunk_document(
        document_id="doc-001",
        text=SAMPLE_DOCUMENT_1,
        metadata={"source": "azure-docs", "category": "search"}
    )

    print(f"\nDocument ID: {hierarchy.document_id}")
    print(f"Total Parents: {hierarchy.total_parents}")
    print(f"Total Children: {hierarchy.total_children}")

    print("\n--- Parent Chunks ---")
    for parent in hierarchy.parent_chunks:
        print(f"\nID: {parent.chunk_id}")
        print(f"Position: {parent.position}")
        print(f"Content Preview: {parent.content[:100]}...")
        print(f"Character Range: {parent.start_char} - {parent.end_char}")

        children = hierarchy.get_children(parent.chunk_id)
        print(f"Children Count: {len(children)}")

    print("\n--- Sample Child Chunk ---")
    if hierarchy.child_chunks:
        child = hierarchy.child_chunks[0]
        print(f"ID: {child.chunk_id}")
        print(f"Parent ID: {child.parent_id}")
        print(f"Content: {child.content[:150]}...")


# =============================================================================
# EXAMPLE 2: Custom Configuration
# =============================================================================

def example_custom_config():
    """Chunking with custom configuration."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Custom Configuration")
    print("=" * 60)

    config = ChunkingConfig(
        parent_chunk_size=1500,
        parent_overlap=150,
        child_chunk_size=300,
        child_overlap=30,
        children_per_parent=4,
        split_strategy=SplitStrategy.SENTENCE,
        id_prefix="ml-doc",
        include_position_in_id=True,
        preserve_metadata=True
    )

    chunker = ParentChildChunker(config)

    hierarchy = chunker.chunk_document(
        document_id="ml-best-practices",
        text=SAMPLE_DOCUMENT_2,
        metadata={
            "author": "AI Team",
            "version": "1.0",
            "tags": ["ml", "deployment", "best-practices"]
        }
    )

    print(f"\nConfiguration:")
    print(f"  Parent Size: {config.parent_chunk_size} chars")
    print(f"  Child Size: {config.child_chunk_size} chars")
    print(f"  Children per Parent: {config.children_per_parent}")
    print(f"  Split Strategy: {config.split_strategy.value}")

    print(f"\nResults:")
    print(f"  Parents: {hierarchy.total_parents}")
    print(f"  Children: {hierarchy.total_children}")

    # Show hierarchy structure
    print("\n--- Hierarchy Structure ---")
    for parent in hierarchy.parent_chunks:
        children = hierarchy.get_children(parent.chunk_id)
        print(f"\n{parent.chunk_id}")
        for child in children:
            print(f"  └── {child.chunk_id}")


# =============================================================================
# EXAMPLE 3: Unique ID Verification
# =============================================================================

def example_unique_ids():
    """Demonstrate deterministic unique ID generation."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Unique ID Generation")
    print("=" * 60)

    chunker = ParentChildChunker()

    # Chunk same document twice
    hierarchy1 = chunker.chunk_document("doc-test", SAMPLE_DOCUMENT_1)
    hierarchy2 = chunker.chunk_document("doc-test", SAMPLE_DOCUMENT_1)

    print("\nDeterministic IDs (same content = same ID):")
    for p1, p2 in zip(hierarchy1.parent_chunks[:3], hierarchy2.parent_chunks[:3]):
        match = "✓" if p1.chunk_id == p2.chunk_id else "✗"
        print(f"  {match} Run 1: {p1.chunk_id}")
        print(f"    Run 2: {p2.chunk_id}")

    # Different document IDs produce different chunk IDs
    hierarchy3 = chunker.chunk_document("different-doc", SAMPLE_DOCUMENT_1)

    print("\nDifferent Doc ID = Different Chunk IDs:")
    print(f"  doc-test:      {hierarchy1.parent_chunks[0].chunk_id}")
    print(f"  different-doc: {hierarchy3.parent_chunks[0].chunk_id}")

    # ID structure breakdown
    sample_id = hierarchy1.parent_chunks[0].chunk_id
    parts = sample_id.split("_")
    print(f"\nID Structure: {sample_id}")
    print(f"  Prefix: {parts[0]}")
    print(f"  Type: {'parent' if parts[1] == 'p' else 'child'}")
    print(f"  Hash: {parts[2]}")


# =============================================================================
# EXAMPLE 4: Export to Azure AI Search Format
# =============================================================================

def example_search_export():
    """Export chunks to Azure AI Search document format."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Azure AI Search Export")
    print("=" * 60)

    chunker = ParentChildChunker()

    hierarchy = chunker.chunk_document(
        document_id="export-demo",
        text=SAMPLE_DOCUMENT_1[:800],  # Shorter for demo
        metadata={"source": "demo"}
    )

    # Get search documents
    search_docs = hierarchy.to_search_documents()

    print(f"\nGenerated {len(search_docs)} search documents")

    # Show sample parent document
    parent_doc = next(d for d in search_docs if d["chunk_type"] == "parent")
    print("\n--- Sample Parent Document ---")
    print(json.dumps({
        "id": parent_doc["id"],
        "chunk_type": parent_doc["chunk_type"],
        "content": parent_doc["content"][:100] + "...",
        "child_content": parent_doc["child_content"][:100] + "..." if parent_doc["child_content"] else None,
        "document_id": parent_doc["document_id"],
        "position": parent_doc["position"]
    }, indent=2))

    # Show sample child document
    child_doc = next(d for d in search_docs if d["chunk_type"] == "child")
    print("\n--- Sample Child Document ---")
    print(json.dumps({
        "id": child_doc["id"],
        "chunk_type": child_doc["chunk_type"],
        "parent_id": child_doc["parent_id"],
        "content": child_doc["content"][:100] + "...",
        "document_id": child_doc["document_id"]
    }, indent=2))

    # Show index schema
    print("\n--- Index Schema ---")
    schema = create_search_index_schema()
    print(f"Fields: {[f['name'] for f in schema['fields']]}")


# =============================================================================
# EXAMPLE 5: Semantic Ranking
# =============================================================================

def example_semantic_ranking():
    """Demonstrate semantic ranking of chunks."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Semantic Ranking")
    print("=" * 60)

    chunker = ParentChildChunker()

    hierarchy = chunker.chunk_document(
        document_id="ranking-demo",
        text=SAMPLE_DOCUMENT_2
    )

    # Simulate embeddings (in production, use real embedding model)
    def mock_embedding(text):
        """Create mock embedding based on keyword presence."""
        keywords = ["monitoring", "logging", "observability", "drift"]
        return [1.0 if kw in text.lower() else 0.0 for kw in keywords] + [0.5] * 1532

    # Add mock embeddings
    for chunk in hierarchy.child_chunks:
        chunk.embedding = mock_embedding(chunk.content)

    # Query embedding (focused on monitoring)
    query = "How to monitor ML models in production?"
    query_embedding = mock_embedding(query)

    # Rank chunks
    ranker = SemanticRanker()
    ranked_chunks = ranker.rank_by_query(hierarchy.child_chunks, query_embedding)

    print(f"\nQuery: {query}")
    print("\nTop 5 Ranked Child Chunks:")
    for i, chunk in enumerate(ranked_chunks[:5], 1):
        print(f"\n{i}. Score: {chunk.semantic_score:.4f}")
        print(f"   ID: {chunk.chunk_id}")
        print(f"   Content: {chunk.content[:80]}...")


# =============================================================================
# EXAMPLE 6: Paragraph-Based Splitting
# =============================================================================

def example_paragraph_splitting():
    """Use paragraph-based splitting strategy."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Paragraph-Based Splitting")
    print("=" * 60)

    config = ChunkingConfig(
        split_strategy=SplitStrategy.PARAGRAPH,
        parent_chunk_size=2500,
        child_chunk_size=500,
        children_per_parent=6
    )

    chunker = ParentChildChunker(config)

    hierarchy = chunker.chunk_document(
        document_id="paragraph-demo",
        text=SAMPLE_DOCUMENT_2
    )

    print(f"\nSplit Strategy: {config.split_strategy.value}")
    print(f"Parents: {hierarchy.total_parents}")
    print(f"Children: {hierarchy.total_children}")

    print("\n--- Child Chunks (Paragraph-Based) ---")
    for i, child in enumerate(hierarchy.child_chunks[:4], 1):
        print(f"\n{i}. {child.chunk_id}")
        print(f"   {child.content[:120]}...")


# =============================================================================
# EXAMPLE 7: Retrieval Pattern (Search Children, Return Parents)
# =============================================================================

def example_retrieval_pattern():
    """Common RAG pattern: Search children for precision, return parents for context."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Retrieval Pattern")
    print("=" * 60)

    chunker = ParentChildChunker()

    hierarchy = chunker.chunk_document(
        document_id="retrieval-demo",
        text=SAMPLE_DOCUMENT_2
    )

    # Simulate: Child chunk matched by search
    matched_child = hierarchy.child_chunks[3]

    print("Scenario: Search matched a child chunk")
    print(f"\nMatched Child ID: {matched_child.chunk_id}")
    print(f"Child Content: {matched_child.content[:100]}...")

    # Retrieve parent for full context
    parent = hierarchy.get_parent(matched_child.parent_id)

    print(f"\nParent Context (full chunk):")
    print(f"Parent ID: {parent.chunk_id}")
    print(f"Parent Content: {parent.content[:200]}...")

    # Get sibling children for additional context
    siblings = hierarchy.get_children(parent.chunk_id)

    print(f"\nSibling chunks in same parent: {len(siblings)}")
    for sib in siblings:
        marker = "→ " if sib.chunk_id == matched_child.chunk_id else "  "
        print(f"{marker}{sib.chunk_id}: {sib.content[:50]}...")


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

def main():
    """Run all examples."""
    example_basic_chunking()
    example_custom_config()
    example_unique_ids()
    example_search_export()
    example_semantic_ranking()
    example_paragraph_splitting()
    example_retrieval_pattern()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
