SKIPUNZIP=0

ui_print "- Installing LHDC & LHDC V5 Codec Libraries..."
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/lib64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/lib" 0 0 0755 0644

ui_print "- Preparing APEX overlay directory..."
APEX_LIB64="$MODPATH/apex_lib64"
mkdir -p "$APEX_LIB64"
cp -a /apex/com.android.btservices/lib64/* "$APEX_LIB64/" 2>/dev/null || true
cp -f "$MODPATH/system/lib64/liblhdcBT_enc.so" "$APEX_LIB64/liblhdcBT_enc.so"
cp -f "$MODPATH/work/libbluetooth_jni.so" "$APEX_LIB64/libbluetooth_jni.so"
cp -f "$MODPATH/system/lib64/liblhdcv5BT_enc.so" "$APEX_LIB64/liblhdcv5BT_enc.so"
cp -f "$MODPATH/system/lib64/liblhdcv5.so" "$APEX_LIB64/liblhdcv5.so"
set_perm_recursive "$APEX_LIB64" 0 0 0755 0644

ui_print "- LHDC V5 enabler installed successfully!"
