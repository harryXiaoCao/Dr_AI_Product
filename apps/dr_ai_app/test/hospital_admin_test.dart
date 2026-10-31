import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/hospital_admin/presentation/hospital_admin_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

class AdminRepository extends FakeDrAiRepository {
  AdminRepository({required this.workspace, this.fail = false});

  final Map<String, dynamic> workspace;
  final bool fail;
  String? changedBookingStatus;

  @override
  Future<Map<String, dynamic>> loadHospitalWorkspace({
    String? clinicId,
    String? status,
    int page = 1,
  }) async {
    if (fail) throw StateError('offline');
    return workspace;
  }

  @override
  Future<void> updateHospitalBooking(
    String id,
    Map<String, dynamic> data,
  ) async {
    changedBookingStatus = data['status'] as String;
  }
}

Map<String, dynamic> _workspace({bool empty = false}) => <String, dynamic>{
  'hospital': <String, dynamic>{
    'id': 'hospital-a',
    'name': 'Synthetic Hospital',
  },
  'clinics': <Map<String, dynamic>>[
    <String, dynamic>{'id': 'clinic-a', 'name': 'Imaging'},
  ],
  'counts': <String, dynamic>{
    'equipment_requests': <String, int>{'requested': empty ? 0 : 1},
    'appointments': <String, int>{'completed': 2},
  },
  'bookings': empty
      ? <Map<String, dynamic>>[]
      : <Map<String, dynamic>>[
          <String, dynamic>{
            'id': 'booking-a',
            'clinic_id': 'clinic-a',
            'clinic_name': 'Imaging',
            'equipment': 'Scanner 1',
            'status': 'requested',
            'purpose': 'Synthetic scan',
            'start_at': '2026-10-01T10:00:00Z',
          },
        ],
  'resources': <Map<String, dynamic>>[],
  'staff': <Map<String, dynamic>>[],
  'total': empty ? 0 : 1,
};

Future<void> _show(
  WidgetTester tester,
  AdminRepository repository, {
  Size size = const Size(1100, 900),
  Locale locale = const Locale('en'),
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: const HospitalAdminScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'shows scoped operational counts and reason-gated request actions',
    (tester) async {
      final repository = AdminRepository(workspace: _workspace());
      await _show(tester, repository);
      expect(find.text('Synthetic Hospital'), findsOneWidget);
      expect(find.textContaining('Completed: 2'), findsOneWidget);
      await tester.tap(find.text('Requests').first);
      await tester.pumpAndSettle();
      expect(find.textContaining('Scanner 1'), findsOneWidget);
      await tester.tap(find.widgetWithText(OutlinedButton, 'Approve'));
      await tester.pumpAndSettle();
      expect(find.text('Reason for audit record'), findsOneWidget);
      await tester.enterText(find.byType(TextField).last, 'Capacity verified');
      await tester.pumpAndSettle();
      await tester.tap(find.text('Confirm'));
      await tester.pumpAndSettle();
      expect(repository.changedBookingStatus, 'approved');
    },
  );

  testWidgets('shows Chinese empty state on a narrow screen', (tester) async {
    await _show(
      tester,
      AdminRepository(workspace: _workspace(empty: true)),
      size: const Size(390, 844),
      locale: const Locale('zh'),
    );
    expect(find.text('医院运营工作台'), findsOneWidget);
    await tester.tap(find.text('申请').first);
    await tester.pumpAndSettle();
    expect(find.text('没有符合筛选条件的预约。'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('shows retry state when loading fails', (tester) async {
    await _show(tester, AdminRepository(workspace: _workspace(), fail: true));
    expect(find.text('Unable to load hospital data.'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
  });
}
