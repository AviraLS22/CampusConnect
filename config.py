
club_leaders = {
    "leader1@sit.edu": "CLUB123",
    "leader2@sit.edu": "EVENT456",
   
}

def validate_leader(email: str, code: str) -> bool:
    return club_leaders.get(email.lower()) == code
