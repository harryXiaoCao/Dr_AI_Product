import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/l10n/locale_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class DrAiApp extends ConsumerStatefulWidget {
  const DrAiApp({super.key});

  @override
  ConsumerState<DrAiApp> createState() => _DrAiAppState();
}

class _DrAiAppState extends ConsumerState<DrAiApp> {
  late GoRouter _router;
  AppRole? _routerRole;
  late final bool _publicBetaSupportRoute;

  @override
  void initState() {
    super.initState();
    _publicBetaSupportRoute = _isPublicBetaSupportRoute();
    _router = createRouter(
      null,
      initialLocation: _publicBetaSupportRoute ? '/beta-support' : null,
    );
  }

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final locale = ref.watch(localeControllerProvider);
    if (auth.isLoading && !_publicBetaSupportRoute) {
      return MaterialApp(
        onGenerateTitle: (context) => context.l10n.appName,
        initialRoute: '/',
        debugShowCheckedModeBanner: false,
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        localeResolutionCallback: resolveDrAiLocale,
        builder: _focusTraversalBuilder,
        onGenerateRoute: (settings) => MaterialPageRoute<void>(
          settings: settings,
          builder: (context) => const SessionLoadingScreen(),
        ),
        home: const SessionLoadingScreen(),
      );
    }
    final role = auth.value?.status == AuthStatus.signedIn
        ? auth.value?.user?.role
        : null;
    if (_routerRole != role) {
      _router.dispose();
      _router = createRouter(
        role,
        initialLocation: _publicBetaSupportRoute ? '/beta-support' : null,
      );
      _routerRole = role;
    }
    return MaterialApp.router(
      onGenerateTitle: (context) => context.l10n.appName,
      debugShowCheckedModeBanner: false,
      theme: DrAiTheme.light,
      locale: locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      localeResolutionCallback: resolveDrAiLocale,
      builder: _focusTraversalBuilder,
      routerConfig: _router,
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
          label: context.l10n.restoringSession,
          child: const CircularProgressIndicator(),
        ),
      ),
    );
  }
}
