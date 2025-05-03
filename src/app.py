import os
from dotenv import load_dotenv
import requests
import rpy2.robjects as ro
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import FloatVector, StrVector
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Set directory paths for R
os.environ['R_HOME'] = "/oscar/rt/9.2/software/0.20-generic/0.20.1/opt/spack/linux-rhel9-x86_64_v3/gcc-11.3.1/r-4.4.2-re5rjx36kzbvfrx7wgaozglvvskxxx5c/rlib/R"
os.environ['R_USER'] = "/oscar/rt/9.2/software/0.20-generic/0.20.1/opt/spack/linux-rhel9-x86_64_v3/gcc-11.3.1/r-4.4.2-re5rjx36kzbvfrx7wgaozglvvskxxx5c/rlib/R/library"


# Import the PooledCohort package in R
pooled_cohort = importr("PooledCohort")

FHIR_SERVER_BASE_URL = os.getenv("FHIR_SERVER_BASE_URL")
username = os.getenv("FHIR_USERNAME")
password = os.getenv("FHIR_PASSWORD")

# Load CSV data
diabetes_codes = pd.read_csv('diabetes.csv')['target_concept_code'].tolist()
smoker_codes = pd.read_csv('smoker.csv')['target_concept_code'].tolist()
hypertension_codes = pd.read_csv('hypertension.csv')['target_concept_code'].tolist()

observation_codes = {
    "Systolic Blood Pressure": "8480-6",
    "Diastolic Blood Pressure": "8462-4",
    "Total Cholesterol": "2093-3",
    "HDL Cholesterol": "2085-9",
    "LDL Cholesterol": "18262-6"
}

race_mapping = {
    "American Indian or Alaska Native": "white",
    "Asian": "white",
    "Black or African American": "black",
    "Native Hawaiian or Other Pacific Islander": "white",
    "White": "white"
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
        for extension in patient.get('extension', []):
            if extension['url'] == 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-race':
                for ext in extension.get('extension', []):
                    if ext['url'] == 'ombCategory':
                        race = race_mapping.get(ext['valueCoding']['display'], 'white')
                        break
        return {'age': age, 'sex': sex, 'race': race}
    else:
        return {'age': 'Not Found', 'sex': 'Not Found', 'race': 'Not Found'}

def check_code_presence(patient_id, code_list, credentials):
    for code in code_list:
        response = requests.get(FHIR_SERVER_BASE_URL + f"/Condition?patient={patient_id}&code={code}", auth=credentials)
        if response.status_code == 200:
            data = response.json()
            if 'entry' in data and data['entry']:
                return 'yes'
    return 'no'

def get_patient_observations(patient_id, credentials):
    observations = {}
    demographics = get_patient_demographics(patient_id, credentials)
    
    # Fetch observations from FHIR
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

    # Check presence of specific conditions based on codes
    observations['Diabetes'] = check_code_presence(patient_id, diabetes_codes, credentials)
    observations['Smoker'] = check_code_presence(patient_id, smoker_codes, credentials)
    observations['Hypertension'] = check_code_presence(patient_id, hypertension_codes, credentials)
    
    return observations, demographics

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

    # Convert sex and race to R compatible formats
    sex_r = StrVector([sex])
    race_r = StrVector([race_mapping.get(race, 'white')])

    # Convert other inputs to R compatible formats
    age_r = FloatVector([age])
    total_cholesterol_r = FloatVector([total_cholesterol])
    hdl_cholesterol_r = FloatVector([hdl_cholesterol])
    systolic_bp_r = FloatVector([systolic_bp])
    diabetes_r = StrVector([diabetes])
    smoker_r = StrVector([smoker])
    hypertension_r = StrVector([hypertension])

    # Call the ASCVD risk calculation function from PooledCohort
    ascvd_risk_r = pooled_cohort.predict_10yr_ascvd_risk(
        sex=sex_r,
        race=race_r,
        age_years=age_r,
        chol_total_mgdl=total_cholesterol_r,
        chol_hdl_mgdl=hdl_cholesterol_r,
        bp_sys_mmhg=systolic_bp_r,
        bp_meds=hypertension_r,
        smoke_current=smoker_r,
        diabetes=diabetes_r
    )

    # Convert the result back to Python and multiply by 100 to get percentage
    ascvd_risk_percentage = list(ascvd_risk_r)[0] * 100

    demographics = {'age': age, 'sex': sex, 'race': race}
    observations = {
        'Total Cholesterol': total_cholesterol,
        'HDL Cholesterol': hdl_cholesterol,
        'Systolic Blood Pressure': systolic_bp,
        'Diastolic Blood Pressure': request.form['diastolic_blood_pressure'] if 'diastolic_blood_pressure' in request.form else 'Not Found',
        'Diabetes': diabetes,
        'Smoker': smoker,
        'Hypertension': hypertension
    }

    return render_template(
        'index.html',
        ascvd_risk=ascvd_risk_percentage,
        demographics=demographics,
        observations=observations,
        patient_id=patient_id,
        diabetes=diabetes,
        smoker=smoker,
        hypertension=hypertension
    )

if __name__ == '__main__':
    port_str = os.environ['FHIR_PORT']
    port_int = int(port_str)
    app.run(debug=True, port=port_int)
