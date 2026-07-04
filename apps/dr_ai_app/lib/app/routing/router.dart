import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/features/auth/presentation/login_screen.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_dashboard_screen.dart';
import 'package:dr_ai_app/features/foundation/presentation/unauthorized_screen.dart';
import 'package:dr_ai_app/features/patient/presentation/patient_dashboard_screen.dart';
import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

GoRouter createRouter(AppRole? role) {
  final homePath = role == AppRole.patient ? '/patient' : '/doctor';
  return GoRouter(
    initialLocation: role == null ? '/login' : homePath,
    redirect: (BuildContext context, GoRouterState state) {
      final path = state.uri.path;
      if (role == null) {
        return path == '/login' ? null : '/login';
      }
      if (path == '/login') {
        return homePath;
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
      ),
      GoRoute(
        path: '/patient',
        builder: (context, state) => const PatientDashboardScreen(),
      ),
      GoRoute(
        path: '/unauthorized',
        builder: (context, state) => UnauthorizedScreen(role: role),
      ),
    ],
  );
}
