import 'package:dr_ai_app/app/app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  const email = String.fromEnvironment('DR_AI_SMOKE_EMAIL');
  const password = String.fromEnvironment('DR_AI_SMOKE_PASSWORD');
  const dashboardText = String.fromEnvironment(
    'DR_AI_SMOKE_DASHBOARD_TEXT',
    defaultValue: 'Quick Access',
  );

  testWidgets('seeded user can sign in and see the seeded dashboard', (
    tester,
  ) async {
    assert(email.isNotEmpty, 'DR_AI_SMOKE_EMAIL must be supplied.');
    assert(password.isNotEmpty, 'DR_AI_SMOKE_PASSWORD must be supplied.');

    await tester.pumpWidget(const ProviderScope(child: DrAiApp()));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('email-field')), email);
    await tester.enterText(find.byKey(const Key('password-field')), password);
    await tester.tap(find.byKey(const Key('login-button')));
    await tester.pumpAndSettle(const Duration(seconds: 8));

    expect(find.text(dashboardText), findsWidgets);
  });
}
