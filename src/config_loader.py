import yaml

class ConfigLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.config = self._load_yaml()

    def _load_yaml(self) -> dict:
        """Private method to load YAML content into a dictionary."""
        with open(self.file_path, "r") as f:
            return yaml.safe_load(f)

    def get(self, key: str, default=None):
        """Fetch a config value with optional default."""
        return self.config.get(key, default)
