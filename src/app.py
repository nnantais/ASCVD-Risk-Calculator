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
        race = next((extension['valueCodeableConcept']['text']
                     for extension in patient.get('extension', [])
                     if extension['url'] == 'http://hl7.org/fhir/StructureDefinition/us-core-race'), 'Not Found')
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

@app.route('/', methods=['GET', 'POST'])
def index():
    observations = None
    demographics = None
    additional_fields = {}

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        additional_fields['diabetes'] = request.form.get('diabetes')
        additional_fields['smoker'] = request.form.get('smoker')
        additional_fields['hypertension'] = request.form.get('hypertension')
        additional_fields['statin'] = request.form.get('statin')
        additional_fields['aspirin'] = request.form.get('aspirin')
        credentials = (username, password)
        observations, demographics = get_patient_observations(patient_id, credentials)
        # Capture additional inputs from the user
        demographics['age'] = request.form.get('age') or demographics['age']
        demographics['sex'] = request.form.get('sex') or demographics['sex']
        demographics['race'] = request.form.get('race') or demographics['race']
        for obs_name in observation_codes.keys():
            form_name = obs_name.replace(' ', '_').lower()
            observations[obs_name] = request.form.get(form_name) or observations[obs_name]

    return render_template('index.html', observations=observations, demographics=demographics, additional_fields=additional_fields)

if __name__ == '__main__':
    port_str = os.environ['FHIR_PORT']
    port_int = int(port_str)
    app.run(debug=True, port=port_int)
