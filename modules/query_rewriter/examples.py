"""
Query Rewriter Examples
=======================
Demonstrates query rewriting with follow-up question generation.
"""

import asyncio
from rewriter import QueryRewriter, ClarificationType


# =============================================================================
# EXAMPLE 1: Basic Query Rewriting
# =============================================================================

async def example_basic_rewriting():
    """Basic query rewriting without LLM."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Query Rewriting")
    print("=" * 60)

    rewriter = QueryRewriter()

    # Ambiguous query
    query = "How do I fix the error?"
    result = await rewriter.rewrite(query)

    print(f"\nOriginal Query: {query}")
    print(f"Detected Intent: {result.detected_intent.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Needs Clarification: {result.needs_clarification}")

    print("\nRewritten Queries:")
    for i, q in enumerate(result.rewritten_queries, 1):
        print(f"  {i}. {q}")

    print("\nFollow-up Questions:")
    for fq in result.follow_up_questions:
        print(f"  [{fq.priority}] {fq.question}")
        if fq.options:
            print(f"      Options: {', '.join(fq.options)}")


# =============================================================================
# EXAMPLE 2: Troubleshooting Query
# =============================================================================

async def example_troubleshooting():
    """Troubleshooting query with context gathering."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Troubleshooting Query")
    print("=" * 60)

    rewriter = QueryRewriter()

    query = "My API is not working"
    result = await rewriter.rewrite(query)

    print(f"\nOriginal Query: {query}")
    print(f"Detected Intent: {result.detected_intent.value}")
    print(f"Ambiguity Score: {result.metadata['ambiguity_score']:.2f}")

    print("\nFollow-up Questions for Troubleshooting:")
    for fq in result.follow_up_questions:
        print(f"  Q: {fq.question}")
        print(f"     Type: {fq.clarification_type.value}")

    # Simulate user answering follow-ups
    print("\n--- User provides clarification ---")
    if result.follow_up_questions:
        rewriter.apply_clarification(
            result.follow_up_questions[0].question_id,
            "Getting 401 Unauthorized error"
        )

    refined = rewriter.get_refined_query()
    print(f"\nRefined Query: {refined}")


# =============================================================================
# EXAMPLE 3: Comparative Query
# =============================================================================

async def example_comparative():
    """Comparative query with preference options."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Comparative Query")
    print("=" * 60)

    rewriter = QueryRewriter()

    query = "Azure Cosmos DB vs MongoDB - which is better?"
    result = await rewriter.rewrite(query)

    print(f"\nOriginal Query: {query}")
    print(f"Detected Intent: {result.detected_intent.value}")
    print(f"Extracted Technologies: {result.entities['technologies']}")

    print("\nRewritten Queries:")
    for q in result.rewritten_queries:
        print(f"  - {q}")

    print("\nFollow-up to Refine Comparison:")
    for fq in result.follow_up_questions:
        print(f"  Q: {fq.question}")
        if fq.options:
            print(f"     Choose from: {fq.options}")


# =============================================================================
# EXAMPLE 4: Multi-Turn Conversation
# =============================================================================

async def example_multi_turn():
    """Multi-turn conversation with progressive clarification."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Multi-Turn Conversation")
    print("=" * 60)

    rewriter = QueryRewriter()

    # Turn 1: Vague query
    print("\n--- Turn 1 ---")
    query1 = "How do I set up the thing?"
    result1 = await rewriter.rewrite(query1)
    print(f"User: {query1}")
    print(f"Confidence: {result1.confidence:.2f}")
    print(f"Follow-up: {result1.follow_up_questions[0].question if result1.follow_up_questions else 'None'}")

    # User clarifies
    if result1.follow_up_questions:
        rewriter.apply_clarification(
            result1.follow_up_questions[0].question_id,
            "I mean the Azure Search index"
        )

    # Turn 2: More specific
    print("\n--- Turn 2 ---")
    query2 = "How do I configure it for semantic search?"
    result2 = await rewriter.rewrite(
        query2,
        conversation_context=rewriter.conversation_history
    )
    print(f"User: {query2}")
    print(f"Confidence: {result2.confidence:.2f}")

    # Get final refined query
    refined = rewriter.get_refined_query()
    print(f"\nFinal Refined Query: {refined}")


# =============================================================================
# EXAMPLE 5: Procedural Query with Experience Level
# =============================================================================

async def example_procedural():
    """Procedural query adjusting for experience level."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Procedural Query")
    print("=" * 60)

    rewriter = QueryRewriter()

    query = "How to deploy a Kubernetes cluster on Azure?"
    result = await rewriter.rewrite(query)

    print(f"\nOriginal Query: {query}")
    print(f"Detected Intent: {result.detected_intent.value}")
    print(f"Technologies Found: {result.entities['technologies']}")

    print("\nRewritten for Search:")
    for q in result.rewritten_queries:
        print(f"  - {q}")

    print("\nFollow-up for Personalization:")
    for fq in result.follow_up_questions:
        if fq.clarification_type == ClarificationType.PREFERENCE:
            print(f"  Q: {fq.question}")
            print(f"     Options: {fq.options}")


# =============================================================================
# EXAMPLE 6: Clear Query (No Clarification Needed)
# =============================================================================

async def example_clear_query():
    """Clear, specific query that doesn't need clarification."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Clear Query")
    print("=" * 60)

    rewriter = QueryRewriter()

    query = "What is the maximum document size limit for Azure Cognitive Search indexing in the Standard S2 tier?"
    result = await rewriter.rewrite(query)

    print(f"\nOriginal Query: {query}")
    print(f"Detected Intent: {result.detected_intent.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Needs Clarification: {result.needs_clarification}")
    print(f"Follow-ups Generated: {len(result.follow_up_questions)}")

    print("\nThis query is specific enough - proceed directly to search.")


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

async def main():
    """Run all examples."""
    await example_basic_rewriting()
    await example_troubleshooting()
    await example_comparative()
    await example_multi_turn()
    await example_procedural()
    await example_clear_query()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
