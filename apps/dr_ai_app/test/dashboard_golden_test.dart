import 'dart:ui';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

void setGoldenViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> pumpGoldenApp(
  WidgetTester tester,
  FakeDrAiRepository repository,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: const DrAiApp(),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('doctor dashboard matches the frozen 1280x832 visual target', (
    tester,
  ) async {
    setGoldenViewport(tester, const Size(1280, 832));
    await pumpGoldenApp(
      tester,
      FakeDrAiRepository(restoredSession: doctorSession),
    );

    await expectLater(
      find.byType(DrAiApp),
      matchesGoldenFile('goldens/doctor_dashboard_1280x832.png'),
    );
  });

  testWidgets('patient dashboard matches the frozen 412x917 visual target', (
    tester,
  ) async {
    setGoldenViewport(tester, const Size(412, 917));
    await pumpGoldenApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
      ),
    );

    await expectLater(
      find.byType(DrAiApp),
      matchesGoldenFile('goldens/patient_dashboard_412x917.png'),
    );
  });
}
