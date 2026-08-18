
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import shap

BASE = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE / "models"

class MLService:
    FEATURES = [
        "age","condition_count","diabetes","hypertension","heart_disease",
        "er_visits_30d","hospitalizations_30d","outpatient_visits_30d",
        "total_utilization_30d","acute_utilization_30d",
        "recent_discharge_30d","days_since_discharge","post_discharge_24h",
        "care_gap_count","overdue_screening","overdue_lab","medication_gap",
        "transportation_barrier","food_insecurity","housing_instability",
        "financial_barrier","social_risk_count"
    ]

    READABLE = {
        "age": "Age",
        "condition_count": "Chronic condition burden",
        "diabetes": "Diabetes",
        "hypertension": "Hypertension",
        "heart_disease": "Heart disease",
        "er_visits_30d": "ER visits (30d)",
        "hospitalizations_30d": "Hospitalizations (30d)",
        "outpatient_visits_30d": "Outpatient visits (30d)",
        "total_utilization_30d": "Total utilization (30d)",
        "acute_utilization_30d": "Acute utilization (30d)",
        "recent_discharge_30d": "Recent hospital discharge",
        "days_since_discharge": "Days since discharge",
        "post_discharge_24h": "Very recent post-discharge signal",
        "care_gap_count": "Care-gap burden",
        "overdue_screening": "Overdue screening",
        "overdue_lab": "Overdue lab",
        "medication_gap": "Medication gap",
        "transportation_barrier": "Transportation barrier",
        "food_insecurity": "Food insecurity",
        "housing_instability": "Housing instability",
        "financial_barrier": "Financial barrier",
        "social_risk_count": "Social-risk burden",
    }

    def __init__(self):
        self.model = joblib.load(MODEL_DIR / "final_model.joblib")
        # Ensure compatibility across scikit-learn versions
        if hasattr(self.model, "named_steps"):
            for step in self.model.named_steps.values():
                if hasattr(step, "predict_proba") and not hasattr(step, "multi_class"):
                    step.multi_class = "auto"
        elif hasattr(self.model, "predict_proba") and not hasattr(self.model, "multi_class"):
            self.model.multi_class = "auto"
        self.shap_values = np.load(MODEL_DIR / "shap_values.npy")
        self.metadata = json.loads((MODEL_DIR / "metadata.json").read_text())
        self.metrics = pd.read_csv(MODEL_DIR / "model_metrics.csv")
        self.member_positions = {}

    def prepare(self, df):
        x = df[self.FEATURES].copy()
        x["days_since_discharge"] = x["days_since_discharge"].fillna(-1)
        return x

    def initialize(self, df):
        x = self.prepare(df)
        for i, mid in enumerate(df["member_id"].astype(str)):
            self.member_positions[mid] = i
        # Scores were calculated on the full dataset when the artifact was built.
        probs = self.model.predict_proba(x)[:, 1]
        scores = probs * 100
        bands = np.where(scores >= 70, "High Priority",
                 np.where(scores >= 40, "Medium Priority", "Low Priority"))
        return probs, scores, bands

    def explanation(self, member_id):
        pos = self.member_positions.get(str(member_id))
        if pos is None:
            return None
        row_values = self.shap_values[pos]
        feature_values = self._feature_row_values(pos)
        items = []
        for feature, shap_value, value in zip(self.FEATURES, row_values, feature_values):
            items.append({
                "feature": feature,
                "label": self.READABLE.get(feature, feature.replace("_"," ").title()),
                "value": None if pd.isna(value) else float(value),
                "shap_value": float(shap_value),
                "direction": "increases_priority" if shap_value > 0 else "decreases_priority"
            })
        positive = sorted([x for x in items if x["shap_value"] > 1e-6],
                          key=lambda x: x["shap_value"], reverse=True)[:5]
        negative = sorted([x for x in items if x["shap_value"] < -1e-6],
                          key=lambda x: x["shap_value"])[:5]
        return {
            "member_id": str(member_id),
            "positive_factors": positive,
            "negative_factors": negative,
            "top_positive": positive[:3],
            "method": "SHAP LinearExplainer on the deployed Logistic Regression model"
        }

    def _feature_row_values(self, pos):
        # The saved SHAP array is aligned with the final dataset feature order.
        # Reconstructing from the dataset happens in the API service.
        from .data_service import data_service
        row = data_service.df.iloc[pos]
        x = data_service.df.iloc[[pos]][self.FEATURES].copy()
        x["days_since_discharge"] = x["days_since_discharge"].fillna(-1)
        return x.iloc[0].tolist()

ml_service = MLService()
