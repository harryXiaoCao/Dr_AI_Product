import 'package:dio/dio.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class DrAiRepository {
  Future<AuthSession?> restore();
  Future<AuthSession> login(String email, String password);
  Future<void> logout();
  Future<DashboardData> loadDashboard(AppRole role);
}

class DioDrAiRepository implements DrAiRepository {
  DioDrAiRepository({required this.client, required this.secureStorage});

  static const _refreshTokenKey = 'dr_ai_refresh_token';
  final Dio client;
  final FlutterSecureStorage secureStorage;
  AuthSession? _session;

  @override
  Future<AuthSession?> restore() async {
    final refreshToken = await secureStorage.read(key: _refreshTokenKey);
    if (refreshToken == null) {
      return null;
    }
    try {
      return await _refresh(refreshToken);
    } on ApiError {
      await secureStorage.delete(key: _refreshTokenKey);
      return null;
    }
  }

  @override
  Future<AuthSession> login(String email, String password) async {
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/login',
        data: <String, String>{'email': email.trim(), 'password': password},
      );
      return await _saveSession(AuthSession.fromJson(response.data!));
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  Future<AuthSession> _refresh(String refreshToken) async {
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        data: <String, String>{'refresh_token': refreshToken},
      );
      return await _saveSession(AuthSession.fromJson(response.data!));
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  Future<AuthSession> _saveSession(AuthSession session) async {
    _session = session;
    await secureStorage.write(
      key: _refreshTokenKey,
      value: session.refreshToken,
    );
    return session;
  }

  @override
  Future<void> logout() async {
    final session = _session;
    try {
      if (session != null) {
        await client.post<void>(
          '/api/v1/auth/logout',
          data: <String, String>{'refresh_token': session.refreshToken},
          options: Options(
            headers: <String, String>{
              'Authorization': 'Bearer ${session.accessToken}',
            },
          ),
        );
      }
    } on DioException {
      // Local token removal is mandatory even when the network is unavailable.
    } finally {
      _session = null;
      await secureStorage.delete(key: _refreshTokenKey);
    }
  }

  @override
  Future<DashboardData> loadDashboard(AppRole role) async {
    final path = role == AppRole.patient
        ? '/api/v1/patient/me/today'
        : '/api/v1/me/dashboard';
    try {
      return await _getDashboard(path);
    } on ApiError catch (error) {
      if (error.statusCode != 401 || _session == null) {
        rethrow;
      }
      await _refresh(_session!.refreshToken);
      return _getDashboard(path);
    }
  }

  Future<DashboardData> _getDashboard(String path) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.get<Map<String, dynamic>>(
        path,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return DashboardData.fromJson(response.data!);
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  ApiError _toApiError(DioException error) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final envelope = data['error'];
      if (envelope is Map<String, dynamic>) {
        return ApiError(
          code: envelope['code'] as String? ?? 'service_unavailable',
          message:
              envelope['message'] as String? ??
              'The request could not be completed.',
          requestId: envelope['request_id'] as String?,
          statusCode: error.response?.statusCode,
        );
      }
    }
    return ApiError(
      code: 'service_unavailable',
      message: 'Unable to reach Dr. AI. Check your connection and try again.',
      statusCode: error.response?.statusCode,
    );
  }
}
