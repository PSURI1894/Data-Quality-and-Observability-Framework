import yaml
import json

class RegistryValidator:
    def __init__(self, registry_path):
        self.registry_path = registry_path
        
    def load_registry(self):
        with open(self.registry_path, 'r') as f:
            return yaml.safe_load(f)
            
    def run_checks(self):
        config = self.load_registry()
        print(f"Loaded {len(config.get('datasets', []))} datasets from registry.")
        for ds in config.get('datasets', []):
            print(f"Validating URN: {ds['urn']}")
