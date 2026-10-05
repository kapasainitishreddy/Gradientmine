"""Conservative settlement retry decisions from finalized RPC evidence."""


def recovery_decision(status, finalized_height, last_valid_height, bounty_state):
    if bounty_state not in (0, 1, 2):
        raise ValueError("Unrecognized bounty state; do not retry")
    if bounty_state == 2:
        return "refunded"
    if bounty_state == 1:
        return "confirm"
    if status and status.get("err") is None:
        return "confirm"
    if status and status.get("confirmationStatus") != "finalized":
        return "wait"
    if finalized_height > last_valid_height:
        return "retry"
    return "wait"
