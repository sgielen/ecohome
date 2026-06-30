Share endpoints
===============

All requests use the standard headers from `login.md` plus the `x-token` and
`Cookie` headers. Both endpoints return the result in both `object_result` and
`objectResult`; prefer `object_result`.


getMyDeviceShareDataList
------------------------

Lists devices you have shared with others.

POST https://ehome.ne01.com/cloudservice/api/app/device/getMyDeviceShareDataList.json?lang=nl_NL

Body:

    {"from_user": "<your user_id>"}

Returns `object_result` as a list of share records (empty if you have shared nothing).


getMyAcceptDeviceShareDataList
------------------------------

Lists devices others have shared with you.

POST https://ehome.ne01.com/cloudservice/api/app/device/getMyAcceptDeviceShareDataList.json?lang=nl_NL

Body:

    {"to_user": "<your user_id>"}

Returns `object_result` as a list of share records (empty if nothing has been shared with you).
