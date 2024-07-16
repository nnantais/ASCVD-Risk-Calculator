import requests
import os
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv
from datetime import datetime

app = Flask(__name__)

FHIR_SERVER_BASE_URL = "http://pwebmedcit.services.brown.edu:9091/fhir"

load_dotenv()

username = os.getenv("FHIR_USERNAME")
password = os.getenv("FHIR_PASSWORD")

observation_codes = {
    "Systolic Blood Pressure": "8480-6",
    "Diastolic Blood Pressure": "8462-4",
    "Total Cholesterol": "2093-3",
    "HDL Cholesterol": "2085-9",
    "LDL Cholesterol": "18262-6"
}

def get_observation_value(entry):
    if 'valueQuantity' in entry['resource']:
        return entry['resource']['valueQuantity']['value']
    elif 'valueString' in entry['resource']:
        return entry['resource']['valueString']
    else:
        return 'Not Found'

def get_latest_observation(entries):
    if not entries:
        return 'Not Found'
    latest_entry = max(entries, key=lambda e: e['resource']['effectiveDateTime'])
    return get_observation_value(latest_entry)

def calculate_age(birth_date):
    birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_patient_demographics(patient_id, credentials):
    response = requests.get(FHIR_SERVER_BASE_URL + f"/Patient/{patient_id}", auth=credentials)
    if response.status_code == 200:
        patient = response.json()
        birth_date = patient['birthDate']
        age = calculate_age(birth_date)
        sex = patient['gender']
        race = 'Not Found'
        
        # Extract race from extensions
        for extension in patient.get('extension', []):
            if extension['url'] == 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-race':
                for ext in extension.get('extension', []):
                    if ext['url'] == 'ombCategory':
                        race = ext['valueCoding']['display']
                        break

        return {'age': age, 'sex': sex, 'race': race}
    else:
        return {'age': 'Not Found', 'sex': 'Not Found', 'race': 'Not Found'}

def get_patient_observations(patient_id, credentials):
    observations = {}
    demographics = get_patient_demographics(patient_id, credentials)
    for obs_name, code in observation_codes.items():
        response = requests.get(FHIR_SERVER_BASE_URL + f"/Observation?patient={patient_id}&code={code}", auth=credentials)
        if response.status_code == 200:
            data = response.json()
            if 'entry' in data and data['entry']:
                observations[obs_name] = get_latest_observation(data['entry'])
            else:
                observations[obs_name] = 'Not Found'
        else:
            observations[obs_name] = 'Not Found'
    return observations, demographics

def calculate_ascvd_risk(age, sex, race, total_cholesterol, hdl_cholesterol, systolic_bp, on_hypertension_treatment, diabetes, smoker):
    # Simplified ASCVD risk calculation
    # Note: This is a placeholder. Use a proper ASCVD risk calculator for accurate results.
    risk_score = 0
    if sex == 'male':
        risk_score += 1
    if race == 'African American':
        risk_score += 1
    risk_score += age / 10
    risk_score += total_cholesterol / 50
    risk_score -= hdl_cholesterol / 50
    risk_score += systolic_bp / 20
    if on_hypertension_treatment == 'yes':
        risk_score += 1
    if diabetes == 'yes':
        risk_score += 1
    if smoker == 'yes':
        risk_score += 1
    return round(risk_score, 2)

@app.route('/', methods=['GET', 'POST'])
def index():
    observations = None
    demographics = None
    ascvd_risk = None

    return render_template('index.html', observations=observations, demographics=demographics, ascvd_risk=ascvd_risk)

@app.route('/fetch_patient_data', methods=['POST'])
def fetch_patient_data():
    patient_id = request.form['patient_id']
    credentials = (username, password)
    observations, demographics = get_patient_observations(patient_id, credentials)
    return render_template('index.html', observations=observations, demographics=demographics, patient_id=patient_id)

@app.route('/calculate_risk', methods=['POST'])
def calculate_risk():
    patient_id = request.form.get('patient_id')
    age = int(request.form['age'])
    sex = request.form['sex']
    race = request.form['race']
    total_cholesterol = float(request.form['total_cholesterol'])
    hdl_cholesterol = float(request.form['hdl_cholesterol'])
    systolic_bp = float(request.form['systolic_blood_pressure'])
    diabetes = request.form['diabetes']
    smoker = request.form['smoker']
    hypertension = request.form['hypertension']

    ascvd_risk = calculate_ascvd_risk(age, sex, race, total_cholesterol, hdl_cholesterol, systolic_bp, hypertension, diabetes, smoker)

    # Maintain the form values for observations and demographics
    demographics = {'age': age, 'sex': sex, 'race': race}
    observations = {
        'Total Cholesterol': total_cholesterol,
        'HDL Cholesterol': hdl_cholesterol,
        'Systolic Blood Pressure': systolic_bp,
        'Diastolic Blood Pressure': request.form['diastolic_blood_pressure'] if 'diastolic_blood_pressure' in request.form else 'Not Found',
        'LDL Cholesterol': request.form['ldl_cholesterol'] if 'ldl_cholesterol' in request.form else 'Not Found'
    }

    return render_template('index.html', ascvd_risk=ascvd_risk, demographics=demographics, observations=observations, patient_id=patient_id)

if __name__ == '__main__':
    port_str = os.environ['FHIR_PORT']
    port_int = int(port_str)
    app.run(debug=True, port=port_int)
