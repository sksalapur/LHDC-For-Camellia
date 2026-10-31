package com.lhdc.autoswitch;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothA2dp;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothProfile;
import android.bluetooth.BluetoothCodecConfig;
import android.bluetooth.BluetoothCodecStatus;
import android.os.Looper;
import android.os.Handler;
import java.lang.reflect.Method;
import java.lang.reflect.Constructor;
import java.util.List;

public class LhdcAutoSwitch {
    public static void main(String[] args) {
        System.out.println("=== LHDC AutoSwitch Starting ===");
        try {
            Looper.prepare();
            final Looper looper = Looper.myLooper();
            final Handler handler = new Handler(looper);

            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) {
                System.err.println("BluetoothAdapter is null!");
                return;
            }

            adapter.getProfileProxy(null, new BluetoothProfile.ServiceListener() {
                @Override
                public void onServiceConnected(int profile, BluetoothProfile proxy) {
                    if (profile == BluetoothProfile.A2DP) {
                        final BluetoothA2dp a2dp = (BluetoothA2dp) proxy;
                        System.out.println("A2DP proxy connected!");

                        handler.post(new Runnable() {
                            @Override
                            public void run() {
                                try {
                                    List<BluetoothDevice> devices = a2dp.getConnectedDevices();
                                    System.out.println("Connected A2DP devices: " + devices.size());

                                    for (BluetoothDevice dev : devices) {
                                        System.out.println("Device: " + dev.getName() + " [" + dev.getAddress() + "]");

                                        // Enable optional codecs first
                                        try {
                                            Method mOpt = BluetoothA2dp.class.getMethod("setOptionalCodecsEnabled", BluetoothDevice.class, int.class);
                                            mOpt.invoke(a2dp, dev, 1);
                                            System.out.println("setOptionalCodecsEnabled(1) called");
                                        } catch (Throwable t) {
                                            System.err.println("setOptionalCodecsEnabled error: " + t);
                                        }

                                        // Build LHDC V3 config (type=10, priority=1000000, 96kHz=4, 24bit=2, stereo=2)
                                        BluetoothCodecConfig lhdcConfig = null;
                                        try {
                                            Constructor<BluetoothCodecConfig> ctor = BluetoothCodecConfig.class.getConstructor(
                                                int.class, int.class, int.class, int.class, int.class,
                                                long.class, long.class, long.class, long.class
                                            );
                                            lhdcConfig = ctor.newInstance(10, 1000000, 4, 2, 2, 0L, 0L, 0L, 0L);
                                        } catch (Throwable t) {
                                            System.err.println("Constructor failed, trying Builder: " + t);
                                            BluetoothCodecConfig.Builder builder = new BluetoothCodecConfig.Builder()
                                                .setCodecType(10)
                                                .setCodecPriority(1000000)
                                                .setSampleRate(4)
                                                .setBitsPerSample(2)
                                                .setChannelMode(2);
                                            lhdcConfig = builder.build();
                                        }

                                        if (lhdcConfig != null) {
                                            Method mSet = BluetoothA2dp.class.getMethod("setCodecConfigPreference", BluetoothDevice.class, BluetoothCodecConfig.class);
                                            mSet.invoke(a2dp, dev, lhdcConfig);
                                            System.out.println("setCodecConfigPreference(LHDC_V3) called successfully!");
                                        }
                                    }
                                } catch (Throwable t) {
                                    t.printStackTrace();
                                } finally {
                                    handler.postDelayed(new Runnable() {
                                        @Override
                                        public void run() {
                                            looper.quit();
                                        }
                                    }, 1000);
                                }
                            }
                        });
                    }
                }

                @Override
                public void onServiceDisconnected(int profile) {}
            }, BluetoothProfile.A2DP);

            Looper.loop();
            System.out.println("=== LHDC AutoSwitch Complete ===");
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
