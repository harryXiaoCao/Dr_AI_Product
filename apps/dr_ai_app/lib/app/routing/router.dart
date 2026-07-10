import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/features/auth/presentation/legal_placeholder_screen.dart';
import 'package:dr_ai_app/features/auth/presentation/login_screen.dart';
import 'package:dr_ai_app/features/beta/presentation/beta_support_screen.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_dashboard_screen.dart';
import 'package:dr_ai_app/features/doctor/presentation/patient_management_screen.dart';
import 'package:dr_ai_app/features/foundation/presentation/unauthorized_screen.dart';
import 'package:dr_ai_app/features/patient/presentation/patient_contacts_screen.dart';
import 'package:dr_ai_app/features/patient/presentation/patient_dashboard_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

GoRouter createRouter(AppRole? role, {String? initialLocation}) {
  final homePath = switch (role) {
    AppRole.doctor => '/doctor',
    AppRole.patient => '/patient',
    AppRole.unsupported => '/unauthorized',
    null => '/login',
  };
  return GoRouter(
    initialLocation: initialLocation,
    redirect: (BuildContext context, GoRouterState state) {
      final path = state.uri.path;
      if (path == '/') {
        return role == null ? '/login' : homePath;
      }
      if (path == '/beta-support') {
        return '/privacy';
      }
      final publicLegalPath =
          path == '/privacy' || path == '/terms' || path == '/privacy-policy';
      if (role == null) {
        return path == '/login' || path == '/register' || publicLegalPath
            ? null
            : '/login';
      }
      if (path == '/login' || path == '/register') {
        return homePath;
      }
      if (role == AppRole.unsupported) {
        return path == '/unauthorized' || publicLegalPath
            ? null
            : '/unauthorized';
      }
      if (path.startsWith('/doctor') && role != AppRole.doctor) {
        return '/unauthorized';
      }
      if (path.startsWith('/patient') && role != AppRole.patient) {
        return '/unauthorized';
      }
      return null;
    },
    routes: <RouteBase>[
      GoRoute(
        path: '/login',
        pageBuilder: (context, state) => _drAiPage(state, const LoginScreen()),
      ),
      GoRoute(
        path: '/register',
        pageBuilder: (context, state) =>
            _drAiPage(state, const LoginScreen(initiallyRegistering: true)),
      ),
      GoRoute(
        path: '/doctor',
        pageBuilder: (context, state) =>
            _drAiPage(state, const DoctorDashboardScreen()),
        routes: <RouteBase>[
          GoRoute(
            path: 'patients',
            pageBuilder: (context, state) =>
                _drAiPage(state, const PatientManagementScreen()),
          ),
          GoRoute(
            path: 'account',
            pageBuilder: (context, state) =>
                _drAiPage(state, const DoctorAccountScreen()),
          ),
        ],
      ),
      GoRoute(
        path: '/patient',
        pageBuilder: (context, state) =>
            _drAiPage(state, const PatientDashboardScreen()),
        routes: <RouteBase>[
          GoRoute(
            path: 'contact',
            pageBuilder: (context, state) =>
                _drAiPage(state, const PatientContactsScreen()),
          ),
          GoRoute(
            path: 'medical-service',
            redirect: (context, state) => '/patient',
          ),
          GoRoute(
            path: 'recovery-plan',
            pageBuilder: (context, state) =>
                _drAiPage(state, const PatientRecoveryPlanScreen()),
          ),
          GoRoute(
            path: 'account',
            pageBuilder: (context, state) =>
                _drAiPage(state, const PatientAccountScreen()),
          ),
        ],
      ),
      GoRoute(
        path: '/privacy',
        pageBuilder: (context, state) =>
            _drAiPage(state, const BetaSupportScreen()),
      ),
      GoRoute(
        path: '/terms',
        pageBuilder: (context, state) => _drAiPage(
          state,
          LegalPlaceholderScreen(title: context.l10n.termsOfService),
        ),
      ),
      GoRoute(
        path: '/privacy-policy',
        pageBuilder: (context, state) => _drAiPage(
          state,
          LegalPlaceholderScreen(title: context.l10n.privacyPolicy),
        ),
      ),
      GoRoute(
        path: '/unauthorized',
        pageBuilder: (context, state) =>
            _drAiPage(state, UnauthorizedScreen(role: role)),
      ),
    ],
  );
}

CustomTransitionPage<void> _drAiPage(GoRouterState state, Widget child) {
  return CustomTransitionPage<void>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 280),
    reverseTransitionDuration: const Duration(milliseconds: 210),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      if (MediaQuery.maybeOf(context)?.disableAnimations ?? false) {
        return child;
      }
      final eased = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOutCubic,
        reverseCurve: Curves.easeInCubic,
      );
      final exit = CurvedAnimation(
        parent: secondaryAnimation,
        curve: Curves.easeOutCubic,
      );
      return FadeTransition(
        opacity: eased,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0.035, 0),
            end: Offset.zero,
          ).animate(eased),
          child: ScaleTransition(
            scale: Tween<double>(begin: 0.992, end: 1).animate(eased),
            child: FadeTransition(
              opacity: Tween<double>(begin: 1, end: 0.92).animate(exit),
              child: child,
            ),
          ),
        ),
      );
    },
  );
}
