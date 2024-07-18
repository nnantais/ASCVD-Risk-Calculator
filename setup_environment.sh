#!/bin/bash

python3 -m venv venv
source venv/bin/activate

# install python packages
pip install -r requirements.txt

# install R pacakges
Rscript -e "install.packages('devtools', repos='http://cran.rstudio.com/')"
Rscript -e "devtools::install_github('bcjaeger/PooledCohort')"
