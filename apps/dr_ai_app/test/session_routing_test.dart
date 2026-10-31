import 'dart:async';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/foundation/presentation/unauthorized_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'fakes.dart';

Future<void> pumpRoute(
  WidgetTester tester, {
  required FakeDrAiRepository repository,
  required String initialLocation,
}) async {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = const Size(1280, 900);
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: DrAiApp(initialLocation: initialLocation),
    ),
  );
  await tester.pumpAndSettle();
}

String currentLocation(WidgetTester tester) {
  final context = tester.element(find.byType(Scaffold).first);
  return GoRouter.of(context).routeInformationProvider.value.uri.toString();
}

Future<void> loginThroughUi(WidgetTester tester) async {
  await tester.enterText(
    find.byKey(const Key('email-field')),
    'synthetic.user@example.com',
  );
  await tester.enterText(
    find.byKey(const Key('password-field')),
    'synthetic-test-only',
  );
  await tester.tap(find.byKey(const Key('login-button')));
  await tester.pumpAndSettle();
}

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues(<String, String>{});
  });

  test('browser locations preserve path and hash routing forms', () {
    expect(
      initialAppLocation(
        Uri.parse('https://example.test/patient/contact/private?id=doctor-1'),
      ),
      '/patient/contact/private?id=doctor-1',
    );
    expect(
      initialAppLocation(
        Uri.parse('https://example.test/#/payer/requests?status=open'),
      ),
      '/payer/requests?status=open',
    );
    expect(
      safeProtectedLocation(Uri.parse('https://evil.test/doctor')),
      isNull,
    );
    expect(safeProtectedLocation(Uri.parse('//evil.test/doctor')), isNull);
  });

  testWidgets('restored doctor session preserves a protected deep link', (
    tester,
  ) async {
    final restore = Completer<AuthSession?>();
    final repository = FakeDrAiRepository(restoreCompleter: restore);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [repositoryProvider.overrideWithValue(repository)],
        child: const DrAiApp(initialLocation: '/doctor/contact'),
      ),
    );
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    restore.complete(doctorSession);
    await tester.pumpAndSettle();

    expect(currentLocation(tester), '/doctor/contact');
    expect(find.text('Contacts'), findsWidgets);
  });

  testWidgets('restored patient session preserves nested route and query', (
    tester,
  ) async {
    const location =
        '/patient/contact/private?id=doctor-test-id&name=Synthetic%20Doctor';
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(restoredSession: patientSession),
      initialLocation: location,
    );
    expect(currentLocation(tester), location);
    expect(find.text('Synthetic Doctor'), findsWidgets);
  });

  for (final section in <String>['imaging', 'medications']) {
    testWidgets('patient medical $section deep link keeps its section', (
      tester,
    ) async {
      final location = '/patient/medical-service/$section';
      await pumpRoute(
        tester,
        repository: FakeDrAiRepository(restoredSession: patientSession),
        initialLocation: location,
      );
      expect(currentLocation(tester), location);
    });
  }

  testWidgets('medical section control updates the shareable route', (
    tester,
  ) async {
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(restoredSession: patientSession),
      initialLocation: '/patient/medical-service/records',
    );
    await tester.tap(find.text('Imaging').last);
    await tester.pumpAndSettle();
    expect(currentLocation(tester), '/patient/medical-service/imaging');
  });

  testWidgets('restored payer session preserves a nested payer route', (
    tester,
  ) async {
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(restoredSession: payerSession),
      initialLocation: '/payer/requests',
    );
    expect(currentLocation(tester), '/payer/requests');
    expect(find.byType(Scaffold), findsWidgets);
  });

  testWidgets('provisioned admin lands in hospital workspace and cannot open doctor routes', (
    tester,
  ) async {
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(restoredSession: adminSession),
      initialLocation: '/admin',
    );
    expect(currentLocation(tester), '/admin');
    expect(find.text('Hospital operations'), findsOneWidget);
    final context = tester.element(find.byType(Scaffold).first);
    GoRouter.of(context).go('/doctor/hospital-resources');
    await tester.pumpAndSettle();
    expect(currentLocation(tester), '/unauthorized');
  });

  testWidgets('payer account exposes the interface language choice', (
    tester,
  ) async {
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(restoredSession: payerSession),
      initialLocation: '/payer/account',
    );
    expect(find.byKey(const Key('interface-language-field')), findsOneWidget);
  });

  for (final scenario in <(AuthSession, String, String)>[
    (doctorSession, '/patient/care-costs', '/doctor'),
    (patientSession, '/doctor/contact', '/patient'),
    (payerSession, '/patient/recovery-plan', '/payer'),
  ]) {
    testWidgets('wrong-role route renders unauthorized for ${scenario.$3}', (
      tester,
    ) async {
      await pumpRoute(
        tester,
        repository: FakeDrAiRepository(restoredSession: scenario.$1),
        initialLocation: scenario.$2,
      );
      expect(currentLocation(tester), '/unauthorized');
      expect(find.byType(UnauthorizedScreen), findsOneWidget);
      expect(
        find.byKey(const Key('unauthorized-return-button')),
        findsOneWidget,
      );
      expect(tester.binding.focusManager.primaryFocus, isNotNull);

      await tester.tap(find.byKey(const Key('unauthorized-return-button')));
      await tester.pumpAndSettle();
      expect(currentLocation(tester), scenario.$3);
    });
  }

  testWidgets('matching login resumes a protected route', (tester) async {
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(loginSession: patientSession),
      initialLocation: '/patient/recovery-plan?source=bookmark',
    );
    expect(currentLocation(tester), '/login');

    await loginThroughUi(tester);

    expect(currentLocation(tester), '/patient/recovery-plan?source=bookmark');
  });

  testWidgets('wrong-role login resolves a protected route to unauthorized', (
    tester,
  ) async {
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(loginSession: doctorSession),
      initialLocation: '/patient/care-costs',
    );
    await loginThroughUi(tester);
    expect(currentLocation(tester), '/unauthorized');
  });

  testWidgets('logout and account switching do not leak a pending route', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      restoredSession: doctorSession,
      loginSession: patientSession,
    );
    await pumpRoute(
      tester,
      repository: repository,
      initialLocation: '/doctor/contact',
    );
    final container = ProviderScope.containerOf(
      tester.element(find.byType(Scaffold).first),
    );

    await container.read(authControllerProvider.notifier).logout();
    await tester.pumpAndSettle();
    expect(currentLocation(tester), '/login');

    await loginThroughUi(tester);
    expect(currentLocation(tester), '/patient');
  });

  testWidgets('normal login lands on the authenticated role dashboard', (
    tester,
  ) async {
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(loginSession: payerSession),
      initialLocation: '/login',
    );
    await loginThroughUi(tester);
    expect(currentLocation(tester), '/payer');
  });

  for (final route in <String>['/privacy', '/terms', '/privacy-policy']) {
    testWidgets('public legal route remains accessible: $route', (
      tester,
    ) async {
      await pumpRoute(
        tester,
        repository: FakeDrAiRepository(),
        initialLocation: route,
      );
      expect(currentLocation(tester), route);
      expect(find.byType(Scaffold), findsWidgets);
    });
  }

  testWidgets('unauthorized copy is available in Simplified Chinese', (
    tester,
  ) async {
    FlutterSecureStorage.setMockInitialValues(<String, String>{
      'dr_ai_interface_locale': 'zh_Hans',
    });
    await pumpRoute(
      tester,
      repository: FakeDrAiRepository(restoredSession: doctorSession),
      initialLocation: '/patient/care-costs',
    );
    await tester.pumpAndSettle();
    expect(find.text('当前身份无法访问此页面。'), findsOneWidget);
    expect(find.text('返回首页'), findsOneWidget);
  });
}
