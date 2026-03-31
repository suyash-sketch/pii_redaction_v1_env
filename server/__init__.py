# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Pii Redaction V1 environment server components."""

try:
    from .pii_redaction_v1_environment import PiiRedactionV1Environment
except ImportError:
    import os as _os
    import sys as _sys
    _server_dir = _os.path.dirname(_os.path.abspath(__file__))
    if _server_dir not in _sys.path:
        _sys.path.insert(0, _server_dir)
    from pii_redaction_v1_environment import PiiRedactionV1Environment

__all__ = ["PiiRedactionV1Environment"]
