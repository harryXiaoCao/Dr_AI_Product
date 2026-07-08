import 'dart:async';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'fakes.dart';

Future<void> pumpApp(WidgetTester tester, FakeDrAiRepository repository) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: const DrAiApp(),
    ),
  );
  await tester.pumpAndSettle();
}

void setViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

double contrastRatio(Color foreground, Color background) {
  final light = foreground.computeLuminance();
  final dark = background.computeLuminance();
  final lighter = light > dark ? light : dark;
  final darker = light > dark ? dark : light;
  return (lighter + 0.05) / (darker + 0.05);
}

Future<void> openDoctorPatientWorkflow(
  WidgetTester tester, {
  String section = 'imaging',
}) async {
  await tester.tap(find.text('Patient Management'));
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const Key('patient-row-SYN-PATIENT-001')));
  await tester.pumpAndSettle();
  if (section != 'overview') {
    final sectionButton = find.byKey(Key('doctor-section-$section'));
    if (section == 'imaging' || section == 'consultationActivity') {
      await tester.drag(
        find.byKey(const Key('doctor-workspace-section-nav')),
        const Offset(0, -260),
      );
      await tester.pumpAndSettle();
    }
    await tester.ensureVisible(sectionButton);
    await tester.tap(sectionButton, warnIfMissed: false);
  }
  await tester.pumpAndSettle();
}

void main() {
  test('core Dr. AI color pairs keep readable contrast', () {
    expect(contrastRatio(DrAiColors.white, DrAiColors.brand), greaterThan(4.5));
    expect(
      contrastRatio(DrAiColors.white, DrAiColors.brandDark),
      greaterThan(4.5),
    );
    expect(contrastRatio(DrAiColors.ink, DrAiColors.white), greaterThan(4.5));
    expect(
      contrastRatio(DrAiColors.ink, DrAiColors.patientAccent),
      greaterThan(4.5),
    );
    expect(
      contrastRatio(DrAiColors.danger, DrAiColors.white),
      greaterThan(4.5),
    );
  });

  testWidgets('signed-out users see validation before a login request', (
    tester,
  ) async {
    await pumpApp(tester, FakeDrAiRepository());

    expect(find.text('Welcome to Dr. AI'), findsOneWidget);
    await tester.tap(find.byKey(const Key('login-button')));
    await tester.pump();

    expect(find.text('Enter a valid email address.'), findsOneWidget);
    expect(find.text('Enter your password.'), findsOneWidget);
  });

  testWidgets('login shows loading then routes a doctor to the dashboard', (
    tester,
  ) async {
    final completer = Completer<AuthSession>();
    final repository = FakeDrAiRepository(loginCompleter: completer);
    await pumpApp(tester, repository);

    await tester.enterText(
      find.byKey(const Key('email-field')),
      'doctor.demo@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('password-field')),
      'test-only password',
    );
    await tester.tap(find.byKey(const Key('login-button')));
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    completer.complete(doctorSession);
    await tester.pumpAndSettle();
    expect(find.text('Quick Access'), findsOneWidget);
    expect(find.text('Dr. Avery Demo'), findsWidgets);
  });

  testWidgets('login displays the standardized safe API error', (tester) async {
    final repository = FakeDrAiRepository(
      loginError: const ApiError(
        code: 'unauthenticated',
        message: 'The email or password is incorrect.',
        statusCode: 401,
      ),
    );
    await pumpApp(tester, repository);

    await tester.enterText(
      find.byKey(const Key('email-field')),
      'doctor.demo@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('password-field')),
      'wrong test password',
    );
    await tester.tap(find.byKey(const Key('login-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login-error')), findsOneWidget);
    expect(find.text('The email or password is incorrect.'), findsOneWidget);
  });

  testWidgets('login distinguishes network failures from credentials', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      loginError: const ApiError(
        code: 'service_unavailable',
        message: 'The service is temporarily unavailable.',
        statusCode: 503,
      ),
    );
    await pumpApp(tester, repository);

    await tester.enterText(
      find.byKey(const Key('email-field')),
      'doctor.demo@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('password-field')),
      'test-only password',
    );
    await tester.tap(find.byKey(const Key('login-button')));
    await tester.pumpAndSettle();

    expect(
      find.text('Unable to reach Dr. AI. Check your connection and try again.'),
      findsOneWidget,
    );
  });

  testWidgets('a secure stored patient session restores to the patient route', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    await pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
      ),
    );

    expect(find.text('Recovery Plan'), findsWidgets);
    expect(find.text('Contact Doctor'), findsOneWidget);
    expect(find.text('Medical Fee'), findsOneWidget);
  });

  testWidgets('logout clears the session and returns to sign in', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);

    await tester.tap(find.byKey(const Key('logout-button')));
    await tester.pumpAndSettle();

    expect(repository.logoutCalled, isTrue);
    expect(find.text('Welcome to Dr. AI'), findsOneWidget);
    expect(find.byKey(const Key('login-notice')), findsOneWidget);
    expect(find.text('You have signed out.'), findsOneWidget);
  });

  testWidgets(
    'logout still gives local feedback when the server is unreachable',
    (tester) async {
      final repository = FakeDrAiRepository(
        restoredSession: doctorSession,
        logoutError: Exception('network unavailable'),
      );
      await pumpApp(tester, repository);

      await tester.tap(find.byKey(const Key('logout-button')));
      await tester.pumpAndSettle();

      expect(repository.logoutCalled, isTrue);
      expect(find.text('Welcome to Dr. AI'), findsOneWidget);
      expect(
        find.text(
          'You have signed out locally. The server could not be reached.',
        ),
        findsOneWidget,
      );
    },
  );

  testWidgets('beta support surface is reachable and local-only', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    await pumpApp(tester, FakeDrAiRepository());

    await tester.tap(find.byKey(const Key('login-beta-support-link')));
    await tester.pumpAndSettle();

    expect(find.text('Beta support'), findsOneWidget);
    expect(find.byKey(const Key('beta-privacy-section')), findsOneWidget);
    expect(find.byKey(const Key('beta-consent-section')), findsOneWidget);

    Future<void> tapConsentCheckbox(Key rowKey) async {
      final row = find.byKey(rowKey);
      await tester.ensureVisible(row);
      await tester.pumpAndSettle();
      await tester.tap(
        find.descendant(of: row, matching: find.byType(Checkbox)),
      );
      await tester.pumpAndSettle();
    }

    await tapConsentCheckbox(const Key('consent-synthetic-only-checkbox'));
    await tapConsentCheckbox(const Key('consent-no-emergency-checkbox'));
    await tapConsentCheckbox(const Key('consent-no-real-data-checkbox'));
    await tester.pumpAndSettle();
    expect(find.text('Consent readiness prepared locally.'), findsOneWidget);

    await tester.dragUntilVisible(
      find.byKey(const Key('beta-deletion-section')),
      find.byKey(const Key('beta-support-list')),
      const Offset(0, -520),
    );
    expect(find.byKey(const Key('beta-deletion-section')), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('account-deletion-confirm-field')),
      'REQUEST DEMO DELETION',
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const Key('account-deletion-prepare-button')),
    );
    final deletionButton = tester.widget<FilledButton>(
      find.byKey(const Key('account-deletion-prepare-button')),
    );
    expect(deletionButton.onPressed, isNotNull);
    await tester.tap(find.byKey(const Key('account-deletion-prepare-button')));
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('account-deletion-prepared-status')),
      findsOneWidget,
    );

    await tester.dragUntilVisible(
      find.byKey(const Key('beta-feedback-section')),
      find.byKey(const Key('beta-support-list')),
      const Offset(0, -520),
    );
    await tester.enterText(
      find.byKey(const Key('beta-feedback-field')),
      'Synthetic beta feedback draft only.',
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const Key('beta-feedback-prepare-button')),
    );
    await tester.tap(find.byKey(const Key('beta-feedback-prepare-button')));
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('beta-feedback-prepared-status')),
      findsOneWidget,
    );

    await tester.dragUntilVisible(
      find.byKey(const Key('beta-limitations-section')),
      find.byKey(const Key('beta-support-list')),
      const Offset(0, -520),
    );
    expect(find.byKey(const Key('beta-limitations-section')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('beta support route is public from a direct web path', (
    tester,
  ) async {
    final router = createRouter(null);
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(child: MaterialApp.router(routerConfig: router)),
    );

    router.go('/beta-support');
    await tester.pumpAndSettle();

    expect(find.text('Beta support'), findsOneWidget);
    expect(find.byKey(const Key('beta-support-list')), findsOneWidget);
  });

  testWidgets('patient role cannot navigate to the doctor route', (
    tester,
  ) async {
    final router = createRouter(AppRole.patient);
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          repositoryProvider.overrideWithValue(
            FakeDrAiRepository(
              restoredSession: patientSession,
              dashboard: patientDashboard,
            ),
          ),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();

    router.go('/doctor');
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.lock_outline), findsOneWidget);
    expect(find.textContaining('not available for your role'), findsOneWidget);
  });

  testWidgets(
    'future unsupported roles fail closed instead of using doctor UI',
    (tester) async {
      expect(AppRole.fromWire('specialist'), AppRole.unsupported);
      expect(AppRole.fromWire('admin'), AppRole.unsupported);

      final router = createRouter(AppRole.unsupported);
      addTearDown(router.dispose);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            repositoryProvider.overrideWithValue(
              FakeDrAiRepository(restoredSession: unsupportedRoleSession),
            ),
          ],
          child: MaterialApp.router(routerConfig: router),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.lock_outline), findsOneWidget);
      expect(
        find.textContaining('not available for your role'),
        findsOneWidget,
      );
      expect(find.text('Quick Access'), findsNothing);
      final button = tester.widget<FilledButton>(find.byType(FilledButton));
      expect(button.onPressed, isNull);
    },
  );

  testWidgets('doctor dashboard renders seeded desktop state at 1280x832', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: doctorSession));

    expect(find.text('Synthetic Community Hospital'), findsOneWidget);
    expect(find.text('Quick Access'), findsOneWidget);
    expect(find.text('Recent Activities'), findsOneWidget);
    expect(find.text('Resource Overview'), findsOneWidget);
    expect(find.text('Team Management'), findsOneWidget);
    expect(find.byKey(const Key('doctor-panel-Quick Access')), findsOneWidget);
    expect(
      find.byKey(const Key('doctor-panel-Resource Overview')),
      findsOneWidget,
    );
    expect(find.byIcon(Icons.logout), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('doctor can search and open assigned patient management', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);

    await tester.tap(find.text('Patient Management'));
    await tester.pumpAndSettle();
    expect(find.text('Patient Management'), findsWidgets);
    expect(
      find.byKey(const Key('patient-row-SYN-PATIENT-001')),
      findsOneWidget,
    );

    await tester.enterText(
      find.byKey(const Key('patient-search-field')),
      'Riley',
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('patient-row-SYN-PATIENT-001')));
    await tester.pumpAndSettle();

    expect(find.text('Patient Workspace'), findsOneWidget);
    expect(
      find.byKey(const Key('selected-patient-summary-header')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('active-clinical-event-bar')), findsOneWidget);
    expect(
      find.textContaining('Synthetic headache care episode'),
      findsWidgets,
    );
    expect(
      find.byKey(const Key('doctor-workspace-section-nav')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('medical-history-overview-section')),
      findsOneWidget,
    );
    expect(find.textContaining('Workflow: review ready'), findsWidgets);

    await tester.tap(find.byKey(const Key('doctor-section-medicalHistory')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('allergies-section')), findsOneWidget);
    expect(find.text('Synthetic pollen sensitivity'), findsOneWidget);
    final historyReviewButton = find.byKey(
      const Key('medical-history-review-save-button'),
    );
    await tester.ensureVisible(historyReviewButton);
    await tester.pumpAndSettle();
    await tester.tap(historyReviewButton);
    await tester.pumpAndSettle();
    expect(repository.medicalHistoryReviewCreated, isTrue);
    expect(find.textContaining('Medical history review saved'), findsWidgets);

    await tester.tap(find.byKey(const Key('doctor-section-profile')));
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('doctor-profile-read-only-notice')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const Key('doctor-section-clinicalEvents')));
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('clinical-event-context-card')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('clinical-event-editor')), findsOneWidget);
    expect(
      find.byKey(const Key('clinical-event-doctor-owned-notice')),
      findsOneWidget,
    );
    await tester.enterText(
      find.byKey(const Key('clinical-event-title-field')),
      'Updated synthetic headache care episode',
    );
    await tester.tap(find.byKey(const Key('clinical-event-save-button')));
    await tester.pumpAndSettle();
    expect(repository.clinicalEventSaved, isTrue);
    expect(repository.lastClinicalEventId, 'clinical-event-test-id');
    expect(
      find.byKey(const Key('clinical-event-save-success')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const Key('clinical-event-new-button')));
    await tester.pumpAndSettle();
    expect(find.text('Create Clinical Event'), findsOneWidget);
    await tester.tap(
      find.byKey(const Key('clinical-event-chip-clinical-event-test-id')),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('visit-history-section')), findsOneWidget);
    expect(find.text('Synthetic observation'), findsOneWidget);

    expect(find.byKey(const Key('doctor-section-reminders')), findsNothing);
    await tester.tap(
      find.byKey(const Key('doctor-section-medicationPrescriptions')),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('medications-section')), findsOneWidget);
    expect(find.byKey(const Key('prescriptions-section')), findsOneWidget);
    expect(
      find.byKey(const Key('medication-reminders-section')),
      findsOneWidget,
    );
    await tester.dragUntilVisible(
      find.byKey(const Key('create-prescription-button')),
      find.byKey(const Key('doctor-section-list-medicationPrescriptions')),
      const Offset(0, -260),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('create-prescription-button')));
    await tester.pumpAndSettle();
    expect(repository.prescriptionCreated, isTrue);
    expect(
      repository.patientCareBundle.prescriptions.first.clinicalEventId,
      'clinical-event-test-id',
    );
    await tester.dragUntilVisible(
      find.byKey(const Key('save-medication-button')),
      find.byKey(const Key('doctor-section-list-medicationPrescriptions')),
      const Offset(0, -260),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('save-medication-button')));
    await tester.pumpAndSettle();
    expect(repository.medicationSaved, isTrue);
    expect(
      repository.patientCareBundle.medications.first.clinicalEventId,
      'clinical-event-test-id',
    );
    expect(find.byKey(const Key('medication-workflow-success')), findsWidgets);
    expect(
      find.byKey(const Key('create-medication-reminder-button')),
      findsNothing,
    );

    await tester.drag(
      find.byKey(const Key('doctor-workspace-section-nav')),
      const Offset(0, -260),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('doctor-section-imaging')),
      warnIfMissed: false,
    );
    await tester.pumpAndSettle();
    expect(
      find.textContaining('Research simulation - not for diagnosis.'),
      findsOneWidget,
    );
    await tester.dragUntilVisible(
      find.byKey(const Key('demo-upload-presign-button')),
      find.byKey(const Key('doctor-section-list-imaging')),
      const Offset(0, -220),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('demo-upload-presign-button')));
    await tester.pumpAndSettle();
    expect(find.text('Demo upload prepared'), findsOneWidget);

    await tester.dragUntilVisible(
      find.byKey(const Key('imaging-prepare-button')),
      find.byKey(const Key('doctor-section-list-imaging')),
      const Offset(0, -280),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('imaging-prepare-button')));
    await tester.pumpAndSettle();
    expect(repository.imagingPrepared, isTrue);
    expect(find.byKey(const Key('imaging-workflow-status')), findsOneWidget);
    await tester.tap(find.byKey(const Key('imaging-complete-button')));
    await tester.pumpAndSettle();
    expect(repository.imagingCompleted, isTrue);
    await tester.ensureVisible(find.byKey(const Key('imaging-review-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('imaging-review-button')));
    await tester.pumpAndSettle();
    expect(repository.imagingReviewed, isTrue);
    expect(find.textContaining('reviewed'), findsWidgets);
    expect(
      find.textContaining('Manual demo imaging finding/result'),
      findsWidgets,
    );
    expect(find.textContaining('Manual demo measurement note'), findsWidgets);

    await tester.drag(
      find.byKey(const Key('doctor-section-list-imaging')),
      const Offset(0, -480),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('assessment-run-button')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Risk: moderate'), findsWidgets);
    expect(find.text('Fixture model: fixture-simulator-1.0.0'), findsWidgets);

    await tester.tap(find.byKey(const Key('doctor-section-recoveryPlans')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('recovery-plan-title-field')),
      'Updated synthetic recovery plan',
    );
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pumpAndSettle();
    await tester.drag(
      find.byKey(const Key('doctor-section-list-recoveryPlans')),
      const Offset(0, -680),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('recovery-plan-save-button')));
    await tester.pumpAndSettle();
    expect(find.textContaining('saved as'), findsOneWidget);
    expect(
      repository.recoveryPlans.items.first.clinicalEventId,
      'clinical-event-test-id',
    );

    await tester.tap(
      find.byKey(const Key('recovery-plan-submit-review-button')),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('in_review'), findsWidgets);

    await tester.tap(find.byKey(const Key('recovery-plan-activate-button')));
    await tester.pumpAndSettle();
    expect(find.textContaining('active'), findsWidgets);
  });

  testWidgets('upload failure preserves metadata and recovers on retry', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    final repository = FakeDrAiRepository(
      restoredSession: doctorSession,
      presignError: const ApiError(
        code: 'service_unavailable',
        message: 'Upload preparation is temporarily unavailable.',
        statusCode: 503,
      ),
    );
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester);

    await tester.ensureVisible(
      find.byKey(const Key('demo-upload-filename-field')),
    );
    await tester.enterText(
      find.byKey(const Key('demo-upload-filename-field')),
      'retry-synthetic-scan.png',
    );
    await tester.enterText(
      find.byKey(const Key('demo-upload-size-field')),
      '4096',
    );
    await tester.tap(find.byKey(const Key('demo-upload-presign-button')));
    await tester.pumpAndSettle();

    expect(
      find.text('Unable to reach Dr. AI. Check your connection and try again.'),
      findsOneWidget,
    );
    expect(find.text('retry-synthetic-scan.png'), findsOneWidget);
    expect(find.text('4096'), findsOneWidget);

    repository.presignError = null;
    await tester.tap(find.byKey(const Key('demo-upload-presign-button')));
    await tester.pumpAndSettle();

    expect(find.text('Demo upload prepared'), findsOneWidget);
    expect(find.text('retry-synthetic-scan.png'), findsOneWidget);
    expect(find.text('4096'), findsOneWidget);
  });

  testWidgets('doctor patient workspace uses compact navigation on phone', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: doctorSession));

    GoRouter.of(
      tester.element(find.text('Dr. AI').first),
    ).go('/doctor/patients');
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('patient-row-SYN-PATIENT-001')), findsNothing);
    expect(find.byKey(const Key('open-patient-picker-button')), findsOneWidget);

    await tester.tap(find.byKey(const Key('open-patient-picker-button')));
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('patient-row-SYN-PATIENT-001')),
      findsOneWidget,
    );
    await tester.tap(find.byKey(const Key('patient-row-SYN-PATIENT-001')));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('selected-patient-summary-header')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('doctor-compact-section-picker')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('doctor-workspace-section-nav')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('assessment failure preserves form state and recovers on retry', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester);

    repository.assessmentError = const ApiError(
      code: 'service_unavailable',
      message: 'Assessment simulation is temporarily unavailable.',
      statusCode: 503,
    );
    await tester.dragUntilVisible(
      find.byKey(const Key('assessment-run-button')),
      find.byKey(const Key('doctor-section-list-imaging')),
      const Offset(0, -300),
    );
    await tester.ensureVisible(find.byKey(const Key('assessment-run-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('assessment-run-button')));
    await tester.pumpAndSettle();

    expect(
      find.text('Unable to reach Dr. AI. Check your connection and try again.'),
      findsOneWidget,
    );
    expect(find.text('synthetic_lung_case_001'), findsOneWidget);

    repository.assessmentError = null;
    await tester.tap(find.byKey(const Key('assessment-run-button')));
    await tester.pumpAndSettle();

    expect(find.textContaining('Risk: moderate'), findsWidgets);
    expect(find.text('synthetic_lung_case_001'), findsOneWidget);
  });

  testWidgets('patient dashboard renders seeded mobile state at 412x917', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
    );
    await pumpApp(tester, repository);

    expect(find.text('Today'), findsWidgets);
    expect(find.text('Demo medication reminder'), findsOneWidget);
    expect(
      find.byKey(const Key('patient-medication-notification-shell')),
      findsOneWidget,
    );
    expect(find.text('Contact Doctor'), findsOneWidget);
    expect(find.text('Medical Fee'), findsOneWidget);
    expect(find.text('Dashboard'), findsOneWidget);
    await tester.drag(
      find.byKey(const Key('patient-dashboard-list')),
      const Offset(0, -920),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('patient-self-records')), findsOneWidget);
    expect(
      find.byKey(const Key('patient-self-imaging-assets')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('patient-self-history-summary')),
      findsOneWidget,
    );
    expect(
      find.textContaining('Allergies: Synthetic pollen sensitivity'),
      findsOneWidget,
    );
    expect(
      find.textContaining('Diagnoses: Synthetic observation'),
      findsOneWidget,
    );
    await tester.dragUntilVisible(
      find.byKey(const Key('patient-event-update-title')),
      find.byKey(const Key('patient-dashboard-list')),
      const Offset(0, -420),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('patient-event-update-title')), findsOneWidget);
    final eventUpdateSubmitButton = find.byKey(
      const Key('patient-event-update-submit-button'),
    );
    await tester.ensureVisible(eventUpdateSubmitButton);
    await tester.pumpAndSettle();
    await tester.drag(
      find.byKey(const Key('patient-dashboard-list')),
      const Offset(0, -160),
    );
    await tester.pumpAndSettle();
    await tester.tap(eventUpdateSubmitButton);
    await tester.pumpAndSettle();
    expect(repository.clinicalEventUpdateSubmitted, isTrue);
    expect(find.textContaining('Update submitted'), findsWidgets);
    await tester.dragUntilVisible(
      find.byKey(const Key('patient-self-prescriptions')),
      find.byKey(const Key('patient-dashboard-list')),
      const Offset(0, -520),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('patient-self-prescriptions')), findsOneWidget);
    expect(find.textContaining('Refill reminder'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('patient can complete a Today recovery task', (tester) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
    );
    await pumpApp(tester, repository);

    expect(find.byKey(const Key('today-task-medication')), findsOneWidget);
    expect(
      find.byKey(const Key('patient-today-progress-summary')),
      findsOneWidget,
    );
    await tester.tap(find.byKey(const Key('today-task-medication')));
    await tester.pumpAndSettle();

    expect(repository.patientToday.tasks.first.isCompleted, isTrue);
    expect(find.byKey(const Key('today-task-medication')), findsOneWidget);
  });

  testWidgets('patient educational chat streams and clears after success', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
    );
    await pumpApp(tester, repository);

    await tester.dragUntilVisible(
      find.byKey(const Key('educational-chat-input')),
      find.byKey(const Key('patient-dashboard-list')),
      const Offset(0, -360),
    );
    await tester.enterText(
      find.byKey(const Key('educational-chat-input')),
      'What should I ask about the synthetic recovery plan?',
    );
    await tester.ensureVisible(
      find.byKey(const Key('educational-chat-send-button')),
    );
    await tester.tap(find.byKey(const Key('educational-chat-send-button')));
    await tester.pumpAndSettle();

    expect(repository.chatMessagesSent, 1);
    expect(
      repository.lastChatMessage,
      'What should I ask about the synthetic recovery plan?',
    );
    final container = ProviderScope.containerOf(
      tester.element(find.byType(DrAiApp)),
    );
    final chatState = container.read(educationalChatControllerProvider);
    expect(
      chatState.messages.last.content,
      contains('Prepare questions for your clinician'),
    );
    final input = tester.widget<TextField>(
      find.byKey(const Key('educational-chat-input')),
    );
    expect(input.controller?.text, isEmpty);
  });

  testWidgets('patient chat failure preserves typed question', (tester) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
      chatError: const ApiError(
        code: 'rate_limited',
        message: 'Educational chat is temporarily rate limited.',
        statusCode: 429,
      ),
    );
    await pumpApp(tester, repository);

    await tester.dragUntilVisible(
      find.byKey(const Key('educational-chat-input')),
      find.byKey(const Key('patient-dashboard-list')),
      const Offset(0, -360),
    );
    await tester.enterText(
      find.byKey(const Key('educational-chat-input')),
      'Keep this typed question after failure',
    );
    await tester.ensureVisible(
      find.byKey(const Key('educational-chat-send-button')),
    );
    await tester.tap(find.byKey(const Key('educational-chat-send-button')));
    await tester.pumpAndSettle();

    expect(find.textContaining('temporarily rate limited'), findsOneWidget);
    final input = tester.widget<TextField>(
      find.byKey(const Key('educational-chat-input')),
    );
    expect(input.controller?.text, 'Keep this typed question after failure');
  });

  testWidgets(
    'patient completion failure keeps local Today interaction visible',
    (tester) async {
      setViewport(tester, const Size(412, 917));
      final repository = FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
        completionError: const ApiError(
          code: 'service_unavailable',
          message: 'Completion sync failed.',
          statusCode: 503,
        ),
      );
      await pumpApp(tester, repository);

      await tester.tap(find.byKey(const Key('today-task-medication')));
      await tester.pumpAndSettle();

      expect(find.textContaining('Completion could not sync'), findsOneWidget);
      expect(find.byKey(const Key('today-task-medication')), findsOneWidget);
    },
  );

  testWidgets('doctor can request specialist consultation and read status', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1000));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester, section: 'consultationActivity');

    await tester.ensureVisible(
      find.byKey(const Key('consultation-request-button')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('consultation-request-button')));
    await tester.pumpAndSettle();

    expect(repository.consultations.items, isNotEmpty);
    expect(
      repository.consultations.items.first.clinicalEventId,
      'clinical-event-test-id',
    );
    expect(find.textContaining('consultation requested'), findsWidgets);
    expect(
      find.textContaining('Pulmonology demo review - requested'),
      findsWidgets,
    );
  });

  testWidgets('core controls expose accessible labels and disabled states', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    try {
      setViewport(tester, const Size(412, 917));
      await pumpApp(
        tester,
        FakeDrAiRepository(
          restoredSession: patientSession,
          loginSession: patientSession,
          dashboard: patientDashboard,
        ),
      );

      expect(
        find.bySemanticsLabel('See more recovery tasks unavailable in summary'),
        findsWidgets,
      );
      expect(
        find.bySemanticsLabel('Pay now unavailable in Week 1'),
        findsOneWidget,
      );
      expect(find.byTooltip('Sign out'), findsOneWidget);
    } finally {
      semantics.dispose();
    }
  });

  testWidgets('app shell exposes deterministic keyboard focus traversal', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    await pumpApp(tester, FakeDrAiRepository());

    expect(find.byType(FocusTraversalGroup), findsWidgets);
    await tester.tap(find.byKey(const Key('email-field')));
    await tester.pump();
    expect(FocusManager.instance.primaryFocus, isNotNull);
  });

  testWidgets('patient dashboard supports enlarged text on narrow mobile', (
    tester,
  ) async {
    tester.binding.platformDispatcher.textScaleFactorTestValue = 1.3;
    addTearDown(
      tester.binding.platformDispatcher.clearTextScaleFactorTestValue,
    );
    setViewport(tester, const Size(360, 780));
    await pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
      ),
    );

    expect(find.byKey(const Key('patient-dashboard-list')), findsOneWidget);
    expect(find.text('Today'), findsWidgets);
    for (var index = 0; index < 4; index++) {
      await tester.drag(
        find.byKey(const Key('patient-dashboard-list')),
        const Offset(0, -520),
      );
      await tester.pumpAndSettle();
    }
    expect(tester.takeException(), isNull);
  });

  testWidgets('dashboard network and empty states are explicit', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      restoredSession: doctorSession,
      dashboardError: const ApiError(
        code: 'service_unavailable',
        message: 'Unable to reach Dr. AI.',
        statusCode: 503,
      ),
    );
    await pumpApp(tester, repository);

    expect(find.byKey(const Key('dashboard-error')), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);

    repository.dashboardError = null;
    repository.dashboard = const DashboardData(
      role: AppRole.doctor,
      data: <String, dynamic>{},
    );
    final container = ProviderScope.containerOf(
      tester.element(find.byType(DrAiApp)),
    );
    container.invalidate(dashboardProvider);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('doctor-empty')), findsOneWidget);
  });
}
