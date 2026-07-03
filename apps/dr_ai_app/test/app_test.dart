import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('doctor role opens the doctor foundation', (tester) async {
    await tester.pumpWidget(DrAiApp(role: AppRole.doctor));
    await tester.pumpAndSettle();

    expect(find.text('Doctor dashboard foundation'), findsOneWidget);
    expect(find.textContaining('synthetic content only'), findsOneWidget);
  });

  testWidgets('patient role opens the patient foundation', (tester) async {
    await tester.pumpWidget(DrAiApp(role: AppRole.patient));
    await tester.pumpAndSettle();

    expect(find.text('Today'), findsWidgets);
    expect(find.text('Recovery plan'), findsOneWidget);
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Medical Service'), findsOneWidget);
    expect(find.text('Recovery Plan'), findsOneWidget);
  });

  testWidgets('patient role cannot open doctor route', (tester) async {
    final app = DrAiApp(role: AppRole.patient);
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();

    app.router.go('/doctor');
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.lock_outline), findsOneWidget);
    expect(find.textContaining('selected role'), findsOneWidget);
  });
}
