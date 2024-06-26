import requests
import os
from flask import Flask, request, render_template
from dotenv import load_dotenv


app = Flask(__name__)

FHIR_SERVER_BASE_URL="http://pwebmedcit.services.brown.edu:9091/fhir"

load_dotenv()

username = os.getenv("FHIR_USERNAME")
password = os.getenv("FHIR_PASSWORD")


def request_patient(patient_id, credentials):

    req = requests.get(FHIR_SERVER_BASE_URL + "/Patient/" + str(patient_id), auth = credentials)

    print(f"Requests status: {req.status_code}")

    response = req.json()
    print(response.keys())

    return response

def search_patients_by_condition(condition_id, credentials):
    # Search for patients with a specific condition
    search_url = f"{FHIR_SERVER_BASE_URL}/Condition?code={condition_id}"
    req = requests.get(search_url, auth=credentials)

    if req.status_code == 200:
        conditions = req.json()['entry']
        patient_ids = [entry['resource']['subject']['reference'].split('/')[-1] for entry in conditions]
        patients = [request_patient(patient_id, credentials) for patient_id in patient_ids]
         # Convert patient details into set of tuples to ensure uniqueness
        unique_patients = set((patient['id'], patient['name'][0]['given'][0], patient['name'][0]['family'], patient['gender'], patient['birthDate']) for patient in patients)

        total_patients = len(unique_patients)
        return {'unique_patients': unique_patients, 'total_patients': total_patients}
    else:
        return None





@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    credentials = (username, password)

    if request.method == 'POST':
        try:
            condition_id = request.form['condition_id']
            result = search_patients_by_condition(condition_id, credentials)
        except ValueError:
            result = 'Invalid input. Please enter a valid condition ID.'

    return render_template('index.html', result=result)


if __name__ == '__main__':
    port_str = os.environ['FHIR_PORT']
    port_int = int(port_str)
    app.run(debug=True, port=port_int)