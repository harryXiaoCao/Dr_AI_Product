import 'dart:io';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/doctor/presentation/patient_management_screen.dart';
import 'package:dr_ai_app/shared/widgets/brand_mark.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'fakes.dart';

final skipPatientManagementGoldensOnCi =
    Platform.environment['CI'] == 'true' ||
    Directory.current.path.contains('dr_ai_flutter_verify');

void setPatientManagementGoldenViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> pumpPatientManagementGolden(
  WidgetTester tester, {
  required bool useChinese,
}) async {
  FlutterSecureStorage.setMockInitialValues(<String, String>{
    'dr_ai_interface_locale': useChinese ? 'zh_Hans' : 'en',
  });
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        repositoryProvider.overrideWithValue(
          FakeDrAiRepository(restoredSession: doctorSession),
        ),
      ],
      child: const DrAiApp(),
    ),
  );
  await tester.pumpAndSettle();
  GoRouter.of(
    tester.element(find.byType(DrAiBrandMark).first),
  ).go('/doctor/patients');
  await tester.pumpAndSettle();

  final patientRow = find.byKey(const Key('patient-row-SYN-PATIENT-001'));
  if (patientRow.evaluate().isEmpty) {
    await tester.tap(find.byKey(const Key('open-patient-picker-button')));
    await tester.pumpAndSettle();
  }
  await tester.tap(patientRow);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'patient management matches the desktop visual target',
    (tester) async {
      setPatientManagementGoldenViewport(tester, const Size(1440, 1024));
      await pumpPatientManagementGolden(tester, useChinese: false);

      await expectLater(
        find.byType(PatientManagementScreen),
        matchesGoldenFile('goldens/patient_management_1440x1024.png'),
      );
    },
    skip: skipPatientManagementGoldensOnCi,
  );

  testWidgets(
    'patient management matches the Chinese mobile visual target',
    (tester) async {
      setPatientManagementGoldenViewport(tester, const Size(412, 917));
      await pumpPatientManagementGolden(tester, useChinese: true);

      await expectLater(
        find.byType(PatientManagementScreen),
        matchesGoldenFile('goldens/patient_management_zh_412x917.png'),
      );
    },
    skip: skipPatientManagementGoldensOnCi,
  );
}
