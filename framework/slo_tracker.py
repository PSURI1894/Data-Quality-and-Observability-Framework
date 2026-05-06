import psycopg2
from datetime import datetime, timedelta

class SLOTracker:
    def __init__(self, db_conn_str):
        self.db_conn_str = db_conn_str
        
    def calculate_slo(self, dataset_urn):
        conn = psycopg2.connect(self.db_conn_str)
        cur = conn.cursor()
        
        # Calculate freshness
        cur.execute(
            """
            SELECT MAX(run_at) FROM checks_results WHERE dataset_urn = %s
            """,
            (dataset_urn,)
        )
        last_run = cur.fetchone()[0]
        freshness_ok = 1.0 if last_run and (datetime.now() - last_run) < timedelta(hours=1) else 0.0
        
        # Calculate validity (passing check ratio)
        cur.execute(
            """
            SELECT 
                COUNT(CASE WHEN status = 'PASS' THEN 1 END) * 100.0 / COUNT(*)
            FROM checks_results 
            WHERE dataset_urn = %s AND run_at >= NOW() - INTERVAL '24 HOURS'
            """,
            (dataset_urn,)
        )
        validity = cur.fetchone()[0] or 100.0
        
        # Write state
        cur.execute(
            """
            INSERT INTO slo_state (dataset_urn, freshness_sla_pct, completeness_sla_pct, validity_sla_pct, status, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (dataset_urn, freshness_ok * 100.0, 100.0, validity, "Healthy" if validity > 99.0 and freshness_ok > 0 else "Degraded")
        )
        conn.commit()
        cur.close()
        conn.close()
