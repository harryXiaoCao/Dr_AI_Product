import 'dart:io';

import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_resources_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

final skipResourceGoldensOnCi =
    Platform.environment['CI'] == 'true' ||
    Directory.current.path.contains('dr_ai_flutter_verify');

void setResourceGoldenViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> pumpResourceGolden(
  WidgetTester tester, {
  required Locale locale,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp(
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: const DoctorResourcesScreen(loadFromApi: false),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'doctor resources matches the desktop visual target',
    (tester) async {
      setResourceGoldenViewport(tester, const Size(1280, 832));
      await pumpResourceGolden(tester, locale: const Locale('en'));

      await expectLater(
        find.byType(DoctorResourcesScreen),
        matchesGoldenFile('goldens/doctor_resources_1280x832.png'),
      );
    },
    skip: skipResourceGoldensOnCi,
  );

  testWidgets(
    'doctor resources matches the Chinese mobile visual target',
    (tester) async {
      setResourceGoldenViewport(tester, const Size(412, 917));
      await pumpResourceGolden(tester, locale: const Locale('zh'));

      await expectLater(
        find.byType(DoctorResourcesScreen),
        matchesGoldenFile('goldens/doctor_resources_zh_412x917.png'),
      );
    },
    skip: skipResourceGoldensOnCi,
  );
}
