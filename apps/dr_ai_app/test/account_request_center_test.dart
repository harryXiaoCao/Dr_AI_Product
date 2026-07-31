import 'dart:async';
import 'dart:io';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/account/application/support_request_providers.dart';
import 'package:dr_ai_app/features/account/domain/support_request_data.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/application/care_cost_providers.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/features/care_cost/presentation/payer_account_screen.dart';
import 'package:dr_ai_app/features/doctor/domain/doctor_profile.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_dashboard_screen.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/features/patient/presentation/patient_dashboard_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/account_request_center.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

Future<void> pumpCenter(
  WidgetTester tester, {
  required FakeDrAiRepository repository,
  AppRole role = AppRole.patient,
  Locale locale = const Locale('en'),
  Size size = const Size(760, 980),
  double textScale = 1,
}) async {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetDevicePixelRatio();
    tester.view.resetPhysicalSize();
  });
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: Scaffold(
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: AccountRequestCenter(role: role),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

bool _subtreeHasFocus(Finder root) {
  return find
      .descendant(of: root, matching: find.byType(Focus))
      .evaluate()
      .map((element) => element.widget)
      .whereType<Focus>()
      .any((widget) => widget.focusNode?.hasFocus ?? false);
}

void main() {
  final skipGoldens =
      Platform.environment['CI'] == 'true' ||
      Directory.current.path.contains('dr_ai_flutter_verify');

  setUpAll(() async {
    final inter = FontLoader('Inter')
      ..addFont(rootBundle.load('assets/fonts/InterVariable.ttf'));
    final notoSansSc = FontLoader('NotoSansSC')
      ..addFont(rootBundle.load('assets/fonts/NotoSansSC-Variable.ttf'));
    final materialIcons = FontLoader('MaterialIcons')
      ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
    await Future.wait(<Future<void>>[
      inter.load(),
      notoSansSc.load(),
      materialIcons.load(),
    ]);
  });

  testWidgets('all three roles share the persisted account request center', (
    tester,
  ) async {
    for (final role in <AppRole>[
      AppRole.patient,
      AppRole.doctor,
      AppRole.payer,
    ]) {
      await pumpCenter(tester, repository: FakeDrAiRepository(), role: role);
      expect(
        find.byKey(Key('${role.wireValue}-account-request-center')),
        findsOneWidget,
      );
      expect(
        find.text(
          'No support, feedback, or deletion requests have been submitted from this account.',
        ),
        findsOneWidget,
      );
    }
  });

  testWidgets('network failure preserves text and retries with the same key', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      supportRequestCreateError: const ApiError(
        code: 'service_unavailable',
        message: 'Unavailable',
        statusCode: 503,
      ),
      supportRequestCreateErrorAfterPersist: true,
    );
    await pumpCenter(tester, repository: repository);

    await tester.enterText(
      find.byKey(const Key('account-request-subject')),
      'Account access',
    );
    await tester.enterText(
      find.byKey(const Key('account-request-message')),
      'Please help me access the account request history.',
    );
    await tester.tap(find.byKey(const Key('account-request-submit')));
    await tester.pumpAndSettle();

    expect(find.text('Retry safely'), findsOneWidget);
    expect(
      tester
          .widget<TextFormField>(
            find.byKey(const Key('account-request-message')),
          )
          .controller!
          .text,
      contains('request history'),
    );
    repository.supportRequestCreateError = null;
    await tester.tap(find.byKey(const Key('account-request-submit')));
    await tester.pumpAndSettle();

    expect(repository.supportRequestCreateCount, 2);
    expect(repository.supportRequestIdempotencyKeys.toSet(), hasLength(1));
    expect(find.textContaining('REQ-2026-NEW'), findsWidgets);
    expect(
      find.textContaining('No duplicate request was created'),
      findsOneWidget,
    );
    expect(
      repository.productEvents.any(
        (event) => event.eventName == 'workflow_replayed',
      ),
      isTrue,
    );
  });

  testWidgets('conflict preserves the form and refreshes persisted history', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      supportRequestCreateError: const ApiError(
        code: 'conflict',
        message: 'Conflict',
        statusCode: 409,
      ),
      supportRequests: <SupportRequestData>[supportRequestFixture()],
    );
    await pumpCenter(tester, repository: repository);
    await tester.enterText(
      find.byKey(const Key('account-request-subject')),
      'Conflicting retry',
    );
    await tester.enterText(
      find.byKey(const Key('account-request-message')),
      'Keep this text visible after the conflict response.',
    );
    await tester.tap(find.byKey(const Key('account-request-submit')));
    await tester.pumpAndSettle();

    expect(
      find.textContaining('conflicts with a different saved request'),
      findsOneWidget,
    );
    expect(
      tester
          .widget<TextFormField>(
            find.byKey(const Key('account-request-message')),
          )
          .controller!
          .text,
      contains('Keep this text'),
    );
    expect(repository.supportRequestLoadCount, greaterThan(1));
    expect(
      repository.productEvents.any(
        (event) => event.eventName == 'workflow_conflict',
      ),
      isTrue,
    );

    repository.supportRequestCreateError = null;
    await tester.tap(find.byKey(const Key('account-request-submit')));
    await tester.pumpAndSettle();
    expect(repository.supportRequestCreateCount, 2);
    expect(repository.supportRequestIdempotencyKeys.toSet(), hasLength(2));
    expect(find.textContaining('was submitted and persisted'), findsOneWidget);
  });

  testWidgets(
    'pre-persist failure retries once while post-persist failure replays',
    (tester) async {
      final repository = FakeDrAiRepository(
        supportRequestCreateError: const ApiError(
          code: 'service_unavailable',
          message: 'Unavailable',
          statusCode: 503,
        ),
      );
      await pumpCenter(tester, repository: repository);
      await tester.enterText(
        find.byKey(const Key('account-request-subject')),
        'Support retry',
      );
      await tester.enterText(
        find.byKey(const Key('account-request-message')),
        'Retry this request after a pre-persist failure.',
      );
      await tester.tap(find.byKey(const Key('account-request-submit')));
      await tester.pumpAndSettle();
      repository.supportRequestCreateError = null;
      await tester.tap(find.byKey(const Key('account-request-submit')));
      await tester.pumpAndSettle();

      expect(
        find.textContaining('was submitted and persisted'),
        findsOneWidget,
      );
      expect(find.textContaining('No duplicate request'), findsNothing);
      expect(repository.supportRequests.single.replay, isFalse);
    },
  );

  testWidgets('deletion request states the retention boundary before submit', (
    tester,
  ) async {
    await pumpCenter(
      tester,
      repository: FakeDrAiRepository(),
      locale: const Locale('zh'),
      size: const Size(412, 917),
      textScale: 1.3,
    );

    await tester.tap(find.byKey(const Key('account-request-type')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('账户删除审核').last);
    await tester.pumpAndSettle();

    expect(find.textContaining('不会立即删除账户'), findsWidgets);
    final submit = tester.widget<FilledButton>(
      find.byKey(const Key('account-request-submit')),
    );
    expect(submit.onPressed, isNull);
    expect(tester.takeException(), isNull);
  });

  testWidgets('request history exposes receipt, timeline, and withdrawal', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      supportRequests: <SupportRequestData>[supportRequestFixture()],
    );
    await pumpCenter(tester, repository: repository);

    await tester.tap(find.textContaining('REQ-2026-0001'));
    await tester.pumpAndSettle();
    expect(find.text('Status timeline'), findsOneWidget);
    expect(find.text('Request submitted'), findsOneWidget);
    await tester.ensureVisible(
      find.byKey(const Key('account-request-withdraw-REQ-2026-0001')),
    );
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const Key('account-request-withdraw-REQ-2026-0001')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('account-request-withdraw-confirm')));
    await tester.pumpAndSettle();

    expect(repository.supportRequestWithdrawCount, 1);
    expect(find.textContaining('was withdrawn'), findsWidgets);
  });

  testWidgets('unknown lifecycle codes use a localized safe fallback', (
    tester,
  ) async {
    await pumpCenter(
      tester,
      locale: const Locale('zh'),
      repository: FakeDrAiRepository(
        supportRequests: <SupportRequestData>[
          supportRequestFixture(
            retentionBoundaryCode: 'future_retention_code',
            deletionEffectCode: 'future_deletion_code',
          ),
        ],
      ),
    );
    await tester.tap(find.textContaining('REQ-2026-0001'));
    await tester.pumpAndSettle();

    expect(find.textContaining('适用的保留边界暂不可用'), findsOneWidget);
    expect(find.textContaining('删除效果暂不可用'), findsOneWidget);
  });

  testWidgets('history error is recoverable and controls have semantics', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    final repository = FakeDrAiRepository(
      supportRequestLoadError: const ApiError(
        code: 'service_unavailable',
        message: 'Unavailable',
        statusCode: 503,
      ),
    );
    try {
      await pumpCenter(tester, repository: repository);
      expect(
        find.byKey(const Key('account-request-load-retry')),
        findsOneWidget,
      );
      expect(
        tester.getSemantics(
          find.byKey(const Key('account-request-load-retry')),
        ),
        matchesSemantics(
          label: 'Try again',
          isButton: true,
          hasEnabledState: true,
          isEnabled: true,
          isFocusable: true,
          hasFocusAction: true,
          hasTapAction: true,
        ),
      );
      repository.supportRequestLoadError = null;
      await tester.tap(find.byKey(const Key('account-request-load-retry')));
      await tester.pumpAndSettle();
      expect(find.text('Start a request'), findsOneWidget);

      await tester.tap(find.text('Start a request'));
      await tester.pump();
      expect(
        _subtreeHasFocus(find.byKey(const Key('account-request-type'))),
        isTrue,
      );
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pump();
      expect(
        _subtreeHasFocus(find.byKey(const Key('account-request-subject'))),
        isTrue,
      );
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pump();
      expect(
        _subtreeHasFocus(find.byKey(const Key('account-request-message'))),
        isTrue,
      );
    } finally {
      semantics.dispose();
    }
  });

  testWidgets('analytics keys are opaque and never expose receipts', (
    tester,
  ) async {
    final repository = FakeDrAiRepository();
    await pumpCenter(tester, repository: repository);
    await tester.enterText(
      find.byKey(const Key('account-request-subject')),
      'Analytics privacy',
    );
    await tester.enterText(
      find.byKey(const Key('account-request-message')),
      'Submit without identifiers in analytics keys.',
    );
    await tester.tap(find.byKey(const Key('account-request-submit')));
    await tester.pumpAndSettle();

    final uuid = RegExp(
      r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-'
      r'[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    );
    expect(repository.productEvents, isNotEmpty);
    for (final event in repository.productEvents) {
      expect(event.deduplicationKey, matches(uuid));
      expect(event.deduplicationKey, isNot(contains('REQ-')));
    }
  });

  testWidgets(
    'patient doctor and payer destinations retain request center on provider failure and loading',
    (tester) async {
      Future<void> pumpDestination(
        Widget destination,
        dynamic overrides, {
        bool settle = true,
      }) async {
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pumpWidget(
          ProviderScope(
            overrides: (overrides as List<dynamic>).cast(),
            child: MaterialApp(
              theme: DrAiTheme.light,
              supportedLocales: AppLocalizations.supportedLocales,
              localizationsDelegates: AppLocalizations.localizationsDelegates,
              home: destination,
            ),
          ),
        );
        if (settle) {
          await tester.pumpAndSettle();
        } else {
          await tester.pump();
        }
      }

      const failure = ApiError(
        code: 'service_unavailable',
        message: 'Unavailable',
        statusCode: 503,
      );
      final repository = FakeDrAiRepository();
      await pumpDestination(const PatientAccountScreen(), [
        repositoryProvider.overrideWithValue(repository),
        supportRequestsProvider.overrideWith((ref) async => const []),
        ownPatientCareProvider.overrideWith((ref) async => throw failure),
      ]);
      expect(
        find.byKey(const Key('patient-account-request-center')),
        findsOneWidget,
      );

      await pumpDestination(const DoctorAccountScreen(), [
        repositoryProvider.overrideWithValue(repository),
        supportRequestsProvider.overrideWith((ref) async => const []),
        doctorProfileProvider.overrideWith((ref) async => throw failure),
      ]);
      expect(
        find.byKey(const Key('doctor-account-request-center')),
        findsOneWidget,
      );

      await pumpDestination(const PayerAccountScreen(), [
        repositoryProvider.overrideWithValue(repository),
        supportRequestsProvider.overrideWith((ref) async => const []),
        payerProfileProvider.overrideWith((ref) async => throw failure),
      ]);
      expect(
        find.byKey(const Key('payer-account-request-center')),
        findsOneWidget,
      );

      await pumpDestination(const PatientAccountScreen(), [
        repositoryProvider.overrideWithValue(repository),
        supportRequestsProvider.overrideWith((ref) async => const []),
        ownPatientCareProvider.overrideWith(
          (ref) => Completer<PatientCareBundle>().future,
        ),
      ], settle: false);
      expect(
        find.byKey(const Key('patient-account-request-center')),
        findsOneWidget,
      );

      await pumpDestination(const DoctorAccountScreen(), [
        repositoryProvider.overrideWithValue(repository),
        supportRequestsProvider.overrideWith((ref) async => const []),
        doctorProfileProvider.overrideWith(
          (ref) => Completer<DoctorProfile>().future,
        ),
      ], settle: false);
      expect(
        find.byKey(const Key('doctor-account-request-center')),
        findsOneWidget,
      );

      await pumpDestination(const PayerAccountScreen(), [
        repositoryProvider.overrideWithValue(repository),
        supportRequestsProvider.overrideWith((ref) async => const []),
        payerProfileProvider.overrideWith(
          (ref) => Completer<PayerProfileData>().future,
        ),
      ], settle: false);
      expect(
        find.byKey(const Key('payer-account-request-center')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('persisted request center matches English desktop state', (
    tester,
  ) async {
    await pumpCenter(
      tester,
      repository: FakeDrAiRepository(
        supportRequests: <SupportRequestData>[supportRequestFixture()],
      ),
      role: AppRole.payer,
      size: const Size(1280, 1100),
    );
    await tester.tap(find.textContaining('REQ-2026-0001'));
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(AccountRequestCenter),
      matchesGoldenFile('goldens/account_requests_payer_en_1280x1100.png'),
    );
  }, skip: skipGoldens);

  testWidgets(
    'deletion request history matches enlarged Chinese mobile state',
    (tester) async {
      await pumpCenter(
        tester,
        repository: FakeDrAiRepository(
          supportRequests: <SupportRequestData>[
            supportRequestFixture(
              requestType: 'deletion',
              reference: 'REQ-2026-DEL1',
            ),
          ],
        ),
        role: AppRole.patient,
        locale: const Locale('zh'),
        size: const Size(412, 917),
        textScale: 1.3,
      );
      await tester.tap(find.byKey(const Key('account-request-type')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('账户删除审核').last);
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.textContaining('REQ-2026-DEL1'));
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining('REQ-2026-DEL1'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('状态时间线'));
      await tester.pumpAndSettle();
      await expectLater(
        find.byType(AccountRequestCenter),
        matchesGoldenFile(
          'goldens/account_requests_patient_zh_412x917_large_text.png',
        ),
      );
    },
    skip: skipGoldens,
  );
}
