import 'package:dr_ai_app/shared/widgets/navigation_back_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  testWidgets('deep-linked detail returns to its section', (tester) async {
    final router = GoRouter(
      initialLocation: '/detail',
      routes: <RouteBase>[
        GoRoute(path: '/section', builder: (_, _) => const Text('Section')),
        GoRoute(
          path: '/detail',
          builder: (_, _) => const Scaffold(
            body: NavigationBackButton(fallbackPath: '/section'),
          ),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.tap(find.byTooltip('Back'));
    await tester.pumpAndSettle();
    expect(router.routeInformationProvider.value.uri.path, '/section');
  });

  testWidgets('pushed detail returns to the actual previous page', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/section',
      routes: <RouteBase>[
        GoRoute(
          path: '/section',
          builder: (context, _) => Scaffold(
            body: TextButton(
              onPressed: () => context.push('/detail'),
              child: const Text('Open'),
            ),
          ),
        ),
        GoRoute(
          path: '/detail',
          builder: (_, _) => const Scaffold(
            body: NavigationBackButton(fallbackPath: '/wrong-fallback'),
          ),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Back'));
    await tester.pumpAndSettle();
    expect(router.routeInformationProvider.value.uri.path, '/section');
  });
}
