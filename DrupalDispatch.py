import random
import string
import sys
import os 
import shutil
import getpass
import pwd,grp,json

class DrupalDispatch:

    def getSettings(self):
        #########################################
        ###### Database Creation ###############
        # - Creates mysql user
        # - Create database for new Drupal site
        ########################################

	#Get settings from outside root directory
        # To create settings file, use the example below,
	# and store it outside your webroot
	# Create python object from json. 
	# Settings file format should be valid json and include the following
	# JSON object:
        #{
        #    "mysql_username":"your-mysql-username",
        #    "mysql_pass":"your-mysql-password",
	#    "domain":"example.com"
        #}
	#
	# Mysql username & password is self explanatory,
	# 'domain' is appended to the user requested site names. 
        # for example, a user requiests a website called 'samscakes'
	# DrupalDispatch takes this and appends the domain to the 
	# requested subdomain (siteName) resulting in:
	# samscakes.example.com


	#If manually running script, get settings from stdin
	if __name__ == "__main__":
		settings = {"mysql_user":'',"mysql_pass":''}
		settings['mysql_username'] = raw_input("Enter your mysql admin username (e.g. root):")
		settings['mysql_pass'] = getpass.getpass("Enter your mysql admin password:")
		self.settings = settings
	else: #Read settings from settings.json from outside webroot
		try:
			fp = open('/home/settings.json')
		except IOError:
			exit("Exiting because could not open settings.json")

		self.settings = json.load(fp)

    def buildWebsite(self, siteName):

	#Check site dosent alreay exist
	if os.system('findsite ' + siteName) == 0:
		exit("Sitenme already exists!")

	#Get settings if not already set (this may happen from stdin for example)
	try:
		self.settings #If not defined, get settings
	except:    
		self.getSettings() 
        #Create new Drupal database username
        drupal_db_user = 'drpl_user' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(5)])

        drupal_db_name = drupal_db_user

        drupal_db_pass = 'drpl_db_pass_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(5)])

        #Create mysql sql script which createss user & database for new drupal site
        f = open('createUser.sql','w')

        #Write create user SQL statement to file
        f.write("CREATE USER '" + drupal_db_user + \
                "'@'localhost' IDENTIFIED BY '" +  drupal_db_pass + "';\n")

        #Write create database SQL statement to file
        f.write("CREATE DATABASE " + drupal_db_name + ';\n')

        #Write SQL statement to grantingnew user permissions to their database
        f.write("GRANT ALL ON " + drupal_db_name + ".* TO " + "'" + \
                drupal_db_user + "'@'localhost';\n") 
        f.close()
        os.system("mysql -u " + self.settings['mysql_username'] + " --password=" + self.settings['mysql_pass'] + " < createUser.sql")

        # Create website directory
        #   Get permissions right
        #   Get group www-data uid & gid
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        drupal_path = '/var/www/' + drupal_db_user + '/'
        os.mkdir(drupal_path, 775) # Create website directory 
        os.chown(drupal_path, uid, gid) # Set owner to www-data
        os.chmod(drupal_path,775)
	os.system("chmod -R 775 " + drupal_path)

        # Extract Drupal tar archive into drupal_path
        os.system("tar xf /var/www/drupal-7.41.tar.gz -C /var/www/")

        # Move download into drupal_path web directory
        drupal_path = '/var/www/' + drupal_db_user + '/'
        os.system("mv /var/www/drupal-7.41/ " + drupal_path)
        print "Move command: " + "mv /var/www/drupal-7.41/ " + drupal_path
        print "Moved Drupal to " + drupal_path

        #Move everything up one directory 
        os.system("mv " + drupal_path + "drupal-7.41/* " + drupal_path)
        os.system("mv " + drupal_path + "drupal-7.41/.htaccess " + drupal_path)
        os.system("mv " + drupal_path + "drupal-7.41/.gitignore " + drupal_path)
        os.system("rm -R " + drupal_path + 'drupal-7.41')

        ###############################################
        #######  Apache configuration #################
        # - Adds site to apache's /etc/apache/sites-available
        # - Enables the website using a2ensite tool
        # - Adds website to /etc/hosts file 
        #      - This makes <sitename>.localhost work!
        ###############################################

	#Append domain to user requested subdomain
	# E.g. siteName of 'acecorp' becomes acecorp.example.co.uk
        server_name = siteName + '.' + self.settings['domain'] 
        document_root = drupal_path

        f_VirtualHostConf = open('/etc/apache2/sites-available/' + drupal_db_user \
                                 + '.conf', 'w')

        f_VirtualHostConf.write("<VirtualHost *:80>\n")
        f_VirtualHostConf.write("ServerName " + server_name + "\n")
        f_VirtualHostConf.write("DocumentRoot " + document_root + "\n")
        f_VirtualHostConf.write("</VirtualHost>" + "\n")

        os.chown(drupal_path, uid, gid) # Set owner to www-data
        os.system("chmod -R 775 " + drupal_path)
        os.system("chown -R www-data " + drupal_path)
        os.system("chown -R www-data " + drupal_path + ".htaccess")
	print 'Closing f_VirtualHostConf file'
	f_VirtualHostConf.close()
        # Enable the website's config
        os.system("a2ensite " + drupal_db_user)


        ##################################################
        ########## Drupal config file ####################
        ##################################################

        import fileinput
        for line in fileinput.FileInput(drupal_path + 'sites/default/default.settings.php', inplace=1):
            database_cfg = "\
            $databases['default']['default'] = array(\n\
                'driver' => 'mysql',\n\
                'database' => '" + drupal_db_user + "',\n\
                'username' => '" + drupal_db_user + "',\n\
                'password' => '" + drupal_db_pass + "',\n\
                'host' => 'localhost',\n\
                'prefix' => '',\n\
            );\n"
            line = line.replace('$databases = array();',database_cfg)
            if line:
                print line,
            else:
                print line,

        #Copy default.settings to settings.php & set permissions etc
        os.system("cp " + drupal_path + "sites/default/default.settings.php " + \
                 drupal_path + "sites/default/settings.php")

        os.system("chmod 550 " + drupal_path + "sites/default/settings.php")
        os.system("chown www-data " + drupal_path + "sites/default/settings.php")
        os.system("chgrp www-data " + drupal_path + "sites/default/settings.php")

        ############################################
        ############ Drupal prep ##################
        # - modules folder group & permissions
        ###########################################
        os.system("chmod -R 775 " + drupal_path + "sites/all/modules")
        os.system("chgrp -R www-data -R " + drupal_path + "sites/all/modules")

        os.system("mkdir " + drupal_path + "sites/default/files")
        os.system("chgrp -R www-data -R " + drupal_path + "sites/default/files")

        #Sane permissions for files directory
        os.system("chmod -R 775 " + drupal_path + "sites/default/files")

        ######################
        ### Finish message ####
        #######################

        print "#" * 80
        print 'Drupal database username: ' + drupal_db_user
        print 'Drupal database password: ' + drupal_db_pass
        print '  -- This install tries to launch the browser for you.'
        print 'If not, go to: http://' + siteName + '.' + self.settings['domain'] + '/install.php ' + \
                'on your browser to complete installation.'
        print "#" * 80

        # Reload apache2 confiruation to include new website
        os.system("sudo /etc/init.d/apache2 graceful")

        def downloadDrupal(self):
            ##########################################
            ########## Drupal Download #############
            # - Create site directory /var/www/sitename
            ##########################################

            # Get group www-data uid & gid
            uid = pwd.getpwnam("www-data").pw_uid
            gid = grp.getgrnam("www-data").gr_gid


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

    def toMigrate(self):


        #TODO remove /tmp/createuser.sql

        # Try to launch webbrowser
        import webbrowser
        webbrowser.open_new("http://" + drupal_db_user + '.localhost/install.php')

if __name__ == "__main__":
	builder = DrupalDispatch()
	sitename = raw_input("Enter desired site subdomain. e.g. enter 'mysite' for mysite.yourdomain.com:")
	builder.getSettings()
	#Build site
        builder.buildWebsite(sitename)
