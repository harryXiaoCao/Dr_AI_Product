import 'dart:io';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/clinical_event_intelligence/presentation/clinical_event_intelligence_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

final _skipGoldens =
    Platform.environment['CI'] == 'true' ||
    Directory.current.path.contains('dr_ai_flutter_verify');

void _viewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> _pump(
  WidgetTester tester, {
  required AppRole role,
  required Locale locale,
  required Size size,
}) async {
  _viewport(tester, size);
  final session = switch (role) {
    AppRole.doctor => doctorSession,
    AppRole.patient => patientSession,
    AppRole.payer => payerSession,
    AppRole.unsupported => null,
    AppRole.admin => null,
  };
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        repositoryProvider.overrideWithValue(
          FakeDrAiRepository(restoredSession: session),
        ),
      ],
      child: MaterialApp(
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: ClinicalEventIntelligenceScreen(
          role: role,
          requestId: 'payer-request-test-id',
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  for (final role in <AppRole>[
    AppRole.patient,
    AppRole.doctor,
    AppRole.payer,
  ]) {
    for (final configuration in <(String, Locale, Size)>[
      ('mobile_zh_412x917', const Locale('zh'), const Size(412, 917)),
      ('desktop_en_1280x1000', const Locale('en'), const Size(1280, 1000)),
    ]) {
      testWidgets(
        '${role.wireValue} CEI ${configuration.$1} matches rendered target',
        (tester) async {
          await _pump(
            tester,
            role: role,
            locale: configuration.$2,
            size: configuration.$3,
          );
          expect(tester.takeException(), isNull);
          await expectLater(
            find.byType(ClinicalEventIntelligenceScreen),
            matchesGoldenFile(
              'goldens/cei_${role.wireValue}_${configuration.$1}.png',
            ),
          );
        },
        skip: _skipGoldens,
      );
    }
  }
}
