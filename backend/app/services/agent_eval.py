"""Optional AgentEval observability for Veriq interview turns."""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class _SafeAgentEvalCallback(BaseCallbackHandler):
    """Keep AgentEval transport failures outside the interview execution path."""

    def __init__(self, callback: Any):
        self._callback = callback

    def __getattr__(self, name: str) -> Any:
        return getattr(self._callback, name)

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> Any:
        try:
            return self._callback.on_chain_end(outputs, **kwargs)
        except Exception as exc:
            logger.warning("AgentEval trace delivery failed; continuing interview: %s", exc)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> Any:
        """Attempt to persist a failed node, without masking the original error."""
        try:
            callback = self._callback
            run_id = str(kwargs.get("run_id"))
            node_data = callback.active_runs.get(run_id)
            if node_data is not None:
                node_data["timestamp_end"] = datetime.now(timezone.utc).isoformat()
                node_data["outputs"] = {"error": str(error)}
                if callback.client is not None:
                    callback.client.submit_trace({
                        **node_data,
                        "parent_session_id": callback.parent_session_id,
                    })
                else:
                    callback.store.save_trace_node(node_data)
                callback.completed_nodes.append(node_data["node_id"])
                del callback.active_runs[run_id]
        except Exception as exc:
            logger.warning("AgentEval failed-trace delivery failed; continuing interview: %s", exc)


def create_agent_eval_callback(interview_id: str) -> Optional[Any]:
    """Create one hosted AgentEval callback per interview when fully configured."""
    api_url = os.getenv("AGENTEVAL_API_URL")
    api_key = os.getenv("AGENTEVAL_API_KEY")
    if not api_url or not api_key:
        logger.warning(
            "AgentEval disabled for interview %s: AGENTEVAL_API_URL and AGENTEVAL_API_KEY are required",
            interview_id,
        )
        return None

    try:
        from agenteval import AgentEvalCallbackHandler

        return _SafeAgentEvalCallback(AgentEvalCallbackHandler(
            session_id=f"veriq_{interview_id}",
            api_url=api_url,
            api_key=api_key,
        ))
    except Exception as exc:
        logger.warning("AgentEval disabled for interview %s: %s", interview_id, exc)
        return None


def merge_agent_eval_callback(
    config: Optional[Dict[str, Any]], callback: Optional[Any]
) -> Dict[str, Any]:
    """Add AgentEval while preserving callbacks and all other runnable config."""
    merged = dict(config or {})
    if callback is None:
        return merged
    callbacks = list(merged.get("callbacks") or [])
    callbacks.append(callback)
    merged["callbacks"] = callbacks
    return merged
