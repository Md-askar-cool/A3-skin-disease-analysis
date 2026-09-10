import 'dart:io';
import 'package:dio/dio.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../core/constants.dart';
import '../models/screening_result.dart';

/// SafeSkin AI - API Service
/// Handles all HTTP communication with the FastAPI backend using Dio.
class ApiService {
  late final Dio _dio;

  ApiService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 60),
        sendTimeout: const Duration(seconds: 60),
        headers: {
          'Accept': 'application/json',
        },
      ),
    );

    // Add interceptors
    _dio.interceptors.add(_AuthInterceptor());
    _dio.interceptors.add(LogInterceptor(
      requestBody: false,
      responseBody: false,
      error: true,
    ));
  }

  // ---------- Image Upload ----------

  /// Upload an image file and get back image_path and signed_url
  Future<ImageUploadResponse> uploadImage(File image) async {
    try {
      final fileName = image.path.split(Platform.pathSeparator).last;
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          image.path,
          filename: fileName,
        ),
      });

      final response = await _dio.post(
        AppConstants.uploadEndpoint,
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );

      return ImageUploadResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // ---------- Analyze Image ----------

  /// Run AI analysis on an uploaded image path
  Future<ScreeningResult> analyzeImage(String imagePath) async {
    try {
      final response = await _dio.post(
        AppConstants.analyzeEndpoint,
        data: {'image_path': imagePath},
      );

      return ScreeningResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // ---------- Screening History ----------

  /// Fetch all screenings for the current user
  Future<List<ScreeningHistoryItem>> getScreeningHistory() async {
    try {
      final response = await _dio.get(AppConstants.screeningsEndpoint);

      final list = response.data as List<dynamic>;
      return list
          .map((item) =>
              ScreeningHistoryItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Get a single screening by ID
  Future<ScreeningResult> getScreening(String id) async {
    try {
      final response =
          await _dio.get('${AppConstants.screeningsEndpoint}/$id');
      return ScreeningResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Delete a screening record
  Future<void> deleteScreening(String id) async {
    try {
      await _dio.delete('${AppConstants.screeningsEndpoint}/$id');
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Delete ALL screening records for current user
  Future<void> deleteAllScreenings() async {
    try {
      await _dio.delete(AppConstants.screeningsEndpoint);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // ---------- Progress ----------

  /// Fetch all progress images for current user
  Future<List<ProgressImage>> getProgress() async {
    try {
      final response = await _dio.get(AppConstants.progressEndpoint);
      final list = response.data as List<dynamic>;
      return list
          .map((item) =>
              ProgressImage.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Add a new progress image
  Future<ProgressImage> addProgressImage(File image, {String? notes, String? bodyPart}) async {
    try {
      final fileName = image.path.split(Platform.pathSeparator).last;
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(image.path, filename: fileName),
        if (notes != null) 'notes': notes,
        if (bodyPart != null) 'body_part': bodyPart,
      });

      final response = await _dio.post(
        AppConstants.progressEndpoint,
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );

      return ProgressImage.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Compare two progress images
  Future<CompareResult> compareImages(String id1, String id2) async {
    try {
      final response = await _dio.post(
        AppConstants.compareEndpoint,
        data: {'id1': id1, 'id2': id2},
      );
      return CompareResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Delete a progress entry
  Future<void> deleteProgressEntry(String id) async {
    try {
      await _dio.delete('${AppConstants.progressEndpoint}/$id');
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Delete all progress images for current user
  Future<void> deleteAllProgress() async {
    try {
      await _dio.delete(AppConstants.progressEndpoint);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // ---------- Error Handling ----------
  String _handleDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Request timed out. Check your connection and try again.';
      case DioExceptionType.connectionError:
        return 'Cannot connect to server. Ensure the backend is running.';
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final message = e.response?.data?['detail'] ??
            e.response?.data?['message'] ??
            'Server error';
        return '$statusCode: $message';
      default:
        return e.message ?? 'An unexpected error occurred.';
    }
  }
}

/// Dio interceptor that adds the Supabase Bearer token to every request
class _AuthInterceptor extends Interceptor {
  @override
  void onRequest(
      RequestOptions options, RequestInterceptorHandler handler) {
    final token =
        Supabase.instance.client.auth.currentSession?.accessToken;
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}

/// Global singleton instance
final apiService = ApiService();
