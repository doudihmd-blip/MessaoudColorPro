package com.messaoud.colorpro

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.webViewClient = WebViewClient()
        // تحميل واجهة التطبيق المحلية المدمجة داخل الـ Assets
        webView.loadUrl("file:///android_asset/index.html")
        setContentView(webView)
    }
}
