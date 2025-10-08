import json
from typing import Any, Optional


def load_config() -> Optional[dict[str, Any]]:
    result = {}
    with open("../config/config.json", mode="r") as config:
        result.update(json.load(config))
        config.close()
    return result