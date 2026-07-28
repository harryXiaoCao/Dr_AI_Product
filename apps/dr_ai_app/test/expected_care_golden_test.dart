import 'dart:io';

import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/expected_care/domain/expected_care_data.dart';
import 'package:dr_ai_app/features/expected_care/presentation/expected_care_screens.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

final skipExpectedCareGoldensOnCi =
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
  required Widget child,
  required FakeDrAiRepository repository,
  required Locale locale,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: child,
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'doctor expected-care review matches desktop evidence workspace',
    (tester) async {
      _viewport(tester, const Size(1280, 832));
      await _pump(
        tester,
        repository: FakeDrAiRepository(restoredSession: doctorSession),
        locale: const Locale('en'),
        child: const DoctorExpectedCareReviewScreen(
          patientId: 'patient-profile-test-id',
          eventId: 'clinical-event-test-id',
        ),
      );
      expect(find.textContaining('No clinician can edit'), findsOneWidget);
      expect(find.text('Acknowledge'), findsOneWidget);
      expect(find.text('Clinically concur'), findsOneWidget);
      expect(find.text('Reject'), findsNothing);
      await expectLater(
        find.byType(DoctorExpectedCareReviewScreen),
        matchesGoldenFile('goldens/expected_care_doctor_1280x832.png'),
      );
    },
    skip: skipExpectedCareGoldensOnCi,
  );

  testWidgets(
    'patient immutable expected-care baseline matches Chinese mobile state',
    (tester) async {
      _viewport(tester, const Size(412, 917));
      await _pump(
        tester,
        repository: FakeDrAiRepository(restoredSession: patientSession),
        locale: const Locale('zh'),
        child: const PatientExpectedCareScreen(
          eventId: 'clinical-event-test-id',
        ),
      );
      expect(find.textContaining('不是报价'), findsOneWidget);
      expect(find.textContaining('AI 候选'), findsNothing);
      await expectLater(
        find.byType(PatientExpectedCareScreen),
        matchesGoldenFile('goldens/expected_care_patient_zh_412x917.png'),
      );
    },
    skip: skipExpectedCareGoldensOnCi,
  );

  testWidgets(
    'payer immutable baseline matches desktop evidence separation',
    (tester) async {
      _viewport(tester, const Size(1280, 832));
      await _pump(
        tester,
        repository: FakeDrAiRepository(restoredSession: payerSession),
        locale: const Locale('en'),
        child: const PayerExpectedCareScreen(
          requestId: 'payer-request-test-id',
        ),
      );
      expect(find.text('AI candidate'), findsOneWidget);
      expect(find.text('Deterministic validation'), findsOneWidget);
      expect(find.text('Human payer review'), findsOneWidget);
      expect(find.textContaining('No automated reimbursement'), findsOneWidget);
      await expectLater(
        find.byType(PayerExpectedCareScreen),
        matchesGoldenFile('goldens/expected_care_payer_1280x832.png'),
      );
    },
    skip: skipExpectedCareGoldensOnCi,
  );

  testWidgets('doctor can inspect used, excluded, and missing cost facts', (
    tester,
  ) async {
    _viewport(tester, const Size(1280, 832));
    await _pump(
      tester,
      repository: FakeDrAiRepository(restoredSession: doctorSession),
      locale: const Locale('en'),
      child: const DoctorExpectedCareReviewScreen(
        patientId: 'patient-profile-test-id',
        eventId: 'clinical-event-test-id',
      ),
    );

    await tester.scrollUntilVisible(
      find.text('Cost-estimation fact accounting'),
      700,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Facts used'), findsOneWidget);
    expect(find.text('Facts not used'), findsOneWidget);
    expect(find.text('Missing facts'), findsOneWidget);
    expect(
      find.textContaining('not linked to this Clinical Event'),
      findsOneWidget,
    );
  });

  testWidgets('patient sees the fact accounting in Simplified Chinese', (
    tester,
  ) async {
    _viewport(tester, const Size(412, 917));
    await _pump(
      tester,
      repository: FakeDrAiRepository(restoredSession: patientSession),
      locale: const Locale('zh'),
      child: const PatientExpectedCareScreen(eventId: 'clinical-event-test-id'),
    );

    await tester.scrollUntilVisible(
      find.text('费用估算事实清单'),
      600,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('已使用事实'), findsOneWidget);
    expect(find.text('未使用事实'), findsOneWidget);
    expect(find.text('缺失事实'), findsOneWidget);
    expect(find.textContaining('不支持图像输入'), findsOneWidget);
  });

  testWidgets('payer evidence includes the server-built fact accounting', (
    tester,
  ) async {
    _viewport(tester, const Size(1280, 832));
    await _pump(
      tester,
      repository: FakeDrAiRepository(restoredSession: payerSession),
      locale: const Locale('en'),
      child: const PayerExpectedCareScreen(requestId: 'payer-request-test-id'),
    );

    await tester.scrollUntilVisible(
      find.text('Cost-estimation fact accounting'),
      700,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Facts used'), findsOneWidget);
    expect(find.text('Facts not used'), findsOneWidget);
    expect(find.text('Missing facts'), findsOneWidget);
  });

  test('fact snapshot parsing preserves redaction and legacy availability', () {
    final snapshot = CostEstimationFactSnapshotData.fromJson(<String, Object>{
      'facts_used': <Object>[
        <String, Object>{
          'category': 'medical_history',
          'count': 1,
          'value': <String, Object>{'present': true, 'detail_withheld': true},
        },
      ],
      'facts_not_used': <Object>[],
      'missing_facts': <Object>[],
    });

    expect(snapshot.available, isTrue);
    expect(snapshot.factsUsed.single.detailWithheld, isTrue);
    expect(CostEstimationFactSnapshotData.fromJson(null).available, isFalse);
  });
}
