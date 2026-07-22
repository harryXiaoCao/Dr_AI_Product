import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final ownCareCostLedgerProvider =
    FutureProvider.autoDispose<CareCostLedgerData>((ref) {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadOwnCareCosts();
    });

final patientCareCostLedgerProvider = FutureProvider.autoDispose
    .family<CareCostLedgerData, String>((ref, patientId) {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadPatientCareCosts(patientId);
    });

final payerOrganizationsProvider =
    FutureProvider.autoDispose<List<PayerOrganizationData>>((ref) {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadPayerOrganizations();
    });

final doctorPayerRequestsProvider =
    FutureProvider.autoDispose<List<PayerRequestData>>((ref) {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadDoctorPayerRequests();
    });

final ownPatientPayerRequestsProvider =
    FutureProvider.autoDispose<List<PayerRequestData>>((ref) {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadOwnPatientPayerRequests();
    });

final payerDashboardProvider = FutureProvider.autoDispose<PayerDashboardData>((
  ref,
) {
  ref.watch(authControllerProvider);
  return ref.read(repositoryProvider).loadPayerDashboard();
});

final payerProfileProvider = FutureProvider.autoDispose<PayerProfileData>((
  ref,
) {
  ref.watch(authControllerProvider);
  return ref.read(repositoryProvider).loadPayerProfile();
});

final payerRequestsProvider =
    FutureProvider.autoDispose<List<PayerRequestData>>((ref) {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadPayerRequests();
    });

Future<void> refreshDoctorCareCostData(Ref ref, String patientId) async {
  ref.invalidate(patientCareCostLedgerProvider(patientId));
  ref.invalidate(doctorPayerRequestsProvider);
}
