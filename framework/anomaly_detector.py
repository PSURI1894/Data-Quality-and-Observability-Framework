import numpy as np
import pandas as pd

class AnomalyDetector:
    def __init__(self, window_size=30, z_threshold=3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        
    def detect_row_count_anomaly(self, row_counts):
        if len(row_counts) < 5:
            return False, 0.0
            
        series = pd.Series(row_counts)
        ewma = series.ewm(span=self.window_size).mean()
        std = series.ewm(span=self.window_size).std()
        
        last_val = series.iloc[-1]
        mean_val = ewma.iloc[-1]
        std_val = std.iloc[-1] if std.iloc[-1] > 0 else 1.0
        
        z_score = abs(last_val - mean_val) / std_val
        is_anomaly = z_score > self.z_threshold
        return bool(is_anomaly), float(z_score)
