import 'package:dio/dio.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class DrAiRepository {
  Future<AuthSession?> restore();
  Future<AuthSession> login(String email, String password);
  Future<void> logout();
  Future<DashboardData> loadDashboard(AppRole role);
  Future<PatientListData> loadPatients({String? query});
  Future<PatientCareBundle> loadPatientCareBundle(String patientId);
  Future<PatientCareBundle> loadOwnPatientCare();
  Future<DemoAssetPresign> presignDemoAsset({
    required String patientId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  });
  Future<AssessmentListData> loadAssessments(String patientId);
  Future<AssessmentResult> createSimulatedAssessment({
    required String patientId,
    required String fixtureId,
    required String idempotencyKey,
  });
  Future<RecoveryPlanListData> loadRecoveryPlans(String patientId);
  Future<RecoveryPlanData> createRecoveryPlan({
    required String patientId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  });
  Future<RecoveryPlanData> updateRecoveryPlan({
    required String patientId,
    required String planId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  });
  Future<RecoveryPlanData> activateRecoveryPlan({
    required String patientId,
    required String planId,
  });
  Future<PatientTodayData> loadPatientToday();
  Future<RecoveryTaskItem> completeRecoveryTask(String taskId);
  Future<MedicationNotificationScheduleResult> scheduleMedicationNotifications(
    List<RecoveryTaskItem> tasks,
  );
  Future<ChatMessageResult> sendEducationalChatMessage({
    required String threadId,
    required String message,
  });
  Future<ConsultationListData> loadConsultations();
  Future<ConsultationRequestItem> createConsultation({
    required String patientId,
    required String specialty,
    required String questionSummary,
    required String priority,
  });
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
    final response = await _authorizedGet(path);
    return DashboardData.fromJson(response);
  }

  @override
  Future<PatientListData> loadPatients({String? query}) async {
    final trimmed = query?.trim();
    final response = await _authorizedGet(
      '/api/v1/patients',
      queryParameters: <String, dynamic>{
        if (trimmed != null && trimmed.isNotEmpty) 'q': trimmed,
      },
    );
    return PatientListData.fromJson(response);
  }

  @override
  Future<PatientCareBundle> loadPatientCareBundle(String patientId) async {
    final response = await _authorizedGet('/api/v1/patients/$patientId/care');
    return PatientCareBundle.fromJson(response);
  }

  @override
  Future<PatientCareBundle> loadOwnPatientCare() async {
    final response = await _authorizedGet('/api/v1/patient/me/care');
    return PatientCareBundle.fromJson(response);
  }

  @override
  Future<DemoAssetPresign> presignDemoAsset({
    required String patientId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/assets/presign',
      data: <String, dynamic>{
        'filename': filename,
        'content_type': contentType,
        'size_bytes': sizeBytes,
      },
    );
    return DemoAssetPresign.fromJson(response);
  }

  @override
  Future<AssessmentListData> loadAssessments(String patientId) async {
    final response = await _authorizedGet(
      '/api/v1/patients/$patientId/assessments',
    );
    return AssessmentListData.fromJson(response);
  }

  @override
  Future<AssessmentResult> createSimulatedAssessment({
    required String patientId,
    required String fixtureId,
    required String idempotencyKey,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/assessments',
      data: <String, String>{
        'mode': 'simulated',
        'fixture_id': fixtureId,
        'idempotency_key': idempotencyKey,
      },
    );
    return AssessmentResult.fromJson(response);
  }

  @override
  Future<RecoveryPlanListData> loadRecoveryPlans(String patientId) async {
    final response = await _authorizedGet(
      '/api/v1/patients/$patientId/recovery-plans',
    );
    return RecoveryPlanListData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> createRecoveryPlan({
    required String patientId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans',
      data: _recoveryPlanPayload(
        title: title,
        instructions: instructions,
        tasks: tasks,
      ),
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> updateRecoveryPlan({
    required String patientId,
    required String planId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  }) async {
    final response = await _authorizedPut(
      '/api/v1/patients/$patientId/recovery-plans/$planId',
      data: _recoveryPlanPayload(
        title: title,
        instructions: instructions,
        tasks: tasks,
      ),
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> activateRecoveryPlan({
    required String patientId,
    required String planId,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans/$planId/activate',
      data: const <String, dynamic>{},
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<PatientTodayData> loadPatientToday() async {
    final response = await _authorizedGet('/api/v1/patient/me/today');
    return PatientTodayData.fromDashboardJson(response);
  }

  @override
  Future<RecoveryTaskItem> completeRecoveryTask(String taskId) async {
    final response = await _authorizedPost(
      '/api/v1/patient/me/tasks/$taskId/completion',
      data: const <String, bool>{'completed': true},
    );
    return RecoveryTaskItem.fromJson(response['task'] as Map<String, dynamic>);
  }

  @override
  Future<MedicationNotificationScheduleResult> scheduleMedicationNotifications(
    List<RecoveryTaskItem> tasks,
  ) async {
    final medicationTasks = tasks
        .where((task) => task.category == 'medication' && !task.isCompleted)
        .length;
    return MedicationNotificationScheduleResult(
      scheduledCount: medicationTasks,
      label:
          'Local demo medication notifications armed for $medicationTasks task(s).',
    );
  }

  @override
  Future<ChatMessageResult> sendEducationalChatMessage({
    required String threadId,
    required String message,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/chat/threads/$threadId/messages',
      data: <String, dynamic>{'message': message, 'stream': true},
    );
    return ChatMessageResult.fromJson(response);
  }

  @override
  Future<ConsultationListData> loadConsultations() async {
    final response = await _authorizedGet('/api/v1/consultations');
    return ConsultationListData.fromJson(response);
  }

  @override
  Future<ConsultationRequestItem> createConsultation({
    required String patientId,
    required String specialty,
    required String questionSummary,
    required String priority,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/consultations',
      data: <String, dynamic>{
        'patient_id': patientId,
        'specialty': specialty,
        'question_summary': questionSummary,
        'priority': priority,
      },
    );
    return ConsultationRequestItem.fromJson(response);
  }

  Map<String, dynamic> _recoveryPlanPayload({
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  }) {
    return <String, dynamic>{
      'title': title,
      'instructions': instructions,
      'tasks': tasks.map((task) => task.toJson()).toList(),
    };
  }

  Future<Map<String, dynamic>> _authorizedGet(
    String path, {
    Map<String, dynamic>? queryParameters,
    bool allowRefresh = true,
  }) async {
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
        queryParameters: queryParameters,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedGet(
          path,
          queryParameters: queryParameters,
          allowRefresh: false,
        );
      }
      throw apiError;
    }
  }

  Future<Map<String, dynamic>> _authorizedPost(
    String path, {
    required Map<String, dynamic> data,
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.post<Map<String, dynamic>>(
        path,
        data: data,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedPost(path, data: data, allowRefresh: false);
      }
      throw apiError;
    }
  }

  Future<Map<String, dynamic>> _authorizedPut(
    String path, {
    required Map<String, dynamic> data,
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.put<Map<String, dynamic>>(
        path,
        data: data,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedPut(path, data: data, allowRefresh: false);
      }
      throw apiError;
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
