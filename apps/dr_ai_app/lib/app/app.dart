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
  const DrAiApp({this.initialLocation, super.key});

  final String? initialLocation;

  @override
  ConsumerState<DrAiApp> createState() => _DrAiAppState();
}

class _DrAiAppState extends ConsumerState<DrAiApp> {
  late GoRouter _router;
  late final RouterSessionState _routerSession;
  bool _authTransitionStartedSignedIn = false;

  @override
  void initState() {
    super.initState();
    _routerSession = RouterSessionState.hydrating();
    _router = createRouter(
      null,
      initialLocation: widget.initialLocation ?? initialAppLocation(Uri.base),
      sessionState: _routerSession,
    );
    ref.listenManual<AsyncValue<AuthState>>(authControllerProvider, (
      previous,
      next,
    ) {
      if (next.isLoading) {
        _authTransitionStartedSignedIn =
            previous?.value?.status == AuthStatus.signedIn;
        _routerSession.setHydrating();
        return;
      }
      final auth = next.value;
      if (auth?.status == AuthStatus.signedIn && auth?.user != null) {
        _authTransitionStartedSignedIn = false;
        _routerSession.setSignedIn(auth!.user!.role);
        return;
      }
      final explicitLogout =
          _authTransitionStartedSignedIn && auth?.noticeMessage != null;
      _authTransitionStartedSignedIn = false;
      _routerSession.setSignedOut(clearPending: explicitLogout);
    }, fireImmediately: true);
  }

  @override
  void dispose() {
    _router.dispose();
    _routerSession.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final locale = ref.watch(localeControllerProvider);
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

  Widget _focusTraversalBuilder(BuildContext context, Widget? child) {
    return FocusTraversalGroup(
      policy: ReadingOrderTraversalPolicy(),
      child: child ?? const SizedBox.shrink(),
    );
  }
}
