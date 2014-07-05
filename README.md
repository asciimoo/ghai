GHAI
====

GitHub activity interface.


demo: [here](http://ghai.0x2a.tk/)


### Install

```bash
# get git, python, setuptools, virtualenv, unzip
sudo apt-get install git python python-setuptools python-virtualenv zip

# clone the repo
git clone git@github.com:asciimoo/ghai.git
cd ghai

# run install.sh
./install.sh

# edit your config
# register github app here: https://github.com/settings/applications/new (set callback url to http://your.domain/callback)
vi .ghairc

# start the application
./env/bin/python ghai/webapp.py
```
