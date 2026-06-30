Device endpoints
================

All requests use the standard headers from `login.md` plus the `x-token` and
`Cookie` headers.

Cloudservice uses snake_case envelope fields (`error_code`, `error_msg`, `is_reuslt_suc`).
The result payload is inconsistently named per endpoint — see each section below.
Crmservice uses camelCase throughout (`errorCode`, `objectResult`) with no `isReusltSuc`.


deviceList
----------

POST https://ehome.ne01.com/cloudservice/api/app/device/deviceList.json?lang=nl_NL

Body:

    {"page_index": "1", "page_size": "1000"}

Returns `object_result` as a list of devices:

- `device_id`: opaque string ID
- `device_code`: hardware serial used to identify the device in other endpoints
- `device_nick_name`: user-assigned name
- `device_name`: product name (e.g. "Heating & Cooling Heat Pump")
- `device_type`: "1" for heat pump
- `device_status`: "ONLINE" / "OFFLINE"
- `running_status`: "Standby" etc.
- `cur_unit`: temperature unit ("℃")
- `water_temp`, `air_temp`, `floor_temp`: current sensor readings; `air_temp` is a 16-character hex string of unclear meaning


getDeviceBaseInfo
-----------------

POST https://ehome.ne01.com/cloudservice/api/app/deviceInfo/getDeviceBaseInfo.json?lang=nl_NL

Body:

    {"device_code": "WQ[........]"}

Returns `object_result`:

- `device_id`, `device_code`, `device_name`, `device_nick_name`
- `mac_address`: MAC of the device
- `sn`: serial number
- `is_mine`: whether the authenticated user owns the device


getDeviceDetailV3
-----------------

Note: this is on **crmservice**, not cloudservice.

POST https://ehome.ne01.com/crmservice/api/app/deviceInfo/getDeviceDetailV3?lang=nl_NL

Body:

    {"deviceCode": "WQ[........]"}

Returns `objectResult`:

- `switchAddress`: Modbus-style register address for the master on/off switch (1017)
- `curSwitch`: current on/off state of the device
- `isFault` / `faultNum`: fault status
- `curUnit`: temperature unit
- `hasSilentMode`, `hasSpa`: feature flags
- `cardList`: list of subsystems (cards), each with:
  - `card`: index ("0" = heating/cooling circuit, "2" = hot water)
  - `switchAddress`: on/off register for this card (1018 for heating, 1020 for hot water)
  - `curSwitch`: current on/off state of this card
  - `curMode` / `modeList`: active mode and available modes, each with `modeAddress`, `modeValue`, `modeMeaning`
  - `isClimateCurve`: whether climate curve mode is active
  - `settingAddress` / `settingTemp`: register and current target temperature (1023 for heating, 1024 for hot water)
  - `upperTemp` / `lowerTemp`: allowed temperature range
  - `curTempMain` / `curTempMinor`: current measured temperatures
  - `stepLength`: temperature adjustment step size


updateSwitchState
-----------------

Note: the URL contains a typo — "Sate" instead of "State".

POST https://ehome.ne01.com/cloudservice/api/app/deviceInfo/updateSwitchSate.json?lang=nl_NL

Body:

    {"device_code": "WQ[........]", "address": "1020", "value": true}

`address` is a `switchAddress` value from the `getDeviceDetailV3` response (1017 for the
whole device, 1018 for heating/cooling, 1020 for hot water).

Returns only a success/failure envelope; no result payload.
