"""
Tests — AI Pipeline
Run: pytest tests/ -v

Tests the full stack without hitting real APIs (mocked).
Also has integration test markers that hit real APIs when INTEGRATION=1.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# ── Unit tests ────────────────────────────────────────────────────────────────

class TestIntentExtractor:
    """Test LLM intent extraction logic."""

    @pytest.mark.asyncio
    async def test_fees_intent(self):
        mock_response = {
            "intents": ["fees"],
            "entities": {"doctor_name_normalized": "ravi", "speciality_normalized": None}
        }
        with patch("app.services.intent_extractor.groq_client") as mock_groq:
            mock_groq.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='{"intents":["fees"],"entities":{"doctor_name_normalized":"ravi","speciality_normalized":null,"patient_name":null,"date":null,"time_preference":null,"confirmation":null,"emotion":null,"is_correction":false,"need_alternative":false,"same_problem":false}}'))]
                )
            )
            from app.services.intent_extractor import extract
            result = await extract("Dr Ravi fee enna?")

        assert "fees" in result["intents"]

    @pytest.mark.asyncio
    async def test_unknown_input_returns_dict(self):
        with patch("app.services.intent_extractor.groq_client") as mock_groq:
            mock_groq.chat.completions.create = AsyncMock(side_effect=Exception("network"))
            from app.services.intent_extractor import extract
            result = await extract("asdfasdf")

        assert "intents" in result
        assert "unknown" in result["intents"]


class TestSessionService:
    """Test Redis session management."""

    @pytest.mark.asyncio
    async def test_get_session_default(self):
        with patch("app.services.session_service.redis_client") as mock_redis:
            mock_redis.get_session = AsyncMock(return_value={
                "state": "active",
                "data": {"doctor": None, "speciality": None, "date": None,
                         "time_preference": None, "last_intent": None, "need_alternative": False}
            })
            from app.services.session_service import get_session
            session = await get_session("+91test123")

        assert session["state"] == "active"
        assert session["data"]["doctor"] is None

    def test_merge_entities_doctor(self):
        from app.services.session_service import merge_entities
        session = {"data": {"doctor": None, "speciality": None, "date": None,
                            "time_preference": None, "need_alternative": False}}
        entities = {"doctor_name_normalized": "ravi", "speciality_normalized": None}
        result = merge_entities(session, entities)
        assert result["data"]["doctor"] == "ravi"

    def test_merge_entities_speciality_resets_doctor(self):
        from app.services.session_service import merge_entities
        session = {"data": {"doctor": "ravi", "speciality": None, "date": None,
                            "time_preference": None, "need_alternative": False}}
        entities = {"speciality_normalized": "cardiology"}
        result = merge_entities(session, entities)
        assert result["data"]["speciality"] == "cardiology"
        assert result["data"]["doctor"] is None   # reset


class TestAIBrain:
    """Test clinic logic engine."""

    @pytest.mark.asyncio
    async def test_fees_with_doctor(self):
        doctors = [
            {"id": "1", "name": "Dr Ravi", "speciality": "General",
             "consultation_fee": 300, "schedule_days": ["mon","wed","fri"],
             "schedule_sessions": ["morning"]}
        ]
        with patch("app.services.ai_brain.doctor_service.get_doctors", AsyncMock(return_value=doctors)):
            from app.services.ai_brain import run
            reply = await run(
                intents=["fees"],
                entities={"doctor_name_normalized": "ravi"},
                session={"data": {}},
                clinic_id="test-clinic"
            )
        assert "300" in reply
        assert "Ravi" in reply

    @pytest.mark.asyncio
    async def test_no_doctors_ask_name(self):
        doctors = [
            {"id": "1", "name": "Dr Meena", "speciality": "Gynecology",
             "consultation_fee": 400, "schedule_days": ["tue","thu"],
             "schedule_sessions": ["morning"]},
            {"id": "2", "name": "Dr Kumar", "speciality": "General",
             "consultation_fee": 250, "schedule_days": ["mon","wed","fri"],
             "schedule_sessions": ["evening"]}
        ]
        with patch("app.services.ai_brain.doctor_service.get_doctors", AsyncMock(return_value=doctors)):
            from app.services.ai_brain import run
            reply = await run(
                intents=["doctor_available"],
                entities={},
                session={"data": {"doctor": None, "speciality": None}},
                clinic_id="test-clinic"
            )
        assert "Meena" in reply or "Kumar" in reply


class TestRedisRateLimit:
    """Test sliding window rate limiter."""

    @pytest.mark.asyncio
    async def test_allows_under_limit(self):
        with patch("app.core.redis_client.redis_client._client") as mock:
            mock.pipeline.return_value.__aenter__ = AsyncMock()
            mock.pipeline.return_value.execute = AsyncMock(return_value=[1, True])
            mock.pipeline.return_value.incr = MagicMock()
            mock.pipeline.return_value.expire = MagicMock()

            from app.core.redis_client import RedisClient
            client = RedisClient()
            client._client = mock

            # Simulate pipeline correctly
            pipe = MagicMock()
            pipe.execute = AsyncMock(return_value=[5, True])
            mock.pipeline = MagicMock(return_value=pipe)

            result = await client.check_rate_limit("test-ip", limit=60)
            # count=5 < limit=60 → allowed
            assert result is True


# ── Integration tests (run with INTEGRATION=1 env var) ───────────────────────

@pytest.mark.skipif(
    not __import__("os").environ.get("INTEGRATION"),
    reason="Set INTEGRATION=1 to run integration tests"
)
class TestIntegration:
    """Full pipeline integration tests — hits real APIs."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        from app.services.ai_service import process_message
        reply = await process_message(
            "Dr Ravi eppo varuvaanga?",
            phone="+91test",
            clinic_id=__import__("os").environ.get("DEFAULT_CLINIC_ID", "")
        )
        assert isinstance(reply, str)
        assert len(reply) > 0