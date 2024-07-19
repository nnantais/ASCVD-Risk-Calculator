# ASCVD Risk Calculator

This ASCVD Risk calculator is used to study the risk prediction for cardiovascular disease (CVD).

This calculator uses the Pooled Cohort risk prediction equations to predict 10-year atherosclerotic cardiovascular disease risk. More information about the predictor equation can be found here https://github.com/bcjaeger/PooledCohort/tree/master

# Steps to run the ASCVD Risk Calculator

## 1. Check if R and python are installed where you are running this app.

```
python3 --version
R --version
```

## 2. Before running the app

Change these parameters in the .env file. Use the port number assigned to you to run the app for FHIR_PORT.

```
FHIR_SERVER_BASE_URL= http://pwebmedcit.services.brown.edu:????/fhir
FHIR_USERNAME = ???
FHIR_PASSWORD = ???
FHIR_PORT=????

```

Start R and run the R.home() and .libPaths() commands to get the directory names

```
> R.home()
[1] "/Library/Frameworks/R.framework/Resources"
> .libPaths()
[1] "/Library/Frameworks/R.framework/Versions/4.3-arm64/Resources/library"
```


## 3. Clone the repo
```
git clone https://github.com/bcbi/ASCVD-Risk-Calculator.git

cd ASCVD-Risk-Calculator
```

## 4. Update the above R dirceory paths in the app.py file in the ASCVD-Risk-Calculator directory in line 8 and 9

```
os.environ['R_HOME'] = "????"
os.environ['R_USER'] = "????"
```
## 5. Run the setup script
```
./setup_environment.sh
```

## 6. Activate the virtual environment
```
source venv/bin/activate
```

## 7. Run the flask app
```
python src/app.py
```

This will start the app on port "FHIR_PORT". You can open your preferred browser and see the app running on `http://localhost:FHIR_PORT` replace the FHIR_PORT with the actual port number assigned to you. 
The exact URL to the app can also be found on the terminal output after running the app.


