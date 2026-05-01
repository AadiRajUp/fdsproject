import numpy as np
import joblib

# Load saved files
print("Loading model...")
scaler         = joblib.load("./model/scaler.pkl")
pca            = joblib.load("./model/pca.pkl")
model          = joblib.load("./model/model.pkl")
label_encoders = joblib.load("./model/label_encoders.pkl")
top4           = joblib.load("./model/top_features.pkl")
print(f"Model loaded.")
print(f"Required features: {top4}\n")

# Take user input for only top 4 features
print("Enter the student's details:")
print("-" * 40)
def model_predict(input_values):
    

# Predict
    input_array = np.array(input_values).reshape(1, -1)
    scaled      = scaler.transform(input_array)
    pca_input   = pca.transform(scaled)
    prediction  = model.predict(pca_input)
    return float(prediction.ravel()[0])