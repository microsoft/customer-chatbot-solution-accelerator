"""Unit tests for app.utils.llm_token_telemetry.

Covers:
- TokenUsage arithmetic and realtime sub-fields
- All extractors (dict / object / raw_representation / aggregated messages /
  streaming chunks / realtime / Mock-input safety)
- detect_invoked_tools
- TokenUsageEmitter: enabled/disabled, sink-throws-doesn't-propagate,
  static_dimensions merge, all typed emitters, emit_all distinct models
- TokenUsageScope: happy path, exception in body still emits, multi-add
"""
from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from app.utils.llm_token_telemetry import (
    EVENT_AGENT,
    EVENT_MODEL,
    EVENT_SPEECH,
    EVENT_SUMMARY,
    TokenUsage,
    TokenUsageEmitter,
    TokenUsageScope,
    detect_invoked_tools,
    extract_realtime_usage,
    extract_usage,
    extract_usage_from_dict,
    extract_usage_from_stream_chunk,
)


# ---------------------------------------------------------------------------
# TokenUsage
# ---------------------------------------------------------------------------
class TestTokenUsage:
    def test_has_any_false_when_zero(self):
        assert TokenUsage().has_any is False

    def test_has_any_true_when_any_nonzero(self):
        assert TokenUsage(input_tokens=1).has_any is True
        assert TokenUsage(total_tokens=5).has_any is True

    def test_addition_basic(self):
        a = TokenUsage(1, 2, 3)
        b = TokenUsage(4, 5, 9)
        assert a + b == TokenUsage(5, 7, 12)

    def test_addition_realtime_subfields(self):
        a = TokenUsage(1, 2, 3, input_audio_tokens=10)
        b = TokenUsage(4, 5, 9, input_audio_tokens=20, output_audio_tokens=7)
        c = a + b
        assert c.input_audio_tokens == 30
        assert c.output_audio_tokens == 7  # None + 7 -> 7

    def test_addition_returns_notimplemented_for_other_types(self):
        assert TokenUsage(1).__add__("nope") is NotImplemented

    def test_to_event_props_omits_none_subfields(self):
        props = TokenUsage(1, 2, 3).to_event_props()
        assert props == {"input_tokens": "1", "output_tokens": "2", "total_tokens": "3"}

    def test_to_event_props_includes_realtime_when_present(self):
        props = TokenUsage(1, 2, 3, input_audio_tokens=4).to_event_props()
        assert props["input_audio_tokens"] == "4"


# ---------------------------------------------------------------------------
# extract_usage_from_dict
# ---------------------------------------------------------------------------
class TestExtractFromDict:
    @pytest.mark.parametrize("data,expected", [
        ({"prompt_tokens": 12, "completion_tokens": 8}, (12, 8, 20)),
        ({"input_tokens": 5, "output_tokens": 7, "total_tokens": 12}, (5, 7, 12)),
        ({"input_token_count": 3, "output_token_count": 4}, (3, 4, 7)),
        ({"promptTokens": 1, "completionTokens": 2, "totalTokens": 3}, (1, 2, 3)),
    ])
    def test_aliases(self, data, expected):
        u = extract_usage_from_dict(data)
        assert (u.input_tokens, u.output_tokens, u.total_tokens) == expected

    def test_none_returns_none(self):
        assert extract_usage_from_dict(None) is None

    def test_empty_returns_none(self):
        assert extract_usage_from_dict({}) is None

    def test_total_falls_back_to_sum(self):
        u = extract_usage_from_dict({"input_tokens": 4, "output_tokens": 6})
        assert u.total_tokens == 10

    def test_string_digits_coerced(self):
        u = extract_usage_from_dict({"input_tokens": "10", "output_tokens": "20"})
        assert u.input_tokens == 10
        assert u.output_tokens == 20


# ---------------------------------------------------------------------------
# extract_usage (object shapes)
# ---------------------------------------------------------------------------
class _Bag:
    """Minimal attribute bag (acts like an SDK model object)."""
    pass


class TestExtractUsage:
    def test_usage_details_dict(self):
        r = _Bag()
        r.usage_details = {"input_token_count": 5, "output_token_count": 7}
        u = extract_usage(r)
        assert u.total_tokens == 12

    def test_usage_details_object(self):
        r = _Bag()
        details = _Bag()
        details.input_token_count = 5
        details.output_token_count = 7
        details.total_token_count = 12
        r.usage_details = details
        u = extract_usage(r)
        assert u.total_tokens == 12

    def test_raw_representation_openai_shape(self):
        r = _Bag()
        raw = _Bag()
        raw.usage = {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}
        r.raw_representation = raw
        u = extract_usage(r)
        assert (u.input_tokens, u.output_tokens, u.total_tokens) == (3, 4, 7)

    def test_aggregated_messages(self):
        r = _Bag()
        msg = _Bag()
        c1 = _Bag()
        c1.usage_details = {"input_tokens": 2, "output_tokens": 3}
        c2 = _Bag()
        c2.usage_details = {"input_tokens": 4, "output_tokens": 1}
        msg.contents = [c1, c2]
        r.messages = [msg]
        u = extract_usage(r)
        assert u.input_tokens == 6
        assert u.output_tokens == 4

    def test_none_input_returns_none(self):
        assert extract_usage(None) is None

    def test_no_usage_returns_none(self):
        assert extract_usage(_Bag()) is None

    def test_mock_input_does_not_raise(self):
        """Mock objects expose every attribute as another Mock -- previously
        this caused TypeError on iteration of .messages."""
        m = Mock()
        # Should silently return None, never raise.
        assert extract_usage(m) is None


# ---------------------------------------------------------------------------
# extract_usage_from_stream_chunk
# ---------------------------------------------------------------------------
class TestStreamChunk:
    def test_chunk_with_metadata_usage(self):
        c = _Bag()
        c.metadata = {"usage": {"input_tokens": 1, "output_tokens": 2}}
        u = extract_usage_from_stream_chunk(c)
        assert u.input_tokens == 1
        assert u.output_tokens == 2

    def test_no_usage_returns_none(self):
        assert extract_usage_from_stream_chunk(_Bag()) is None


# ---------------------------------------------------------------------------
# extract_realtime_usage
# ---------------------------------------------------------------------------
class TestRealtime:
    def test_basic(self):
        r = _Bag()
        r.usage = {
            "input_tokens": 3, "output_tokens": 4, "total_tokens": 7,
            "input_token_details": {"audio_tokens": 2, "text_tokens": 1, "cached_tokens": 0},
            "output_token_details": {"audio_tokens": 4, "text_tokens": 0},
        }
        u = extract_realtime_usage(r)
        assert u.input_audio_tokens == 2
        assert u.output_audio_tokens == 4
        assert u.total_tokens == 7

    def test_total_derived_when_missing(self):
        r = _Bag()
        r.usage = {"input_tokens": 3, "output_tokens": 4}
        u = extract_realtime_usage(r)
        assert u.total_tokens == 7

    def test_no_usage_returns_none(self):
        assert extract_realtime_usage(_Bag()) is None


# ---------------------------------------------------------------------------
# detect_invoked_tools
# ---------------------------------------------------------------------------
class TestDetectInvokedTools:
    def test_finds_function_calls(self):
        r = _Bag()
        c1 = _Bag()
        c1.type = "function_call"
        c1.name = "product_agent"
        c2 = _Bag()
        c2.type = "text"
        c2.name = "n/a"
        c3 = _Bag()
        c3.type = "function_call"
        c3.name = "policy_agent"
        msg = _Bag()
        msg.contents = [c1, c2, c3]
        r.messages = [msg]
        assert detect_invoked_tools(r) == {"product_agent", "policy_agent"}

    def test_empty_when_no_messages(self):
        assert detect_invoked_tools(_Bag()) == set()

    def test_mock_input_safe(self):
        assert detect_invoked_tools(Mock()) == set()

    def test_skips_function_calls_without_name(self):
        r = _Bag()
        c = _Bag()
        c.type = "function_call"
        c.name = None
        msg = _Bag()
        msg.contents = [c]
        r.messages = [msg]
        assert detect_invoked_tools(r) == set()


# ---------------------------------------------------------------------------
# TokenUsageEmitter
# ---------------------------------------------------------------------------
class TestEmitter:
    def _make(self, **kw):
        captured: list[tuple[str, dict]] = []
        kw.setdefault("connection_string", "fake-conn")
        kw.setdefault("event_sink", lambda n, p: captured.append((n, dict(p))))
        em = TokenUsageEmitter(**kw)
        return em, captured

    def test_disabled_when_no_connection_string(self):
        em = TokenUsageEmitter(connection_string="", event_sink=lambda *a: None)
        assert em.enabled is False

    def test_disabled_when_no_sink(self):
        em = TokenUsageEmitter(connection_string="x", event_sink=None)
        # _default_event_sink may or may not be available; force-disable:
        em._sink = None
        assert em.enabled is False

    def test_static_dimensions_prestringified_and_merged(self):
        em, captured = self._make(static_dimensions={"app": "x", "tenant": 42})
        em.emit("X", user_id="u1")
        name, props = captured[0]
        assert name == "X"
        assert props["app"] == "x"
        assert props["tenant"] == "42"  # stringified
        assert props["user_id"] == "u1"

    def test_call_dimension_overrides_static(self):
        em, captured = self._make(static_dimensions={"app": "default"})
        em.emit("X", app="override")
        assert captured[0][1]["app"] == "override"

    def test_none_dimension_dropped(self):
        em, captured = self._make()
        em.emit("X", user_id=None, session_id="s1")
        assert "user_id" not in captured[0][1]
        assert captured[0][1]["session_id"] == "s1"

    def test_sink_exception_does_not_propagate(self, caplog):
        def boom(_n, _p):
            raise RuntimeError("sink broken")
        em = TokenUsageEmitter(connection_string="x", event_sink=boom)
        with caplog.at_level(logging.WARNING):
            em.emit("X")  # must not raise

    def test_emit_agent_skips_zero_usage(self):
        em, captured = self._make()
        em.emit_agent(agent_name="a", model_deployment_name="m", usage=TokenUsage())
        assert captured == []

    def test_emit_agent_populates_props(self):
        em, captured = self._make()
        em.emit_agent(agent_name="chat", model_deployment_name="gpt-4o",
                      usage=TokenUsage(10, 20, 30), user_id="u")
        name, props = captured[0]
        assert name == EVENT_AGENT
        assert props["agent_name"] == "chat"
        assert props["model_deployment_name"] == "gpt-4o"
        assert props["total_tokens"] == "30"
        assert props["user_id"] == "u"

    def test_emit_all_emits_summary_agent_and_per_distinct_model(self):
        em, captured = self._make()
        em.emit_all(
            agent_name="orchestrator",
            model_deployment_name="gpt-4o",
            usage=TokenUsage(10, 20, 30),
            additional_agents={"tool_a": "gpt-4o", "tool_b": "gpt-35"},
            user_id="u1",
        )
        names = [n for n, _ in captured]
        # exactly one summary + one agent + two model events (gpt-4o, gpt-35)
        assert names.count(EVENT_SUMMARY) == 1
        assert names.count(EVENT_AGENT) == 1
        assert names.count(EVENT_MODEL) == 2
        # summary records agent + model counts
        summary = next(p for n, p in captured if n == EVENT_SUMMARY)
        assert summary["agent_count"] == "3"
        assert summary["model_count"] == "2"
        assert summary["total_input_tokens"] == "10"

    def test_emit_speech_includes_audio_subfields(self):
        em, captured = self._make()
        em.emit_speech(
            model_deployment_name="gpt-4o-realtime",
            source="voice_chat",
            usage=TokenUsage(1, 2, 3, input_audio_tokens=5, output_audio_tokens=6),
        )
        name, props = captured[0]
        assert name == EVENT_SPEECH
        assert props["source"] == "voice_chat"
        assert props["input_audio_tokens"] == "5"
        assert props["output_audio_tokens"] == "6"


# ---------------------------------------------------------------------------
# Pricing / cost computation
# ---------------------------------------------------------------------------
class TestPricing:
    def _make(self, pricing):
        captured: list[tuple[str, dict]] = []
        em = TokenUsageEmitter(
            connection_string="x",
            event_sink=lambda n, p: captured.append((n, dict(p))),
            pricing=pricing,
        )
        return em, captured

    def test_cost_attached_to_agent_event(self):
        em, captured = self._make({"gpt-4o": (0.0025, 0.01)})
        em.emit_agent(agent_name="a", model_deployment_name="gpt-4o",
                      usage=TokenUsage(1000, 500, 1500))
        # 1000 * 0.0025/1k + 500 * 0.01/1k = 0.0025 + 0.005 = 0.0075
        assert captured[0][1]["estimated_cost_usd"] == "0.007500"

    def test_cost_case_insensitive_model_lookup(self):
        em, captured = self._make({"GPT-4o": (0.001, 0.001)})
        em.emit_model(model_deployment_name="gpt-4o",
                      usage=TokenUsage(1000, 1000, 2000))
        assert "estimated_cost_usd" in captured[0][1]

    def test_no_cost_when_model_unknown(self):
        em, captured = self._make({"gpt-4o": (0.001, 0.001)})
        em.emit_agent(agent_name="a", model_deployment_name="gpt-mystery",
                      usage=TokenUsage(10, 10, 20))
        assert "estimated_cost_usd" not in captured[0][1]

    def test_summary_picks_up_cost_via_emit_all(self):
        em, captured = self._make({"gpt-4o": (0.0025, 0.01)})
        em.emit_all(agent_name="chat", model_deployment_name="gpt-4o",
                    usage=TokenUsage(1000, 500, 1500))
        summary = next(p for n, p in captured if n == EVENT_SUMMARY)
        assert summary["estimated_cost_usd"] == "0.007500"

    def test_malformed_pricing_entry_ignored(self, caplog):
        with caplog.at_level(logging.WARNING):
            em = TokenUsageEmitter(
                connection_string="x",
                event_sink=lambda *a: None,
                pricing={"bad-model": "not-a-tuple"},  # type: ignore[dict-item]
            )
        # Emitter still constructs; bad entry skipped.
        assert "bad-model" not in em._pricing


# ---------------------------------------------------------------------------
# user_id PII hashing
# ---------------------------------------------------------------------------
class TestUserIdHasher:
    def _make(self, hasher):
        captured: list[tuple[str, dict]] = []
        em = TokenUsageEmitter(
            connection_string="x",
            event_sink=lambda n, p: captured.append((n, dict(p))),
            user_id_hasher=hasher,
        )
        return em, captured

    def test_hasher_applied_to_call_kwargs(self):
        em, captured = self._make(lambda v: f"H({v})")
        em.emit("X", user_id="alice")
        assert captured[0][1]["user_id"] == "H(alice)"

    def test_hasher_applied_to_static_dimensions_at_construction(self):
        em = TokenUsageEmitter(
            connection_string="x",
            event_sink=lambda *a: None,
            user_id_hasher=lambda v: f"H({v})",
            static_dimensions={"user_id": "bob"},
        )
        assert em._static["user_id"] == "H(bob)"

    def test_hasher_exception_falls_back_to_raw(self, caplog):
        def boom(_v):
            raise RuntimeError("hasher broken")
        em, captured = self._make(boom)
        with caplog.at_level(logging.WARNING):
            em.emit("X", user_id="alice")
        # Falls back to original value -- never breaks telemetry.
        assert captured[0][1]["user_id"] == "alice"

    def test_no_hasher_passes_through(self):
        em, captured = self._make(None)
        em.emit("X", user_id="alice")
        assert captured[0][1]["user_id"] == "alice"

    def test_empty_user_id_not_hashed_or_emitted(self):
        em, captured = self._make(lambda v: f"H({v})")
        em.emit("X", user_id="")
        # Empty user_id should be dropped, not hashed to "H()".
        assert "user_id" not in captured[0][1]


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
class TestSampling:
    def _make(self, rate):
        captured: list[tuple[str, dict]] = []
        em = TokenUsageEmitter(
            connection_string="x",
            event_sink=lambda n, p: captured.append((n, dict(p))),
            sample_rate=rate,
        )
        return em, captured

    def test_rate_clamped_to_unit_interval(self):
        assert TokenUsageEmitter(connection_string="x", sample_rate=-0.5,
                                 event_sink=lambda *a: None).sample_rate == 0.0
        assert TokenUsageEmitter(connection_string="x", sample_rate=2.0,
                                 event_sink=lambda *a: None).sample_rate == 1.0

    def test_invalid_rate_defaults_to_one(self):
        em = TokenUsageEmitter(connection_string="x", sample_rate="nope",  # type: ignore[arg-type]
                               event_sink=lambda *a: None)
        assert em.sample_rate == 1.0

    def test_zero_rate_drops_agent_event(self):
        em, captured = self._make(0.0)
        em.emit_agent(agent_name="a", model_deployment_name="m",
                      usage=TokenUsage(1, 2, 3))
        assert captured == []

    def test_zero_rate_still_emits_summary(self):
        em, captured = self._make(0.0)
        em.emit_summary(usage=TokenUsage(1, 2, 3))
        assert captured and captured[0][0] == EVENT_SUMMARY

    def test_summary_records_sample_rate(self):
        em, captured = self._make(0.25)
        em.emit_summary(usage=TokenUsage(1, 2, 3))
        assert captured[0][1]["sample_rate"] == "0.2500"

    def test_emit_all_with_zero_rate_only_emits_summary(self):
        em, captured = self._make(0.0)
        em.emit_all(agent_name="chat", model_deployment_name="gpt-4o",
                    usage=TokenUsage(10, 20, 30))
        assert [n for n, _ in captured] == [EVENT_SUMMARY]

    def test_full_rate_emits_everything(self):
        em, captured = self._make(1.0)
        em.emit_all(agent_name="chat", model_deployment_name="gpt-4o",
                    usage=TokenUsage(10, 20, 30),
                    additional_agents={"a2": "gpt-35"})
        names = [n for n, _ in captured]
        assert EVENT_SUMMARY in names
        assert EVENT_AGENT in names
        assert names.count(EVENT_MODEL) == 2


# ---------------------------------------------------------------------------
# TokenUsageScope (continued)
# ---------------------------------------------------------------------------
class TestScope:
    def _emitter(self):
        captured: list[tuple[str, dict]] = []
        em = TokenUsageEmitter(
            connection_string="x",
            event_sink=lambda n, p: captured.append((n, dict(p))),
        )
        return em, captured

    def test_happy_path_emits_on_exit(self):
        em, captured = self._emitter()
        r = _Bag()
        r.usage_details = {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
        with TokenUsageScope(em, agent_name="a", model_deployment_name="m") as s:
            s.add(r)
        assert any(n == EVENT_SUMMARY for n, _ in captured)
        assert any(n == EVENT_AGENT for n, _ in captured)

    def test_multi_add_accumulates(self):
        em, captured = self._emitter()
        r1 = _Bag()
        r1.usage_details = {"input_tokens": 1, "output_tokens": 2}
        r2 = _Bag()
        r2.usage_details = {"input_tokens": 4, "output_tokens": 5}
        with TokenUsageScope(em, agent_name="a", model_deployment_name="m") as s:
            s.add(r1)
            s.add(r2)
        agent = next(p for n, p in captured if n == EVENT_AGENT)
        assert agent["input_tokens"] == "5"
        assert agent["output_tokens"] == "7"
        assert agent["total_tokens"] == "12"

    def test_exception_in_body_still_emits(self):
        em, captured = self._emitter()
        r = _Bag()
        r.usage_details = {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
        with pytest.raises(ValueError):
            with TokenUsageScope(em, agent_name="a", model_deployment_name="m") as s:
                s.add(r)
                raise ValueError("boom")
        # Emission still happened
        assert any(n == EVENT_AGENT for n, _ in captured)

    def test_add_with_mock_does_not_raise(self):
        em, _ = self._emitter()
        with TokenUsageScope(em, agent_name="a", model_deployment_name="m") as s:
            assert s.add(Mock()) is None

    def test_zero_usage_does_not_emit(self):
        em, captured = self._emitter()
        with TokenUsageScope(em, agent_name="a", model_deployment_name="m"):
            pass
        assert captured == []

    def test_dimensions_flow_to_events(self):
        em, captured = self._emitter()
        r = _Bag()
        r.usage_details = {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
        with TokenUsageScope(em, agent_name="a", model_deployment_name="m",
                             user_id="u1", session_id="s1") as s:
            s.add(r)
        for _, p in captured:
            assert p["user_id"] == "u1"
            assert p["session_id"] == "s1"

    def test_additional_agents_after_scope_open(self):
        em, captured = self._emitter()
        r = _Bag()
        r.usage_details = {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
        with TokenUsageScope(em, agent_name="orchestrator",
                             model_deployment_name="gpt-4o") as s:
            s.add(r)
            # Mutate additional_agents after the call -- mirrors the
            # detect_invoked_tools usage pattern.
            s.additional_agents["tool_a"] = "gpt-35"
        model_events = [p for n, p in captured if n == EVENT_MODEL]
        models = {p["model_deployment_name"] for p in model_events}
        assert models == {"gpt-4o", "gpt-35"}
