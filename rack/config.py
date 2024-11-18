import os

import yaml


def load_rack_config(working_dir: str):
    """Load rack config from working_dir/.rack.yaml"""

    rack_config_path = os.path.join(working_dir, ".rack.yaml")
    if not os.path.exists(rack_config_path):
        return {}

    with open(rack_config_path, "r") as f:
        rack_config = yaml.safe_load(f)
    return rack_config
