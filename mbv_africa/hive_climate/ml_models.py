"""
Simple ML Models for Climate Data Analysis
Uses Linear Regression for temperature prediction and visualization
"""
import numpy as np
from typing import Dict, List, Tuple, Any
from django.db.models import Avg, Count
from hive_climate.models import ClimateObservation, WeatherStation


def prepare_regression_data() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare data for linear regression: predict temp_mean from month and other features
    Returns X (features), y (target), feature_names
    """
    observations = ClimateObservation.objects.filter(
        temp_mean__isnull=False,
        humidity__isnull=False,
        precipitation__isnull=False
    ).values('month', 'humidity', 'precipitation', 'temp_mean', 'year')[:5000]
    
    if len(observations) < 10:
        return np.array([]), np.array([]), []
    
    # Convert to numpy arrays
    X = []
    y = []
    for obs in observations:
        # Features: month (cyclical), humidity, precipitation
        month_sin = np.sin(2 * np.pi * obs['month'] / 12)
        month_cos = np.cos(2 * np.pi * obs['month'] / 12)
        X.append([month_sin, month_cos, obs['humidity'], obs['precipitation']])
        y.append(obs['temp_mean'])
    
    return np.array(X), np.array(y), ['month_sin', 'month_cos', 'humidity', 'precipitation']


class SimpleLinearRegression:
    """
    Simple Linear Regression implementation without sklearn dependency
    Uses ordinary least squares (OLS) via normal equation
    """
    
    def __init__(self):
        self.coefficients = None
        self.intercept = None
        self.feature_names = []
        
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None):
        """Fit the model using normal equation: β = (X'X)^(-1)X'y"""
        if len(X) == 0:
            return self
            
        # Add bias term (column of ones)
        X_with_bias = np.column_stack([np.ones(len(X)), X])
        
        try:
            # Normal equation: β = (X'X)^(-1)X'y
            XtX = X_with_bias.T @ X_with_bias
            Xty = X_with_bias.T @ y
            beta = np.linalg.solve(XtX, Xty)
            
            self.intercept = beta[0]
            self.coefficients = beta[1:]
            self.feature_names = feature_names or [f'feature_{i}' for i in range(len(self.coefficients))]
        except np.linalg.LinAlgError:
            # Fallback if matrix is singular
            self.intercept = np.mean(y)
            self.coefficients = np.zeros(X.shape[1])
            self.feature_names = feature_names or []
            
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the fitted model"""
        if self.coefficients is None:
            return np.zeros(len(X))
        return self.intercept + X @ self.coefficients
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate R² score"""
        if len(X) == 0 or self.coefficients is None:
            return 0.0
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    def get_metrics(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Calculate regression metrics: RMSE, MAE, R²"""
        if len(X) == 0 or self.coefficients is None:
            return {'rmse': 0, 'mae': 0, 'r2': 0}
        
        y_pred = self.predict(X)
        errors = y - y_pred
        
        rmse = np.sqrt(np.mean(errors ** 2))
        mae = np.mean(np.abs(errors))
        r2 = self.score(X, y)
        
        return {
            'rmse': round(rmse, 3),
            'mae': round(mae, 3),
            'r2': round(r2, 3)
        }
    
    def get_feature_importance(self) -> List[Dict[str, Any]]:
        """Get feature importance based on coefficient magnitudes"""
        if self.coefficients is None or len(self.coefficients) == 0:
            return []
        
        # Normalize coefficients to get relative importance
        abs_coefs = np.abs(self.coefficients)
        total = np.sum(abs_coefs)
        
        if total == 0:
            return []
        
        importance = []
        for name, coef in zip(self.feature_names, self.coefficients):
            importance.append({
                'feature': name,
                'coefficient': round(float(coef), 4),
                'importance': round(float(np.abs(coef) / total * 100), 1)
            })
        
        # Sort by importance descending
        importance.sort(key=lambda x: x['importance'], reverse=True)
        return importance


def train_temperature_model() -> Dict[str, Any]:
    """
    Train a linear regression model on climate data
    Returns model info, metrics, predictions for visualization
    """
    X, y, feature_names = prepare_regression_data()
    
    if len(X) < 10:
        return {
            'status': 'no_data',
            'message': 'Not enough data to train model. Run: python manage.py load_sample_data',
            'metrics': {'rmse': 0, 'mae': 0, 'r2': 0},
            'feature_importance': [],
            'predictions': [],
            'actuals': [],
        }
    
    # Split data (80% train, 20% test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Train model
    model = SimpleLinearRegression()
    model.fit(X_train, y_train, feature_names)
    
    # Get metrics on test set
    metrics = model.get_metrics(X_test, y_test)
    
    # Get predictions for visualization (sample of test data)
    sample_size = min(50, len(X_test))
    y_pred = model.predict(X_test[:sample_size])
    
    return {
        'status': 'trained',
        'message': f'Model trained on {len(X_train)} samples, tested on {len(X_test)} samples',
        'metrics': metrics,
        'feature_importance': model.get_feature_importance(),
        'predictions': [round(float(p), 2) for p in y_pred],
        'actuals': [round(float(a), 2) for a in y_test[:sample_size]],
        'model_equation': _format_equation(model),
        'train_size': len(X_train),
        'test_size': len(X_test),
    }


def _format_equation(model: SimpleLinearRegression) -> str:
    """Format the regression equation for display"""
    if model.coefficients is None:
        return "y = 0"
    
    terms = [f"{model.intercept:.2f}"]
    for name, coef in zip(model.feature_names, model.coefficients):
        sign = "+" if coef >= 0 else "-"
        terms.append(f"{sign} {abs(coef):.3f}×{name}")
    
    return "temp_mean = " + " ".join(terms)


def get_monthly_predictions() -> List[Dict[str, Any]]:
    """
    Generate monthly temperature predictions using the model
    Returns predictions for each month for visualization
    """
    X, y, feature_names = prepare_regression_data()
    
    if len(X) < 10:
        return []
    
    # Train model on all data
    model = SimpleLinearRegression()
    model.fit(X, y, feature_names)
    
    # Generate predictions for each month
    predictions = []
    avg_humidity = np.mean(X[:, 2]) if len(X) > 0 else 60
    avg_precip = np.mean(X[:, 3]) if len(X) > 0 else 50
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for month in range(1, 13):
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        X_pred = np.array([[month_sin, month_cos, avg_humidity, avg_precip]])
        pred_temp = model.predict(X_pred)[0]
        
        # Get actual average for this month
        actual_avg = ClimateObservation.objects.filter(
            month=month, temp_mean__isnull=False
        ).aggregate(avg=Avg('temp_mean'))['avg'] or pred_temp
        
        predictions.append({
            'month': month_names[month - 1],
            'predicted': round(float(pred_temp), 1),
            'actual': round(float(actual_avg), 1),
        })
    
    return predictions
