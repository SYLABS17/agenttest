"""
Query Rewriter with Follow-Up Question Generation
==================================================
Advanced RAG component for query understanding and clarification.

Features:
- Query expansion and reformulation
- Intent detection
- Follow-up question generation
- Multi-turn conversation support
- Ambiguity detection
"""

import json
import re
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class QueryIntent(Enum):
    """Detected intent types for queries."""
    FACTUAL = "factual"           # Looking for specific facts
    EXPLORATORY = "exploratory"   # Open-ended exploration
    COMPARATIVE = "comparative"   # Comparing options
    PROCEDURAL = "procedural"     # How-to questions
    TROUBLESHOOT = "troubleshoot" # Problem-solving
    AMBIGUOUS = "ambiguous"       # Unclear intent


class ClarificationType(Enum):
    """Types of clarification needed."""
    SCOPE = "scope"               # Narrow down scope
    TIMEFRAME = "timeframe"       # Specify time period
    CONTEXT = "context"           # Add context
    PREFERENCE = "preference"     # User preferences
    SPECIFICITY = "specificity"   # More specific details


@dataclass
class FollowUpQuestion:
    """A follow-up question for clarification."""
    question_id: str
    question: str
    clarification_type: ClarificationType
    options: list = field(default_factory=list)  # Optional multiple choice
    priority: int = 1  # 1=high, 2=medium, 3=low
    context: str = ""


@dataclass
class RewrittenQuery:
    """Result of query rewriting."""
    original_query: str
    rewritten_queries: list          # Multiple reformulations
    detected_intent: QueryIntent
    entities: dict                   # Extracted entities
    follow_up_questions: list        # FollowUpQuestion list
    confidence: float                # 0.0 to 1.0
    needs_clarification: bool
    metadata: dict = field(default_factory=dict)


class QueryRewriter:
    """
    Rewrites queries for better retrieval and generates follow-up questions.

    Usage:
        rewriter = QueryRewriter()
        result = await rewriter.rewrite("How do I fix the error?")

        if result.needs_clarification:
            for q in result.follow_up_questions:
                print(f"Follow-up: {q.question}")
    """

    # Ambiguity indicators
    AMBIGUOUS_TERMS = [
        "it", "this", "that", "thing", "stuff", "issue", "problem",
        "error", "something", "anything", "everything", "the one"
    ]

    # Intent patterns
    INTENT_PATTERNS = {
        QueryIntent.PROCEDURAL: [
            r"\bhow (do|can|to|should)\b", r"\bsteps to\b", r"\bprocess of\b",
            r"\bway to\b", r"\bguide\b", r"\btutorial\b"
        ],
        QueryIntent.COMPARATIVE: [
            r"\bvs\.?\b", r"\bversus\b", r"\bcompare\b", r"\bdifference\b",
            r"\bbetter\b", r"\bworse\b", r"\bor\b.*\bor\b"
        ],
        QueryIntent.TROUBLESHOOT: [
            r"\berror\b", r"\bfail\b", r"\bnot working\b", r"\bbroken\b",
            r"\bfix\b", r"\bsolve\b", r"\bdebug\b", r"\bissue\b"
        ],
        QueryIntent.FACTUAL: [
            r"\bwhat is\b", r"\bwho is\b", r"\bwhen\b", r"\bwhere\b",
            r"\bdefine\b", r"\bmeaning of\b"
        ],
        QueryIntent.EXPLORATORY: [
            r"\btell me about\b", r"\bexplain\b", r"\boverview\b",
            r"\blearn about\b", r"\bunderstand\b"
        ]
    }

    # Follow-up templates by clarification type
    FOLLOWUP_TEMPLATES = {
        ClarificationType.SCOPE: [
            "Which specific {entity} are you referring to?",
            "Are you asking about {option1} or {option2}?",
            "Could you specify which area/component you mean?"
        ],
        ClarificationType.TIMEFRAME: [
            "What time period are you interested in?",
            "Are you looking for recent information or historical data?",
            "Should I focus on the latest version or a specific release?"
        ],
        ClarificationType.CONTEXT: [
            "What is your current setup or environment?",
            "Can you provide more background on what you're trying to achieve?",
            "What have you already tried?"
        ],
        ClarificationType.PREFERENCE: [
            "Do you prefer a detailed explanation or a quick summary?",
            "Are you looking for code examples or conceptual explanation?",
            "What's your experience level with this topic?"
        ],
        ClarificationType.SPECIFICITY: [
            "Could you be more specific about {aspect}?",
            "What exactly do you mean by '{term}'?",
            "Can you describe the expected vs actual behavior?"
        ]
    }

    def __init__(self, llm_client=None):
        """
        Initialize query rewriter.

        Args:
            llm_client: Optional LLM client for advanced rewriting
        """
        self.llm_client = llm_client
        self.conversation_history = []

    def _generate_id(self, text: str) -> str:
        """Generate unique ID for a question."""
        return f"fq_{hashlib.md5(text.encode()).hexdigest()[:8]}"

    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the intent of a query."""
        query_lower = query.lower()

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent

        # Check for ambiguity
        for term in self.AMBIGUOUS_TERMS:
            if re.search(rf"\b{term}\b", query_lower):
                return QueryIntent.AMBIGUOUS

        return QueryIntent.EXPLORATORY

    def _extract_entities(self, query: str) -> dict:
        """Extract entities from query."""
        entities = {
            "technologies": [],
            "actions": [],
            "objects": [],
            "modifiers": []
        }

        # Technology keywords
        tech_patterns = [
            r"\b(azure|aws|gcp|python|javascript|api|database|sql|nosql)\b",
            r"\b(kubernetes|docker|terraform|react|node)\b",
            r"\b(ai|ml|llm|gpt|search|index)\b"
        ]
        for pattern in tech_patterns:
            matches = re.findall(pattern, query.lower())
            entities["technologies"].extend(matches)

        # Action verbs
        action_patterns = r"\b(create|update|delete|get|set|configure|deploy|build|fix|debug)\b"
        entities["actions"] = re.findall(action_patterns, query.lower())

        return entities

    def _calculate_ambiguity_score(self, query: str) -> float:
        """Calculate how ambiguous a query is (0=clear, 1=very ambiguous)."""
        score = 0.0
        query_lower = query.lower()
        words = query_lower.split()

        # Short queries are more ambiguous
        if len(words) < 4:
            score += 0.3

        # Check for ambiguous terms
        for term in self.AMBIGUOUS_TERMS:
            if term in query_lower:
                score += 0.15

        # Missing context indicators
        if not any(word in query_lower for word in ["in", "for", "with", "using", "about"]):
            score += 0.1

        # Questions without specifics
        if query.endswith("?") and len(words) < 6:
            score += 0.2

        return min(score, 1.0)

    def _generate_follow_ups(
        self,
        query: str,
        intent: QueryIntent,
        entities: dict,
        ambiguity_score: float
    ) -> list:
        """Generate relevant follow-up questions."""
        follow_ups = []

        # High ambiguity - ask for specificity
        if ambiguity_score > 0.5:
            for term in self.AMBIGUOUS_TERMS:
                if term in query.lower():
                    q = FollowUpQuestion(
                        question_id=self._generate_id(f"spec_{term}"),
                        question=f"Could you clarify what you mean by '{term}'?",
                        clarification_type=ClarificationType.SPECIFICITY,
                        priority=1
                    )
                    follow_ups.append(q)
                    break

        # Intent-specific follow-ups
        if intent == QueryIntent.TROUBLESHOOT:
            follow_ups.extend([
                FollowUpQuestion(
                    question_id=self._generate_id("error_msg"),
                    question="What is the exact error message you're seeing?",
                    clarification_type=ClarificationType.CONTEXT,
                    priority=1
                ),
                FollowUpQuestion(
                    question_id=self._generate_id("tried"),
                    question="What have you already tried to resolve this?",
                    clarification_type=ClarificationType.CONTEXT,
                    priority=2
                )
            ])

        if intent == QueryIntent.PROCEDURAL:
            follow_ups.append(
                FollowUpQuestion(
                    question_id=self._generate_id("exp_level"),
                    question="What's your experience level with this topic?",
                    clarification_type=ClarificationType.PREFERENCE,
                    options=["Beginner", "Intermediate", "Advanced"],
                    priority=2
                )
            )

        if intent == QueryIntent.COMPARATIVE:
            follow_ups.append(
                FollowUpQuestion(
                    question_id=self._generate_id("criteria"),
                    question="What criteria are most important for your comparison?",
                    clarification_type=ClarificationType.PREFERENCE,
                    options=["Cost", "Performance", "Ease of use", "Features"],
                    priority=1
                )
            )

        # Context-based follow-ups
        if not entities["technologies"]:
            follow_ups.append(
                FollowUpQuestion(
                    question_id=self._generate_id("tech_stack"),
                    question="What technology stack or platform are you working with?",
                    clarification_type=ClarificationType.CONTEXT,
                    priority=2
                )
            )

        # Limit to top 3 by priority
        follow_ups.sort(key=lambda x: x.priority)
        return follow_ups[:3]

    def _expand_query(self, query: str, entities: dict) -> list:
        """Generate multiple query reformulations."""
        expansions = [query]  # Original always included

        # Add entity-enriched version
        if entities["technologies"]:
            tech_str = " ".join(entities["technologies"])
            expansions.append(f"{query} ({tech_str})")

        # Add action-focused version
        if entities["actions"]:
            action = entities["actions"][0]
            expansions.append(f"How to {action}: {query}")

        # Add semantic variations
        semantic_expansions = {
            "fix": ["resolve", "solve", "troubleshoot"],
            "create": ["build", "make", "set up"],
            "get": ["retrieve", "fetch", "obtain"],
            "error": ["issue", "problem", "failure"]
        }

        for word, synonyms in semantic_expansions.items():
            if word in query.lower():
                for syn in synonyms[:1]:  # Add one synonym version
                    expansions.append(query.lower().replace(word, syn))
                break

        return list(set(expansions))  # Remove duplicates

    async def rewrite(
        self,
        query: str,
        conversation_context: list = None,
        require_clarification: bool = True
    ) -> RewrittenQuery:
        """
        Rewrite a query for better retrieval.

        Args:
            query: User's original query
            conversation_context: Previous turns for context
            require_clarification: Whether to generate follow-up questions

        Returns:
            RewrittenQuery with reformulations and follow-ups
        """
        # Store in conversation history
        if conversation_context:
            self.conversation_history = conversation_context
        self.conversation_history.append({"role": "user", "query": query})

        # Detect intent and extract entities
        intent = self._detect_intent(query)
        entities = self._extract_entities(query)
        ambiguity_score = self._calculate_ambiguity_score(query)

        # Generate query expansions
        rewritten_queries = self._expand_query(query, entities)

        # Generate follow-up questions if needed
        follow_ups = []
        if require_clarification and ambiguity_score > 0.3:
            follow_ups = self._generate_follow_ups(query, intent, entities, ambiguity_score)

        # Use LLM for advanced rewriting if available
        if self.llm_client:
            llm_result = await self._llm_rewrite(query, intent, entities)
            if llm_result:
                rewritten_queries.extend(llm_result.get("queries", []))
                follow_ups.extend(llm_result.get("follow_ups", []))

        return RewrittenQuery(
            original_query=query,
            rewritten_queries=rewritten_queries,
            detected_intent=intent,
            entities=entities,
            follow_up_questions=follow_ups,
            confidence=1.0 - ambiguity_score,
            needs_clarification=len(follow_ups) > 0 and ambiguity_score > 0.4,
            metadata={
                "ambiguity_score": ambiguity_score,
                "conversation_turn": len(self.conversation_history)
            }
        )

    async def _llm_rewrite(self, query: str, intent: QueryIntent, entities: dict) -> dict:
        """Use LLM for advanced query rewriting (if client available)."""
        if not self.llm_client:
            return None

        prompt = f"""Rewrite this query for semantic search retrieval.
Original: {query}
Intent: {intent.value}
Entities: {json.dumps(entities)}

Return JSON with:
- queries: list of 2-3 reformulated queries
- follow_ups: list of clarifying questions if the query is ambiguous
"""
        try:
            response = await self.llm_client.complete(prompt)
            return json.loads(response)
        except Exception:
            return None

    def apply_clarification(self, question_id: str, answer: str) -> None:
        """
        Apply user's answer to a follow-up question.

        Args:
            question_id: ID of the follow-up question
            answer: User's answer
        """
        self.conversation_history.append({
            "role": "clarification",
            "question_id": question_id,
            "answer": answer
        })

    def get_refined_query(self) -> str:
        """Get refined query based on all clarifications."""
        if len(self.conversation_history) < 2:
            return self.conversation_history[0]["query"] if self.conversation_history else ""

        # Combine original query with clarifications
        original = self.conversation_history[0]["query"]
        clarifications = [
            h["answer"] for h in self.conversation_history
            if h.get("role") == "clarification"
        ]

        if clarifications:
            return f"{original} (Context: {'; '.join(clarifications)})"
        return original
