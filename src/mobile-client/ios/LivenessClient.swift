/**
 * iOS Client SDK for Liveness Detection Pipeline
 *
 * Integrates with the Azure-based liveness detection pipeline.
 * Uses Azure AI Vision Face SDK for client-side liveness detection.
 *
 * Prerequisites:
 * - Azure AI Vision Face SDK (AzureAIVisionFace)
 * - iOS 14.0+
 */

import Foundation
import UIKit
// Import Azure Face SDK
// import AzureAIVisionFace
// import AzureAIVisionCore

// MARK: - Models

/// Pipeline session response
public struct PipelineSession: Codable {
    public let sessionId: String
    public let status: String
    public let token: String
    public let tokenExpiresAt: String
    public let livenessResult: String?
    public let livenessConfidence: Double?
    public let applicantId: String?
    public let error: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case status
        case token
        case tokenExpiresAt = "token_expires_at"
        case livenessResult = "liveness_result"
        case livenessConfidence = "liveness_confidence"
        case applicantId = "applicant_id"
        case error
    }
}

/// Azure liveness session for SDK
public struct AzureLivenessSession: Codable {
    public let azureSessionId: String
    public let authToken: String
    public let pipelineSessionId: String
    public let pipelineToken: String

    enum CodingKeys: String, CodingKey {
        case azureSessionId = "azure_session_id"
        case authToken = "auth_token"
        case pipelineSessionId = "pipeline_session_id"
        case pipelineToken = "pipeline_token"
    }
}

/// Applicant data for submission
public struct ApplicantData: Codable {
    public var firstName: String?
    public var lastName: String?
    public var email: String?
    public var phone: String?
    public var dateOfBirth: String?
    public var address: String?
    public var customFields: [String: String]?

    public init(
        firstName: String? = nil,
        lastName: String? = nil,
        email: String? = nil,
        phone: String? = nil,
        dateOfBirth: String? = nil,
        address: String? = nil,
        customFields: [String: String]? = nil
    ) {
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.phone = phone
        self.dateOfBirth = dateOfBirth
        self.address = address
        self.customFields = customFields
    }

    enum CodingKeys: String, CodingKey {
        case firstName = "first_name"
        case lastName = "last_name"
        case email
        case phone
        case dateOfBirth = "date_of_birth"
        case address
        case customFields = "custom_fields"
    }
}

/// Session creation request
public struct CreateSessionRequest: Codable {
    public let clientId: String
    public let applicantData: ApplicantData
    public var callbackUrl: String?
    public var metadata: [String: String]?

    public init(
        clientId: String,
        applicantData: ApplicantData,
        callbackUrl: String? = nil,
        metadata: [String: String]? = nil
    ) {
        self.clientId = clientId
        self.applicantData = applicantData
        self.callbackUrl = callbackUrl
        self.metadata = metadata
    }

    enum CodingKeys: String, CodingKey {
        case clientId = "client_id"
        case applicantData = "applicant_data"
        case callbackUrl = "callback_url"
        case metadata
    }
}

/// Liveness detection result
public enum LivenessResult: String {
    case live = "live"
    case spoof = "spoof"
    case uncertain = "uncertain"
    case unknown

    public init(rawValue: String) {
        switch rawValue.lowercased() {
        case "live": self = .live
        case "spoof": self = .spoof
        case "uncertain": self = .uncertain
        default: self = .unknown
        }
    }
}

/// Pipeline completion result
public struct PipelineResult {
    public let sessionId: String
    public let livenessResult: LivenessResult
    public let livenessConfidence: Double
    public let applicantId: String?
    public let isSuccess: Bool
    public let error: String?
}

// MARK: - Errors

public enum LivenessClientError: Error, LocalizedError {
    case invalidConfiguration
    case networkError(Error)
    case invalidResponse
    case sessionExpired
    case livenessCheckFailed(String)
    case serverError(String)

    public var errorDescription: String? {
        switch self {
        case .invalidConfiguration:
            return "Invalid client configuration"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid server response"
        case .sessionExpired:
            return "Session has expired"
        case .livenessCheckFailed(let reason):
            return "Liveness check failed: \(reason)"
        case .serverError(let message):
            return "Server error: \(message)"
        }
    }
}

// MARK: - Client Configuration

public struct LivenessClientConfig {
    public let baseUrl: String
    public let clientId: String
    public var functionKey: String?
    public var timeout: TimeInterval = 30

    public init(
        baseUrl: String,
        clientId: String,
        functionKey: String? = nil,
        timeout: TimeInterval = 30
    ) {
        self.baseUrl = baseUrl
        self.clientId = clientId
        self.functionKey = functionKey
        self.timeout = timeout
    }
}

// MARK: - Liveness Client

/// Main client for interacting with the liveness detection pipeline
public class LivenessClient {

    private let config: LivenessClientConfig
    private let urlSession: URLSession
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    /// Current active session
    private(set) public var currentSession: PipelineSession?

    /// Initialize the client with configuration
    public init(config: LivenessClientConfig) {
        self.config = config

        let sessionConfig = URLSessionConfiguration.default
        sessionConfig.timeoutIntervalForRequest = config.timeout
        self.urlSession = URLSession(configuration: sessionConfig)
    }

    // MARK: - Session Management

    /// Start a new liveness detection session
    public func startSession(
        applicantData: ApplicantData,
        callbackUrl: String? = nil,
        metadata: [String: String]? = nil
    ) async throws -> PipelineSession {
        let request = CreateSessionRequest(
            clientId: config.clientId,
            applicantData: applicantData,
            callbackUrl: callbackUrl,
            metadata: metadata
        )

        let session: PipelineSession = try await post(
            path: "/api/sessions",
            body: request
        )

        self.currentSession = session
        return session
    }

    /// Create Azure liveness session for SDK integration
    public func createLivenessSession(
        deviceCorrelationId: String? = nil
    ) async throws -> AzureLivenessSession {
        guard let session = currentSession else {
            throw LivenessClientError.invalidConfiguration
        }

        let body: [String: String] = deviceCorrelationId.map {
            ["device_correlation_id": $0]
        } ?? [:]

        return try await post(
            path: "/api/sessions/\(session.sessionId)/liveness",
            body: body,
            token: session.token
        )
    }

    /// Complete the liveness flow after Azure SDK finishes
    public func completeLiveness(
        azureSessionId: String
    ) async throws -> PipelineSession {
        guard let session = currentSession else {
            throw LivenessClientError.invalidConfiguration
        }

        let body = ["azure_session_id": azureSessionId]

        let result: PipelineSession = try await post(
            path: "/api/sessions/\(session.sessionId)/complete",
            body: body,
            token: session.token
        )

        self.currentSession = result
        return result
    }

    /// Submit image for server-side liveness detection
    public func submitImage(_ image: UIImage) async throws -> PipelineSession {
        guard let session = currentSession else {
            throw LivenessClientError.invalidConfiguration
        }

        guard let imageData = image.jpegData(compressionQuality: 0.9) else {
            throw LivenessClientError.invalidResponse
        }

        let result: PipelineSession = try await postImage(
            path: "/api/sessions/\(session.sessionId)/image",
            imageData: imageData,
            token: session.token
        )

        self.currentSession = result
        return result
    }

    /// Get current session status
    public func getSessionStatus() async throws -> PipelineSession {
        guard let session = currentSession else {
            throw LivenessClientError.invalidConfiguration
        }

        let result: PipelineSession = try await get(
            path: "/api/sessions/\(session.sessionId)",
            token: session.token
        )

        self.currentSession = result
        return result
    }

    /// Cancel the current session
    public func cancelSession() async throws {
        guard let session = currentSession else {
            return
        }

        try await delete(
            path: "/api/sessions/\(session.sessionId)",
            token: session.token
        )

        self.currentSession = nil
    }

    // MARK: - Complete Flow Helper

    /// Execute the complete liveness detection flow
    /// This is a convenience method that handles the entire pipeline
    public func performLivenessCheck(
        applicantData: ApplicantData,
        image: UIImage
    ) async throws -> PipelineResult {
        // Step 1: Start session
        let session = try await startSession(applicantData: applicantData)

        // Step 2: Submit image for liveness detection
        let result = try await submitImage(image)

        // Step 3: Build result
        let livenessResult = LivenessResult(rawValue: result.livenessResult ?? "unknown")

        return PipelineResult(
            sessionId: result.sessionId,
            livenessResult: livenessResult,
            livenessConfidence: result.livenessConfidence ?? 0,
            applicantId: result.applicantId,
            isSuccess: livenessResult == .live && result.applicantId != nil,
            error: result.error
        )
    }

    // MARK: - Network Helpers

    private func buildURL(path: String) -> URL? {
        let baseUrl = config.baseUrl.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        return URL(string: baseUrl + path)
    }

    private func buildRequest(
        url: URL,
        method: String,
        token: String? = nil
    ) -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method

        if let key = config.functionKey {
            request.setValue(key, forHTTPHeaderField: "x-functions-key")
        }

        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        return request
    }

    private func get<T: Decodable>(
        path: String,
        token: String? = nil
    ) async throws -> T {
        guard let url = buildURL(path: path) else {
            throw LivenessClientError.invalidConfiguration
        }

        let request = buildRequest(url: url, method: "GET", token: token)

        return try await execute(request)
    }

    private func post<T: Decodable, B: Encodable>(
        path: String,
        body: B,
        token: String? = nil
    ) async throws -> T {
        guard let url = buildURL(path: path) else {
            throw LivenessClientError.invalidConfiguration
        }

        var request = buildRequest(url: url, method: "POST", token: token)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)

        return try await execute(request)
    }

    private func postImage<T: Decodable>(
        path: String,
        imageData: Data,
        token: String? = nil
    ) async throws -> T {
        guard let url = buildURL(path: path) else {
            throw LivenessClientError.invalidConfiguration
        }

        var request = buildRequest(url: url, method: "POST", token: token)
        request.setValue("image/jpeg", forHTTPHeaderField: "Content-Type")
        request.httpBody = imageData

        return try await execute(request)
    }

    private func delete(
        path: String,
        token: String? = nil
    ) async throws {
        guard let url = buildURL(path: path) else {
            throw LivenessClientError.invalidConfiguration
        }

        let request = buildRequest(url: url, method: "DELETE", token: token)

        do {
            let (_, response) = try await urlSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw LivenessClientError.invalidResponse
            }

            if httpResponse.statusCode >= 400 {
                throw LivenessClientError.serverError("HTTP \(httpResponse.statusCode)")
            }
        } catch let error as LivenessClientError {
            throw error
        } catch {
            throw LivenessClientError.networkError(error)
        }
    }

    private func execute<T: Decodable>(_ request: URLRequest) async throws -> T {
        do {
            let (data, response) = try await urlSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw LivenessClientError.invalidResponse
            }

            if httpResponse.statusCode == 401 {
                throw LivenessClientError.sessionExpired
            }

            if httpResponse.statusCode >= 400 {
                if let errorData = try? decoder.decode([String: String].self, from: data),
                   let error = errorData["error"] {
                    throw LivenessClientError.serverError(error)
                }
                throw LivenessClientError.serverError("HTTP \(httpResponse.statusCode)")
            }

            return try decoder.decode(T.self, from: data)
        } catch let error as LivenessClientError {
            throw error
        } catch let error as DecodingError {
            print("Decoding error: \(error)")
            throw LivenessClientError.invalidResponse
        } catch {
            throw LivenessClientError.networkError(error)
        }
    }
}

// MARK: - Azure SDK Integration

/**
 * Integration with Azure AI Vision Face SDK
 *
 * Example usage:
 *
 * ```swift
 * let client = LivenessClient(config: LivenessClientConfig(
 *     baseUrl: "https://your-function-app.azurewebsites.net",
 *     clientId: "your-client-id",
 *     functionKey: "your-function-key"
 * ))
 *
 * // Start session
 * let session = try await client.startSession(applicantData: ApplicantData(
 *     firstName: "John",
 *     lastName: "Doe",
 *     email: "john@example.com"
 * ))
 *
 * // Get Azure liveness session
 * let azureSession = try await client.createLivenessSession()
 *
 * // Initialize Azure Face SDK with the auth token
 * // let faceAnalyzer = try FaceAnalyzerBuilder()
 * //     .sessionAuthToken(azureSession.authToken)
 * //     .build()
 *
 * // Present liveness check UI and get result
 * // ... Azure SDK liveness check ...
 *
 * // Complete the flow
 * let result = try await client.completeLiveness(
 *     azureSessionId: azureSession.azureSessionId
 * )
 *
 * if result.livenessResult == "live" {
 *     print("Applicant verified! ID: \(result.applicantId ?? "N/A")")
 * }
 * ```
 */
extension LivenessClient {

    /// Execute liveness check using Azure Face SDK
    /// This method integrates with Azure AI Vision Face SDK for client-side liveness
    public func performAzureLivenessCheck(
        applicantData: ApplicantData,
        presentingViewController: UIViewController
    ) async throws -> PipelineResult {
        // Step 1: Start pipeline session
        let _ = try await startSession(applicantData: applicantData)

        // Step 2: Create Azure liveness session
        let azureSession = try await createLivenessSession(
            deviceCorrelationId: UIDevice.current.identifierForVendor?.uuidString
        )

        // Step 3: Run Azure Face SDK liveness check
        // Note: Uncomment and implement when Azure Face SDK is added
        /*
        let faceAnalyzer = try FaceAnalyzerBuilder()
            .sessionAuthToken(azureSession.authToken)
            .build()

        let livenessResult = try await faceAnalyzer.analyzeFace(
            from: presentingViewController
        )
        */

        // Placeholder for SDK integration
        // In production, replace with actual Azure SDK call
        let sdkCompleted = true

        guard sdkCompleted else {
            throw LivenessClientError.livenessCheckFailed("SDK check cancelled")
        }

        // Step 4: Complete the pipeline
        let result = try await completeLiveness(
            azureSessionId: azureSession.azureSessionId
        )

        let livenessResult = LivenessResult(rawValue: result.livenessResult ?? "unknown")

        return PipelineResult(
            sessionId: result.sessionId,
            livenessResult: livenessResult,
            livenessConfidence: result.livenessConfidence ?? 0,
            applicantId: result.applicantId,
            isSuccess: livenessResult == .live && result.applicantId != nil,
            error: result.error
        )
    }
}
