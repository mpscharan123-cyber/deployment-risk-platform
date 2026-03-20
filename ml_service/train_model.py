import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import os
import shap

def generate_mock_data(n_samples=2000):
    np.random.seed(42)
    data = {
        'files_changed': np.random.randint(1, 50, n_samples),
        'lines_added': np.random.randint(0, 1000, n_samples),
        'lines_deleted': np.random.randint(0, 1000, n_samples),
        'dev_experience': np.random.choice([0, 1, 2], n_samples), # 0: Junior, 1: Mid, 2: Senior
        'time_of_deployment': np.random.randint(0, 24, n_samples),
        'previous_failures': np.random.randint(0, 5, n_samples),
        'code_complexity': np.random.uniform(1.0, 10.0, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Simple risk logic for synthetic labels
    risk_score = (
        df['files_changed'] * 0.5 + 
        df['lines_added'] * 0.05 + 
        df['code_complexity'] * 2.0 + 
        (df['previous_failures'] * 10) - 
        (df['dev_experience'] * 5)
    )
    
    # 0: Low, 1: Medium, 2: High
    df['risk_level'] = 0
    df.loc[risk_score > 40, 'risk_level'] = 1
    df.loc[risk_score > 75, 'risk_level'] = 2
    
    return df

def main():
    df = generate_mock_data()
    X = df.drop('risk_level', axis=1)
    y = df['risk_level']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 1. Train XGBoost Classifier
    model = XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    # 2. Train Anomaly Detection (Isolation Forest)
    # This detects unusual deployment patterns
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    iso_forest.fit(X_train)
    
    # 3. Initialize SHAP Explainer
    explainer = shap.TreeExplainer(model)
    
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {acc:.4f}")
    
    # Save everything for enterprise inference
    model_data = {
        'model': model,
        'anomaly_detector': iso_forest,
        'explainer': explainer,
        'features': X.columns.tolist(),
        'mapper': {0: 'Low', 1: 'Medium', 2: 'High'}
    }
    
    with open('risk_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    print("Enterprise Model & Explainer saved to risk_model.pkl")

if __name__ == "__main__":
    main()
