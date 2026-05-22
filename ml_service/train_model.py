import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle
import os

def generate_mock_data(n_samples=5000):
    """
    Generates synthetic dataset for deployment risk prediction.
    Features:
    - files_changed: Number of files changed
    - lines_modified: Lines of code modified (added + deleted)
    - deployment_time_hour: Hour of the day (0-23)
    - previous_outage_history: Count of historical outages caused by author
    - failed_build_count: Number of failed CI builds for this PR
    - rollback_frequency: Number of rollbacks in the past 30 days for this service
    - team_experience: 0=Junior, 1=Mid, 2=Senior
    - test_coverage_pct: Code coverage percentage (0-100)
    """
    np.random.seed(42)
    data = {
        'files_changed': np.random.randint(1, 100, n_samples),
        'lines_modified': np.random.randint(10, 5000, n_samples),
        'deployment_time_hour': np.random.randint(0, 24, n_samples),
        'previous_outage_history': np.random.randint(0, 5, n_samples),
        'failed_build_count': np.random.randint(0, 10, n_samples),
        'rollback_frequency': np.random.randint(0, 5, n_samples),
        'team_experience': np.random.choice([0, 1, 2], n_samples),
        'test_coverage_pct': np.random.uniform(30.0, 100.0, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Define heuristic logic to create ground truth labels
    # High risk correlates with low test coverage, high lines modified, low experience, high previous outages
    risk_score = (
        (df['files_changed'] * 0.5) + 
        (df['lines_modified'] * 0.01) + 
        ((100 - df['test_coverage_pct']) * 1.5) + 
        (df['previous_outage_history'] * 15) + 
        (df['failed_build_count'] * 5) + 
        (df['rollback_frequency'] * 10) - 
        (df['team_experience'] * 20)
    )
    
    # Add penalty for late-night deployments (between 11 PM and 5 AM)
    night_mask = (df['deployment_time_hour'] >= 23) | (df['deployment_time_hour'] <= 5)
    risk_score += night_mask * 20
    
    # Categorize into 0: Low, 1: Medium, 2: High
    df['risk_level'] = 0 # Low Risk
    df.loc[risk_score > 80, 'risk_level'] = 1 # Medium Risk
    df.loc[risk_score > 150, 'risk_level'] = 2 # High Risk
    
    return df

def train_and_evaluate():
    print("1. Data Preprocessing & Feature Engineering...")
    df = generate_mock_data()
    X = df.drop('risk_level', axis=1)
    y = df['risk_level']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("2. Hyperparameter Tuning (XGBoost)...")
    # Using XGBoost as the primary model
    xgb_base = XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='mlogloss')
    
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1, 0.2]
    }
    
    grid_search = GridSearchCV(estimator=xgb_base, param_grid=param_grid, cv=3, scoring='accuracy', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    print(f"Best Parameters: {grid_search.best_params_}")
    
    print("3. Model Evaluation...")
    y_pred = best_model.predict(X_test)
    
    # Accuracy Metrics
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    target_names = ['Low Risk', 'Medium Risk', 'High Risk']
    print(classification_report(y_test, y_pred, target_names=target_names))
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=target_names, yticklabels=target_names)
    plt.title('Confusion Matrix - Deployment Risk Prediction')
    plt.ylabel('True Risk Level')
    plt.xlabel('Predicted Risk Level')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    print("Confusion matrix saved as 'confusion_matrix.png'")
    
    # Train Isolation Forest for anomaly detection (Out-of-distribution deployments)
    print("\n4. Training Anomaly Detector...")
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    iso_forest.fit(X_train)
    
    # Save the model
    print("\n5. Saving Models...")
    model_data = {
        'model': best_model,
        'anomaly_detector': iso_forest,
        'features': X.columns.tolist(),
        'mapper': {0: 'Low Risk', 1: 'Medium Risk', 2: 'High Risk'}
    }
    
    with open('risk_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    print("Models successfully saved to 'risk_model.pkl'.")

if __name__ == "__main__":
    train_and_evaluate()
