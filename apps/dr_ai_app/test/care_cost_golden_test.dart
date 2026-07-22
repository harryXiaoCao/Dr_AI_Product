import 'dart:io';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/shared/widgets/brand_mark.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'fakes.dart';

final skipCareCostGoldensOnCi =
    Platform.environment['CI'] == 'true' ||
    Directory.current.path.contains('dr_ai_flutter_verify');

void setCareCostGoldenViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> pumpCareCostGolden(
  WidgetTester tester, {
  required FakeDrAiRepository repository,
  required String route,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: const DrAiApp(),
    ),
  );
  await tester.pumpAndSettle();
  GoRouter.of(tester.element(find.byType(DrAiBrandMark).first)).go(route);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'patient care and cost timeline matches the mobile visual target',
    (tester) async {
      setCareCostGoldenViewport(tester, const Size(412, 917));
      await pumpCareCostGolden(
        tester,
        repository: FakeDrAiRepository(restoredSession: patientSession),
        route: '/patient/care-costs',
      );

      await expectLater(
        find.byType(DrAiApp),
        matchesGoldenFile('goldens/patient_care_costs_412x917.png'),
      );
    },
    skip: skipCareCostGoldensOnCi,
  );

  testWidgets(
    'payer review queue matches the desktop visual target',
    (tester) async {
      setCareCostGoldenViewport(tester, const Size(1280, 832));
      await pumpCareCostGolden(
        tester,
        repository: FakeDrAiRepository(restoredSession: payerSession),
        route: '/payer/requests',
      );

      await expectLater(
        find.byType(DrAiApp),
        matchesGoldenFile('goldens/payer_review_queue_1280x832.png'),
      );
    },
    skip: skipCareCostGoldensOnCi,
  );
}
