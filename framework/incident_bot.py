import requests
import subprocess

class IncidentBot:
    def __init__(self, slack_webhook, pagerduty_routing_key):
        self.slack_webhook = slack_webhook
        self.pagerduty_routing_key = pagerduty_routing_key
        
    def trigger_incident(self, dataset_urn, expectation_id, observed_value, file_path):
        git_blame = self._get_git_blame(file_path)
        slack_payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 Data SLO Breach Detected!"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Dataset:* `{dataset_urn}`\n*Failed Assertion:* `{expectation_id}`\n*Observed Value:* `{observed_value}`"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Suspected Author:* {git_blame}\n*Runbook:* <http://runbooks/data_validation_failure.md|Validation Recovery Runbook>"
                    }
                }
            ]
        }
        requests.post(self.slack_webhook, json=slack_payload, timeout=5)
        
    def _get_git_blame(self, file_path):
        try:
            res = subprocess.run(
                ["git", "log", "-n", "1", "--pretty=format:%an (%ae)", "--", file_path],
                capture_output=True, text=True, check=True
            )
            return res.stdout.strip()
        except Exception:
            return "Unknown Developer"
