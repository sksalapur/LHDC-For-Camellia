#!/system/bin/sh
LAST_ANC_MODE=""
PREFS_FILE="/data/data/com.music.bypass/shared_prefs/realme_anc_prefs.xml"
while true; do
    if [ -f "$PREFS_FILE" ]; then
        ACTIVE_MODE=$(grep -o 'name="active_mode">[^<]*' "$PREFS_FILE" 2>/dev/null | cut -d'>' -f2)
        if [ -n "$ACTIVE_MODE" ] && [ "$ACTIVE_MODE" != "$LAST_ANC_MODE" ]; then
            LAST_ANC_MODE="$ACTIVE_MODE"
            /data/adb/apd resetprop -n persist.bluetooth.lhdc_mtu 600
            if [ "$ACTIVE_MODE" = "NORMAL" ]; then
                /data/adb/apd resetprop -n persist.bluetooth.lhdc_bitrate 900
            else
                /data/adb/apd resetprop -n persist.bluetooth.lhdc_bitrate 500
            fi
        fi
    fi
    sleep 1
done
