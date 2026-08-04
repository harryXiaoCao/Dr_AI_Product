import 'package:dio/dio.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'repository uses exact request-scoped CEI paths and safe action body',
    () async {
      FlutterSecureStorage.setMockInitialValues(<String, String>{});
      final requests = <RequestOptions>[];
      final client = Dio(BaseOptions(baseUrl: 'https://example.invalid'));
      client.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            requests.add(options);
            if (options.path == '/api/v1/auth/login') {
              handler.resolve(
                Response<Map<String, dynamic>>(
                  requestOptions: options,
                  statusCode: 200,
                  data: <String, dynamic>{
                    'access_token': 'access',
                    'refresh_token': 'refresh',
                    'user': <String, dynamic>{
                      'id': 'doctor-id',
                      'email': 'doctor@example.invalid',
                      'role': 'doctor',
                      'display_name': 'Doctor',
                    },
                  },
                ),
              );
              return;
            }
            if (options.path.endsWith('/responses')) {
              handler.resolve(
                Response<Map<String, dynamic>>(
                  requestOptions: options,
                  statusCode: 200,
                  data: <String, dynamic>{
                    'response_id': 'response-id',
                    'idempotent_replay': false,
                  },
                ),
              );
              return;
            }
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                statusCode: 200,
                data: <String, dynamic>{
                  'artifact': <String, dynamic>{
                    'artifact_id': 'artifact-id',
                    'artifact_version': 1,
                    'lifecycle_state': 'validated',
                    'location': <String, dynamic>{'source': 'clinical_event'},
                    'requested_item_assessments': <Object>[],
                    'pathways': <Object>[],
                    'critic': <String, dynamic>{'state': 'unavailable'},
                  },
                },
              ),
            );
          },
        ),
      );
      final repository = DioDrAiRepository(
        client: client,
        secureStorage: const FlutterSecureStorage(),
      );
      await repository.login('doctor@example.invalid', 'password');

      for (final role in <AppRole>[
        AppRole.doctor,
        AppRole.patient,
        AppRole.payer,
      ]) {
        await repository.loadClinicalEventIntelligence(
          role: role,
          requestId: 'request-id',
          locale: 'en',
        );
      }
      await repository.generateClinicalEventIntelligence(
        requestId: 'request-id',
        idempotencyKey: 'generate-key-123',
      );
      await repository.appendIntelligenceClinicianResponse(
        requestId: 'request-id',
        artifactId: 'artifact-id',
        action: 'disagree',
        rationale: 'Documented clinical disagreement.',
        idempotencyKey: 'response-key-123',
      );

      expect(
        requests.map((request) => request.path),
        containsAll(<String>[
          '/api/v1/doctor/payer-requests/request-id/intelligence',
          '/api/v1/patient/payer-requests/request-id/intelligence',
          '/api/v1/payer/requests/request-id/intelligence',
          '/api/v1/doctor/payer-requests/request-id/intelligence/artifact-id/responses',
        ]),
      );
      final responseRequest = requests.last;
      expect(responseRequest.method, 'POST');
      expect(responseRequest.data, <String, dynamic>{
        'action': 'disagree',
        'rationale': 'Documented clinical disagreement.',
      });
      expect(responseRequest.headers['Idempotency-Key'], 'response-key-123');
    },
  );
}
