#!/usr/bin/env bash
set -euo pipefail

echo "$(date -u +%FT%TZ) Fetching heat pump status..."
STATUS=$(pyecohome status --json)

# Current state from getDeviceDetailV3
HW_CURRENT=$(echo "$STATUS" | jq -r '.hot_water.current_temp')
HW_TARGET=$(echo "$STATUS"  | jq -r '.hot_water.target_temp')
HW_ON=$(echo "$STATUS"      | jq -r '.hot_water.on')
H_CURRENT=$(echo "$STATUS"  | jq -r '.heating.current_temp_main')
H_TARGET=$(echo "$STATUS"   | jq -r '.heating.target_temp')
H_ON=$(echo "$STATUS"       | jq -r '.heating.on')

# Operational params from paramListV3 type=1
# address 2072: Compressorsnelheid (rpm)
# address 2192: Omvormer waterpomp stroomsnelheid (L/H)
COMPRESSOR_RPM=$(echo "$STATUS"     | jq '(.operational["2072"].value // 0)')
PUMP_LPH=$(echo "$STATUS"           | jq '(.operational["2192"].value // 0)')
COMPRESSOR_RUNNING=$(echo "$STATUS" | jq '(.operational["2072"].value // 0) > 0')
PUMP_RUNNING=$(echo "$STATUS"       | jq '(.operational["2192"].value // 0) > 0')

# Derived
HW_BELOW=$(echo "$STATUS" | jq '(.hot_water.target_temp // 0) - (.hot_water.current_temp // 0)')
HW_NEEDS_HEAT=$(echo "$STATUS" | jq '(.hot_water.target_temp // 0) - (.hot_water.current_temp // 0) > 10')
HW_NEAR_TARGET=$(echo "$STATUS" | jq '(.hot_water.target_temp // 0) - (.hot_water.current_temp // 0) < 2')

# Report
echo "Hot water:  current=${HW_CURRENT}°C  target=${HW_TARGET}°C  enabled=${HW_ON}"
echo "Heating:    current=${H_CURRENT}°C  target=${H_TARGET}°C  enabled=${H_ON}"
echo "Compressor: running=${COMPRESSOR_RUNNING} (${COMPRESSOR_RPM} rpm)"
echo "Circ. pump: running=${PUMP_RUNNING} (${PUMP_LPH} L/H)"

# Decision 1: hot water is off and more than 10°C below target → enable it
if [ "$HW_ON" = "false" ] && [ "$HW_NEEDS_HEAT" = "true" ]; then
    echo "Action: hot water off, ${HW_BELOW}°C below target — enabling hot water"
    pyecohome hot-water on
fi

# Decision 2: circulation pump running, compressor stopped, heating off,
# hot water on, and within 2°C of target → hot water is done, disable it
if [ "$PUMP_RUNNING" = "true" ] && \
   [ "$COMPRESSOR_RUNNING" = "false" ] && \
   [ "$H_ON" = "false" ] && \
   [ "$HW_ON" = "true" ] && \
   [ "$HW_NEAR_TARGET" = "true" ]; then
    echo "Action: pump running, compressor stopped, heating off, hot water ${HW_BELOW}°C below target — disabling hot water"
    pyecohome hot-water off
fi

echo "$(date -u +%FT%TZ) Done."
