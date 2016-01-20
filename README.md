# DrupalDispatch
Deploy a Drupal 7 site in secconds on your localhost from command line, great for spinning up clean Drupal sites over &amp; over for test purposes. Make sure you have apache2 &amp; mysql server installed.

It's a bit like a localhost alternative to simplytest.me except this sucks in comparison feature wise. 

This script is only tested on Ubuntu, it won't work  on Windows (os.system calls) but will probably work on most debian distros.

## What it does
- Creates database, and user for you
- Downloads and extracts Drupal 7
- Creates an configures an Apache virtual host for you
- Launches your browser with the new Drupal install

## Install mysql & apache2 first 
Note, you probably already have this if you've been working on a Drupal site on your localhost...

sudo apt-get install mysql-server apache2 php5 php5-gd php5-mysql

Note your mysql admin username & pass during mysql install, you'll need this when using DrupalDeploy.

#Configure it (not necessary if running script directly!) 
If wanting to call this script from a wsgi application (like Flask for example)
Create a settings.json in your /home/<yourusername> directory (script presumes your have configured apache run user acess to this file)

The structure of the file must be:

{
    "mysql_username":"yourUsername",
    "mysql_pass":"yourPassword",
    "domain":"example.com"
}


#Run it
sudo python drupalDispatch.py




