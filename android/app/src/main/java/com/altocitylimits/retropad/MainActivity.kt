package com.altocitylimits.retropad

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import org.webrtc.*
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    companion object {
        private const val REQ_CAPTURE = 9001
        private const val REQ_NEARBY = 9002
    }

    private lateinit var status: TextView
    private lateinit var detail: TextView
    private lateinit var castButton: Button

    private var host: String? = null
    private var port: Int = 8080
    private var room: String? = null

    private val http = OkHttpClient.Builder().readTimeout(0, TimeUnit.MILLISECONDS).build()
    private var socket: WebSocket? = null
    private var signalOpen = false
    private var displayReady = false

    private var egl: EglBase? = null
    private var factory: PeerConnectionFactory? = null
    private var peer: PeerConnection? = null
    private var capturer: ScreenCapturerAndroid? = null
    private var surfaceHelper: SurfaceTextureHelper? = null
    private var videoSource: VideoSource? = null
    private var videoTrack: VideoTrack? = null
    private var offerSent = false
    private var captureStarted = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        buildUi()
        handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    private fun buildUi() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(48, 72, 48, 48)
            setBackgroundColor(Color.rgb(13, 15, 19))
        }
        val title = TextView(this).apply {
            text = "RETROPAD"
            setTextColor(Color.WHITE)
            textSize = 30f
            gravity = Gravity.CENTER
        }
        status = TextView(this).apply {
            text = "Scan the QR code on a RetroPad Display."
            setTextColor(Color.WHITE)
            textSize = 22f
            gravity = Gravity.CENTER
            setPadding(0, 56, 0, 20)
        }
        detail = TextView(this).apply {
            text = "The first Android build streams your phone screen to the paired display."
            setTextColor(Color.rgb(170, 177, 190))
            textSize = 15f
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 40)
        }
        castButton = Button(this).apply {
            text = "Start Cast"
            isEnabled = false
            visibility = View.GONE
            setOnClickListener { requestCapture() }
        }
        root.addView(title, LinearLayout.LayoutParams(-1, -2))
        root.addView(status, LinearLayout.LayoutParams(-1, -2))
        root.addView(detail, LinearLayout.LayoutParams(-1, -2))
        root.addView(castButton, LinearLayout.LayoutParams(-1, -2))
        setContentView(root)
    }

    private fun handleIntent(intent: Intent) {
        val uri = intent.data ?: return
        if (uri.scheme != "retropad" || uri.host != "pair") return
        host = uri.getQueryParameter("host")
        port = uri.getQueryParameter("port")?.toIntOrNull() ?: 8080
        room = uri.getQueryParameter("room")?.uppercase()
        if (host.isNullOrBlank() || room.isNullOrBlank()) {
            status.text = "Invalid RetroPad pairing code"
            return
        }
        status.text = "Paired with ${host}:${port}"
        detail.text = "Room ${room}. Tap Start Cast, approve Android screen sharing, then open FullRoid."
        castButton.visibility = View.VISIBLE
        castButton.isEnabled = true
        ensureLanPermissionAndConnect()
    }

    private fun ensureLanPermissionAndConnect() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.NEARBY_WIFI_DEVICES) != PackageManager.PERMISSION_GRANTED) {
            status.text = "Allow nearby-device access"
            detail.text = "RetroPad needs local-network access to reach the display on your Wi-Fi."
            requestPermissions(arrayOf(Manifest.permission.NEARBY_WIFI_DEVICES), REQ_NEARBY)
            return
        }
        connectSignal()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQ_NEARBY) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                status.text = "Local network allowed"
                connectSignal()
            } else {
                status.text = "Nearby-device access is required"
                detail.text = "Allow Nearby devices for RetroPad, then scan the display QR again."
            }
        }
    }

    private fun connectSignal() {
        socket?.cancel()
        signalOpen = false
        displayReady = false
        val url = "ws://${host}:${port}/ws"
        val req = Request.Builder().url(url).build()
        socket = http.newWebSocket(req, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                signalOpen = true
                send(JSONObject().put("type", "join").put("role", "android").put("room", room).put("name", "RetroPad Android"))
                runOnUiThread { status.text = "Connected to RetroPad Display" }
                maybeOffer()
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                val m = runCatching { JSONObject(text) }.getOrNull() ?: return
                when (m.optString("type")) {
                    "status" -> {
                        displayReady = m.optInt("displays", 0) > 0
                        maybeOffer()
                    }
                    "answer" -> {
                        val s = m.optJSONObject("sdp") ?: return
                        val desc = SessionDescription(SessionDescription.Type.ANSWER, s.optString("sdp"))
                        peer?.setRemoteDescription(SimpleSdpObserver(), desc)
                        runOnUiThread { status.text = "Streaming to display" }
                    }
                    "ice" -> {
                        val c = m.optJSONObject("candidate") ?: return
                        peer?.addIceCandidate(IceCandidate(c.optString("sdpMid"), c.optInt("sdpMLineIndex"), c.optString("candidate")))
                    }
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                signalOpen = false
                runOnUiThread {
                    status.text = "Could not reach RetroPad Display"
                    detail.text = "${t.javaClass.simpleName}: ${t.message ?: "LAN connection failed"}"
                }
            }
        })
    }

    private fun send(json: JSONObject) { socket?.send(json.toString()) }

    private fun requestCapture() {
        val mgr = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        startActivityForResult(mgr.createScreenCaptureIntent(), REQ_CAPTURE)
    }

    @Deprecated("Deprecated in Android SDK; kept for broad device compatibility")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != REQ_CAPTURE) return
        if (resultCode != RESULT_OK || data == null) {
            status.text = "Screen sharing was not approved"
            return
        }
        startForegroundService(Intent(this, CaptureForegroundService::class.java))
        startWebRtcCapture(data)
    }

    private fun startWebRtcCapture(permissionData: Intent) {
        if (captureStarted) return
        captureStarted = true
        castButton.isEnabled = false
        castButton.text = "Casting"
        status.text = "Starting screen stream…"

        PeerConnectionFactory.initialize(
            PeerConnectionFactory.InitializationOptions.builder(applicationContext).createInitializationOptions()
        )
        egl = EglBase.create()
        factory = PeerConnectionFactory.builder()
            .setVideoEncoderFactory(DefaultVideoEncoderFactory(egl!!.eglBaseContext, true, true))
            .setVideoDecoderFactory(DefaultVideoDecoderFactory(egl!!.eglBaseContext))
            .createPeerConnectionFactory()

        val config = PeerConnection.RTCConfiguration(emptyList())
        config.sdpSemantics = PeerConnection.SdpSemantics.UNIFIED_PLAN
        peer = factory!!.createPeerConnection(config, peerObserver)

        videoSource = factory!!.createVideoSource(false)
        capturer = ScreenCapturerAndroid(permissionData, object : MediaProjection.Callback() {
            override fun onStop() {
                runOnUiThread {
                    status.text = "Casting stopped"
                    castButton.isEnabled = true
                    castButton.text = "Start Cast"
                }
                stopCapture()
            }
        })
        surfaceHelper = SurfaceTextureHelper.create("RetroPadCapture", egl!!.eglBaseContext)
        capturer!!.initialize(surfaceHelper, applicationContext, videoSource!!.capturerObserver)
        capturer!!.startCapture(1280, 720, 30)

        videoTrack = factory!!.createVideoTrack("RETROPAD_SCREEN", videoSource)
        peer!!.addTrack(videoTrack, listOf("retropad"))
        send(JSONObject().put("type", "stream-meta").put("label", "Android screen"))
        maybeOffer()
    }

    private fun maybeOffer() {
        if (!captureStarted || !signalOpen || !displayReady || offerSent || peer == null) return
        offerSent = true
        peer!!.createOffer(object : SimpleSdpObserver() {
            override fun onCreateSuccess(desc: SessionDescription) {
                peer?.setLocalDescription(SimpleSdpObserver(), desc)
                val sdp = JSONObject().put("type", "offer").put("sdp", desc.description)
                send(JSONObject().put("type", "offer").put("sdp", sdp))
            }
        }, MediaConstraints())
    }

    private val peerObserver = object : PeerConnection.Observer {
        override fun onSignalingChange(state: PeerConnection.SignalingState?) {}
        override fun onIceConnectionChange(state: PeerConnection.IceConnectionState?) {}
        override fun onStandardizedIceConnectionChange(newState: PeerConnection.IceConnectionState?) {}
        override fun onConnectionChange(newState: PeerConnection.PeerConnectionState?) {
            runOnUiThread {
                if (newState == PeerConnection.PeerConnectionState.CONNECTED) status.text = "Streaming to display"
                if (newState == PeerConnection.PeerConnectionState.FAILED) status.text = "Stream connection failed"
            }
        }
        override fun onIceConnectionReceivingChange(receiving: Boolean) {}
        override fun onIceGatheringChange(state: PeerConnection.IceGatheringState?) {}
        override fun onIceCandidate(candidate: IceCandidate?) {
            candidate ?: return
            val c = JSONObject()
                .put("candidate", candidate.sdp)
                .put("sdpMid", candidate.sdpMid)
                .put("sdpMLineIndex", candidate.sdpMLineIndex)
            send(JSONObject().put("type", "ice").put("candidate", c))
        }
        override fun onIceCandidatesRemoved(candidates: Array<out IceCandidate>?) {}
        override fun onAddStream(stream: MediaStream?) {}
        override fun onRemoveStream(stream: MediaStream?) {}
        override fun onDataChannel(channel: DataChannel?) {}
        override fun onRenegotiationNeeded() {}
        override fun onAddTrack(receiver: RtpReceiver?, mediaStreams: Array<out MediaStream>?) {}
        override fun onTrack(transceiver: RtpTransceiver?) {}
    }

    private fun stopCapture() {
        runCatching { capturer?.stopCapture() }
        runCatching { capturer?.dispose() }
        runCatching { surfaceHelper?.dispose() }
        runCatching { videoSource?.dispose() }
        runCatching { peer?.close() }
        runCatching { factory?.dispose() }
        runCatching { egl?.release() }
        capturer = null; surfaceHelper = null; videoSource = null; videoTrack = null
        peer = null; factory = null; egl = null
        captureStarted = false; offerSent = false
        stopService(Intent(this, CaptureForegroundService::class.java))
    }

    override fun onDestroy() {
        stopCapture()
        socket?.close(1000, "bye")
        http.dispatcher.executorService.shutdown()
        super.onDestroy()
    }

    open class SimpleSdpObserver : SdpObserver {
        override fun onCreateSuccess(desc: SessionDescription) {}
        override fun onSetSuccess() {}
        override fun onCreateFailure(error: String?) {}
        override fun onSetFailure(error: String?) {}
    }
}
