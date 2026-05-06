import requests
import time
import os

class OpenLineageEmitter:
    def __init__(self, endpoint_url, namespace="payments_security"):
        self.endpoint_url = endpoint_url
        self.namespace = namespace
        
    def emit_job_event(self, job_name, run_id, event_type, inputs=None, outputs=None):
        payload = {
            "eventType": event_type,
            "eventTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run": {
                "runId": run_id
            },
            "job": {
                "namespace": self.namespace,
                "name": job_name
            },
            "inputs": inputs or [],
            "outputs": outputs or [],
            "producer": "https://github.com/parth/data-quality-framework"
        }
        try:
            res = requests.post(f"{self.endpoint_url}/api/v1/lineage", json=payload, timeout=5)
            return res.status_code == 201
        except Exception as e:
            print(f"Failed to emit OpenLineage event: {e}")
            return False
