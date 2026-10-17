from datetime import datetime


def timestamp(moment: datetime) -> str:
    return f"<t:{int(moment.timestamp())}:f>"


def mention(user_id: int) -> str:
    return f"<@{user_id}>"
