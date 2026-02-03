"""
Gemini Client module - Wrapper for Google's Gemini API.

Provides methods for generating compliance analysis responses
with appropriate system prompts.
"""

import logging

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from compliance_auditor.config import get_settings

logger = logging.getLogger(__name__)

# System prompts for different analysis tasks
GAP_ANALYSIS_PROMPT = """You are an expert compliance analyst. Your task is to analyze company policies
against regulatory requirements and identify compliance gaps.

For each gap found, provide:
1. The specific regulatory requirement
2. What the company policy states (or doesn't state)
3. The gap description
4. Risk level (High/Medium/Low)
5. Recommendation to close the gap

Be thorough but concise. Focus on actionable insights."""

POLICY_COMPARISON_PROMPT = """You are an expert policy analyst. Your task is to compare two documents
and identify similarities, differences, and potential conflicts.

Analyze:
1. Common topics covered by both documents
2. Key differences in approach or requirements
3. Any conflicts or contradictions
4. Elements present in one document but missing in the other

Provide a structured comparison that helps understand how the documents relate."""


class GeminiClient:
    """
    Client for Google's Gemini API.

    Handles model initialization and provides methods for
    compliance-specific text generation.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the Gemini client.

        Args:
            model_name: Gemini model to use (default: gemini-2.5-flash)
        """
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key)

        self.model = genai.GenerativeModel(model_name)
        logger.info(f"GeminiClient initialized with model: {model_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: User prompt
            system_prompt: Optional system instructions

        Returns:
            Generated text response
        """
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        response = self.model.generate_content(full_prompt)
        return response.text

    def analyze_compliance_gaps(
        self,
        regulation_text: str,
        company_policy_text: str,
        regulation_name: str = "Regulation",
        policy_name: str = "Company Policy",
    ) -> str:
        """
        Analyze compliance gaps between a regulation and company policy.

        Args:
            regulation_text: Relevant excerpts from the regulation
            company_policy_text: Relevant excerpts from the company policy
            regulation_name: Name of the regulation (for context)
            policy_name: Name of the company policy (for context)

        Returns:
            Structured gap analysis report
        """
        prompt = f"""
## Regulation: {regulation_name}
{regulation_text}

## Company Policy: {policy_name}
{company_policy_text}

Please analyze the company policy against the regulatory requirements and identify any compliance gaps.
"""
        return self.generate(prompt, system_prompt=GAP_ANALYSIS_PROMPT)

    def compare_policies(
        self,
        doc1_text: str,
        doc2_text: str,
        doc1_name: str = "Document 1",
        doc2_name: str = "Document 2",
    ) -> str:
        """
        Compare two policy documents.

        Args:
            doc1_text: Text from first document
            doc2_text: Text from second document
            doc1_name: Name of first document
            doc2_name: Name of second document

        Returns:
            Structured comparison report
        """
        prompt = f"""
## {doc1_name}
{doc1_text}

## {doc2_name}
{doc2_text}

Please compare these two documents and provide a detailed analysis of their similarities, differences, and any conflicts.
"""
        return self.generate(prompt, system_prompt=POLICY_COMPARISON_PROMPT)
