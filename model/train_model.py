import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression  
from sklearn.metrics import r2_score, mean_squared_error

print("STEP 1: Loading dataset...")
df = pd.read_csv("dataset.csv")
df.dropna(inplace=True)
print(f"Shape: {df.shape}")

print("\nSTEP 2: Preprocessing...")
if 'student_id' in df.columns:
    df.drop(columns=['student_id'], inplace=True)

label_encoders = {}
for col in df.columns:
    if df[col].dtype == 'object' or df[col].dtype.name == 'category' or df[col].apply(lambda x: isinstance(x, str)).any():
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
        print(f"  Encoded: {col} -> {list(le.classes_)}")

joblib.dump(label_encoders, "label_encoders.pkl")

print("\nSTEP 3: Finding top 4 features by correlation with productivity_score...")
corr = df.corr()["productivity_score"].drop("productivity_score").abs().sort_values(ascending=False)
print("\nCorrelation of all features with productivity_score:")
print(corr)

top4 = corr.head(4).index.tolist()
print(f"\nTop 4 selected features: {top4}")
joblib.dump(top4, "top_features.pkl")

print("\nSTEP 4: Splitting...")
X = df[top4]
y = df["productivity_score"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"  Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

print("\nSTEP 5: Scaling...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)
joblib.dump(scaler, "scaler.pkl")
print("  scaler.pkl saved.")

print("\nSTEP 6: PCA...")
pca = PCA(n_components=0.95, random_state=42)
X_train_pca = pca.fit_transform(X_train_scaled)
X_test_pca  = pca.transform(X_test_scaled)
joblib.dump(pca, "pca.pkl")
print(f"  Components: {pca.n_components_} | Variance: {sum(pca.explained_variance_ratio_)*100:.2f}%")
print("  pca.pkl saved.")

print("\nSTEP 7: Training model...")
model = LinearRegression() 
model.fit(X_train_pca, y_train)
joblib.dump(model, "model.pkl")
print("  model.pkl saved.")

print("\nSTEP 8: Evaluating...")
y_pred = model.predict(X_test_pca)
r2  = r2_score(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
print(f"  R2 Score : {r2:.4f} ({r2*100:.2f}%)")
print(f"  RMSE     : {np.sqrt(mse):.4f}")
print(f"\nDone! Top 4 features: {top4}")
print("Files saved: scaler.pkl | pca.pkl | model.pkl | top_features.pkl")