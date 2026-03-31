# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Pii Redaction V1 Environment.

The pii_redaction_v1 environment is a simple test environment that echoes back messages.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import Literal, Optional, List

class PiiRedactionV1Action(Action):
    # """Action for the Pii Redaction V1 environment - just a message to echo."""

    # message: str = Field(..., description="Message to echo back")
    command : Literal["Redact", "SubmitTicket"] = Field(
        ..., 
        description="Choose 'Redact' to obscure the test or 'SubmitTicket' to finalize the current ticket and get the next one."   
        )
    text_to_redact : Optional[str] = Field(
        default=None,
        description="The exact string to redact. Required if command is 'Redact'."
    )

class PiiRedactionV1Observation(Observation):
    # """Observation from the Pii Redaction V1 environment - the echoed message."""
# 
    # echoed_message: str = Field(default="", description="The echoed message")
    # message_length: int = Field(default=0, description="Length of the echoed message")
    ticket_id : str = Field(default="", description="Unique identifier for the current ticket.")
    ticket_content : str = Field(default="", description="The full text of the current ticket.")
    active_rules : str = Field(default="", description="The current complaince rules you must follow.")
    tickets_remaining : int = Field(default=0, description="How many tickets are left in the queue.")
    applied_redactions : List[str] = Field(default_factory=list, description="List of strings redacted so far")