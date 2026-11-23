
import unittest
from unittest.mock import patch

from backend.app.agents.orchestration_agent import process_query


class TestOrchestrationAgent(unittest.TestCase):

    @patch(
        "backend.app.agents.orchestration_agent.generate_response"
    )
    @patch(
        "backend.app.agents.orchestration_agent.retrieve_with_agent"
    )
    def test_factual_query(
        self,
        mock_retrieval,
        mock_response
    ):
        mock_retrieval.return_value = {
            "success": True,
            "status": "retrieved",
            "results_count": 1,
            "retrieval_confidence": 0.85,
            "results": [{"source": "notes.pdf", "text": "Sample facts"}]
        }

        mock_response.return_value = {
            "success": True,
            "status": "generated",
            "answer": "This is a factual answer. [Source 1]",
            "sources": [{"source_id": "Source 1"}]
        }

        result = process_query("What is artificial intelligence?")

        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["classification"]["query_type"], "factual")
        mock_retrieval.assert_called_once()
        mock_response.assert_called_once()

    @patch(
        "backend.app.agents.orchestration_agent.generate_response"
    )
    @patch(
        "backend.app.agents.orchestration_agent.retrieve_with_agent"
    )
    def test_procedural_query(
        self,
        mock_retrieval,
        mock_response
    ):
        mock_retrieval.return_value = {
            "success": True,
            "status": "retrieved",
            "results_count": 1,
            "retrieval_confidence": 0.80,
            "results": [{"source": "guide.pdf", "text": "Step 1"}]
        }

        mock_response.return_value = {
            "success": True,
            "status": "generated",
            "answer": "Follow these steps. [Source 1]",
            "sources": [{"source_id": "Source 1"}]
        }

        result = process_query("How to configure a network?")

        self.assertEqual(result["classification"]["query_type"], "procedural")
        self.assertEqual(result["status"], "generated")
        mock_retrieval.assert_called_once()

    @patch(
        "backend.app.agents.orchestration_agent.generate_response"
    )
    @patch(
        "backend.app.agents.orchestration_agent.retrieve_with_agent"
    )
    def test_comparative_query(
        self,
        mock_retrieval,
        mock_response
    ):
        mock_retrieval.return_value = {
            "success": True,
            "status": "retrieved",
            "results_count": 1,
            "retrieval_confidence": 0.75,
            "results": [{"source": "comparison.pdf", "text": "Comparison data"}]
        }

        mock_response.return_value = {
            "success": True,
            "status": "generated",
            "answer": "Here is the comparison. [Source 1]",
            "sources": [{"source_id": "Source 1"}]
        }

        result = process_query("Compare TCP and UDP.")

        self.assertEqual(result["classification"]["query_type"], "comparative")
        self.assertEqual(result["status"], "generated")
        mock_retrieval.assert_called_once()

    @patch(
        "backend.app.agents.orchestration_agent.retrieve_with_agent"
    )
    def test_ambiguous_query(self, mock_retrieval):
        result = process_query("Tell me more.")

        self.assertEqual(result["status"], "clarification_required")
        self.assertTrue(
            result["classification"]["requires_clarification"]
        )
        self.assertIsNotNone(result["clarification"])
        self.assertIsNone(result["retrieval"])
        mock_retrieval.assert_not_called()

    @patch(
        "backend.app.agents.orchestration_agent.generate_response"
    )
    @patch(
        "backend.app.agents.orchestration_agent.retrieve_with_agent"
    )
    def test_no_relevant_results(
        self,
        mock_retrieval,
        mock_response
    ):
        mock_retrieval.return_value = {
            "success": True,
            "status": "no_relevant_results",
            "results_count": 0,
            "retrieval_confidence": 0.0,
            "results": []
        }

        mock_response.return_value = {
            "success": True,
            "status": "no_relevant_results",
            "answer": "No relevant information found.",
            "sources": []
        }

        result = process_query("What is artificial intelligence?")

        self.assertEqual(result["status"], "no_relevant_results")
        mock_response.assert_called_once()

    @patch(
        "backend.app.agents.orchestration_agent.generate_response"
    )
    @patch(
        "backend.app.agents.orchestration_agent.retrieve_with_agent"
    )
    def test_generation_failure(
        self,
        mock_retrieval,
        mock_response
    ):
        mock_retrieval.return_value = {
            "success": True,
            "status": "retrieved",
            "results_count": 1,
            "retrieval_confidence": 0.80,
            "results": [{"source": "notes.pdf", "text": "Sample facts"}]
        }

        mock_response.return_value = {
            "success": False,
            "status": "generation_failed",
            "answer": None,
            "sources": [],
            "message": "Generation failed."
        }

        result = process_query("What is artificial intelligence?")

        self.assertEqual(result["status"], "generation_failed")
        self.assertFalse(result["success"])

    def test_empty_query(self):
        with self.assertRaises(ValueError):
            process_query("")

    def test_invalid_top_k(self):
        with self.assertRaises(ValueError):
            process_query("What is artificial intelligence?", top_k=0)


if __name__ == "__main__":
    unittest.main()
