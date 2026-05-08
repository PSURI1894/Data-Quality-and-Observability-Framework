import os
import yaml
import psycopg2
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

class RegistryValidator:
    def __init__(self, registry_path, db_conn_str):
        self.registry_path = registry_path
        self.db_conn_str = db_conn_str
        self.context = ge.get_context()
        
    def load_registry(self):
        with open(self.registry_path, 'r') as f:
            return yaml.safe_load(f)
            
    def run_validation(self, dataset_urn, data_df):
        config = self.load_registry()
        dataset_cfg = next((d for d in config['datasets'] if d['urn'] == dataset_urn), None)
        if not dataset_cfg:
            raise ValueError(f"Dataset {dataset_urn} not in registry.")
            
        suite_name = f"{dataset_urn.replace('.', '_')}_suite"
        suite = self.context.add_or_update_expectation_suite(expectation_suite_name=suite_name)
        
        # Translate expectations
        for exp in dataset_cfg['expectations']:
            suite.add_expectation(ge.core.ExpectationConfiguration(
                expectation_type=exp['expectation_type'],
                kwargs=exp['kwargs']
            ))
            
        batch_request = RuntimeBatchRequest(
            datasource_name="payment_warehouse",
            data_connector_name="default_runtime_data_connector",
            data_asset_name=dataset_urn,
            runtime_parameters={"batch_data": data_df},
            batch_identifiers={"default_identifier_name": "run_id_001"}
        )
        
        validator = self.context.get_validator(
            batch_request=batch_request,
            expectation_suite_name=suite_name
        )
        
        results = validator.validate()
        self._write_results_to_postgres(dataset_urn, results)
        return results

    def _write_results_to_postgres(self, urn, results):
        conn = psycopg2.connect(self.db_conn_str)
        cur = conn.cursor()
        for res in results.results:
            cur.execute(
                """
                INSERT INTO checks_results (run_id, dataset_urn, expectation_id, severity, status, observed_value, threshold, run_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                ("run_001", urn, res.expectation_config.expectation_type, "Critical", "PASS" if res.success else "FAIL", str(res.result.get('observed_value')), str(res.expectation_config.kwargs))
            )
        conn.commit()
        cur.close()
        conn.close()
