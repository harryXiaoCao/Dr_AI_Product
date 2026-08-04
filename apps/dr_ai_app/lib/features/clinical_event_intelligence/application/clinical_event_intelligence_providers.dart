import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/clinical_event_intelligence/domain/clinical_event_intelligence_data.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

typedef ClinicalEventIntelligenceScope = ({
  AppRole role,
  String requestId,
  String locale,
});

final clinicalEventIntelligenceProvider = FutureProvider.autoDispose
    .family<ClinicalEventIntelligenceData?, ClinicalEventIntelligenceScope>((
      ref,
      scope,
    ) {
      ref.watch(authControllerProvider);
      return ref
          .read(repositoryProvider)
          .loadClinicalEventIntelligence(
            role: scope.role,
            requestId: scope.requestId,
            locale: scope.locale,
          );
    });
