from typing import List, Dict, Optional
from datetime import datetime, timedelta
import math

class DemandForecaster:
    """
    Forecasting pipeline for predicting blood component demand.
    Implements baseline models and a simple interface for advanced models.
    """

    @staticmethod
    def naive_forecast(historical_demand: List[int], horizon: int = 1) -> List[float]:
        """
        Baseline 1: Naive Forecast.
        The prediction for the next `horizon` days is just the demand from the last observed day.
        """
        if not historical_demand:
            return [0.0] * horizon
        last_value = float(historical_demand[-1])
        return [last_value] * horizon

    @staticmethod
    def moving_average(historical_demand: List[int], window: int = 7, horizon: int = 1) -> List[float]:
        """
        Baseline 2: Moving Average Forecast.
        Predicts based on the average of the last `window` days.
        """
        if not historical_demand:
            return [0.0] * horizon
        
        # Ensure window isn't larger than available data
        window = min(window, len(historical_demand))
        
        recent_data = historical_demand[-window:]
        avg = float(sum(recent_data)) / window
        
        # Simple projection: flat average for the horizon
        return [avg] * horizon

    @staticmethod
    def exponential_smoothing(historical_demand: List[int], alpha: float = 0.3, horizon: int = 1) -> List[float]:
        """
        Baseline 3: Simple Exponential Smoothing.
        """
        if not historical_demand:
            return [0.0] * horizon
            
        # Calculate smoothed series
        smoothed = float(historical_demand[0])
        for val in historical_demand[1:]:
            smoothed = alpha * val + (1 - alpha) * smoothed
            
        return [smoothed] * horizon

    @staticmethod
    def gradient_boosting(historical_demand: List[int], horizon: int = 1) -> List[float]:
        """
        Model 2: Gradient Boosting using engineered temporal features.
        """
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            import numpy as np
        except ImportError:
            return DemandForecaster.naive_forecast(historical_demand, horizon)

        if len(historical_demand) < 14:
            return DemandForecaster.moving_average(historical_demand, window=7, horizon=horizon)

        # Feature engineering (basic temporal features)
        X = []
        y = []
        for i in range(7, len(historical_demand) - 1):
            window = historical_demand[i-7:i]
            target = historical_demand[i+1]
            features = [
                np.mean(window),           # Rolling mean
                np.std(window) if np.std(window) > 0 else 0, # Rolling std
                window[-1],                # Lag 1
                window[-7]                 # Lag 7
            ]
            X.append(features)
            y.append(target)

        if not X:
            return DemandForecaster.moving_average(historical_demand, horizon=horizon)

        model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)

        predictions = []
        current_window = historical_demand[-7:]
        
        for _ in range(horizon):
            features = [[
                np.mean(current_window),
                np.std(current_window) if np.std(current_window) > 0 else 0,
                current_window[-1],
                current_window[-7]
            ]]
            pred = model.predict(features)[0]
            predictions.append(max(0.0, float(pred)))
            current_window.append(pred)
            current_window.pop(0)

        return predictions

    @staticmethod
    def calculate_mae(actuals: List[int], predictions: List[float]) -> float:
        """Calculates Mean Absolute Error for model evaluation."""
        if not actuals or not predictions or len(actuals) != len(predictions):
            return 0.0
        return sum(abs(a - p) for a, p in zip(actuals, predictions)) / len(actuals)
