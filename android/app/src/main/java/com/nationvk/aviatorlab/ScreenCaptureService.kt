package com.nationvk.aviatorlab

import android.app.*
import android.content.Intent
import android.graphics.Bitmap
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.*
import android.util.DisplayMetrics
import android.view.WindowManager
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import java.util.concurrent.atomic.AtomicBoolean
import java.util.regex.Pattern

class ScreenCaptureService : Service() {
    companion object {
        const val ACTION_MULTIPLIER = "com.nationvk.aviatorlab.MULTIPLIER"
        const val EXTRA_MULTIPLIER = "multiplier"
        const val EXTRA_RESULT_CODE = "result_code"
        const val EXTRA_RESULT_DATA = "result_data"
        private const val CHANNEL = "aviator_capture"
    }
    private var projection: MediaProjection? = null
    private var reader: ImageReader? = null
    private var display: VirtualDisplay? = null
    private val handler = Handler(Looper.getMainLooper())
    private val recognizer by lazy { TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS) }
    private val busy = AtomicBoolean(false)
    private var lastValue = ""
    private var pendingValue = ""
    private var pendingCount = 0
    private var lastScan = 0L

    override fun onBind(intent: Intent?) = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent == null) { stopSelf(); return START_NOT_STICKY }
        val code = intent.getIntExtra(EXTRA_RESULT_CODE, Activity.RESULT_CANCELED)
        val data: Intent? = if (Build.VERSION.SDK_INT >= 33) intent.getParcelableExtra(EXTRA_RESULT_DATA, Intent::class.java) else legacyResultData(intent)
        if (code != Activity.RESULT_OK || data == null) { stopSelf(); return START_NOT_STICKY }
        createNotification()
        startProjection(code, data)
        return START_NOT_STICKY
    }

    @Suppress("DEPRECATION")
    private fun legacyResultData(intent: Intent): Intent? = intent.getParcelableExtra(EXTRA_RESULT_DATA)

    private fun createNotification() {
        val manager = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) manager.createNotificationChannel(NotificationChannel(CHANNEL, "Research screen capture", NotificationManager.IMPORTANCE_LOW))
        val builder = if (Build.VERSION.SDK_INT >= 26) Notification.Builder(this, CHANNEL) else Notification.Builder(this).setPriority(Notification.PRIORITY_LOW)
        val notification = builder
            .setContentTitle("Aviator Research Lab")
            .setContentText("Screen OCR is active. Tap Stop in the app to end capture.")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .setOngoing(true).build()
        if (Build.VERSION.SDK_INT >= 29) startForeground(7, notification, android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        else startForeground(7, notification)
    }

    private fun startProjection(code: Int, data: Intent) {
        val manager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        projection = manager.getMediaProjection(code, data)
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        (getSystemService(WINDOW_SERVICE) as WindowManager).defaultDisplay.getRealMetrics(metrics)
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi
        reader = ImageReader.newInstance(width, height, android.graphics.PixelFormat.RGBA_8888, 2)
        projection?.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() { stopSelf() }
        }, handler)
        display = projection?.createVirtualDisplay("AviatorResearchCapture", width, height, density, DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR, reader?.surface, null, handler)
        reader?.setOnImageAvailableListener({ source ->
            val now = SystemClock.elapsedRealtime()
            if (now - lastScan < 900 || !busy.compareAndSet(false, true)) {
                source.acquireLatestImage()?.close()
            } else {
                lastScan = now
                val image = source.acquireLatestImage()
                if (image == null) busy.set(false) else processImage(image)
            }
        }, handler)
    }

    private fun processImage(image: Image) {
        try {
            val plane = image.planes[0]
            val buffer = plane.buffer
            val pixelStride = plane.pixelStride
            val rowStride = plane.rowStride
            val paddedWidth = rowStride / pixelStride
            val full = Bitmap.createBitmap(paddedWidth, image.height, Bitmap.Config.ARGB_8888)
            full.copyPixelsFromBuffer(buffer)
            val bitmap = Bitmap.createBitmap(full, 0, 0, image.width, image.height)
            full.recycle()
            image.close()
            recognizer.process(InputImage.fromBitmap(bitmap, 0))
                .addOnSuccessListener { result ->
                    // Prefer a large, central multiplier line over small historical values.
                    val pattern = Pattern.compile("(?i)([0-9]{1,6}(?:[.,][0-9]{1,4})?)\\s*[x×]")
                    var candidate: String? = null
                    var bestScore = -1f
                    for (block in result.textBlocks) {
                        for (line in block.lines) {
                            val matcher = pattern.matcher(line.text)
                            if (!matcher.find()) continue
                            val raw = matcher.group(1)?.replace(',', '.') ?: continue
                            val bounds = line.boundingBox
                            val height = (bounds?.height() ?: 0).toFloat()
                            val centerPenalty = if (bounds == null) 1f else {
                                val dx = kotlin.math.abs(bounds.centerX() - image.width / 2f) / (image.width / 2f)
                                val dy = kotlin.math.abs(bounds.centerY() - image.height / 2f) / (image.height / 2f)
                                1f - (0.35f * dx + 0.25f * dy).coerceAtMost(0.6f)
                            }
                            val score = height * centerPenalty
                            if (score > bestScore) { bestScore = score; candidate = raw }
                        }
                    }
                    val value = candidate?.toFloatOrNull()
                    if (candidate != null && value != null && value >= 1f) {
                        if (candidate == pendingValue) pendingCount++ else {
                            pendingValue = candidate
                            pendingCount = 1
                        }
                        // Require two consecutive OCR frames to reduce transient misreads.
                        if (pendingCount >= 2 && candidate != lastValue) {
                            lastValue = candidate
                            sendBroadcast(Intent(ACTION_MULTIPLIER).setPackage(packageName).putExtra(EXTRA_MULTIPLIER, value))
                        }
                    } else {
                        pendingValue = ""
                        pendingCount = 0
                    }
                }
                .addOnCompleteListener { bitmap.recycle(); busy.set(false) }
        } catch (_: Exception) {
            try { image.close() } catch (_: Exception) {}
            busy.set(false)
        }
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        display?.release()
        reader?.close()
        projection?.stop()
        try { recognizer.close() } catch (_: Exception) {}
        stopForeground(STOP_FOREGROUND_REMOVE)
        super.onDestroy()
    }
}
