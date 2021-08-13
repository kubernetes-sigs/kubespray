#!/bin/bash
hyperauthserver=$1
echo hyperauthserver : $hyperauthserver

# get Admin Token
token=$(curl -X POST 'http://'$hyperauthserver':8080/auth/realms/master/protocol/openid-connect/token' \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "username=admin" \
 -d 'password=admin' \
 -d 'grant_type=password' \
 -d 'client_id=admin-cli' | jq -r '.access_token')

echo accessToken : $token

# Sed HypercloudServer IP
hypercloudconsole=$2
echo hypercloudconsole : $hypercloudconsole
sed -i 's/172.22.6.14/'$hypercloudconsole'/g' 3.tmax-realm-export.json
sed -i 's/172.22.6.2:31304/'$hypercloudconsole'/g' 3.tmax-realm-export.json

# tmax Realm Import
curl 'http://'$hyperauthserver':8080/auth/admin/realms' \
  -H "authorization: Bearer $token" \
  -H "content-type: application/json;charset=UTF-8" \
  --data-binary @3.tmax-realm-export.json 

# Add hc-admin@tmax.co.kr User
curl -g -i -X POST \
   -H "Content-Type:application/json" \
   -H "Authorization:Bearer $token" \
   -d \
    '{
      "enabled": true,
      "attributes": {
        "dateOfBirth": "2020-09-09",
        "phone": "000-0000-0000",
        "department": "tmaxCloud",
        "description": "hypercloud admin"
      },
      "username": "hc-admin@tmax.co.kr",
      "emailVerified": "true",
      "email": "hc-admin@tmax.co.kr"
    }' \
     'http://'$hyperauthserver':8080/auth/admin/realms/tmax/users'

# Get UserID with UserName 'hc-admin@tmax.co.kr'
userid=$(curl -i -X GET \
   -H "Authorization:Bearer $token" \
 'http://'$hyperauthserver':8080/auth/admin/realms/tmax/users' | grep id | cut -f 2 -d ':' | cut -f 2 -d '"' | sed 's/"/ /g' )

echo userId : $userid

# Set Password as 'admin'
curl 'http://'$hyperauthserver':8080/auth/admin/realms/tmax/users/'$userid'/reset-password' \
  -X 'PUT' \
  -H "authorization: Bearer $token" \
  -H "content-type: application/json;charset=UTF-8" \
  --data-binary '{"type":"password","value":"Tmaxadmin1!","temporary":false}'       
