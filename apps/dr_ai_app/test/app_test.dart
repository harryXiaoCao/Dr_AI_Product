import 'dart:async';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

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

void main() {
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
    expect(find.text('No Medical Records'), findsOneWidget);
    expect(find.text('No Imaging Results'), findsOneWidget);
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

  testWidgets('patient dashboard renders seeded mobile state at 412x917', (
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

    expect(find.text('Today'), findsOneWidget);
    expect(find.text('Contact Doctor'), findsOneWidget);
    expect(find.text('Medical Fee'), findsOneWidget);
    expect(find.text('No Medical Records'), findsOneWidget);
    expect(find.text('Dashboard'), findsOneWidget);
    expect(tester.takeException(), isNull);
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
        find.bySemanticsLabel('See more recovery tasks unavailable in Week 1'),
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
