import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/features/auth/presentation/legal_placeholder_screen.dart';
import 'package:dr_ai_app/features/auth/presentation/login_screen.dart';
import 'package:dr_ai_app/features/beta/presentation/beta_support_screen.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_dashboard_screen.dart';
import 'package:dr_ai_app/features/doctor/presentation/patient_management_screen.dart';
import 'package:dr_ai_app/features/foundation/presentation/unauthorized_screen.dart';
import 'package:dr_ai_app/features/patient/presentation/patient_dashboard_screen.dart';
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
        return path == '/login' || publicLegalPath ? null : '/login';
      }
      if (path == '/login') {
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
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
        path: '/doctor',
        builder: (context, state) => const DoctorDashboardScreen(),
        routes: <RouteBase>[
          GoRoute(
            path: 'patients',
            builder: (context, state) => const PatientManagementScreen(),
          ),
        ],
      ),
      GoRoute(
        path: '/patient',
        builder: (context, state) => const PatientDashboardScreen(),
      ),
      GoRoute(
        path: '/privacy',
        builder: (context, state) => const BetaSupportScreen(),
      ),
      GoRoute(
        path: '/terms',
        builder: (context, state) =>
            const LegalPlaceholderScreen(title: 'Terms of Service'),
      ),
      GoRoute(
        path: '/privacy-policy',
        builder: (context, state) =>
            const LegalPlaceholderScreen(title: 'Privacy Policy'),
      ),
      GoRoute(
        path: '/unauthorized',
        builder: (context, state) => UnauthorizedScreen(role: role),
      ),
    ],
  );
}
