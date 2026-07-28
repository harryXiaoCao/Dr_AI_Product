import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

void main() {
  testWidgets('patient can archive, reopen, and delete a retained chat thread', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1100, 850);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    final now = DateTime.utc(2026, 7, 27);
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
      chatThreads: <PatientChatThreadSummary>[
        PatientChatThreadSummary(
          threadId: 'lifecycle-thread',
          title: 'Blood pressure questions',
          status: 'active',
          createdAt: now,
          lastMessageAt: now,
          retentionUntil: now.add(const Duration(days: 60)),
        ),
      ],
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

    final menu = find.byKey(
      const Key('patient-ai-thread-menu-lifecycle-thread'),
    );
    expect(menu, findsOneWidget);
    await tester.tap(menu);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Archive conversation'));
    await tester.pumpAndSettle();
    expect(find.text('Archived'), findsOneWidget);

    await tester.tap(menu);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Reopen conversation'));
    await tester.pumpAndSettle();
    expect(find.text('Archived'), findsNothing);

    await tester.tap(menu);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Delete from my history'));
    await tester.pumpAndSettle();
    expect(
      find.text(
        'Your health conversations will appear here after you send the first question.',
      ),
      findsOneWidget,
    );
  });

  testWidgets(
    'failed patient chat send has a truthful retry without duplication',
    (tester) async {
      tester.view.physicalSize = const Size(412, 917);
      tester.view.devicePixelRatio = 1;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });
      final repository = FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
        chatError: const ApiError(
          code: 'service_unavailable',
          message: 'synthetic outage',
        ),
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

      const question = 'What should I record with my blood pressure?';
      await tester.enterText(
        find.byKey(const Key('patient-ai-input')),
        question,
      );
      await tester.tap(find.byKey(const Key('patient-ai-send')));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('patient-ai-retry-send')), findsOneWidget);
      expect(find.text(question), findsOneWidget);

      repository.chatError = null;
      await tester.tap(find.byKey(const Key('patient-ai-retry-send')));
      await tester.pumpAndSettle();
      expect(repository.chatMessagesSent, 1);
      expect(find.text(question), findsOneWidget);
      expect(find.byKey(const Key('patient-ai-retry-send')), findsNothing);
    },
  );
}
