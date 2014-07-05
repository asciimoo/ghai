#!/bin/sh
# download fontawesome
wget https://fortawesome.github.io/Font-Awesome/assets/font-awesome-4.1.0.zip -O fontawesome.zip \
&& unzip fontawesome.zip \
&& rm fontawesome.zip \
&& mv font-awesome-4.1.0/fonts/* ghai/static/fonts \
&& mv font-awesome-4.1.0/css/font-awesome.min.css ghai/static/css \
&& rm -r font-awesome-4.1.0
