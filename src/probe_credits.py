"""Cheapest possible probe: succeeds (exit 0) once the account has credits."""
import sys

import anthropic

from api_lib import get_client

try:
    msg = get_client().messages.create(
        model="claude-haiku-4-5", max_tokens=8,
        messages=[{"role": "user", "content": "Reply: OK"}],
    )
    print("CREDITS LIVE - snapshot:", msg.model)
    sys.exit(0)
except anthropic.BadRequestError as e:
    print("still blocked:", str(e)[:120])
    sys.exit(1)
except Exception as e:
    print("error:", str(e)[:120])
    sys.exit(2)
