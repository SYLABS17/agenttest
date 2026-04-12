/**
 * Android Client SDK for Liveness Detection Pipeline
 *
 * Integrates with the Azure-based liveness detection pipeline.
 * Uses Azure AI Vision Face SDK for client-side liveness detection.
 *
 * Prerequisites:
 * - Azure AI Vision Face SDK
 * - Kotlin Coroutines
 * - OkHttp / Retrofit (recommended)
 * - Minimum API Level 24
 */

package com.liveness.pipeline.client

import android.graphics.Bitmap
import android.provider.Settings
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import kotlinx.serialization.json.Json
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit

// MARK: - Models

/**
 * Pipeline session response from the server
 */
@Serializable
data class PipelineSession(
    @SerialName("session_id") val sessionId: String,
    @SerialName("status") val status: String,
    @SerialName("token") val token: String,
    @SerialName("token_expires_at") val tokenExpiresAt: String,
    @SerialName("liveness_result") val livenessResult: String? = null,
    @SerialName("liveness_confidence") val livenessConfidence: Double? = null,
    @SerialName("applicant_id") val applicantId: String? = null,
    @SerialName("error") val error: String? = null
)

/**
 * Azure liveness session for SDK integration
 */
@Serializable
data class AzureLivenessSession(
    @SerialName("azure_session_id") val azureSessionId: String,
    @SerialName("auth_token") val authToken: String,
    @SerialName("pipeline_session_id") val pipelineSessionId: String,
    @SerialName("pipeline_token") val pipelineToken: String
)

/**
 * Applicant data for submission
 */
@Serializable
data class ApplicantData(
    @SerialName("first_name") val firstName: String? = null,
    @SerialName("last_name") val lastName: String? = null,
    @SerialName("email") val email: String? = null,
    @SerialName("phone") val phone: String? = null,
    @SerialName("date_of_birth") val dateOfBirth: String? = null,
    @SerialName("address") val address: String? = null,
    @SerialName("custom_fields") val customFields: Map<String, String>? = null
)

/**
 * Session creation request
 */
@Serializable
data class CreateSessionRequest(
    @SerialName("client_id") val clientId: String,
    @SerialName("applicant_data") val applicantData: ApplicantData,
    @SerialName("callback_url") val callbackUrl: String? = null,
    @SerialName("metadata") val metadata: Map<String, String>? = null
)

/**
 * Liveness detection result
 */
enum class LivenessResult(val value: String) {
    LIVE("live"),
    SPOOF("spoof"),
    UNCERTAIN("uncertain"),
    UNKNOWN("unknown");

    companion object {
        fun fromString(value: String?): LivenessResult {
            return when (value?.lowercase()) {
                "live" -> LIVE
                "spoof" -> SPOOF
                "uncertain" -> UNCERTAIN
                else -> UNKNOWN
            }
        }
    }
}

/**
 * Pipeline completion result
 */
data class PipelineResult(
    val sessionId: String,
    val livenessResult: LivenessResult,
    val livenessConfidence: Double,
    val applicantId: String?,
    val isSuccess: Boolean,
    val error: String?
)

// MARK: - Errors

/**
 * Errors that can occur during liveness detection
 */
sealed class LivenessClientException(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class InvalidConfiguration(message: String = "Invalid client configuration") : LivenessClientException(message)
    class NetworkError(cause: Throwable) : LivenessClientException("Network error: ${cause.message}", cause)
    class InvalidResponse(message: String = "Invalid server response") : LivenessClientException(message)
    class SessionExpired(message: String = "Session has expired") : LivenessClientException(message)
    class LivenessCheckFailed(reason: String) : LivenessClientException("Liveness check failed: $reason")
    class ServerError(message: String) : LivenessClientException("Server error: $message")
}

// MARK: - Client Configuration

/**
 * Configuration for the liveness client
 */
data class LivenessClientConfig(
    val baseUrl: String,
    val clientId: String,
    val functionKey: String? = null,
    val timeoutSeconds: Long = 30
)

// MARK: - Liveness Client

/**
 * Main client for interacting with the liveness detection pipeline
 *
 * Example usage:
 * ```kotlin
 * val client = LivenessClient(LivenessClientConfig(
 *     baseUrl = "https://your-function-app.azurewebsites.net",
 *     clientId = "your-client-id",
 *     functionKey = "your-function-key"
 * ))
 *
 * // Complete flow
 * val result = client.performLivenessCheck(
 *     applicantData = ApplicantData(
 *         firstName = "John",
 *         lastName = "Doe",
 *         email = "john@example.com"
 *     ),
 *     image = capturedBitmap
 * )
 *
 * if (result.isSuccess) {
 *     println("Applicant verified! ID: ${result.applicantId}")
 * }
 * ```
 */
class LivenessClient(private val config: LivenessClientConfig) {

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    /**
     * Current active session
     */
    var currentSession: PipelineSession? = null
        private set

    // MARK: - Session Management

    /**
     * Start a new liveness detection session
     */
    suspend fun startSession(
        applicantData: ApplicantData,
        callbackUrl: String? = null,
        metadata: Map<String, String>? = null
    ): PipelineSession = withContext(Dispatchers.IO) {
        val request = CreateSessionRequest(
            clientId = config.clientId,
            applicantData = applicantData,
            callbackUrl = callbackUrl,
            metadata = metadata
        )

        val session = post<PipelineSession>(
            path = "/api/sessions",
            body = json.encodeToString(request)
        )

        currentSession = session
        session
    }

    /**
     * Create Azure liveness session for SDK integration
     */
    suspend fun createLivenessSession(
        deviceCorrelationId: String? = null
    ): AzureLivenessSession = withContext(Dispatchers.IO) {
        val session = currentSession ?: throw LivenessClientException.InvalidConfiguration()

        val body = deviceCorrelationId?.let {
            json.encodeToString(mapOf("device_correlation_id" to it))
        } ?: "{}"

        post(
            path = "/api/sessions/${session.sessionId}/liveness",
            body = body,
            token = session.token
        )
    }

    /**
     * Complete the liveness flow after Azure SDK finishes
     */
    suspend fun completeLiveness(
        azureSessionId: String
    ): PipelineSession = withContext(Dispatchers.IO) {
        val session = currentSession ?: throw LivenessClientException.InvalidConfiguration()

        val body = json.encodeToString(mapOf("azure_session_id" to azureSessionId))

        val result = post<PipelineSession>(
            path = "/api/sessions/${session.sessionId}/complete",
            body = body,
            token = session.token
        )

        currentSession = result
        result
    }

    /**
     * Submit image for server-side liveness detection
     */
    suspend fun submitImage(image: Bitmap): PipelineSession = withContext(Dispatchers.IO) {
        val session = currentSession ?: throw LivenessClientException.InvalidConfiguration()

        val stream = ByteArrayOutputStream()
        image.compress(Bitmap.CompressFormat.JPEG, 90, stream)
        val imageData = stream.toByteArray()

        val result = postImage(
            path = "/api/sessions/${session.sessionId}/image",
            imageData = imageData,
            token = session.token
        )

        currentSession = result
        result
    }

    /**
     * Get current session status
     */
    suspend fun getSessionStatus(): PipelineSession = withContext(Dispatchers.IO) {
        val session = currentSession ?: throw LivenessClientException.InvalidConfiguration()

        val result = get<PipelineSession>(
            path = "/api/sessions/${session.sessionId}",
            token = session.token
        )

        currentSession = result
        result
    }

    /**
     * Cancel the current session
     */
    suspend fun cancelSession(): Unit = withContext(Dispatchers.IO) {
        val session = currentSession ?: return@withContext

        delete(
            path = "/api/sessions/${session.sessionId}",
            token = session.token
        )

        currentSession = null
    }

    // MARK: - Complete Flow Helper

    /**
     * Execute the complete liveness detection flow
     */
    suspend fun performLivenessCheck(
        applicantData: ApplicantData,
        image: Bitmap
    ): PipelineResult = withContext(Dispatchers.IO) {
        // Step 1: Start session
        startSession(applicantData)

        // Step 2: Submit image for liveness detection
        val result = submitImage(image)

        // Step 3: Build result
        val livenessResult = LivenessResult.fromString(result.livenessResult)

        PipelineResult(
            sessionId = result.sessionId,
            livenessResult = livenessResult,
            livenessConfidence = result.livenessConfidence ?: 0.0,
            applicantId = result.applicantId,
            isSuccess = livenessResult == LivenessResult.LIVE && result.applicantId != null,
            error = result.error
        )
    }

    // MARK: - Network Helpers

    private fun buildUrl(path: String): URL {
        val baseUrl = config.baseUrl.trimEnd('/')
        return URL(baseUrl + path)
    }

    private fun setupConnection(
        url: URL,
        method: String,
        token: String? = null
    ): HttpURLConnection {
        val connection = url.openConnection() as HttpURLConnection
        connection.requestMethod = method
        connection.connectTimeout = TimeUnit.SECONDS.toMillis(config.timeoutSeconds).toInt()
        connection.readTimeout = TimeUnit.SECONDS.toMillis(config.timeoutSeconds).toInt()

        config.functionKey?.let {
            connection.setRequestProperty("x-functions-key", it)
        }

        token?.let {
            connection.setRequestProperty("Authorization", "Bearer $it")
        }

        return connection
    }

    private inline fun <reified T> get(
        path: String,
        token: String? = null
    ): T {
        val url = buildUrl(path)
        val connection = setupConnection(url, "GET", token)

        return executeRequest(connection)
    }

    private inline fun <reified T> post(
        path: String,
        body: String,
        token: String? = null
    ): T {
        val url = buildUrl(path)
        val connection = setupConnection(url, "POST", token)
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json")

        connection.outputStream.use { outputStream ->
            outputStream.write(body.toByteArray(Charsets.UTF_8))
        }

        return executeRequest(connection)
    }

    private fun postImage(
        path: String,
        imageData: ByteArray,
        token: String? = null
    ): PipelineSession {
        val url = buildUrl(path)
        val connection = setupConnection(url, "POST", token)
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "image/jpeg")

        connection.outputStream.use { outputStream ->
            outputStream.write(imageData)
        }

        return executeRequest(connection)
    }

    private fun delete(
        path: String,
        token: String? = null
    ) {
        val url = buildUrl(path)
        val connection = setupConnection(url, "DELETE", token)

        try {
            val responseCode = connection.responseCode

            if (responseCode >= 400 && responseCode != 404) {
                throw LivenessClientException.ServerError("HTTP $responseCode")
            }
        } catch (e: LivenessClientException) {
            throw e
        } catch (e: Exception) {
            throw LivenessClientException.NetworkError(e)
        } finally {
            connection.disconnect()
        }
    }

    private inline fun <reified T> executeRequest(connection: HttpURLConnection): T {
        try {
            val responseCode = connection.responseCode

            if (responseCode == 401) {
                throw LivenessClientException.SessionExpired()
            }

            val responseBody = if (responseCode >= 400) {
                connection.errorStream?.bufferedReader()?.readText() ?: ""
            } else {
                connection.inputStream.bufferedReader().readText()
            }

            if (responseCode >= 400) {
                val errorMessage = try {
                    val errorMap = json.decodeFromString<Map<String, String>>(responseBody)
                    errorMap["error"] ?: "HTTP $responseCode"
                } catch (e: Exception) {
                    "HTTP $responseCode"
                }
                throw LivenessClientException.ServerError(errorMessage)
            }

            return json.decodeFromString(responseBody)
        } catch (e: LivenessClientException) {
            throw e
        } catch (e: IOException) {
            throw LivenessClientException.NetworkError(e)
        } catch (e: Exception) {
            throw LivenessClientException.InvalidResponse("Failed to parse response: ${e.message}")
        } finally {
            connection.disconnect()
        }
    }
}

// MARK: - Azure SDK Integration

/**
 * Extension for Azure Face SDK integration
 *
 * Example usage with Azure Face SDK:
 * ```kotlin
 * val client = LivenessClient(config)
 *
 * // Start session
 * val session = client.startSession(applicantData)
 *
 * // Get Azure liveness session
 * val azureSession = client.createLivenessSession(
 *     deviceCorrelationId = Settings.Secure.getString(
 *         context.contentResolver,
 *         Settings.Secure.ANDROID_ID
 *     )
 * )
 *
 * // Initialize Azure Face SDK with the auth token
 * // val faceAnalyzer = FaceAnalyzerBuilder()
 * //     .setSessionAuthToken(azureSession.authToken)
 * //     .build()
 *
 * // Present liveness check UI and get result
 * // ... Azure SDK liveness check ...
 *
 * // Complete the flow
 * val result = client.completeLiveness(azureSession.azureSessionId)
 *
 * if (result.livenessResult == "live") {
 *     println("Applicant verified! ID: ${result.applicantId}")
 * }
 * ```
 */
suspend fun LivenessClient.performAzureLivenessCheck(
    applicantData: ApplicantData,
    deviceId: String
): PipelineResult = withContext(Dispatchers.IO) {
    // Step 1: Start pipeline session
    startSession(applicantData)

    // Step 2: Create Azure liveness session
    val azureSession = createLivenessSession(deviceCorrelationId = deviceId)

    // Step 3: Run Azure Face SDK liveness check
    // Note: Implement actual Azure SDK integration here
    // val faceAnalyzer = FaceAnalyzerBuilder()
    //     .setSessionAuthToken(azureSession.authToken)
    //     .build()
    // val livenessResult = faceAnalyzer.analyzeFace(activity)

    // Placeholder for SDK integration
    val sdkCompleted = true

    if (!sdkCompleted) {
        throw LivenessClientException.LivenessCheckFailed("SDK check cancelled")
    }

    // Step 4: Complete the pipeline
    val result = completeLiveness(azureSession.azureSessionId)

    val livenessResult = LivenessResult.fromString(result.livenessResult)

    PipelineResult(
        sessionId = result.sessionId,
        livenessResult = livenessResult,
        livenessConfidence = result.livenessConfidence ?: 0.0,
        applicantId = result.applicantId,
        isSuccess = livenessResult == LivenessResult.LIVE && result.applicantId != null,
        error = result.error
    )
}
