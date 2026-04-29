import joblib
import numpy as np

model = joblib.load("model.pkl")
pca   = joblib.load("pca.pkl")
top4  = joblib.load("top_features.pkl")

# Fix: model.coef_ is 1D for LinearRegression, no [0] needed
final_coefs = model.coef_ @ pca.components_

print("=== a, b, c, d Coefficients ===")
a, b, c, d = final_coefs          # ← CHANGED: removed [0]
print(f"  a ({top4[0]}): {a:.6f}")
print(f"  b ({top4[1]}): {b:.6f}")
print(f"  c ({top4[2]}): {c:.6f}")
print(f"  d ({top4[3]}): {d:.6f}")
print(f"  intercept   : {model.intercept_:.6f}")

print("\n=== Full Equation ===")
print(f"Score = {a:.4f}*{top4[0]} + {b:.4f}*{top4[1]} + {c:.4f}*{top4[2]} + {d:.4f}*{top4[3]} + {model.intercept_:.4f}")