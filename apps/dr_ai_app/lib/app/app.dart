import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DrAiApp extends ConsumerWidget {
  const DrAiApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final publicBetaSupportRoute = _isPublicBetaSupportRoute();
    if (auth.isLoading && !publicBetaSupportRoute) {
      return MaterialApp(
        title: 'Dr. AI',
        debugShowCheckedModeBanner: false,
        theme: DrAiTheme.light,
        builder: _focusTraversalBuilder,
        home: const SessionLoadingScreen(),
      );
    }
    final role = auth.value?.status == AuthStatus.signedIn
        ? auth.value?.user?.role
        : null;
    return MaterialApp.router(
      title: 'Dr. AI',
      debugShowCheckedModeBanner: false,
      theme: DrAiTheme.light,
      builder: _focusTraversalBuilder,
      routerConfig: createRouter(
        role,
        initialLocation: publicBetaSupportRoute ? '/beta-support' : null,
      ),
    );
  }

  bool _isPublicBetaSupportRoute() {
    final uri = Uri.base;
    return uri.path == '/beta-support' ||
        uri.fragment == '/beta-support' ||
        uri.fragment.startsWith('/beta-support?');
  }

  Widget _focusTraversalBuilder(BuildContext context, Widget? child) {
    return FocusTraversalGroup(
      policy: ReadingOrderTraversalPolicy(),
      child: child ?? const SizedBox.shrink(),
    );
  }
}

class SessionLoadingScreen extends StatelessWidget {
  const SessionLoadingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Semantics(
          label: 'Restoring secure session',
          child: const CircularProgressIndicator(),
        ),
      ),
    );
  }
}
