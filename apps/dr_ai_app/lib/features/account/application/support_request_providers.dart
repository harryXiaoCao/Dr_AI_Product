import 'package:dr_ai_app/features/account/domain/support_request_data.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final supportRequestsProvider =
    FutureProvider.autoDispose<List<SupportRequestData>>((ref) {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadSupportRequests();
    });
