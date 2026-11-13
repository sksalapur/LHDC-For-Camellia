#!/system/bin/sh
# LHDC Codec For Camellia — Ultra-lightweight WebUI & Launcher Telemetry Daemon (Port 9092)
# Uses pure shell builtins + cached encoder state file (zero dumpsys, zero logcat, zero audio cracks).

SCRIPT_DIR="${0%/*}"
case "$SCRIPT_DIR" in
    /*) ;;
    *) SCRIPT_DIR="$PWD/$SCRIPT_DIR" ;;
esac
MODDIR="${SCRIPT_DIR%/*}"
WEBROOT="$MODDIR/webroot"
LIVE_FILE="/data/misc/bluetooth/lhdc_live.json"
TARGET_FILE_BR="$MODDIR/target_bitrate"
TARGET_FILE_ABR="$MODDIR/target_abr"

RESETPROP="/data/adb/ap/bin/resetprop"
[ -x "$RESETPROP" ] || RESETPROP="/data/adb/apd resetprop"
[ -x /data/adb/ap/bin/resetprop ] || [ -x /data/adb/apd ] || RESETPROP="/data/adb/magisk/resetprop"
[ -x /data/adb/ap/bin/resetprop ] || [ -x /data/adb/apd ] || [ -x /data/adb/magisk/resetprop ] || RESETPROP="resetprop"

CR=$'\r'

IFS= read -r REQUEST_LINE || exit 0
REQUEST_LINE="${REQUEST_LINE%$CR}"
[ -z "$REQUEST_LINE" ] && exit 0

set -- $REQUEST_LINE
METHOD="$1"
FULL_URI="$2"

CONTENT_LENGTH=0
while IFS= read -r HEADER; do
    HEADER="${HEADER%$CR}"
    [ -z "$HEADER" ] && break
    case "$HEADER" in
        [Cc][Oo][Nn][Tt][Ee][Nn][Tt]-[Ll][Ee][Nn][Gg][Tt][Hh]:*)
            CL="${HEADER#*:}"
            while [ "${CL# }" != "$CL" ]; do CL="${CL# }"; done
            CONTENT_LENGTH="$CL"
            ;;
    esac
done

BODY=""
if [ "$METHOD" = "POST" ] && [ -n "$CONTENT_LENGTH" ] && [ "$CONTENT_LENGTH" -gt 0 ] 2>/dev/null; then
    BODY=$(head -c "$CONTENT_LENGTH" 2>/dev/null)
    BODY="${BODY%$CR}"
fi

URI_PATH="${FULL_URI%%\?*}"
case "$FULL_URI" in
    *\?*) QUERY_STRING="${FULL_URI#*\?}" ;;
    *) QUERY_STRING="" ;;
esac
[ -z "$QUERY_STRING" ] && [ -n "$BODY" ] && QUERY_STRING="$BODY"

get_param() {
    KEY="$1"
    OLD_IFS="$IFS"
    IFS='&'
    for PAIR in $QUERY_STRING; do
        case "$PAIR" in
            "${KEY}="*)
                IFS="$OLD_IFS"
                print -rn -- "${PAIR#*=}"
                return 0
                ;;
        esac
    done
    IFS="$OLD_IFS"
}

send_headers() {
    STATUS_CODE="${1:-200 OK}"
    CONTENT_TYPE="${2:-application/json; charset=utf-8}"
    CLENGTH="$3"

    HDR="HTTP/1.1 ${STATUS_CODE}${CR}
Content-Type: ${CONTENT_TYPE}${CR}
Connection: close${CR}
Cache-Control: no-store, no-cache, must-revalidate${CR}
Access-Control-Allow-Origin: *${CR}
Access-Control-Allow-Methods: GET, POST, OPTIONS${CR}
Access-Control-Allow-Headers: Content-Type${CR}"
    if [ -n "$CLENGTH" ]; then
        HDR="${HDR}
Content-Length: ${CLENGTH}${CR}"
    fi
    print -rn -- "${HDR}
${CR}
"
}

if [ "$METHOD" = "OPTIONS" ]; then
    send_headers "200 OK" "text/plain" "0"
    exit 0
fi

read_cfg_br() {
    CFG_BR=""
    if [ -r "$TARGET_FILE_BR" ]; then
        IFS= read -r CFG_BR < "$TARGET_FILE_BR" 2>/dev/null || CFG_BR=""
        CFG_BR="${CFG_BR%%[^0-9]*}"
    fi
    if [ -z "$CFG_BR" ]; then
        CFG_BR=$(getprop persist.bluetooth.lhdc_bitrate 2>/dev/null)
    fi
    case "$CFG_BR" in ''|*[!0-9]*) CFG_BR=500 ;; esac
}

read_cfg_abr() {
    RAW_A=""
    if [ -r "$TARGET_FILE_ABR" ]; then
        IFS= read -r RAW_A < "$TARGET_FILE_ABR" 2>/dev/null || RAW_A=""
    else
        RAW_A=$(getprop persist.vendor.bluetooth.lhdc_abr 2>/dev/null)
        [ -z "$RAW_A" ] && RAW_A=$(getprop vendor.bluetooth.lhdc.abr 2>/dev/null)
    fi
    case "$RAW_A" in
        false|0|off|FALSE) CFG_ABR="false" ;;
        *) CFG_ABR="true" ;;
    esac
}

normalize_bool() {
    case "$1" in
        true|1|on|yes|TRUE) print -rn -- "true" ;;
        false|0|off|no|FALSE) print -rn -- "false" ;;
        *) print -rn -- "" ;;
    esac
}

build_live_json() {
    read_cfg_br
    CFG_MTU=660
    read_cfg_abr

    LIVE_RAW=""
    if [ -r "$LIVE_FILE" ]; then
        IFS= read -r LIVE_RAW < "$LIVE_FILE"
    fi

    case "$LIVE_RAW" in
        \{*\"negotiated_bitrate_kbps\"*\})
            # Extract lightweight fields via pure shell parameter expansion (0 forks)
            TMP="${LIVE_RAW#*\"active\":}"
            IS_ACTIVE="${TMP%%,*}"

            TMP="${LIVE_RAW#*\"negotiated_bitrate_kbps\":}"
            NEG_BR="${TMP%%,*}"
            case "$NEG_BR" in ''|*[!0-9]*) NEG_BR=0 ;; esac

            TMP="${LIVE_RAW#*\"negotiated_mtu\":}"
            NEG_MTU="${TMP%%,*}"
            case "$NEG_MTU" in ''|*[!0-9]*) NEG_MTU="$CFG_MTU" ;; esac

            if [ "$IS_ACTIVE" = "true" ] && [ "$NEG_BR" -gt 0 ] 2>/dev/null; then
                DISP_BR="$NEG_BR"
                DISP_MTU="$NEG_MTU"
            else
                DISP_BR="$CFG_BR"
                DISP_MTU="$CFG_MTU"
            fi

            TRIMMED="${LIVE_RAW%\}}"
            JSON="${TRIMMED},\"configured_bitrate_kbps\":${CFG_BR},\"configured_mtu\":${CFG_MTU},\"configured_abr_enabled\":${CFG_ABR},\"bitrate\":\"${DISP_BR} kbps\",\"bitrate_kbps\":${DISP_BR},\"mtu\":${DISP_MTU}}"
            ;;
        *)
            JSON="{\"active\":false,\"codec\":\"LHDC V5\",\"negotiated_bitrate_kbps\":0,\"target_bitrate_kbps\":${CFG_BR},\"negotiated_mtu\":${CFG_MTU},\"sample_rate\":48000,\"bits_per_sample\":24,\"bitrate_idx\":0,\"target_idx\":0,\"abr_enabled\":${CFG_ABR},\"abr_stepped_down\":false,\"queue_len\":0,\"updated_at\":0,\"configured_bitrate_kbps\":${CFG_BR},\"configured_mtu\":${CFG_MTU},\"configured_abr_enabled\":${CFG_ABR},\"bitrate\":\"${CFG_BR} kbps\",\"bitrate_kbps\":${CFG_BR},\"mtu\":${CFG_MTU}}"
            ;;
    esac
}

case "$URI_PATH" in
    /api/live|/api/status|/api/telemetry)
        build_live_json
        send_headers "200 OK" "application/json; charset=utf-8" "${#JSON}"
        print -rn -- "$JSON"
        ;;

    /api/set|/api/apply|/api/abr)
        NEW_BR=$(get_param "bitrate")
        RAW_ABR=$(get_param "enabled")
        [ -z "$RAW_ABR" ] && RAW_ABR=$(get_param "abr")

        if [ -z "$NEW_BR" ] && [ -z "$RAW_ABR" ]; then
            RES='{"success":false,"error":"Missing bitrate or abr parameter"}'
            send_headers "400 Bad Request" "application/json; charset=utf-8" "${#RES}"
            print -rn -- "$RES"
            exit 0
        fi

        if [ -n "$NEW_BR" ]; then
            case "$NEW_BR" in
                500|900|1000) ;;
                *)
                    RES='{"success":false,"error":"Unsupported bitrate (allowed: 500, 900, 1000)"}'
                    send_headers "400 Bad Request" "application/json; charset=utf-8" "${#RES}"
                    print -rn -- "$RES"
                    exit 0
                    ;;
            esac
        fi

        NEW_ABR=""
        if [ -n "$RAW_ABR" ]; then
            NEW_ABR=$(normalize_bool "$RAW_ABR")
            if [ -z "$NEW_ABR" ]; then
                RES='{"success":false,"error":"Unsupported abr value (allowed: true, false)"}'
                send_headers "400 Bad Request" "application/json; charset=utf-8" "${#RES}"
                print -rn -- "$RES"
                exit 0
            fi
        fi

        if [ -n "$NEW_BR" ]; then
            $RESETPROP -n persist.bluetooth.lhdc_bitrate "$NEW_BR" 2>/dev/null
            $RESETPROP persist.bluetooth.lhdc_bitrate "$NEW_BR" 2>/dev/null
            $RESETPROP -n persist.bluetooth.lhdc_mtu 660 2>/dev/null
            $RESETPROP persist.bluetooth.lhdc_mtu 660 2>/dev/null
            print -r -- "$NEW_BR" > "$TARGET_FILE_BR" 2>/dev/null
        fi

        if [ -n "$NEW_ABR" ]; then
            $RESETPROP -n persist.vendor.bluetooth.lhdc_abr "$NEW_ABR" 2>/dev/null
            $RESETPROP persist.vendor.bluetooth.lhdc_abr "$NEW_ABR" 2>/dev/null
            $RESETPROP -n vendor.bluetooth.lhdc.abr "$NEW_ABR" 2>/dev/null
            $RESETPROP vendor.bluetooth.lhdc.abr "$NEW_ABR" 2>/dev/null
            print -r -- "$NEW_ABR" > "$TARGET_FILE_ABR" 2>/dev/null
        fi

        read_cfg_br
        read_cfg_abr

        RES="{\"success\":true,\"bitrate_kbps\":${CFG_BR},\"mtu\":660,\"abr_enabled\":${CFG_ABR},\"restarted\":false}"
        send_headers "200 OK" "application/json; charset=utf-8" "${#RES}"
        print -rn -- "$RES"
        ;;

    /api/restart_bt)
        cmd bluetooth_manager disable >/dev/null 2>&1
        sleep 1
        cmd bluetooth_manager enable >/dev/null 2>&1
        RES='{"success":true,"restarted":true}'
        send_headers "200 OK" "application/json; charset=utf-8" "${#RES}"
        print -rn -- "$RES"
        ;;

    /|/index.html)
        F="$WEBROOT/index.html"
        if [ -r "$F" ]; then
            CLEN=$(wc -c < "$F" | tr -d ' ')
            send_headers "200 OK" "text/html; charset=utf-8" "$CLEN"
            cat "$F"
        else
            send_headers "404 Not Found" "text/plain" "10"
            print -rn -- "Not Found
"
        fi
        ;;

    /style.css)
        F="$WEBROOT/style.css"
        if [ -r "$F" ]; then
            CLEN=$(wc -c < "$F" | tr -d ' ')
            send_headers "200 OK" "text/css; charset=utf-8" "$CLEN"
            cat "$F"
        else
            send_headers "404 Not Found" "text/plain" "10"
            print -rn -- "Not Found
"
        fi
        ;;

    /app.js)
        F="$WEBROOT/app.js"
        if [ -r "$F" ]; then
            CLEN=$(wc -c < "$F" | tr -d ' ')
            send_headers "200 OK" "application/javascript; charset=utf-8" "$CLEN"
            cat "$F"
        else
            send_headers "404 Not Found" "text/plain" "10"
            print -rn -- "Not Found
"
        fi
        ;;

    *)
        RES='{"error":"Not Found"}'
        send_headers "404 Not Found" "application/json; charset=utf-8" "${#RES}"
        print -rn -- "$RES"
        ;;
esac

exit 0
