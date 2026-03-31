# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Pii Redaction V1 Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""

import copy
from typing import Any
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from pydantic.types import T

try:
    from ..models import PiiRedactionV1Action, PiiRedactionV1Observation
except ImportError:
    import os as _os
    import sys as _sys
    _parent_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _parent_dir not in _sys.path:
        _sys.path.insert(0, _parent_dir)
    from models import PiiRedactionV1Action, PiiRedactionV1Observation


class PiiRedactionV1Environment(Environment):
    # """
    # A simple echo environment that echoes back messages.

    # This environment is designed for testing the HTTP server infrastructure.
    # It maintains minimal state and simply echoes back whatever message it receives.

    # Example:
    #     >>> env = PiiRedactionV1Environment()
    #     >>> obs = env.reset()
    #     >>> print(obs.echoed_message)  # "Pii Redaction V1 environment ready!"
    #     >>>
    #     >>> obs = env.step(PiiRedactionV1Action(message="Hello"))
    #     >>> print(obs.echoed_message)  # "Hello"
    #     >>> print(obs.message_length)  # 5
    # """

    # Enable concurrent WebSocket sessions.
    # Set to True if your environment isolates state between instances.
    # When True, multiple WebSocket clients can connect simultaneously, each
    # getting their own environment instance (when using factory mode in app.py).
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the pii_redaction_v1 environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.queue = []
        self.total_tickets = 0
        self.current_index = 0
        self.current_ticket : dict[str, str | list] = {}
        self.applied_redactions = []
        self.active_rules = ""
        self.task_name = "easy"

        self.tasks = {
            "easy": {
                "initial_rules": "Redact all Email Addresses and Phone Numbers.",
                "data": [
                    {"id": "EASY-001", "text": "Name: Jane Doe\nEmail: jane.doe@example.com\nPhone: 555-0198", "truth": ["jane.doe@example.com", "555-0198"]},

                    {"id": "EASY-002", "text": "Call me directly at 800-555-0199 or email support_request@testdomain.org.", "truth": ["800-555-0199", "support_request@testdomain.org"]},

                    {"id": "EASY-003", "text": "Recovery link sent to admin.backup@company.net. SMS verification sent to 555-0123.", "truth": ["admin.backup@company.net", "555-0123"]},

                    {"id": "EASY-004", "text": "Sales inquiry from enterprise@corp.com. Please call back at (415) 555-9876.", "truth": ["enterprise@corp.com", "(415) 555-9876"]},

                    {"id": "EASY-005", "text": "User user99@webmail.com opted out of SMS notifications for +1-800-555-0000.", "truth": ["user99@webmail.com", "+1-800-555-0000"]}
                ]
            },
           "medium": {
                "initial_rules": "Redact Credit Card and Social Security Numbers EXACTLY as they appear in the raw text. Extract the literal string. DO NOT fix typos, DO NOT convert words to numbers, and DO NOT format the output.",
                "data": [
                    {"id": "MED-001", "text": "Customer states: 'My SSN is nine four two, dash 5 5, dash one two 3 4.'", "truth": ["nine four two, dash 5 5, dash one two 3 4"]},
                    {"id": "MED-002", "text": "Billing error on card four-1-1-1 space 2-2-2-2 space 3-3-3-3 space 4-4-4-4.", "truth": ["four-1-1-1 space 2-2-2-2 space 3-3-3-3 space 4-4-4-4"]},
                    {"id": "MED-003", "text": "The user entered their social as 1 2 3 - 4 5 - 6 7 8 9. Please update the database.", "truth": ["1 2 3 - 4 5 - 6 7 8 9"]},
                    {"id": "MED-004", "text": "Visa ending in 4444. Full number provided over phone: four five three two, 1111, 2222, four four four four.", "truth": ["four five three two, 1111, 2222, four four four four"]}
                ]
            },
            "hard": {
                "initial_rules": "Redact the names of employees who are explicitly marked as 'TERMINATED' or 'GUILTY'. DO NOT redact the names of HR staff, investigators, victims, or suspects who were 'CLEARED'.",
                "data": [
                    {"id": "HARD-001", "text": "HR Director Amanda called a meeting regarding the missing funds. Suspect 1, Kevin, was cleared after providing an alibi. Suspect 2, Oscar, was found guilty of the theft and terminated. Toby from HR filed the paperwork.", "truth": ["Oscar"]},
                    {"id": "HARD-002", "text": "Investigation 99A: Officer Davis interviewed the victim, Sarah. The perpetrator, initially thought to be Mark, was actually confirmed to be Jason. Jason has been terminated. Mark is cleared.", "truth": ["Jason"]},
                    {"id": "HARD-003", "text": "Alice accused Bob of harassment. Charlie investigated. Bob was cleared of all charges. It was discovered Alice fabricated the story, leading to Alice being terminated immediately.", "truth": ["Alice"]},
                    {"id": "HARD-004", "text": "The audit by external firm Smith & Co found that Manager Dave was compliant. However, his assistant, Greg, embezzled $5k. Greg is terminated. Dave receives a warning.", "truth": ["Greg"]},
                    {"id": "HARD-005", "text": "Security logged a breach by user 'admin_jenny'. Jenny proved her account was compromised by intern Marcus. Marcus confessed and is terminated. Jenny is cleared.", "truth": ["Marcus"]}
                ]
            }
            # "hard": {
            #     "initial_rules": "Redact Passwords and API Keys.",
            #     "data": [
            #         {"id": "HARD-001", "text": "Exception in thread 'main' java.sql.SQLException: Access denied for user 'root'@'10.0.0.5' (using password: YES)\nCaused by: com.mysql.cj.exceptions.CJException: Invalid credentials. Auth string: db_admin:SuperSecret123!", "truth": ["SuperSecret123!"]},
            #         {"id": "HARD-002", "text": "2026-03-30T08:14:22Z [WARN] Failed to authenticate webhook. Payload: {\"event\":\"push\",\"repo\":\"auth-service\",\"headers\":{\"Authorization\":\"Bearer AKIAIOSFODNN7EXAMPLE\",\"X-Forwarded-For\":\"192.168.1.10\"}}", "truth": ["AKIAIOSFODNN7EXAMPLE"]},
            #         {"id": "HARD-003", "text": "Staging config dump:\nDB_HOST=172.16.254.1\nSTRIPE_ENV=test\nSTRIPE_SECRET=sk_test_4eC39HqLyjWDarjtT1zdp7dc\nPORT=8080", "truth": ["sk_test_4eC39HqLyjWDarjtT1zdp7dc"]},
            #         {"id": "HARD-004", "text": "User reported login issue. Machine 10.10.10.50. Bash history shows: `curl -u admin:MyP@ssw0rd! https://internal-api.corp/v1/health`", "truth": ["MyP@ssw0rd!"]},
            #         {"id": "HARD-005", "text": "Subnet 192.168.100.2 alert. Exposed commit hash 8f3a1b2c. Environment variable GITHUB_TOKEN=ghp_16C7e42F292c6912E7710c838347Ae178B4a was pushed to public repo.", "truth": ["ghp_16C7e42F292c6912E7710c838347Ae178B4a"]},
            #         {"id": "HARD-006", "text": "FTP transfer failed. \nConnection string: ftp://ftp_admin:Welcome2026@origin.storage.net:21/backups/ \nOrigin IP: 10.0.1.15", "truth": ["Welcome2026"]},
            #         {"id": "HARD-007", "text": "Worker 172.16.0.4 crashed. Env dump: NODE_ENV=prod, SG_KEY=SG.abc123def456.xyz890, MAX_RETRIES=3. Restarting.", "truth": ["SG.abc123def456.xyz890"]},
                    
            #         # --- RULE SHIFT HAPPENS HERE (Index 7) ---
            #         # Now redacting Passwords, API Keys, AND IP Addresses.
            #         {"id": "HARD-008", "text": "Network Timeout Log. Src: 192.168.1.50 Dest: 10.0.0.1. Plaintext auth detected: Admin@99.", "truth": ["192.168.1.50", "Admin@99"]},
            #         {"id": "HARD-009", "text": "Redis cluster configuration mismatch on node-A (10.1.1.20). \nrequirepass Redis!Secure\nmaxmemory 2gb", "truth": ["10.1.1.20", "Redis!Secure"]},
            #         {"id": "HARD-010", "text": "Production deployment via node 172.31.4.99. Env update: LIVE_KEY_V2=sk_live_1234567890abcdef. Deployment successful.", "truth": ["sk_live_1234567890abcdef", "172.31.4.99"]},
            #         {"id": "HARD-011", "text": "Fatal kernel panic on 192.168.2.100. Drop to recovery shell requested. Master unlock hash: Rec0very#Hash.", "truth": ["192.168.2.100", "Rec0very#Hash"]},
            #         {"id": "HARD-012", "text": "VPN gateway proxy from 10.8.0.5 intercepted unencrypted header: `X-Jira-Auth: Basic ATATT3xFfGF0`. Connection dropped.", "truth": ["10.8.0.5", "ATATT3xFfGF0"]},
            #         {"id": "HARD-013", "text": "Router default config found on 192.168.0.1. Setup wizard bypassing auth. HW_PASS=admin123 flag is still true.", "truth": ["192.168.0.1", "admin123"]},
            #         {"id": "HARD-014", "text": "Jenkins build #404 failed on agent 10.0.5.55. \nError: AWS_SECRET_ACCESS_KEY wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY is invalid.", "truth": ["10.0.5.55", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"]},
            #         {"id": "HARD-015", "text": "Docker ps output on 172.17.0.2 shows running container with env arg: MYSQL_ROOT_PASSWORD=r00tP@ss!. Flagged for teardown.", "truth": ["172.17.0.2", "r00tP@ss!"]}
            #     ]
            # }
        }

    def reset(self, task_name : str = "easy") -> PiiRedactionV1Observation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.task_name = task_name
        if task_name not in self.tasks:
            task_config = self.tasks["easy"]
        else:
            task_config = self.tasks[task_name]

        self.queue = copy.deepcopy(task_config["data"])
        self.total_tickets = len(self.queue)
        self.current_index = 0
        self.active_rules = task_config["initial_rules"]
        
        self._load_current_ticket()
        return self._get_observation(reward = 0.0, done=False)
        # """
        # Reset the environment.

        # Returns:
        #     PiiRedactionV1Observation with a ready message
        # """
        # self._state = State(episode_id=str(uuid4()), step_count=0)
        # self._reset_count += 1

        # return PiiRedactionV1Observation(
        #     echoed_message="Pii Redaction V1 environment ready!",
        #     message_length=0,
        #     done=False,
        #     reward=0.0,
        # )

    def _load_current_ticket(self):
        if self.current_index < self.total_tickets:
            self.current_ticket = self.queue[self.current_index]
            self.applied_redactions = []

        #Hard task rule evolution
        # if self.task_name == "hard" and self.current_index == 7:
        #     self.active_rules = "UPDATE: Redact Passwords, API Keys, AND internal IP addresses (e.g., 192.168.x.x)." 

    def step(self, action: PiiRedactionV1Action) -> PiiRedactionV1Observation:  # type: ignore[override]
        
        self._state.step_count +=1
        done = False
        step_reward = 0

        if action.command == "Redact" and action.text_to_redact:
            if action.text_to_redact in self.current_ticket.get("text", ""):
                self.current_ticket["text"] = self.current_ticket["text"].replace(action.text_to_redact, "[REDACTED]")
                self.applied_redactions.append(action.text_to_redact)
        
        elif action.command == "SubmitTicket":
            ticket_f1 = self._calculate_f1score(self.applied_redactions, self.current_ticket.get("truth", []))
            step_reward = ticket_f1 / self.total_tickets

            self.current_index +=1
            if self.current_index >= self.total_tickets:
                done = True
            else:
                self._load_current_ticket()
            
        return self._get_observation(reward=step_reward, done=done)

        # """
        # Execute a step in the environment by echoing the message.

        # Args:
        #     action: PiiRedactionV1Action containing the message to echo

        # Returns:
        #     PiiRedactionV1Observation with the echoed message and its length
        # """
        # self._state.step_count += 1

        # message = action.message
        # length = len(message)

        # # Simple reward: longer messages get higher rewards
        # reward = length * 0.1

        # return PiiRedactionV1Observation(
        #     echoed_message=message,
        #     message_length=length,
        #     done=False,
        #     reward=reward,
        #     metadata={"original_message": message, "step": self._state.step_count},
        # )



    # HELPER Functions

    def _get_observation(self, reward : float, done : bool) -> PiiRedactionV1Observation:
        if self.current_index >= self.total_tickets:
            return PiiRedactionV1Observation(
                ticket_id="DONE", ticket_content="", active_rules="",
                tickets_remaining=0, applied_redactions=[],
                reward=reward, done=done
            )
        
        return PiiRedactionV1Observation(
            ticket_id = self.current_ticket["id"],
            ticket_content = self.current_ticket["text"],
            active_rules= self.active_rules,
            tickets_remaining= self.total_tickets - self.current_index,
            applied_redactions=self.applied_redactions,
            reward=reward, done=done
        )
    
    def _calculate_f1score(self, applied : list, truth : list) -> float:
        if not truth or not applied: return 1.0
        applied_set, truth_set = set(applied), set(truth)
        tp = len(applied_set.intersection(truth_set))
        fp = len(applied_set - truth_set)
        fn = len(truth_set - applied_set)

        precision = tp / ( tp + fp ) if (tp + fp) > 0 else 0.0
        recall = tp / ( tp + fn ) if (tp + fn) > 0 else 0.0
        
        return 2 * (precision*recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state
