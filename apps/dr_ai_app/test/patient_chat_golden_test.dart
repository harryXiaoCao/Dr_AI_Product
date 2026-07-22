import 'dart:io';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

final skipPatientChatGoldenOnCi =
    Platform.environment['CI'] == 'true' ||
    Directory.current.path.contains('dr_ai_flutter_verify');

void main() {
  testWidgets(
    'patient chat practical guidance matches the mobile visual target',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(412, 917);
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });
      final repository = FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [repositoryProvider.overrideWithValue(repository)],
          child: const DrAiApp(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Contacts'));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('dr-ai-contact')));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('patient-ai-input')),
        'I feel dizzy. What could explain it?',
      );
      await tester.tap(find.byKey(const Key('patient-ai-send')));
      await tester.pumpAndSettle();
      await tester.drag(
        find.byKey(const Key('patient-ai-message-list')),
        const Offset(0, -320),
      );
      await tester.pumpAndSettle();

      await expectLater(
        find.byType(DrAiApp),
        matchesGoldenFile(
          'goldens/patient_chat_practical_guidance_412x917.png',
        ),
      );
    },
    skip: skipPatientChatGoldenOnCi,
  );
}
