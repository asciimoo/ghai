#!/bin/sh

# copy and edit config
cp ghairc_sample .ghairc

# create and activate virtualenv
virtualenv env
source env/bin/activate

# install dependencies
pip install -r requirements.txt

# initialize the model
PYTHONPATH=`pwd` python ghai/models.py

# download bootstrap
wget https://github.com/twbs/bootstrap/releases/download/v3.2.0/bootstrap-3.2.0-dist.zip -O bootstrap.zip \
&& unzip bootstrap.zip \
&& rm bootstrap.zip \
&& mv bootstrap-3.2.0-dist/css/bootstrap.min.css ghai/static/ \
&& mv bootstrap-3.2.0-dist/js/bootstrap.min.js ghai/static/js \
&& rm -rf bootstrap-3.2.0-dist \

# download jquery
wget 'https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js' -O ghai/static/js/jquery.min.js

# download fontawesome
wget https://fortawesome.github.io/Font-Awesome/assets/font-awesome-4.1.0.zip -O fontawesome.zip \
&& unzip fontawesome.zip \
&& rm fontawesome.zip \
&& mv font-awesome-4.1.0/fonts/* ghai/static/fonts \
&& mv font-awesome-4.1.0/css/font-awesome.css ghai/static/css \
&& rm -r font-awesome-4.1.0
