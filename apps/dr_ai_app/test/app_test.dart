import 'dart:async';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
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

Future<void> revealPatientEducationalChat(WidgetTester tester) async {
  final dashboardScrollable = find
      .descendant(
        of: find.byKey(const Key('patient-dashboard-list')),
        matching: find.byType(Scrollable),
      )
      .first;
  final state = tester.state<ScrollableState>(dashboardScrollable);
  state.position.jumpTo(state.position.maxScrollExtent);
  await tester.pumpAndSettle();
  expect(
    find.byKey(const Key('educational-chat-message-list')),
    findsOneWidget,
  );
}

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues(<String, String>{});
  });

  test(
    'locale resolution supports Chinese and English with English fallback',
    () {
      expect(
        resolveDrAiLocale(const Locale('zh', 'CN'), const <Locale>[]),
        const Locale('zh'),
      );
      expect(
        resolveDrAiLocale(const Locale('en', 'GB'), const <Locale>[]),
        const Locale('en'),
      );
      expect(
        resolveDrAiLocale(const Locale('fr', 'FR'), const <Locale>[]),
        const Locale('en'),
      );
    },
  );

  test(
    'payer dashboard parsing supports escalated metric and old payloads',
    () {
      Map<String, dynamic> payload({int? escalated}) {
        final result = <String, dynamic>{
          'profile': <String, dynamic>{
            'membership_id': 'membership-id',
            'display_name': 'Synthetic Reviewer',
            'title': 'Reviewer',
            'status': 'active',
            'scope': 'synthetic_review',
            'organization': <String, dynamic>{
              'id': 'organization-id',
              'name': 'Synthetic Payer',
              'organization_type': 'public_payer',
              'jurisdiction_code': 'CN',
              'verification_status': 'synthetic_only',
            },
          },
          'open_requests': 12,
          'clarification_requests': 3,
          'completed_reviews': 9999,
          'pending_requested_total_minor': 987654321,
          'currency': 'CNY',
        };
        if (escalated != null) {
          result['escalated_requests'] = escalated;
        }
        return result;
      }

      expect(
        PayerDashboardData.fromJson(payload(escalated: 7)).escalatedRequests,
        7,
      );
      expect(PayerDashboardData.fromJson(payload()).escalatedRequests, 0);
    },
  );

  test('payer review parses clarification separately from private note', () {
    final review = PayerReviewData.fromJson(<String, dynamic>{
      'id': 'review-id',
      'action': 'request_clarification',
      'reason_code': 'documentation_needed',
      'clarification_message': 'Synthetic doctor-visible question.',
      'note': 'Synthetic payer-private note.',
      'reviewer_membership_id': 'membership-id',
      'reviewer_display_name': 'Synthetic Reviewer',
      'reviewer_title': 'Reviewer',
      'from_status': 'submitted',
      'to_status': 'clarification_requested',
      'version': 2,
      'created_at': '2026-08-13T00:00:00Z',
    });

    expect(review.clarificationMessage, 'Synthetic doctor-visible question.');
    expect(review.note, 'Synthetic payer-private note.');
  });

  test('production typography uses bundled bilingual font families', () {
    final bodyStyle = DrAiTheme.light.textTheme.bodyMedium!;

    expect(bodyStyle.fontFamily, 'Inter');
    expect(bodyStyle.fontFamilyFallback, contains('NotoSansSC'));
  });

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

    expect(
      find.text('Enter a valid email address or phone number.'),
      findsOneWidget,
    );
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
    expect(repository.lastLoginEmail, 'doctor.demo@example.com');

    completer.complete(doctorSession);
    await tester.pumpAndSettle();
    expect(find.text('Quick Access'), findsOneWidget);
    expect(find.text('Team Management'), findsOneWidget);
    expect(find.text('Dr. Avery Demo'), findsNothing);
  });

  testWidgets(
    'doctor navigation opens the dedicated payment request workspace',
    (tester) async {
      setViewport(tester, const Size(1280, 832));
      await pumpApp(tester, FakeDrAiRepository(restoredSession: doctorSession));

      await tester.tap(find.text('Payment requests').last);
      await tester.pumpAndSettle();

      expect(find.text('Payment Requests'), findsOneWidget);
      expect(find.text('New request'), findsOneWidget);
      expect(find.text('Request history'), findsOneWidget);
      expect(find.byKey(const Key('payment-request-patient-search')), findsOne);
    },
  );

  testWidgets('doctor request history opens request-scoped intelligence', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 900));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: doctorSession));

    await tester.tap(find.text('Payment requests').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Request history'));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('payment-request-history-payer-request-test-id')),
    );
    await tester.pumpAndSettle();
    final openReview = find.byKey(
      const Key('doctor-intelligence-payer-request-test-id'),
    );
    await tester.ensureVisible(openReview);
    await tester.tap(openReview);
    await tester.pumpAndSettle();

    expect(find.text('Clinical Event intelligence review'), findsOneWidget);
    expect(find.text('Acknowledge'), findsOneWidget);
    expect(find.text('Disagree'), findsOneWidget);
    expect(find.text('AI support score'), findsNWidgets(2));
    expect(find.text('Model-only exploratory estimate'), findsOneWidget);
    expect(find.text('Reject'), findsNothing);
    expect(
      GoRouter.of(
        tester.element(find.text('Clinical Event intelligence review')),
      ).routeInformationProvider.value.uri.path,
      '/doctor/payer-requests/payer-request-test-id/intelligence',
    );
  });

  testWidgets(
    'doctor request history separates accepted and rejected payer outcomes',
    (tester) async {
      setViewport(tester, const Size(1280, 832));
      final accepted = FakeDrAiRepository.payerRequestFixture(
        id: 'accepted-request-id',
        clinicalEventTitle: 'Accepted respiratory request',
        status: 'accepted',
        reviewedAt: DateTime(2026, 7, 24),
        reviews: <PayerReviewData>[
          PayerReviewData(
            id: 'accepted-review-id',
            action: 'accept',
            reasonCode: 'supported_request',
            createdAt: DateTime(2026, 7, 24),
          ),
        ],
      );
      final rejected = FakeDrAiRepository.payerRequestFixture(
        id: 'rejected-request-id',
        clinicalEventTitle: 'Rejected imaging request',
        status: 'rejected',
        reviewedAt: DateTime(2026, 7, 24),
        reviews: <PayerReviewData>[
          PayerReviewData(
            id: 'rejected-review-id',
            action: 'reject',
            reasonCode: 'unsupported_request',
            createdAt: DateTime(2026, 7, 24),
          ),
        ],
      );
      await pumpApp(
        tester,
        FakeDrAiRepository(
          restoredSession: doctorSession,
          payerRequests: <PayerRequestData>[accepted, rejected],
        ),
      );

      await tester.tap(find.text('Payment requests').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Request history'));
      await tester.pumpAndSettle();

      expect(find.text('Accepted respiratory request'), findsOneWidget);
      expect(find.text('Rejected imaging request'), findsOneWidget);

      await tester.tap(
        find.byKey(const Key('payment-request-filter-accepted')),
      );
      await tester.pumpAndSettle();
      expect(find.text('Accepted respiratory request'), findsOneWidget);
      expect(find.text('Rejected imaging request'), findsNothing);
      await tester.tap(
        find.byKey(const Key('payment-request-history-accepted-request-id')),
      );
      await tester.pumpAndSettle();
      expect(find.text('Accepted by payer reviewer'), findsOneWidget);
      expect(
        find.textContaining('does not guarantee reimbursement or payment'),
        findsOneWidget,
      );

      await tester.tap(
        find.byKey(const Key('payment-request-filter-rejected')),
      );
      await tester.pumpAndSettle();
      expect(find.text('Accepted respiratory request'), findsNothing);
      expect(find.text('Rejected imaging request'), findsOneWidget);
      await tester.tap(
        find.byKey(const Key('payment-request-history-rejected-request-id')),
      );
      await tester.pumpAndSettle();
      expect(find.text('Rejected by payer reviewer'), findsOneWidget);
      expect(
        find.textContaining('is not a final adjudicated patient obligation'),
        findsOneWidget,
      );
      expect(find.textContaining('reviewer-only'), findsNothing);
    },
  );

  testWidgets(
    'doctor history shows clarification but never the payer-private note',
    (tester) async {
      setViewport(tester, const Size(1280, 900));
      final request = FakeDrAiRepository.payerRequestFixture(
        status: 'clarification_requested',
        reviewedAt: DateTime(2026, 8, 13),
        reviews: <PayerReviewData>[
          PayerReviewData(
            id: 'clarification-review-id',
            action: 'request_clarification',
            reasonCode: 'documentation_needed',
            clarificationMessage:
                'Please provide the synthetic dated service record.',
            note: 'SYNTHETIC PRIVATE REVIEW NOTE 8457',
            reviewerDisplayName: 'Lin Reviewer',
            reviewerTitle: 'Medical expenditure reviewer',
            fromStatus: 'submitted',
            toStatus: 'clarification_requested',
            createdAt: DateTime(2026, 8, 13),
          ),
        ],
      );
      await pumpApp(
        tester,
        FakeDrAiRepository(
          restoredSession: doctorSession,
          payerRequests: <PayerRequestData>[request],
        ),
      );

      await tester.tap(find.text('Payment requests').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Request history'));
      await tester.pumpAndSettle();
      await tester.tap(
        find.byKey(const Key('payment-request-history-payer-request-test-id')),
      );
      await tester.pumpAndSettle();

      expect(find.text('Payer clarification request'), findsWidgets);
      expect(
        find.text('Please provide the synthetic dated service record.'),
        findsWidgets,
      );
      expect(find.text('SYNTHETIC PRIVATE REVIEW NOTE 8457'), findsNothing);
      expect(find.text('Add justification or response'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'doctor explicitly selects items and confirms an immutable payment request',
    (tester) async {
      setViewport(tester, const Size(1280, 832));
      final repository = FakeDrAiRepository(
        restoredSession: doctorSession,
        payerRequests: const <PayerRequestData>[],
      );
      await pumpApp(tester, repository);

      await tester.tap(find.text('Payment requests').last);
      await tester.pumpAndSettle();
      await tester.tap(
        find.byKey(
          const Key('payment-request-patient-patient-profile-test-id'),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(
        find.byKey(const Key('payment-request-event-clinical-event-test-id')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('payment-request-continue')));
      await tester.pumpAndSettle();

      await tester.tap(
        find.byKey(const Key('payment-request-item-care-cost-item-test-id')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('payment-request-continue')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('payment-request-payer')));
      await tester.pumpAndSettle();
      await tester.tap(
        find.text('Synthetic Municipal Medical Insurance · Public payer').last,
      );
      await tester.enterText(
        find.byKey(const Key('payment-request-summary')),
        'Doctor-authored clinical context for the selected services.',
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('payment-request-continue')));
      await tester.pumpAndSettle();

      final confirmation = find.byKey(
        const Key('payment-request-confirmation'),
      );
      await tester.ensureVisible(confirmation);
      await tester.tap(confirmation);
      await tester.pumpAndSettle();
      final submit = find.byKey(const Key('payment-request-submit'));
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pumpAndSettle();

      expect(repository.payerRequestCreated, isTrue);
      expect(repository.lastPayerRequestItemIds, const <String>[
        'care-cost-item-test-id',
      ]);
      expect(find.byKey(const Key('payment-request-success')), findsOneWidget);
      expect(find.textContaining('¥500.00'), findsWidgets);
    },
  );

  testWidgets(
    'login prefixes local phone numbers with the selected country code',
    (tester) async {
      final repository = FakeDrAiRepository();
      await pumpApp(tester, repository);

      expect(find.byKey(const Key('login-country-code-field')), findsOneWidget);
      await tester.enterText(
        find.byKey(const Key('email-field')),
        '13718339230',
      );
      await tester.enterText(
        find.byKey(const Key('password-field')),
        'test-only password',
      );
      await tester.tap(find.byKey(const Key('login-button')));
      await tester.pumpAndSettle();

      expect(repository.lastLoginEmail, '+8613718339230');
      expect(repository.lastLoginPassword, 'test-only password');
    },
  );

  testWidgets(
    'phone registration routes a new patient through medical intake',
    (tester) async {
      setViewport(tester, const Size(412, 917));
      final repository = FakeDrAiRepository(
        dashboard: const DashboardData(
          role: AppRole.patient,
          data: <String, Object>{},
        ),
        patientCareBundle: incompleteOnboardingPatientCareBundle,
      );
      await pumpApp(tester, repository);

      await tester.tap(find.byKey(const Key('auth-mode-toggle')));
      await tester.pumpAndSettle();
      expect(find.text('Create your account'), findsOneWidget);
      expect(find.byKey(const Key('register-role-selector')), findsOneWidget);

      await tester.enterText(
        find.byKey(const Key('signup-phone-field')),
        '13800012345',
      );
      await tester.tap(find.byKey(const Key('registration-send-code-button')));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('registration-code-status')), findsOneWidget);
      await tester.enterText(
        find.byKey(const Key('signup-email-field')),
        'new.patient@example.com',
      );
      await tester.enterText(
        find.byKey(const Key('password-field')),
        'Patient9!',
      );
      await tester.enterText(
        find.byKey(const Key('confirm-password-field')),
        'Patient9!',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.byKey(const Key('verification-code-field')),
            )
            .controller!
            .text,
        '123456',
      );
      await tester.enterText(
        find.byKey(const Key('signup-first-name-field')),
        '小明',
      );
      await tester.enterText(
        find.byKey(const Key('signup-last-name-field')),
        '王',
      );
      await tester.ensureVisible(
        find.byKey(const Key('signup-home-address-field')),
      );
      await tester.enterText(
        find.byKey(const Key('signup-home-address-field')),
        '100 Recovery Road',
      );
      await tester.ensureVisible(find.byKey(const Key('terms-checkbox')));
      await tester.tap(find.byKey(const Key('terms-checkbox')));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byKey(const Key('login-button')));
      await tester.tap(find.byKey(const Key('login-button')));
      await tester.pumpAndSettle();

      expect(repository.registerCalled, isTrue);
      expect(find.byKey(const Key('patient-onboarding-list')), findsOneWidget);
      await tester.enterText(
        find.byKey(const Key('onboarding-name-field')),
        '曹',
      );
      await tester.dragUntilVisible(
        find.byKey(const Key('onboarding-height-field')),
        find.byKey(const Key('patient-onboarding-list')),
        const Offset(0, -360),
      );
      await tester.enterText(
        find.byKey(const Key('onboarding-height-field')),
        '168',
      );
      await tester.enterText(
        find.byKey(const Key('onboarding-weight-field')),
        '62',
      );
      for (var index = 0; index < 5; index++) {
        await tester.drag(
          find.byKey(const Key('patient-onboarding-list')),
          const Offset(0, -700),
        );
        await tester.pumpAndSettle();
      }
      await tester.tap(find.byKey(const Key('patient-onboarding-submit')));
      await tester.pumpAndSettle();
      expect(repository.patientProfileUpdated, isTrue);
      expect(find.byKey(const Key('patient-dashboard-list')), findsOneWidget);
    },
  );

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

  testWidgets('forgot password verifies phone and resets credentials', (
    tester,
  ) async {
    setViewport(tester, const Size(620, 900));
    final repository = FakeDrAiRepository();
    await pumpApp(tester, repository);

    await tester.tap(find.byKey(const Key('forgot-password-button')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('forgot-password-phone-field')),
      '13800010002',
    );
    await tester.tap(find.byKey(const Key('forgot-password-send-code')));
    await tester.pumpAndSettle();

    expect(
      tester
          .widget<TextFormField>(
            find.byKey(const Key('forgot-password-code-field')),
          )
          .controller!
          .text,
      '123456',
    );
    await tester.enterText(
      find.byKey(const Key('forgot-password-new-field')),
      'UpdatedPatient9!',
    );
    await tester.enterText(
      find.byKey(const Key('forgot-password-confirm-field')),
      'UpdatedPatient9!',
    );
    await tester.tap(find.byKey(const Key('forgot-password-reset')));
    await tester.pumpAndSettle();

    expect(repository.passwordReset, isTrue);
    expect(find.text('Password updated'), findsOneWidget);
  });

  testWidgets('doctor account changes password and signs out all sessions', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1000));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);

    await tester.tap(find.text('Account').last);
    await tester.pumpAndSettle();
    await tester.dragUntilVisible(
      find.byKey(const Key('doctor-account-change-password-button')),
      find.byKey(const Key('doctor-account-list')),
      const Offset(0, -360),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('doctor-account-change-password-button')),
    );
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('doctor-account-current-password-field')),
      'CurrentDoctor9!',
    );
    await tester.enterText(
      find.byKey(const Key('doctor-account-new-password-field')),
      'UpdatedDoctor9!',
    );
    await tester.enterText(
      find.byKey(const Key('doctor-account-confirm-password-field')),
      'UpdatedDoctor9!',
    );
    await tester.tap(
      find.byKey(const Key('doctor-account-change-password-confirm')),
    );
    await tester.pumpAndSettle();

    expect(repository.passwordChanged, isTrue);
    expect(repository.logoutCalled, isTrue);
    expect(find.text('Welcome to Dr. AI'), findsOneWidget);
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

    expect(find.text('Today'), findsWidgets);
    expect(find.text('My Account'), findsWidgets);
    expect(find.text('Care & Costs summary'), findsOneWidget);
  });

  testWidgets('patient account keeps language changes inside profile editing', (
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

    await tester.tap(find.text('My Account'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('interface-language-field')), findsNothing);
    await tester.ensureVisible(
      find.byKey(const Key('patient-account-edit-profile-button')),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('patient-account-edit-profile-button')),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('onboarding-language-field')), findsOneWidget);
    expect(find.text('My Account'), findsWidgets);
  });

  testWidgets(
    'patient account normalizes exact legacy female value without dropdown assertion',
    (tester) async {
      setViewport(tester, const Size(412, 917));
      final repository = FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
      )..patientCareBundle = patientCareBundleWithLegacyGender('female');
      await pumpApp(tester, repository);

      await tester.tap(find.text('My Account'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(
        find.byKey(const Key('patient-account-edit-profile-button')),
      );
      await tester.pumpAndSettle();
      await tester.tap(
        find.byKey(const Key('patient-account-edit-profile-button')),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('onboarding-gender-field')), findsOneWidget);
      expect(tester.takeException(), isNull);
      final field = tester.widget<DropdownButtonFormField<String>>(
        find.byKey(const Key('onboarding-gender-field')),
      );
      expect(field.initialValue, 'female');
    },
  );

  testWidgets('logout clears the session and returns to sign in', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);

    await tester.tap(find.text('Account').last);
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const Key('account-sign-out-button')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('account-sign-out-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('sign-out-confirm-button')));
    await tester.pumpAndSettle();

    expect(repository.logoutCalled, isTrue);
    expect(find.text('Welcome to Dr. AI'), findsOneWidget);
    expect(find.byKey(const Key('login-notice')), findsOneWidget);
    expect(find.text('You have signed out.'), findsOneWidget);
    await tester.pump(const Duration(seconds: 2));
    await tester.pump();
    expect(find.byKey(const Key('login-notice')), findsNothing);
  });

  testWidgets('auth feedback does not carry from sign in to registration', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      loginError: const ApiError(
        code: 'unauthenticated',
        message: 'Invalid credentials.',
        statusCode: 401,
      ),
    );
    await pumpApp(tester, repository);
    await tester.enterText(
      find.byKey(const Key('email-field')),
      'patient@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('password-field')),
      'incorrect password',
    );
    await tester.tap(find.byKey(const Key('login-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('login-error')), findsOneWidget);

    await tester.tap(find.byKey(const Key('auth-mode-toggle')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('register-role-selector')), findsOneWidget);
    expect(find.byKey(const Key('login-error')), findsNothing);
  });

  testWidgets('patient contacts show services and multiple doctors', (
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

    await tester.tap(find.text('Contacts'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('patient-contact-list')), findsOneWidget);
    expect(find.byKey(const Key('system-contact')), findsOneWidget);
    expect(find.byKey(const Key('dr-ai-contact')), findsOneWidget);
    expect(
      find.byKey(const Key('doctor-contact-doctor-profile-test-id')),
      findsOneWidget,
    );
    expect(find.text('2'), findsOneWidget);
    await tester.dragUntilVisible(
      find.byKey(const Key('doctor-contact-doctor-profile-test-id-2')),
      find.byKey(const Key('patient-contact-list')),
      const Offset(0, -220),
    );
    expect(
      find.byKey(const Key('doctor-contact-doctor-profile-test-id-2')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('group-contact-placeholder')), findsNothing);
  });

  testWidgets('patient controls pending and active doctor relationships', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 1100));
    const contacts = PatientDoctorContactList(
      items: <PatientDoctorContact>[
        PatientDoctorContact(
          doctorId: 'pending-doctor',
          displayName: 'Dr. Pending Review',
          title: 'Synthetic doctor',
          hospitalName: 'Synthetic Hospital',
          specialty: null,
          department: null,
          avatarUrl: null,
          relationshipId: 'pending-relationship',
          relationshipStatus: 'pending_patient_approval',
        ),
        PatientDoctorContact(
          doctorId: 'active-doctor',
          displayName: 'Dr. Active Connection',
          title: 'Synthetic doctor',
          hospitalName: 'Synthetic Hospital',
          specialty: null,
          department: null,
          avatarUrl: null,
          relationshipId: 'active-relationship',
        ),
      ],
    );
    await pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        dashboard: patientDashboard,
        patientDoctorContacts: contacts,
      ),
    );

    await tester.tap(find.text('Contacts'));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('approve-doctor-pending-doctor')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('reject-doctor-pending-doctor')),
      findsOneWidget,
    );
    expect(find.text('Pending approval'), findsOneWidget);
    await tester.dragUntilVisible(
      find.byKey(const Key('remove-doctor-active-doctor')),
      find.byKey(const Key('patient-contact-list')),
      const Offset(0, -220),
    );
    expect(
      find.byKey(const Key('remove-doctor-active-doctor')),
      findsOneWidget,
    );
  });

  testWidgets('patient AI chat keeps the conversation in the current session', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
    );
    await pumpApp(tester, repository);

    await tester.tap(find.text('Contacts'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('dr-ai-contact')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('patient-ai-input')), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('patient-ai-input')),
      'What should I understand about recording blood pressure?',
    );
    await tester.tap(find.byKey(const Key('patient-ai-send')));
    await tester.pumpAndSettle();

    expect(repository.chatMessagesSent, 1);
    expect(find.byKey(const Key('patient-ai-message-list')), findsOneWidget);
    expect(find.textContaining('Prepare questions'), findsOneWidget);
    expect(find.text('Personalized with your records'), findsOneWidget);
    expect(
      find.textContaining('Health measurements · Your profile records'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('patient-ai-uncertainty')), findsOneWidget);
    expect(find.text('Important uncertainty'), findsOneWidget);
    expect(
      find.byKey(const Key('patient-ai-grounding-approved_evidence')),
      findsOneWidget,
    );
  });

  testWidgets('patient AI chat history remains usable at mobile width', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
    );
    await pumpApp(tester, repository);

    await tester.tap(find.text('Contacts'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('dr-ai-contact')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('patient-ai-history-toggle')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('patient-ai-thread-sidebar')), findsOneWidget);
    expect(find.byKey(const Key('patient-ai-input')), findsNothing);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(const Key('patient-ai-new-chat-sidebar')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('patient-ai-thread-sidebar')), findsNothing);
    expect(find.byKey(const Key('patient-ai-input')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  test(
    'patient RAG response parses reviewed source cards and fallback state',
    () {
      final result = ChatMessageResult.fromJson(<String, dynamic>{
        'request_id': 'req-test',
        'session_id': 'session-test',
        'answer_sections': <String>['Reviewed educational answer.'],
        'safety_code': 'permitted_education',
        'emergency': false,
        'fallback_code': null,
        'model_version': 'deepseek-v4-flash',
        'limitation': 'Educational only.',
        'next_action_code': 'contact_connected_doctor',
        'sources': <Map<String, dynamic>>[
          <String, dynamic>{
            'number': 1,
            'passage_id': 'passage-1',
            'title': 'Reviewed source',
            'publisher': 'Health authority',
            'official_locator': 'https://example.invalid/source',
            'publication_date': '2026-01-01',
            'last_medical_review_date': '2026-07-16',
          },
        ],
        'context_used': <Map<String, dynamic>>[
          <String, dynamic>{
            'category': 'measurements',
            'provenance': 'patient_profile',
            'recorded_on': '2026-07-16',
          },
        ],
        'uncertainties': <String>['Important context is missing.'],
      });

      expect(result.content, 'Reviewed educational answer.');
      expect(result.groundingMode, 'approved_evidence');
      expect(result.sources.single.title, 'Reviewed source');
      expect(result.contextUsed.single.category, 'measurements');
      expect(result.nextActionCode, 'contact_connected_doctor');
      expect(result.uncertainties, <String>['Important context is missing.']);
    },
  );

  testWidgets('patient AI chat labels general knowledge without sources', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
      chatResult: ChatMessageResult(
        threadId: 'general-thread',
        threadKey: 'patient-rag',
        messageId: 'general-request',
        assistantMessageId: 'general-request',
        content: 'General information without a reviewed source.',
        responseChunks: const <String>[
          'General information without a reviewed source.',
        ],
        safetyLabel: 'permitted_education',
        isRedFlag: false,
        model: 'general-ai',
        createdAt: DateTime(2026, 7, 24),
        groundingMode: 'general_model_knowledge',
        possibleCauses: const <ChatPossibleCause>[
          ChatPossibleCause(
            name: 'Viral irritation',
            explanation: 'A common possible explanation.',
            status: 'possible_not_confirmed',
          ),
          ChatPossibleCause(
            name: 'Dry air',
            explanation: 'Dryness can irritate the throat.',
            status: 'possible_not_confirmed',
          ),
          ChatPossibleCause(
            name: 'Bacterial infection',
            explanation: 'An important alternative for assessment.',
            status: 'possible_not_confirmed',
          ),
        ],
        warningSigns: const <String>[
          'Difficulty breathing or swallowing saliva',
        ],
        nextSteps: const <String>[
          'Drink fluids and arrange care if symptoms persist.',
        ],
        limitation:
            'General AI-generated information without a supporting Dr. AI source.',
        nextActionCode: 'contact_connected_doctor',
      ),
    );
    await pumpApp(tester, repository);

    await tester.tap(find.text('Contacts'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('dr-ai-contact')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('patient-ai-input')),
      'Explain photosynthesis briefly.',
    );
    await tester.tap(find.byKey(const Key('patient-ai-send')));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('patient-ai-grounding-general_model_knowledge')),
      findsOneWidget,
    );
    expect(
      find.text(
        'General AI-generated information — no supporting Dr. AI source was found.',
      ),
      findsOneWidget,
    );
    expect(find.text('Reviewed sources'), findsNothing);
    expect(find.byKey(const Key('patient-ai-possible-causes')), findsOneWidget);
    expect(find.text('Possible causes'), findsOneWidget);
    expect(
      find.text('These are possibilities, not a confirmed diagnosis.'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('patient-ai-warning-signs')), findsOneWidget);
    expect(find.byKey(const Key('patient-ai-next-steps')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('patient AI emergency renders only the primary call action', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
      chatResult: ChatMessageResult(
        threadId: 'emergency-thread',
        threadKey: 'patient-rag',
        messageId: 'emergency-request',
        assistantMessageId: 'emergency-request',
        content: 'Call 120 now. Do not drive yourself.',
        responseChunks: const <String>['Call 120 now. Do not drive yourself.'],
        safetyLabel: 'emergency',
        emergencyLabel: 'emergency',
        isRedFlag: true,
        model: 'fixed-safety-response',
        createdAt: DateTime(2026, 8, 13),
        suggestedActionCodes: const <String>['call_120'],
        nextActionCode: 'call_120',
      ),
    );
    await pumpApp(tester, repository);

    await tester.tap(find.text('Contacts'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('dr-ai-contact')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('patient-ai-input')),
      'Synthetic emergency test',
    );
    await tester.tap(find.byKey(const Key('patient-ai-send')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('patient-ai-call-120')), findsOneWidget);
    expect(find.text('Call 120 now'), findsOneWidget);
    expect(find.text('Contact my doctor'), findsNothing);
    expect(find.text('Organize my symptoms'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('legal pages return to the registration page', (tester) async {
    final router = createRouter(null, initialLocation: '/terms');
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [repositoryProvider.overrideWithValue(FakeDrAiRepository())],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Terms of Service'), findsOneWidget);

    await tester.ensureVisible(find.text('Back to registration'));
    await tester.tap(find.text('Back to registration'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('register-role-selector')), findsOneWidget);
  });

  testWidgets(
    'logout still gives local feedback when the server is unreachable',
    (tester) async {
      final repository = FakeDrAiRepository(
        restoredSession: doctorSession,
        logoutError: Exception('network unavailable'),
      );
      await pumpApp(tester, repository);

      await tester.tap(find.text('Account').last);
      await tester.pumpAndSettle();
      await tester.ensureVisible(
        find.byKey(const Key('account-sign-out-button')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('account-sign-out-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('sign-out-confirm-button')));
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

  testWidgets(
    'public privacy surface is read-only and routes requests to Account',
    (tester) async {
      setViewport(tester, const Size(412, 917));
      await pumpApp(tester, FakeDrAiRepository());

      await tester.tap(find.byKey(const Key('login-privacy-support-link')));
      await tester.pumpAndSettle();

      expect(find.text('Privacy and support'), findsOneWidget);
      expect(find.byKey(const Key('beta-privacy-section')), findsOneWidget);

      await tester.dragUntilVisible(
        find.byKey(const Key('beta-consent-section')),
        find.byKey(const Key('beta-support-list')),
        const Offset(0, -360),
      );
      expect(find.byKey(const Key('beta-consent-section')), findsOneWidget);

      expect(find.byType(Checkbox), findsNothing);
      expect(find.byKey(const Key('account-request-submit')), findsNothing);
      expect(find.textContaining('Sign in and open Account'), findsOneWidget);

      await tester.dragUntilVisible(
        find.byKey(const Key('beta-limitations-section')),
        find.byKey(const Key('beta-support-list')),
        const Offset(0, -520),
      );
      expect(find.byKey(const Key('beta-limitations-section')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('privacy support route is public from a direct web path', (
    tester,
  ) async {
    final router = createRouter(null);
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(child: MaterialApp.router(routerConfig: router)),
    );

    router.go('/privacy');
    await tester.pumpAndSettle();

    expect(find.text('Privacy and support'), findsOneWidget);
    expect(find.byKey(const Key('beta-support-list')), findsOneWidget);
  });

  testWidgets('legacy beta support route redirects to privacy support', (
    tester,
  ) async {
    final router = createRouter(null);
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(child: MaterialApp.router(routerConfig: router)),
    );

    router.go('/beta-support');
    await tester.pumpAndSettle();

    expect(find.text('Privacy and support'), findsOneWidget);
    expect(find.byKey(const Key('beta-support-list')), findsOneWidget);
  });

  testWidgets('patient role cannot navigate to doctor-only resources', (
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

    router.go('/doctor/resources/KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE/read');
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

    expect(find.text('Synthetic Community Hospital'), findsNothing);
    expect(find.text('Quick Access'), findsOneWidget);
    expect(find.text('Recent Activities'), findsOneWidget);
    expect(find.text('Resource Overview'), findsOneWidget);
    expect(find.text('Team Management'), findsOneWidget);
    expect(
      find.byKey(const Key('doctor-panel-Team Management')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('doctor-panel-Quick Access')), findsOneWidget);
    expect(
      find.byKey(const Key('doctor-panel-Resource Overview')),
      findsOneWidget,
    );
    expect(find.byIcon(Icons.logout), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('doctor account saves real profile fields without fake metrics', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1300));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);

    await tester.tap(find.text('Account').last);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('doctor-account-list')), findsOneWidget);
    expect(find.text('Doctor Account'), findsOneWidget);
    expect(find.text('Rating'), findsNothing);
    expect(find.textContaining('Experience'), findsNothing);
    expect(find.text('License number'), findsNothing);
    expect(find.text('Two-factor authentication'), findsNothing);

    await tester.enterText(
      find.byKey(const Key('doctor-account-specialty-field')),
      'Cardiology',
    );
    await tester.enterText(
      find.byKey(const Key('doctor-account-email-field')),
      'doctor.updated@example.com',
    );
    await tester.tap(find.byKey(const Key('doctor-account-save-button')));
    await tester.pumpAndSettle();

    expect(repository.doctorProfileUpdated, isTrue);
    expect(repository.accountEmailUpdated, isTrue);
    expect(
      find.byKey(const Key('doctor-account-hospital-field')),
      findsNothing,
    );
    expect(
      find.byKey(
        const Key('doctor-account-hospital-read-only'),
        skipOffstage: false,
      ),
      findsOneWidget,
    );
    expect(find.text('Account changes saved.'), findsOneWidget);
  });

  testWidgets('doctor account accepts an empty optional email', (tester) async {
    setViewport(tester, const Size(1280, 1300));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);

    await tester.tap(find.text('Account').last);
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('doctor-account-email-field')),
      '',
    );
    await tester.tap(find.byKey(const Key('doctor-account-save-button')));
    await tester.pumpAndSettle();

    expect(repository.accountEmailUpdated, isTrue);
    expect(find.text('Account changes saved.'), findsOneWidget);
  });

  testWidgets('payer reviewer can record an explicit rejection outcome', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: payerSession));

    await tester.tap(find.text('Review queue'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Record human review'));
    await tester.pumpAndSettle();
    expect(find.text('Documentation needed'), findsOneWidget);
    expect(find.textContaining('documentation_needed'), findsNothing);
    await tester.tap(find.byKey(const Key('payer-review-action')));
    await tester.pumpAndSettle();

    expect(find.text('Accept request'), findsOneWidget);
    expect(find.text('Reject request'), findsOneWidget);
  });

  testWidgets(
    'payer clarification separates doctor-visible content from private notes',
    (tester) async {
      setViewport(tester, const Size(1280, 900));
      final repository = FakeDrAiRepository(restoredSession: payerSession);
      await pumpApp(tester, repository);

      await tester.tap(find.text('Review queue'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Record human review'));
      await tester.pumpAndSettle();

      expect(
        find.text('Question or information needed from the doctor'),
        findsOneWidget,
      );
      expect(
        find.text('Internal payer note (optional — not shared with doctor)'),
        findsOneWidget,
      );
      await tester.tap(find.byKey(const Key('payer-review-submit')));
      await tester.pumpAndSettle();
      expect(repository.payerReviewCallCount, 0);
      expect(
        find.text('Tell the doctor what information is needed.'),
        findsOneWidget,
      );
      final clarificationInput = tester.widget<EditableText>(
        find.descendant(
          of: find.byKey(const Key('payer-clarification-message')),
          matching: find.byType(EditableText),
        ),
      );
      expect(clarificationInput.focusNode.hasFocus, isTrue);

      await tester.enterText(
        find.byKey(const Key('payer-clarification-message')),
        'Please provide the synthetic dated service record.',
      );
      await tester.enterText(
        find.byKey(const Key('payer-private-note')),
        'SYNTHETIC PRIVATE REVIEW NOTE 8457',
      );
      await tester.tap(find.byKey(const Key('payer-review-submit')));
      await tester.pumpAndSettle();

      expect(repository.payerReviewCallCount, 1);
      expect(
        repository.lastPayerClarificationMessage,
        'Please provide the synthetic dated service record.',
      );
      expect(
        repository.lastPayerPrivateNote,
        'SYNTHETIC PRIVATE REVIEW NOTE 8457',
      );
    },
  );

  testWidgets(
    'payer clarification validation and privacy labels render in Chinese',
    (tester) async {
      setViewport(tester, const Size(412, 917));
      FlutterSecureStorage.setMockInitialValues(<String, String>{
        'dr_ai_interface_locale': 'zh_Hans',
      });
      final repository = FakeDrAiRepository(restoredSession: payerSession);
      await pumpApp(tester, repository);

      await tester.tap(find.text('审核队列'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('记录人工审核'));
      await tester.pumpAndSettle();
      expect(find.text('需要医生回答的问题或补充的信息'), findsOneWidget);
      expect(find.text('支付方内部备注（可选——不与医生共享）'), findsOneWidget);
      await tester.tap(find.byKey(const Key('payer-review-submit')));
      await tester.pumpAndSettle();
      expect(find.text('请说明需要医生补充的信息。'), findsOneWidget);
      expect(repository.payerReviewCallCount, 0);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('payer dashboard displays escalated workload on mobile', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: payerSession));

    expect(find.text('Escalated'), findsOneWidget);
    expect(find.text('1'), findsWidgets);
    expect(find.text('Open requests'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('patient payer status opens request-scoped intelligence', (
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

    await tester.tap(find.text('Care & costs'));
    await tester.pumpAndSettle();
    final openRange = find.byKey(
      const Key('patient-intelligence-payer-request-test-id'),
    );
    await tester.dragUntilVisible(
      openRange,
      find.byKey(const Key('care-cost-ledger-list')),
      const Offset(0, -260),
    );
    tester.widget<ListTile>(openRange).onTap!();
    await tester.pumpAndSettle();

    expect(find.text('Your care and cost intelligence'), findsOneWidget);
    expect(find.text('AI support score'), findsNWidgets(2));
    expect(find.textContaining('never approve'), findsOneWidget);
    expect(
      GoRouter.of(
        tester.element(find.text('Your care and cost intelligence')),
      ).routeInformationProvider.value.uri.path,
      '/patient/payer-requests/payer-request-test-id/intelligence',
    );
  });

  testWidgets('payer request opens authorized request intelligence', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 900));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: payerSession));

    await tester.tap(find.text('Review queue'));
    await tester.pumpAndSettle();
    final openEvidence = find.byKey(
      const Key('payer-intelligence-payer-request-test-id'),
    );
    await tester.ensureVisible(openEvidence);
    await tester.tap(openEvidence);
    await tester.pumpAndSettle();

    expect(find.text('Authorized request intelligence'), findsOneWidget);
    expect(find.text('Human review'), findsWidgets);
    expect(find.text('AI support score'), findsNWidgets(2));
    expect(find.text('Model-only exploratory estimate'), findsOneWidget);
    expect(find.textContaining('payer-request-test-id'), findsNothing);
    expect(find.textContaining('validated_baseline_published'), findsNothing);
    expect(
      GoRouter.of(
        tester.element(find.text('Authorized request intelligence')),
      ).routeInformationProvider.value.uri.path,
      '/payer/requests/payer-request-test-id/intelligence',
    );
  });

  testWidgets(
    'payer account separates editable reviewer identity from governed access',
    (tester) async {
      setViewport(tester, const Size(1280, 1100));
      final repository = FakeDrAiRepository(restoredSession: payerSession);
      await pumpApp(tester, repository);

      await tester.tap(find.text('Account').last);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('payer-account-list')), findsOneWidget);
      expect(find.text('Payer Account'), findsOneWidget);
      expect(find.text('Reviewer profile'), findsOneWidget);
      expect(find.text('Organization & access'), findsOneWidget);
      expect(
        find.text('Synthetic Municipal Medical Insurance'),
        findsOneWidget,
      );
      expect(find.text('Public payer'), findsOneWidget);
      expect(find.text('Synthetic review'), findsOneWidget);
      expect(find.text('Synthetic-only'), findsOneWidget);
      expect(
        find.textContaining('Only an authorized administrator'),
        findsOneWidget,
      );
      expect(
        find.byKey(const Key('payer-account-change-password-button')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('account-sign-out-button')), findsOneWidget);
      expect(
        find.byKey(const Key('payer-account-organization-field')),
        findsNothing,
      );

      await tester.tap(find.byKey(const Key('payer-account-save-button')));
      await tester.pumpAndSettle();
      expect(repository.payerProfileUpdated, isFalse);
      expect(repository.accountEmailUpdated, isFalse);
      expect(find.text('No account changes to save.'), findsOneWidget);

      await tester.enterText(
        find.byKey(const Key('payer-account-display-name-field')),
        'Mei Reviewer',
      );
      await tester.enterText(
        find.byKey(const Key('payer-account-title-field')),
        'Senior expenditure reviewer',
      );
      await tester.enterText(
        find.byKey(const Key('payer-account-email-field')),
        'mei.reviewer@example.com',
      );
      await tester.tap(find.byKey(const Key('payer-account-save-button')));
      await tester.pumpAndSettle();

      expect(repository.payerProfileUpdated, isTrue);
      expect(repository.accountEmailUpdated, isTrue);
      expect(repository.payerProfileLoadCount, greaterThan(1));
      expect(find.text('Account changes saved.'), findsOneWidget);
      expect(find.text('Mei Reviewer'), findsWidgets);
    },
  );

  testWidgets(
    'payer account preserves entered values after a recoverable email conflict',
    (tester) async {
      setViewport(tester, const Size(1280, 1100));
      final repository = FakeDrAiRepository(
        restoredSession: payerSession,
        accountEmailError: const ApiError(
          code: 'email_already_in_use',
          message: 'An account already uses this email address.',
          statusCode: 409,
        ),
      );
      await pumpApp(tester, repository);
      await tester.tap(find.text('Account').last);
      await tester.pumpAndSettle();

      await tester.enterText(
        find.byKey(const Key('payer-account-display-name-field')),
        'Mei Reviewer',
      );
      await tester.enterText(
        find.byKey(const Key('payer-account-email-field')),
        'conflict@example.com',
      );
      await tester.tap(find.byKey(const Key('payer-account-save-button')));
      await tester.pumpAndSettle();

      expect(repository.payerProfileUpdateCount, 1);
      expect(
        tester
            .widget<TextFormField>(
              find.byKey(const Key('payer-account-display-name-field')),
            )
            .controller
            ?.text,
        'Mei Reviewer',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.byKey(const Key('payer-account-email-field')),
            )
            .controller
            ?.text,
        'conflict@example.com',
      );
      expect(
        find.textContaining('already linked to another account'),
        findsOneWidget,
      );

      repository.accountEmailError = null;
      await tester.enterText(
        find.byKey(const Key('payer-account-email-field')),
        'mei.reviewer@example.com',
      );
      await tester.tap(find.byKey(const Key('payer-account-save-button')));
      await tester.pumpAndSettle();

      expect(repository.payerProfileUpdateCount, 1);
      expect(find.text('Account changes saved.'), findsOneWidget);
    },
  );

  testWidgets('payer account remains usable at a narrow mobile width', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: payerSession));

    await tester.tap(find.text('Account').last);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('payer-account-list')), findsOneWidget);
    expect(
      find.byKey(const Key('payer-account-identity-card')),
      findsOneWidget,
    );
    await tester.ensureVisible(
      find.byKey(const Key('payer-account-governance-card')),
    );
    await tester.pumpAndSettle();
    expect(find.text('Organization & access'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('patient profile editor accepts an empty optional email', (
    tester,
  ) async {
    setViewport(tester, const Size(900, 1100));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
    );
    await pumpApp(tester, repository);

    GoRouter.of(
      tester.element(find.byKey(const Key('patient-dashboard-list'))),
    ).go('/patient/account');
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('patient-account-edit-profile-button')),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('onboarding-email-field')), '');
    for (var index = 0; index < 2; index++) {
      await tester.drag(
        find.byKey(const Key('patient-onboarding-list')),
        const Offset(0, -420),
      );
      await tester.pumpAndSettle();
    }
    await tester.tap(find.byKey(const Key('onboarding-blood-type-field')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('A+').last);
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('onboarding-systolic-field')),
      '126',
    );
    await tester.enterText(
      find.byKey(const Key('onboarding-diastolic-field')),
      '82',
    );
    for (var index = 0; index < 6; index++) {
      await tester.drag(
        find.byKey(const Key('patient-onboarding-list')),
        const Offset(0, -520),
      );
      await tester.pumpAndSettle();
    }
    await tester.tap(find.byKey(const Key('patient-onboarding-submit')));
    await tester.pumpAndSettle();

    expect(repository.accountEmailUpdated, isTrue);
    expect(repository.patientProfileUpdated, isTrue);
    expect(repository.lastPatientBloodType, 'A+');
    expect(repository.patientMedicalRecordCreated, isFalse);
    expect(repository.patientCareBundle.patient.systolicBloodPressure, 126);
    expect(repository.patientCareBundle.patient.diastolicBloodPressure, 82);
    expect(find.byKey(const Key('patient-account-email-error')), findsNothing);

    await tester.tap(
      find.byKey(const Key('patient-account-edit-profile-button')),
    );
    await tester.pumpAndSettle();
    for (var index = 0; index < 2; index++) {
      await tester.drag(
        find.byKey(const Key('patient-onboarding-list')),
        const Offset(0, -420),
      );
      await tester.pumpAndSettle();
    }
    expect(
      tester
          .widget<TextFormField>(
            find.byKey(const Key('onboarding-systolic-field')),
          )
          .controller
          ?.text,
      '126',
    );
    expect(
      tester
          .widget<TextFormField>(
            find.byKey(const Key('onboarding-diastolic-field')),
          )
          .controller
          ?.text,
      '82',
    );
  });

  testWidgets('patient profile explains a duplicate account email', (
    tester,
  ) async {
    setViewport(tester, const Size(900, 1100));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
      accountEmailError: const ApiError(
        code: 'email_already_in_use',
        message: 'An account already uses this email address.',
        statusCode: 409,
      ),
    );
    await pumpApp(tester, repository);

    GoRouter.of(
      tester.element(find.byKey(const Key('patient-dashboard-list'))),
    ).go('/patient/account');
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('patient-account-edit-profile-button')),
    );
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('onboarding-email-field')),
      'already.used@example.com',
    );
    for (var index = 0; index < 8; index++) {
      await tester.drag(
        find.byKey(const Key('patient-onboarding-list')),
        const Offset(0, -520),
      );
      await tester.pumpAndSettle();
    }
    await tester.tap(find.byKey(const Key('patient-onboarding-submit')));
    await tester.pumpAndSettle();

    expect(repository.accountEmailUpdated, isTrue);
    expect(repository.patientProfileUpdated, isFalse);
    expect(
      find.text(
        'This email is already linked to another account. '
        'Use a different email or leave this field empty.',
      ),
      findsOneWidget,
    );
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
    expect(find.text('Connect patient by code'), findsOneWidget);
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
    expect(find.byKey(const Key('doctor-section-careCosts')), findsNothing);
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
    expect(repository.lastMedicationFinancial, isNotNull);
    expect(repository.lastMedicationFinancial!.pricingState, 'final');
    expect(
      find.byKey(const Key('create-medication-reminder-button')),
      findsNothing,
    );

    await tester.ensureVisible(find.byKey(const Key('doctor-section-imaging')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('doctor-section-imaging')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('demo-upload-presign-button')), findsNothing);
    expect(find.byKey(const Key('assessment-run-button')), findsNothing);

    await tester.tap(find.byKey(const Key('doctor-section-recoveryPlans')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('recovery-plan-title-field')),
      'Updated recovery plan',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-plan-instructions-field')),
      'Follow the reviewed care instructions.',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-medication-task-field')),
      'Review medication schedule',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-exercise-task-field')),
      'Complete mobility exercise',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-diet-task-field')),
      'Follow nutrition guidance',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-follow-up-task-field')),
      'Prepare for follow-up',
    );
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pumpAndSettle();
    await tester.drag(
      find.byKey(const Key('doctor-section-list-recoveryPlans')),
      const Offset(0, -320),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('recovery-add-phase-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('recovery-phase-preview-0')), findsOneWidget);
    await tester.drag(
      find.byKey(const Key('doctor-section-list-recoveryPlans')),
      const Offset(0, -680),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('recovery-plan-save-button')));
    await tester.pumpAndSettle();
    expect(repository.recoveryPlans.items.first.title, 'Updated recovery plan');
    expect(repository.lastRecoveryPhases, hasLength(1));
    expect(repository.lastRecoveryPhases.single.tasks, hasLength(4));
    expect(
      repository.recoveryPlans.items.first.clinicalEventId,
      'clinical-event-test-id',
    );

    await tester.tap(
      find.byKey(const Key('recovery-plan-submit-review-button')),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('in_review'), findsWidgets);

    await tester.drag(
      find.byKey(const Key('doctor-section-list-recoveryPlans')),
      const Offset(0, -260),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('recovery-plan-activate-button')));
    await tester.pumpAndSettle();
    expect(find.textContaining('active'), findsWidgets);
  });

  testWidgets('legacy demo upload stays hidden from production UI', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester);

    await tester.tap(find.byKey(const Key('doctor-section-imaging')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('demo-upload-filename-field')), findsNothing);
    expect(find.byKey(const Key('demo-upload-presign-button')), findsNothing);
  });

  testWidgets(
    'recovery title counter validates locally, focuses, and preserves content',
    (tester) async {
      setViewport(tester, const Size(1280, 1000));
      final repository = FakeDrAiRepository(
        restoredSession: doctorSession,
        recoveryPlans: const RecoveryPlanListData(items: <RecoveryPlanData>[]),
      );
      await pumpApp(tester, repository);
      await openDoctorPatientWorkflow(tester, section: 'recoveryPlans');

      expect(
        find.descendant(
          of: find.byKey(const Key('recovery-plan-title-field')),
          matching: find.text('0/160'),
        ),
        findsOneWidget,
      );
      await tester.enterText(
        find.byKey(const Key('recovery-plan-title-field')),
        '   ',
      );
      tester
          .widget<FilledButton>(
            find.byKey(const Key('recovery-plan-save-button')),
          )
          .onPressed!();
      await tester.pumpAndSettle();
      expect(find.text('Enter a plan title.'), findsOneWidget);
      expect(repository.recoveryPlanSaveCallCount, 0);
      final titleInput = tester.widget<EditableText>(
        find.descendant(
          of: find.byKey(const Key('recovery-plan-title-field')),
          matching: find.byType(EditableText),
        ),
      );
      expect(titleInput.focusNode.hasFocus, isTrue);
      expect(titleInput.controller.text, '   ');

      final validTitle = 'x' * 160;
      await tester.enterText(
        find.byKey(const Key('recovery-plan-title-field')),
        '$validTitle overflow',
      );
      await tester.pump();
      expect(
        tester
            .widget<TextFormField>(
              find.byKey(const Key('recovery-plan-title-field')),
            )
            .controller
            ?.text,
        validTitle,
      );
      expect(
        find.descendant(
          of: find.byKey(const Key('recovery-plan-title-field')),
          matching: find.text('160/160'),
        ),
        findsOneWidget,
      );
      await tester.enterText(
        find.byKey(const Key('recovery-plan-instructions-field')),
        'Synthetic recovery instructions.',
      );
      await tester.enterText(
        find.byKey(const Key('recovery-exercise-task-field')),
        'Synthetic mobility task',
      );
      tester
          .widget<FilledButton>(
            find.byKey(const Key('recovery-plan-save-button')),
          )
          .onPressed!();
      await tester.pumpAndSettle();
      expect(repository.recoveryPlanSaveCallCount, 1);
      expect(repository.recoveryPlans.items.first.title, validTitle);
    },
  );

  testWidgets('backend recovery title 422 maps to the title field', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1000));
    final repository = FakeDrAiRepository(
      restoredSession: doctorSession,
      recoveryPlans: const RecoveryPlanListData(items: <RecoveryPlanData>[]),
      recoveryPlanSaveError: const ApiError(
        code: 'validation_failed',
        message: 'The request could not be validated.',
        statusCode: 422,
        details: <ApiErrorDetail>[
          ApiErrorDetail(field: 'title', code: 'invalid_value'),
        ],
      ),
    );
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester, section: 'recoveryPlans');
    await tester.enterText(
      find.byKey(const Key('recovery-plan-title-field')),
      'Synthetic retained title',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-plan-instructions-field')),
      'Synthetic retained instructions.',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-exercise-task-field')),
      'Synthetic mobility task',
    );
    tester
        .widget<FilledButton>(
          find.byKey(const Key('recovery-plan-save-button')),
        )
        .onPressed!();
    await tester.pumpAndSettle();

    expect(repository.recoveryPlanSaveCallCount, 1);
    expect(
      find.text('Check the plan title and keep it within 160 characters.'),
      findsOneWidget,
    );
    final titleInput = tester.widget<EditableText>(
      find.descendant(
        of: find.byKey(const Key('recovery-plan-title-field')),
        matching: find.byType(EditableText),
      ),
    );
    expect(titleInput.focusNode.hasFocus, isTrue);
    expect(titleInput.controller.text, 'Synthetic retained title');
    expect(
      tester
          .widget<TextField>(
            find.byKey(const Key('recovery-plan-instructions-field')),
          )
          .controller
          ?.text,
      'Synthetic retained instructions.',
    );
  });

  testWidgets('recovery title required error renders in Chinese', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1000));
    FlutterSecureStorage.setMockInitialValues(<String, String>{
      'dr_ai_interface_locale': 'zh_Hans',
    });
    final repository = FakeDrAiRepository(
      restoredSession: doctorSession,
      recoveryPlans: const RecoveryPlanListData(items: <RecoveryPlanData>[]),
    );
    await pumpApp(tester, repository);
    GoRouter.of(
      tester.element(find.byType(Scaffold).first),
    ).go('/doctor/patients');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('patient-row-SYN-PATIENT-001')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const Key('doctor-section-recoveryPlans')),
    );
    await tester.tap(
      find.byKey(const Key('doctor-section-recoveryPlans')),
      warnIfMissed: false,
    );
    await tester.pumpAndSettle();
    tester
        .widget<FilledButton>(
          find.byKey(const Key('recovery-plan-save-button')),
        )
        .onPressed!();
    await tester.pumpAndSettle();
    expect(find.text('请输入计划标题。'), findsOneWidget);
    expect(repository.recoveryPlanSaveCallCount, 0);
  });

  testWidgets(
    'doctor appends and reads back a consultation in the Clinical Event',
    (tester) async {
      setViewport(tester, const Size(1280, 1400));
      final repository = FakeDrAiRepository(restoredSession: doctorSession);
      await pumpApp(tester, repository);
      await openDoctorPatientWorkflow(tester, section: 'clinicalEvents');

      expect(
        find.byKey(const Key('clinical-event-append-panel')),
        findsOneWidget,
      );
      await tester.enterText(
        find.byKey(const Key('event-consultation-reason-field')),
        'Review the synthetic knee injury',
      );
      await tester.enterText(
        find.byKey(const Key('event-consultation-outcome-field')),
        'Exam findings and next steps recorded.',
      );
      await tester.drag(
        find.byKey(const Key('doctor-section-list-clinicalEvents')),
        const Offset(0, -900),
      );
      await tester.pumpAndSettle();
      await tester.tap(
        find.byKey(const Key('clinical-event-append-save-button')),
      );
      await tester.pumpAndSettle();
      expect(repository.consultations.items, isNotEmpty);
      expect(
        repository.lastConsultationFinancial?.pricingState,
        'pending_cost',
      );
      expect(
        find.byKey(const Key('clinical-event-consultations-section')),
        findsOneWidget,
      );
    },
  );

  testWidgets('doctor appends an encounter update to the Clinical Event', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1400));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester, section: 'clinicalEvents');

    await tester.tap(find.byKey(const Key('event-append-mode-update')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('event-update-title-field')),
      'Follow-up examination',
    );
    await tester.enterText(
      find.byKey(const Key('event-update-summary-field')),
      'Swelling and range of motion reviewed.',
    );
    await tester.drag(
      find.byKey(const Key('doctor-section-list-clinicalEvents')),
      const Offset(0, -700),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('clinical-event-append-save-button')),
    );
    await tester.pumpAndSettle();
    expect(repository.patientCareBundle.visitHistory, isNotEmpty);
  });

  testWidgets('doctor appends a diagnosis to the Clinical Event', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1400));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester, section: 'clinicalEvents');

    await tester.tap(find.byKey(const Key('event-append-mode-diagnosis')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('event-diagnosis-label-field')),
      'Synthetic knee sprain',
    );
    await tester.enterText(
      find.byKey(const Key('event-diagnosis-notes-field')),
      'Clinician-authored synthetic diagnosis note.',
    );
    await tester.drag(
      find.byKey(const Key('doctor-section-list-clinicalEvents')),
      const Offset(0, -500),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('clinical-event-append-save-button')),
    );
    await tester.pumpAndSettle();
    expect(repository.patientCareBundle.diagnoses, isNotEmpty);
    expect(
      find.byKey(const Key('clinical-event-append-success')),
      findsOneWidget,
    );
  });

  testWidgets(
    'doctor creates an imaging service before attaching non-billable evidence',
    (tester) async {
      setViewport(tester, const Size(1280, 1800));
      final repository = FakeDrAiRepository(restoredSession: doctorSession);
      await pumpApp(tester, repository);
      await openDoctorPatientWorkflow(tester);

      expect(
        find.byKey(const Key('imaging-clinical-service-panel')),
        findsOneWidget,
      );
      await tester.enterText(
        find.byKey(const Key('imaging-procedure-name')),
        'Low-dose CT chest',
      );
      await tester.enterText(find.byKey(const Key('imaging-modality')), 'CT');
      await tester.enterText(
        find.byKey(const Key('imaging-body-region')),
        'Chest',
      );
      await tester.dragUntilVisible(
        find.byKey(const Key('save-imaging-procedure')),
        find.byKey(const Key('doctor-section-list-imaging')),
        const Offset(0, -360),
      );
      await tester.ensureVisible(
        find.byKey(const Key('save-imaging-procedure')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('save-imaging-procedure')));
      await tester.pumpAndSettle();

      expect(repository.clinicalServiceSaved, isTrue);
      expect(repository.patientCareBundle.clinicalServices, hasLength(1));
      expect(
        repository.patientCareBundle.clinicalServices.first.name,
        'Low-dose CT chest',
      );

      await tester.dragUntilVisible(
        find.byKey(const Key('imaging-evidence-filename')),
        find.byKey(const Key('doctor-section-list-imaging')),
        const Offset(0, -420),
      );
      await tester.ensureVisible(
        find.byKey(const Key('imaging-evidence-filename')),
      );
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('imaging-evidence-filename')),
        'ct-series.dcm',
      );
      await tester.enterText(
        find.byKey(const Key('imaging-evidence-size')),
        '4096',
      );
      await tester.ensureVisible(
        find.byKey(const Key('prepare-imaging-evidence')),
      );
      await tester.tap(find.byKey(const Key('prepare-imaging-evidence')));
      await tester.pumpAndSettle();

      expect(repository.imagingPrepared, isTrue);
      expect(
        repository.lastImagingClinicalServiceId,
        'clinical-service-test-id',
      );
      expect(find.text('Cost pending'), findsWidgets);
      expect(find.text('Attach evidence'), findsWidgets);
    },
  );

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

  testWidgets('doctor workspace sidebars collapse without losing sections', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    await pumpApp(tester, FakeDrAiRepository(restoredSession: doctorSession));
    await openDoctorPatientWorkflow(tester, section: 'overview');

    for (final section in <String>[
      'overview',
      'profile',
      'medicalHistory',
      'clinicalEvents',
      'medicationPrescriptions',
      'recoveryPlans',
      'imaging',
      'consultationActivity',
    ]) {
      expect(find.byKey(Key('doctor-section-$section')), findsOneWidget);
    }

    await tester.tap(find.byKey(const Key('collapse-patient-pane-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('collapsed-patient-pane')), findsOneWidget);
    await tester.tap(find.byKey(const Key('expand-patient-pane-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('patient-search-field')), findsOneWidget);

    await tester.tap(find.byKey(const Key('toggle-section-rail-button')));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<ListTile>(find.byKey(const Key('doctor-section-overview')))
          .title,
      isNull,
    );
    await tester.tap(find.byKey(const Key('toggle-section-rail-button')));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<ListTile>(find.byKey(const Key('doctor-section-overview')))
          .title,
      isNotNull,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('doctor can connect a from-zero patient by code', (tester) async {
    setViewport(tester, const Size(1280, 832));
    final repository = FakeDrAiRepository(
      restoredSession: doctorSession,
      patientList: const PatientListData(items: <PatientSummary>[]),
    );
    await pumpApp(tester, repository);

    await tester.tap(find.text('Patient Management'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('patient-list-empty')), findsOneWidget);

    await tester.enterText(
      find.byKey(const Key('patient-connect-code-field')),
      'SYN-PATIENT-001',
    );
    await tester.tap(find.byKey(const Key('patient-connect-button')));
    await tester.pumpAndSettle();

    expect(repository.patientMatchPreviewed, isTrue);
    expect(find.text('Confirm patient connection'), findsOneWidget);
    expect(repository.patientConnected, isFalse);
    await tester.tap(find.byKey(const Key('patient-match-confirm-button')));
    await tester.pumpAndSettle();

    expect(repository.patientConnected, isTrue);
    expect(find.byKey(const Key('patient-connect-success')), findsOneWidget);
    expect(
      find.byKey(const Key('patient-row-SYN-PATIENT-001')),
      findsOneWidget,
    );
  });

  testWidgets('unfinished assessment simulation is hidden from production UI', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 832));
    final repository = FakeDrAiRepository(restoredSession: doctorSession);
    await pumpApp(tester, repository);
    await openDoctorPatientWorkflow(tester);

    await tester.tap(find.byKey(const Key('doctor-section-imaging')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('assessment-run-button')), findsNothing);
    expect(find.text('Demo Image Upload'), findsNothing);
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
    expect(find.text('Medication reminders'), findsOneWidget);
    expect(
      find.byKey(const Key('patient-medication-notification-read-only')),
      findsOneWidget,
    );
    expect(find.textContaining('are not scheduled in Phase 5'), findsOneWidget);
    expect(find.text('Care & Costs summary'), findsOneWidget);
    expect(find.text('Dashboard'), findsOneWidget);
    GoRouter.of(
      tester.element(find.byKey(const Key('patient-dashboard-list'))),
    ).go('/patient/account');
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('patient-account-list')), findsOneWidget);
    expect(find.byKey(const Key('patient-event-update-title')), findsNothing);
    expect(find.text('Clinical Events'), findsNothing);
    expect(find.text('Medical Records And Imaging'), findsNothing);
    expect(find.text('Medications And Prescriptions'), findsNothing);
    await tester.dragUntilVisible(
      find.byKey(const Key('patient-account-history-summary')),
      find.byKey(const Key('patient-account-list')),
      const Offset(0, -240),
    );
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('patient-account-history-summary')),
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
    expect(tester.takeException(), isNull);
  });

  testWidgets('patient medical destinations read persisted records', (
    tester,
  ) async {
    setViewport(tester, const Size(900, 760));
    await pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
      ),
    );

    GoRouter.of(
      tester.element(find.byKey(const Key('patient-dashboard-list'))),
    ).go('/patient/medical-service/records');
    await tester.pumpAndSettle();
    expect(find.text('My medical information'), findsOneWidget);
    expect(find.text('Synthetic intake summary'), findsOneWidget);

    await tester.tap(find.text('Imaging'));
    await tester.pumpAndSettle();
    expect(find.textContaining('image/png'), findsOneWidget);
    expect(find.textContaining('pending_review'), findsOneWidget);

    await tester.tap(find.text('Medications'));
    await tester.pumpAndSettle();
    expect(find.text('Demo Sumatriptan Fixture'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('fresh patient sees medical intake before the dashboard', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    await pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: const DashboardData(
          role: AppRole.patient,
          data: <String, Object>{},
        ),
        patientCareBundle: incompleteOnboardingPatientCareBundle,
      ),
    );

    expect(find.byKey(const Key('patient-onboarding-list')), findsOneWidget);
    expect(find.text('Medical intake'), findsOneWidget);
    expect(find.byKey(const Key('onboarding-height-field')), findsOneWidget);
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

    expect(
      find.byKey(const Key('patient-today-progress-summary')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('today-task-medication')), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('today-task-medication')));
    await tester.tap(find.byKey(const Key('today-task-medication')));
    await tester.pumpAndSettle();

    expect(repository.patientToday.tasks.first.isCompleted, isTrue);
    expect(find.byKey(const Key('today-task-medication')), findsOneWidget);
    await tester.drag(
      find.byKey(const Key('patient-dashboard-list')),
      const Offset(0, 400),
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('today-task-medication')));
    await tester.tap(find.byKey(const Key('today-task-medication')));
    await tester.pumpAndSettle();

    expect(repository.patientToday.tasks.first.isCompleted, isFalse);
  });

  testWidgets('patient schedule separates every structured task category', (
    tester,
  ) async {
    setViewport(tester, const Size(1280, 1200));
    RecoveryTaskItem task(String id, String category, String title) =>
        RecoveryTaskItem(
          taskId: id,
          planId: 'source-plan',
          planTitle: 'Source recovery plan',
          category: category,
          title: title,
          detail: 'Synthetic structured schedule.',
          dueLabel: 'Display only',
          isCompleted: false,
        );
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      dashboard: patientDashboard,
      patientToday: PatientTodayData(
        safetyLabel: 'Synthetic demonstration data only.',
        progressSummary: const RecoveryPlanProgressData(
          taskCount: 4,
          completedTaskCount: 0,
          remainingTaskCount: 4,
          completionPercent: 0,
        ),
        tasks: <RecoveryTaskItem>[task('today', 'today', 'Due today task')],
        overdueTasks: <RecoveryTaskItem>[
          task('overdue', 'overdue', 'Overdue task'),
        ],
        upcomingTasks: <RecoveryTaskItem>[
          task('upcoming', 'upcoming', 'Upcoming task'),
        ],
        unscheduledTasks: <RecoveryTaskItem>[
          task('unscheduled', 'unscheduled', 'Unscheduled task'),
        ],
      ),
    );
    await pumpApp(tester, repository);

    expect(find.text('Today'), findsWidgets);
    expect(find.text('Overdue'), findsOneWidget);
    await tester.drag(
      find.byKey(const Key('patient-today-task-list')),
      const Offset(0, -500),
    );
    await tester.pumpAndSettle();
    expect(find.text('Upcoming'), findsOneWidget);
    await tester.drag(
      find.byKey(const Key('patient-today-task-list')),
      const Offset(0, -500),
    );
    await tester.pumpAndSettle();
    expect(find.text('Unscheduled'), findsOneWidget);
    expect(find.textContaining('Source recovery plan'), findsWidgets);
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

    await revealPatientEducationalChat(tester);
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

    await revealPatientEducationalChat(tester);
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

      await tester.ensureVisible(
        find.byKey(const Key('today-task-medication')),
      );
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
    await tester.enterText(
      find.byKey(const Key('consultation-specialty-field')),
      'Pulmonology',
    );
    await tester.enterText(
      find.byKey(const Key('consultation-summary-field')),
      'Review respiratory symptoms and recent imaging.',
    );
    expect(
      find.byKey(const Key('specialist-request-not-billable-notice')),
      findsOneWidget,
    );
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.dragUntilVisible(
      find.byKey(const Key('consultation-request-button')),
      find.byKey(const Key('doctor-section-list-consultationActivity')),
      const Offset(0, -240),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('consultation-request-button')));
    await tester.pumpAndSettle();

    expect(repository.consultations.items, isNotEmpty);
    expect(repository.lastConsultationFinancial, isNull);
    expect(
      repository.consultations.items.first.clinicalEventId,
      'clinical-event-test-id',
    );
    expect(find.textContaining('consultation requested'), findsWidgets);
    expect(find.textContaining('Pulmonology - requested'), findsWidgets);

    expect(
      find.byKey(const Key('edit-consultation-cost-created-consultation-id')),
      findsNothing,
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

      await tester.ensureVisible(
        find.byKey(const Key('open-care-costs-button')),
      );
      await tester.pumpAndSettle();
      expect(find.text('View full care and cost details'), findsOneWidget);
      expect(find.text('My Account'), findsOneWidget);
      await tester.tap(find.text('My Account'));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('account-sign-out-button')), findsOneWidget);
      expect(find.byTooltip('Sign out'), findsNothing);
    } finally {
      semantics.dispose();
    }
  });

  testWidgets('patient account exposes the secure password change flow', (
    tester,
  ) async {
    setViewport(tester, const Size(412, 917));
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      loginSession: patientSession,
      dashboard: patientDashboard,
    );
    await pumpApp(tester, repository);

    await tester.tap(find.text('My Account'));
    await tester.pumpAndSettle();
    await tester.dragUntilVisible(
      find.byKey(const Key('patient-account-change-password-button')),
      find.byKey(const Key('patient-account-list')),
      const Offset(0, -240),
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const Key('patient-account-change-password-button')),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('patient-account-change-password-button')),
    );
    await tester.pumpAndSettle();

    expect(find.text('Change password'), findsWidgets);
    expect(
      find.byKey(const Key('patient-account-current-password-field')),
      findsOneWidget,
    );
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
    expect(find.text('Quick Access'), findsOneWidget);
    expect(find.text('Hospital profile pending'), findsNothing);
    expect(find.text('Doctor profile'), findsNothing);
    expect(find.text('Team Management'), findsOneWidget);
  });
}
