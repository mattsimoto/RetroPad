plugins {
    id("com.android.application")
    kotlin("android")
}

android {
    namespace = "com.altocitylimits.retropad"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.altocitylimits.retropad"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "0.4.0-alpha1"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("io.github.webrtc-sdk:android:150.7871.01")
}
