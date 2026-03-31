# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Pii Redaction V1 Environment Client."""

from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import PiiRedactionV1Action, PiiRedactionV1Observation
except ImportError:
    import os as _os
    import sys as _sys
    _pkg_dir = _os.path.dirname(_os.path.abspath(__file__))
    if _pkg_dir not in _sys.path:
        _sys.path.insert(0, _pkg_dir)
    from models import PiiRedactionV1Action, PiiRedactionV1Observation


class PiiRedactionV1Env(
    EnvClient[PiiRedactionV1Action, PiiRedactionV1Observation, State]
):
    """
    Client for the Pii Redaction V1 Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with PiiRedactionV1Env(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.echoed_message)
        ...
        ...     result = client.step(PiiRedactionV1Action(message="Hello!"))
        ...     print(result.observation.echoed_message)

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = PiiRedactionV1Env.from_docker_image("pii_redaction_v1-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(PiiRedactionV1Action(message="Test"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: PiiRedactionV1Action) -> Dict:
        """
        Convert PiiRedactionV1Action to JSON payload for step message.

        Args:
            action: PiiRedactionV1Action instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "command" : action.command,
            "text_to_redact" : action.text_to_redact
        }

    def _parse_result(self, payload: Dict) -> StepResult[PiiRedactionV1Observation]:
        """
        Parse server response into StepResult[PiiRedactionV1Observation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with PiiRedactionV1Observation
        """
        obs_data : dict[str, Any] = payload.get("observation", {})
        observation = PiiRedactionV1Observation(
           ticket_id=obs_data.get("ticket_id", ""),
           ticket_content=obs_data.get("ticket_content", ""),
           active_rules=obs_data.get("active_rules", ""),
           tickets_remaining=obs_data.get("tickets_remaining", 0),
           applied_redactions=obs_data.get("applied_redactions", []),
           done=payload.get("done", False),
           reward=payload.get("reward", 0.0)
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
