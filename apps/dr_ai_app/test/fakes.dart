import 'dart:async';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';

const doctorUser = SessionUser(
  id: 'doctor-test-id',
  email: 'doctor.demo@example.com',
  role: AppRole.doctor,
  displayName: 'Dr. Avery Demo',
);

const patientUser = SessionUser(
  id: 'patient-test-id',
  email: 'patient.demo@example.com',
  role: AppRole.patient,
  displayName: 'Riley Demo Patient',
);

const doctorSession = AuthSession(
  accessToken: 'test-access',
  refreshToken: 'test-refresh',
  user: doctorUser,
);

const patientSession = AuthSession(
  accessToken: 'test-access',
  refreshToken: 'test-refresh',
  user: patientUser,
);

final doctorDashboard = DashboardData(
  role: AppRole.doctor,
  data: <String, dynamic>{
    'safety_label':
        'Synthetic demonstration data only. Do not enter real patient data.',
    'hospital': <String, dynamic>{
      'name': 'Synthetic Community Hospital',
      'location': 'Demo County',
      'summary': 'Invited beta facility using synthetic demonstration data.',
    },
    'doctor': <String, dynamic>{
      'name': 'Dr. Avery Demo',
      'title': 'Head of Synthetic Community Hospital',
      'expertise': 'Synthetic care coordination',
      'rating': 4,
    },
    'quick_access': <String>[
      'AI Supported CT Image Diagnose',
      'AI Supported X-ray Image Diagnose',
      'AI Supported MRI Image Diagnose',
      'Check Patient Medical Records',
      'Check Patient Recovery Plans',
      'Check Imaging Results',
      'Book Medical Equipment',
    ],
    'recent_activity': <String, dynamic>{
      'title': 'Synthetic Patient - Demonstration follow-up',
      'time': '20:00',
    },
    'resources': <Map<String, dynamic>>[
      <String, dynamic>{'name': 'CT', 'available': 1, 'total': 2},
      <String, dynamic>{'name': 'MRI', 'available': 1, 'total': 1},
    ],
    'team': <String>['Dr. Rowan Demo', 'Dr. Lee Demo', 'Dr. Zhao Demo'],
  },
);

final patientDashboard = DashboardData(
  role: AppRole.patient,
  data: <String, dynamic>{
    'safety_label':
        'Synthetic demonstration data only. Do not enter real patient data.',
    'recovery_days': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': 'Today',
        'tasks': <String>[
          '50mg demo medication fixture',
          'Drink plenty of water',
          'Avoid triggers',
        ],
      },
      <String, dynamic>{
        'label': 'Jan. 2',
        'tasks': <String>[
          'Drink plenty of water',
          'Avoid triggers',
          'Contact the demo hospital if needed',
        ],
      },
      <String, dynamic>{
        'label': 'Jan. 3',
        'tasks': <String>[
          'Drink plenty of water',
          'Avoid triggers',
          'Goal: begin light demo activities',
        ],
      },
    ],
    'doctor': <String, dynamic>{
      'name': 'Dr. Avery Demo',
      'title': 'Head of Synthetic Community Hospital',
      'expertise': 'Synthetic care coordination',
    },
    'fee_items': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': 'Consultation',
        'amount': '10 demo credits',
        'selected': true,
      },
      <String, dynamic>{
        'label': 'Blood Test',
        'amount': '50 demo credits',
        'selected': true,
      },
      <String, dynamic>{
        'label': 'Medication',
        'amount': '120 demo credits',
        'selected': true,
      },
      <String, dynamic>{
        'label': 'Ambulance Service',
        'amount': '50 demo credits',
        'selected': false,
      },
    ],
    'medical_records': <Object>[],
    'imaging_results': <Object>[],
  },
);

class FakeDrAiRepository implements DrAiRepository {
  FakeDrAiRepository({
    this.restoredSession,
    this.loginSession = doctorSession,
    DashboardData? dashboard,
    this.loginError,
    this.dashboardError,
    this.loginCompleter,
  }) : dashboard = dashboard ?? doctorDashboard;

  AuthSession? restoredSession;
  AuthSession loginSession;
  DashboardData dashboard;
  ApiError? loginError;
  ApiError? dashboardError;
  Completer<AuthSession>? loginCompleter;
  bool logoutCalled = false;

  @override
  Future<AuthSession?> restore() async => restoredSession;

  @override
  Future<AuthSession> login(String email, String password) async {
    if (loginCompleter != null) {
      return loginCompleter!.future;
    }
    if (loginError != null) {
      throw loginError!;
    }
    return loginSession;
  }

  @override
  Future<void> logout() async {
    logoutCalled = true;
    restoredSession = null;
  }

  @override
  Future<DashboardData> loadDashboard(AppRole role) async {
    if (dashboardError != null) {
      throw dashboardError!;
    }
    return dashboard;
  }
}
