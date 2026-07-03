import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_dashboard_screen.dart';
import 'package:dr_ai_app/features/foundation/presentation/unauthorized_screen.dart';
import 'package:dr_ai_app/features/patient/presentation/patient_dashboard_screen.dart';
import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

GoRouter createRouter(AppRole role) {
  return GoRouter(
    initialLocation: role == AppRole.doctor ? '/doctor' : '/patient',
    redirect: (BuildContext context, GoRouterState state) {
      final path = state.uri.path;
      final isDoctorRoute = path.startsWith('/doctor');
      final isPatientRoute = path.startsWith('/patient');

      if (isDoctorRoute && role != AppRole.doctor) {
        return '/unauthorized';
      }
      if (isPatientRoute && role != AppRole.patient) {
        return '/unauthorized';
      }
      return null;
    },
    routes: <RouteBase>[
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
        builder: (context, state) => const UnauthorizedScreen(),
      ),
    ],
  );
}
