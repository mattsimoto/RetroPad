package com.altocitylimits.retropad

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder

class CaptureForegroundService : Service() {
    companion object {
        const val CHANNEL_ID = "retropad_capture"
        const val NOTIFICATION_ID = 41
    }

    override fun onCreate() {
        super.onCreate()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "RetroPad game casting",
                NotificationManager.IMPORTANCE_LOW
            )
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("RetroPad is casting")
                .setContentText("Your phone screen is being sent to the paired display.")
                .setSmallIcon(android.R.drawable.presence_video_online)
                .setOngoing(true)
                .build()
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
                .setContentTitle("RetroPad is casting")
                .setContentText("Your phone screen is being sent to the paired display.")
                .setSmallIcon(android.R.drawable.presence_video_online)
                .setOngoing(true)
                .build()
        }
        startForeground(NOTIFICATION_ID, notification)
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
