from app.db.mongodb import db

sessions_collection = db["sessions"]

interview_messages_collection = db[
    "interview_messages"
]

def create_indexes():
    sessions_collection.create_index("session_id", unique=True)

    interview_messages_collection.create_index(
        [
            ("session_id", 1),
            ("created_at", 1),
        ]
    )


create_indexes()