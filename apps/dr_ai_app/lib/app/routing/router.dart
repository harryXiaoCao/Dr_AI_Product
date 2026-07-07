import 'package:dr_ai_app/app/routing/app_role.dart';
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
      if (role == null) {
        return path == '/login' || path == '/beta-support' ? null : '/login';
      }
      if (path == '/login') {
        return homePath;
      }
      if (role == AppRole.unsupported) {
        return path == '/unauthorized' || path == '/beta-support'
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
        path: '/beta-support',
        builder: (context, state) => const BetaSupportScreen(),
      ),
      GoRoute(
        path: '/unauthorized',
        builder: (context, state) => UnauthorizedScreen(role: role),
      ),
    ],
  );
}
