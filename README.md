# fhir-condition-finder

This is a FHIR web application written in Python and using Flask as the backend. It can only be used for synthea datasets.

Following are the server port number and their respective datasets

```
9090 -> synthea10 (demo dataset)
9091 -> synthea_ri_adult
9092 -> synthea_ri_peds
```

## 1. Dependencies
This app depends on Python 3 and a few Python packages outlined in the `requirements.txt` file. 

## 2. Before running the app

Change these parameters in the .env file

```
FHIR_USERNAME = ???
FHIR_PASSWORD = ???
FHIR_PORT=5000
```

and change the port number according to the dataset in the app.py file 
FHIR_SERVER_BASE_URL= "http://pwebmedcit.services.brown.edu:????/fhir"

## 3. Running the App

We begin by creating a Python virtual environment using the `venv` module. This is done by running the command below from the "root" of this repo. 

```
python3 -m venv venv                 # create a virtual environment called venv

source venv/bin/activate             # activate our virtual environment

pip3 install -r requirements.txt     # install all our dependencies into the virtual environment
```


After the above steps, we should be able to launch our app using the following command.

```
python3 src/app.py
```


This will start the app on port 5000. You can open your preferred browser and see the app running on `http://localhost:5000`


