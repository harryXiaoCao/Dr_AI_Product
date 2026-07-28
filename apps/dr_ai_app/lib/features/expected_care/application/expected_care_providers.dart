import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/expected_care/domain/expected_care_data.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

typedef ExpectedCareScope = ({String patientId, String eventId});
typedef ExpectedCareExplanationScope = ({
  String role,
  String parentId,
  String eventId,
  String comparisonId,
});

final doctorExpectedCareCandidatesProvider = FutureProvider.autoDispose
    .family<List<ExpectedCareCandidateData>, ExpectedCareScope>((ref, scope) {
      ref.watch(authControllerProvider);
      return ref
          .read(repositoryProvider)
          .loadExpectedCareCandidates(scope.patientId, scope.eventId);
    });

final patientExpectedCareEnvelopeProvider = FutureProvider.autoDispose
    .family<ExpectedCareBaselineData, String>((ref, eventId) {
      ref.watch(authControllerProvider);
      return ref
          .read(repositoryProvider)
          .loadPatientExpectedCareEnvelope(eventId);
    });

final payerExpectedCareEnvelopeProvider = FutureProvider.autoDispose
    .family<PayerExpectedCareData, String>((ref, requestId) {
      ref.watch(authControllerProvider);
      return ref
          .read(repositoryProvider)
          .loadPayerExpectedCareEnvelope(requestId);
    });

final doctorExpectedCareComparisonProvider = FutureProvider.autoDispose
    .family<ExpectedCareComparisonData, ExpectedCareScope>((ref, scope) {
      ref.watch(authControllerProvider);
      return ref
          .read(repositoryProvider)
          .loadDoctorExpectedCareComparison(scope.patientId, scope.eventId);
    });

final patientExpectedCareComparisonProvider = FutureProvider.autoDispose
    .family<ExpectedCareComparisonData, String>((ref, eventId) {
      ref.watch(authControllerProvider);
      return ref
          .read(repositoryProvider)
          .loadPatientExpectedCareComparison(eventId);
    });

final payerExpectedCareComparisonProvider = FutureProvider.autoDispose
    .family<ExpectedCareComparisonData, String>((ref, requestId) {
      ref.watch(authControllerProvider);
      return ref
          .read(repositoryProvider)
          .loadPayerExpectedCareComparison(requestId);
    });

final expectedCareExplanationProvider = FutureProvider.autoDispose
    .family<ExpectedCareExplanationData, ExpectedCareExplanationScope>((
      ref,
      scope,
    ) {
      ref.watch(authControllerProvider);
      final repository = ref.read(repositoryProvider);
      return switch (scope.role) {
        'doctor' => repository.loadDoctorExpectedCareExplanation(
          patientId: scope.parentId,
          eventId: scope.eventId,
          comparisonId: scope.comparisonId,
        ),
        'patient' => repository.loadPatientExpectedCareExplanation(
          eventId: scope.eventId,
          comparisonId: scope.comparisonId,
        ),
        'payer' => repository.loadPayerExpectedCareExplanation(
          requestId: scope.parentId,
          comparisonId: scope.comparisonId,
        ),
        _ => throw ArgumentError.value(scope.role, 'role'),
      };
    });
