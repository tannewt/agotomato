agotomato
=========

An AgoControl module that detects presence via a TomatoUSB router.

This is modeled after http://paulusschoutsen.nl/blog/2013/10/tomato-api-documentation/

You'll need a tomato.conf file with server, username, password and token fields. See the post above to http_id for how to get the token.

Here is an example of tomato.conf:
[tomato]
server=192.168.1.1
username=admin
password=<password>
token=<token>
