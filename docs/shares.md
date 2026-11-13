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

Devices shared with you do **not** appear in `deviceList`; this endpoint is the only way to
discover them. Each record has the same shape as a `deviceList` entry (`device_code`,
`device_nick_name`, `device_status`, `running_status`, `product_img_url`, ...) plus
`product_id` and `customer_id`. No permission level or pending/accepted status was observed.

All per-device read endpoints (`getDeviceBaseInfo`, `getDeviceDetailV3`, `paramListV3`) work
on shared devices with just the `device_code`; `getDeviceBaseInfo` returns `is_mine: false`
for them. Write endpoints (`updateSwitchSate`, `controlOfValue`) have not yet been verified
on shared devices.
