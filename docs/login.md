Login flow
==========

To log in, send a POST request to the Cloudservice:

https://ehome.ne01.com/cloudservice/api/app/user/login.json?lang=nl_NL

I use the following headers:

- 'Content-Type: application/json;charset=UTF-8'
- 'Connection: keep-alive'
- 'Accept: */*'
- 'app-id-type: 0'
- 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) uni-app'
- 'time-zone: Europe/Berlin'
- 'Accept-Language: nl-NL,nl;q=0.9'

The body contains a JSON object with `user_name`, `password` set to the MD5 sum of your password and `type` set to 2.

This then returns a cookie for the Cloudservice and a JSON object
with many fields, some of the interesting ones:

- error_code: 0 and error_msg: "Success"
- object_result.user_id: your user ID
- object_result.real_name: for me, the same as my username?
- object_result.x-token: a token distinct from the cookie

From now on, you can send requests to the Cloudservice with the same cookie and
the `x-token` header set to the same value as in the object_result. Be sure to
use the same headers as above on all requests.

To get information on the logged in user, send all headers and no body as a GET
request to the following endpoint:

https://ehome.ne01.com/cloudservice/api/app/user/getUserInfo.json?lang=nl_NL

To log out a POST request, and a body consisting of a JSON object with
`from_user` key set to your user ID, to the following URL:

https://ehome.ne01.com/cloudservice/api/app/user/logout.json?lang=nl_NL
