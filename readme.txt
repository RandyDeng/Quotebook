Setting up AWS
Code is ideally run on EC2 instance of your choice (I used ubuntu 16.04)
EC2 instance server should have ports 22 (for admin control) and 80 (serve http web pages) open
DynamoDB database is used to store quotes in Quotebook and user login information in Quotebook_Users
Access key, secret access key, and regions is up to the admin. I created a user with only read/write access to DynamoDB and nothing else

Setting up uWSGI and Nginx
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-16-04

Setting up virtual environment: dependencies are isolted in virtual environment so they wont clutter up the main computer
(run this in root directory)
virtualenv quotebookenv
source quotebookenv/bin/activate
* install necessary dependencies (see below)
deactivate (exit virtual shell)

Installs:
sudo apt-get install python-pip python-dev nginx
sudo pip install flask
sudo pip install boto3
sudo pip install flask_login
sudo pip install virtualenv
sudo pip install uwsgi

Config file locations:
sudo mv quotebook_service.txt /etc/systemd/system/quotebook.service
sudo mv quotebook_nginx.txt /etc/nginx/sites-available/quotebook
sudo ln -s /etc/nginx/sites-available/quotebook /etc/nginx/sites-enabled
** make sure to delete default in "/etc/nginx/sites-available" and "/etc/nginx/sites-enabled" and any older versions of the quotebook nginx files that may still be there

To start the engines:
sudo systemctl start quotebook
sudo systemctl enable quotebook
sudo systemctl restart nginx

To stop the engines:
sudo systemctl stop quotebook
sudo systemctl stop nginx