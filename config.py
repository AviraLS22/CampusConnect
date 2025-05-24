# config.py

club_leaders = {
    "leader1@sit.edu": "CLUB123",
    "leader2@sit.edu": "EVENT456",
    # add more as needed
}

def validate_leader(email: str, code: str) -> bool:
    return club_leaders.get(email.lower()) == code
