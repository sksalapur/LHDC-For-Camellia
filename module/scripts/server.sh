#!/system/bin/sh
# ═══════════════════════════════════════════════════════════════════
# LHDC Audiophile Codec Tuner — Micro HTTP Daemon
# Zero-dependency shell HTTP server on port 9092
# ═══════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODDIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WEBROOT="$MODDIR/webroot"

# APatch / Magisk resetprop binary path
RESETPROP="/data/adb/apd resetprop"
[ -f "/data/adb/apd" ] || RESETPROP="/data/adb/ap/bin/resetprop"
[ -f "/data/adb/ap/bin/resetprop" ] || RESETPROP="/data/adb/magisk/resetprop"
[ -f "/data/adb/magisk/resetprop" ] || RESETPROP="resetprop"

# Read primary HTTP request line from stdin
read -r REQUEST_LINE || exit 0
REQUEST_LINE=$(echo "$REQUEST_LINE" | tr -d '\r\n')
[ -z "$REQUEST_LINE" ] && exit 0

# Parse method and target URI
METHOD=$(echo "$REQUEST_LINE" | awk '{print $1}')
FULL_URI=$(echo "$REQUEST_LINE" | awk '{print $2}')

# Read remaining request headers until empty line
CONTENT_LENGTH=0
while IFS= read -r HEADER; do
    HEADER=$(echo "$HEADER" | tr -d '\r\n')
    [ -z "$HEADER" ] && break
    case "$HEADER" in
        [Cc][Oo][Nn][Tt][Ee][Nn][Tt]-[Ll][Ee][Nn][Gg][Tt][Hh]:*)
            CONTENT_LENGTH=$(echo "$HEADER" | awk '{print $2}' | tr -d '\r\n ')
            ;;
    esac
done

# Read body if POST
BODY=""
if [ "$METHOD" = "POST" ] && [ -n "$CONTENT_LENGTH" ] && [ "$CONTENT_LENGTH" -gt 0 ] 2>/dev/null; then
    BODY=$(head -c "$CONTENT_LENGTH" 2>/dev/null | tr -d '\r\n')
fi

# Separate URI path and query string
URI_PATH=$(echo "$FULL_URI" | cut -d'?' -f1)
case "$FULL_URI" in
    *\?*) QUERY_STRING=$(echo "$FULL_URI" | cut -d'?' -f2- | tr -d '\r\n') ;;
    *) QUERY_STRING="" ;;
esac

[ -z "$QUERY_STRING" ] && [ -n "$BODY" ] && QUERY_STRING="$BODY"

get_param() {
    PARAM_NAME="$1"
    echo "$QUERY_STRING" | tr '&' '\n' | grep "^${PARAM_NAME}=" | head -n1 | cut -d'=' -f2- | tr -d '\r\n '
}

send_headers() {
    STATUS_CODE="${1:-200 OK}"
    CONTENT_TYPE="${2:-text/html; charset=utf-8}"
    CLENGTH="$3"

    printf "HTTP/1.1 %s\r\n" "$STATUS_CODE"
    printf "Content-Type: %s\r\n" "$CONTENT_TYPE"
    printf "Connection: close\r\n"
    printf "Access-Control-Allow-Origin: *\r\n"
    printf "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
    printf "Access-Control-Allow-Headers: Content-Type\r\n"
    if [ -n "$CLENGTH" ]; then
        printf "Content-Length: %s\r\n" "$CLENGTH"
    fi
    printf "\r\n"
}

if [ "$METHOD" = "OPTIONS" ]; then
    send_headers "200 OK" "text/plain" "0"
    exit 0
fi

# Dispatch routes
case "$URI_PATH" in
    /api/status)
        PROP_BR=$(getprop persist.bluetooth.lhdc_bitrate 2>/dev/null)
        [ -z "$PROP_BR" ] && PROP_BR="500"

        PROP_MTU=$(getprop persist.bluetooth.lhdc_mtu 2>/dev/null)
        [ -z "$PROP_MTU" ] && PROP_MTU="600"

        PROP_Q=$(getprop persist.bluetooth.lhdc_max_queue 2>/dev/null)
        [ -z "$PROP_Q" ] && PROP_Q="18"

        PROP_ABSOLUTE=$(getprop persist.bluetooth.disableabsvol 2>/dev/null)
        [ -z "$PROP_ABSOLUTE" ] && PROP_ABSOLUTE="false"

        PREFS="/data/data/com.music.bypass/shared_prefs/realme_anc_prefs.xml"
        MODE="NORMAL"
        BATTL="-1"
        BATTR="-1"
        BATTC="-1"
        if [ -f "$PREFS" ]; then
            m=$(grep -o 'name="active_mode">[^<]*' "$PREFS" 2>/dev/null | cut -d'>' -f2)
            [ -n "$m" ] && MODE="$m"
            bl=$(grep -o 'name="cached_battery_left" value="[0-9]*"' "$PREFS" 2>/dev/null | cut -d'"' -f4)
            [ -n "$bl" ] && BATTL="$bl"
            br=$(grep -o 'name="cached_battery_right" value="[0-9]*"' "$PREFS" 2>/dev/null | cut -d'"' -f4)
            [ -n "$br" ] && BATTR="$br"
            bc=$(grep -o 'name="cached_battery_case" value="[0-9]*"' "$PREFS" 2>/dev/null | cut -d'"' -f4)
            [ -n "$bc" ] && BATTC="$bc"
        fi

        case "$BATTL" in ''|*[!0-9]*) BATTL="-1" ;; esac
        case "$BATTR" in ''|*[!0-9]*) BATTR="-1" ;; esac
        case "$BATTC" in ''|*[!0-9]*) BATTC="-1" ;; esac

        LAST_LOG=$(logcat -d -t 15 -s LHDC_V5_SHIM:V 2>/dev/null | grep -E 'written=|congested|clean|ret=' | tail -n 8 | tr '\n' '|' | sed 's/"/\\"/g' | tr -d '\r')

        JSON=$(cat << EOF
{
  "bitrate": "$PROP_BR",
  "mtu": "$PROP_MTU",
  "max_queue": "$PROP_Q",
  "abs_vol_disabled": "$PROP_ABSOLUTE",
  "anc_mode": "$MODE",
  "battery_left": $BATTL,
  "battery_right": $BATTR,
  "battery_case": $BATTC,
  "recent_logs": "$LAST_LOG"
}
EOF
)
        CLEN=$(printf "%s" "$JSON" | wc -c | tr -d ' ')
        send_headers "200 OK" "application/json; charset=utf-8" "$CLEN"
        printf "%s" "$JSON"
        ;;

    /api/set|/api/apply)
        NEW_BR=$(get_param "bitrate")
        NEW_MTU=$(get_param "mtu")
        NEW_Q=$(get_param "max_queue")
        DO_RESTART=$(get_param "restart_bt")

        if [ -n "$NEW_BR" ]; then
            $RESETPROP -n persist.bluetooth.lhdc_bitrate "$NEW_BR"
        fi
        if [ -n "$NEW_MTU" ]; then
            $RESETPROP -n persist.bluetooth.lhdc_mtu "$NEW_MTU"
        fi
        if [ -n "$NEW_Q" ]; then
            $RESETPROP -n persist.bluetooth.lhdc_max_queue "$NEW_Q"
        fi

        RESTARTED=false
        if [ "$DO_RESTART" = "1" ] || [ "$DO_RESTART" = "true" ]; then
            pkill -f com.android.bluetooth >/dev/null 2>&1
            RESTARTED=true
        fi

        RES="{\"success\":true,\"bitrate\":\"$NEW_BR\",\"mtu\":\"$NEW_MTU\",\"max_queue\":\"$NEW_Q\",\"restarted\":$RESTARTED}"
        send_headers "200 OK" "application/json; charset=utf-8" "${#RES}"
        printf "%s" "$RES"
        ;;

    /api/set_anc)
        NEW_MODE=$(get_param "mode")
        if [ -n "$NEW_MODE" ]; then
            am broadcast -a com.music.bypass.ACTION_SET_ANC_MODE -p com.music.bypass --es extra_mode "$NEW_MODE" >/dev/null 2>&1
            AUTO=$(get_param "auto")
            if [ "$AUTO" = "1" ] || [ "$AUTO" = "true" ]; then
                if [ "$NEW_MODE" = "NORMAL" ]; then
                    $RESETPROP -n persist.bluetooth.lhdc_bitrate 900
                else
                    $RESETPROP -n persist.bluetooth.lhdc_bitrate 500
                fi
            fi
            RES="{\"success\":true,\"mode\":\"$NEW_MODE\"}"
        else
            RES='{"success":false,"error":"Missing mode parameter"}'
        fi
        send_headers "200 OK" "application/json; charset=utf-8" "${#RES}"
        printf "%s" "$RES"
        ;;

    /api/restart_bt)
        pkill -f com.android.bluetooth >/dev/null 2>&1
        RES='{"success":true,"message":"Bluetooth stack restarted"}'
        send_headers "200 OK" "application/json; charset=utf-8" "${#RES}"
        printf "%s" "$RES"
        ;;

    /api/logcat)
        LOGS=$(logcat -d -t 40 -s LHDC_V5_SHIM:V 2>/dev/null | tail -n 25 | tr -d '\r')
        send_headers "200 OK" "text/plain; charset=utf-8"
        printf "%s\n" "$LOGS"
        ;;

    /api/exec)
        CMD=$(get_param "cmd")
        if [ -n "$CMD" ]; then
            OUT=$(sh -c "$CMD" 2>&1)
            send_headers "200 OK" "text/plain; charset=utf-8"
            printf "%s\n" "$OUT"
        else
            send_headers "400 Bad Request" "text/plain; charset=utf-8" "11"
            printf "Missing cmd"
        fi
        ;;

    /|/index.html)
        TARGET_FILE="$WEBROOT/index.html"
        if [ -f "$TARGET_FILE" ]; then
            CLEN=$(wc -c < "$TARGET_FILE" | tr -d ' ')
            send_headers "200 OK" "text/html; charset=utf-8" "$CLEN"
            cat "$TARGET_FILE"
        else
            send_headers "404 Not Found" "text/plain" "14"
            printf "404 Not Found\n"
        fi
        ;;

    /style.css)
        TARGET_FILE="$WEBROOT/style.css"
        if [ -f "$TARGET_FILE" ]; then
            CLEN=$(wc -c < "$TARGET_FILE" | tr -d ' ')
            send_headers "200 OK" "text/css; charset=utf-8" "$CLEN"
            cat "$TARGET_FILE"
        else
            send_headers "404 Not Found" "text/plain" "14"
            printf "404 Not Found\n"
        fi
        ;;

    /app.js)
        TARGET_FILE="$WEBROOT/app.js"
        if [ -f "$TARGET_FILE" ]; then
            CLEN=$(wc -c < "$TARGET_FILE" | tr -d ' ')
            send_headers "200 OK" "application/javascript; charset=utf-8" "$CLEN"
            cat "$TARGET_FILE"
        else
            send_headers "404 Not Found" "text/plain" "14"
            printf "404 Not Found\n"
        fi
        ;;

    *)
        CLEAN_PATH=$(echo "$URI_PATH" | sed 's/\.\.//g')
        TARGET_FILE="$WEBROOT$CLEAN_PATH"
        if [ -f "$TARGET_FILE" ]; then
            MIME="application/octet-stream"
            case "$TARGET_FILE" in
                *.svg) MIME="image/svg+xml" ;;
                *.png) MIME="image/png" ;;
                *.ico) MIME="image/x-icon" ;;
                *.json) MIME="application/json" ;;
            esac
            CLEN=$(wc -c < "$TARGET_FILE" | tr -d ' ')
            send_headers "200 OK" "$MIME" "$CLEN"
            cat "$TARGET_FILE"
        else
            send_headers "404 Not Found" "text/plain" "14"
            printf "404 Not Found\n"
        fi
        ;;
esac

exit 0
