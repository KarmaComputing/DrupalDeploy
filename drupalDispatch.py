import random
import string
import sys
import os 
import shutil
import getpass

mysql_user = raw_input("Enter your mysql admin username (e.g. root):")

mysql_pass = getpass.getpass("Enter your mysql admin password:")

#########################################
###### Database Creation ###############
# - Creates mysql user
# - Create database for new Drupal site
########################################
#Create new Drupal database username
drupal_db_user = 'drpl_user' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(5)])

drupal_db_name = drupal_db_user

drupal_db_pass = 'drpl_db_pass_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(5)])

#Create mysql sql script which createss user & database for new drupal site
f = open('/tmp/createUser.sql','w')

#Write create user SQL statement to file
f.write("CREATE USER '" + drupal_db_user + \
        "'@'localhost' IDENTIFIED BY '" +  drupal_db_pass + "';\n")

#Write create database SQL statement to file
f.write("CREATE DATABASE " + drupal_db_name + ';\n')

#Write SQL statement to grantingnew user permissions to their database
f.write("GRANT ALL ON " + drupal_db_name + ".* TO " + "'" + \
        drupal_db_user + "'@'localhost';\n") 
f.close()
os.system("mysql -u " + mysql_user + " --password=" + mysql_pass + " < /tmp/createUser.sql")



##########################################
########## Drupal Download #############
# - Create site directory /var/www/sitename
##########################################
import pwd,grp

# Get group www-data uid & gid
uid = pwd.getpwnam("www-data").pw_uid
gid = grp.getgrnam("www-data").gr_gid

# Create website directory
drupal_path = '/var/www/' + drupal_db_user + '/'
os.mkdir(drupal_path, 775) # Create website directory 
os.chown(drupal_path, uid, gid) # Set owner to www-data
os.chmod(drupal_path,775)

# Download Drupal 7.41
import urllib2

url = "http://ftp.drupal.org/files/projects/drupal-7.41.tar.gz"

file_name = url.split('/')[-1]
u = urllib2.urlopen(url)
f = open(file_name, 'wb')
meta = u.info()
file_size = int(meta.getheaders("Content-Length")[0])
print "Downloading Drupal 7.41: %s Bytes: %s" % (file_name, file_size)

file_size_dl = 0
block_sz = 8192
while True:
    buffer = u.read(block_sz)
    if not buffer:
        break

    file_size_dl += len(buffer)
    f.write(buffer)
    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
    status = status + chr(8)*(len(status)+1)
    print status,

f.close()

# Extract Drupal tar archive into drupal_path
os.system("sudo tar xf " + os.getcwd() + '/drupal-7.41.tar.gz')

# Move download into drupal_path web directory
shutil.move(os.getcwd() + '/drupal-7.41/', drupal_path)
print "Moved Drupal to " + drupal_path

#Move everything up one directory 
os.system("sudo mv " + drupal_path + "drupal-7.41/* " + drupal_path)
os.system("sudo mv " + drupal_path + "drupal-7.41/.htaccess " + drupal_path)
os.system("sudo mv " + drupal_path + "drupal-7.41/.gitignore " + drupal_path)
os.system("sudo rm -R " + drupal_path + 'drupal-7.41')

###############################################
#######  Apache configuration #################
# - Adds site to apache's /etc/apache/sites-available
# - Enables the website using a2ensite tool
# - Adds website to /etc/hosts file 
#      - This makes <sitename>.localhost work!
###############################################

server_name = drupal_db_user + '.localhost'
document_root = drupal_path

f_VirtualHostConf = open('/etc/apache2/sites-available/' + drupal_db_user \
                         + '.conf', 'w')

f_VirtualHostConf.write("<VirtualHost *:80>\n")
f_VirtualHostConf.write("ServerName " + server_name + "\n")
f_VirtualHostConf.write("DocumentRoot " + document_root + "\n")
f_VirtualHostConf.write("</VirtualHost>" + "\n")

#Permissions
os.chown(drupal_path, uid, gid) # Set owner to www-data
os.system("sudo chmod -R 775 " + drupal_path)
os.system("sudo chown -R www-data " + drupal_path)
os.system("sudo chown -R www-data " + drupal_path + ".htaccess")

# Enable the website's config
os.system("sudo a2ensite " + drupal_db_user)

#Add [drupal_db_user].localhost to hosts file
f_hosts = open('/etc/hosts','a')
f_hosts.write('127.0.0.1 ' + drupal_db_user + '.localhost\n')
f_hosts.close()

# Restart networking service to catch hosts file change
os.system("sudo service networking restart")


print "#" * 80
print 'Drupal database username: ' + drupal_db_user
print 'Drupal database password: ' + drupal_db_pass
print '  -- This install tries to launch the browser for you.'
print 'If not, go to: http://' + drupal_db_user + '.localhost ' + \
        'on your browser to complete installation.'
print "#" * 80

# Reload apache2 confiruation to include new website
os.system("sudo service apache2 reload")

#TODO remove /tmp/createuser.sql

# Try to launch webbrowser
import webbrowser
webbrowser.open_new_tab("http://" + drupal_db_user + '.localhost')
