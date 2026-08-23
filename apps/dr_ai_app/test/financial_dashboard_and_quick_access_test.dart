import 'dart:async';

import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'fakes.dart';

Future<void> _pumpApp(
  WidgetTester tester,
  FakeDrAiRepository repository, {
  String? initialLocation,
  bool settle = true,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: DrAiApp(initialLocation: initialLocation),
    ),
  );
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    for (var index = 0; index < 8; index += 1) {
      await tester.pump(const Duration(milliseconds: 50));
    }
  }
}

void _setViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

String _location(WidgetTester tester) {
  final context = tester.element(find.byType(Scaffold).last);
  return GoRouter.of(context).routeInformationProvider.value.uri.toString();
}

CareCostLedgerData _emptyLedger() {
  return const CareCostLedgerData(
    patientId: 'patient-profile-test-id',
    patientDisplayName: 'Riley Demo Patient',
    actualTotalMinor: 0,
    estimatedTotalMinor: 0,
    finalTotalMinor: 0,
    payerRequestedTotalMinor: 0,
    patientResponsibilityTotalMinor: 0,
    pendingCostItemCount: 0,
    currency: 'CNY',
    events: <CareCostEventData>[],
  );
}

CareCostLedgerData _pendingLedger() {
  final item = CareCostItemData(
    id: 'pending-imaging-cost',
    clinicalEventId: 'clinical-event-test-id',
    itemType: 'imaging',
    label: 'Synthetic CT procedure',
    serviceDate: DateTime(2026, 8, 23),
    status: 'planned',
    pricingState: 'pending_cost',
    sourceType: 'imaging',
    sourceCategory: 'imaging',
    sourceStatus: 'scheduled',
    submissionEligible: false,
    ineligibilityReason: 'cost_pending',
    quantity: 1,
    currency: 'CNY',
    actualCostMinor: 0,
    payerRequestedMinor: 0,
    patientResponsibilityMinor: 0,
    aiReviewStatus: 'not_evaluated',
    createdAt: DateTime(2026, 8, 23),
    updatedAt: DateTime(2026, 8, 23),
  );
  return CareCostLedgerData(
    patientId: 'patient-profile-test-id',
    patientDisplayName: 'Riley Demo Patient',
    actualTotalMinor: 0,
    estimatedTotalMinor: 0,
    finalTotalMinor: 0,
    payerRequestedTotalMinor: 0,
    patientResponsibilityTotalMinor: 0,
    pendingCostItemCount: 1,
    currency: 'CNY',
    events: <CareCostEventData>[
      CareCostEventData(
        clinicalEventId: 'clinical-event-test-id',
        title: 'Synthetic imaging episode',
        status: 'active',
        actualTotalMinor: 0,
        payerRequestedTotalMinor: 0,
        patientResponsibilityTotalMinor: 0,
        currency: 'CNY',
        items: <CareCostItemData>[item],
      ),
    ],
  );
}

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues(<String, String>{});
  });

  testWidgets('dashboard and Care & Costs show the same server ledger values', (
    tester,
  ) async {
    _setViewport(tester, const Size(412, 917));
    await _pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
      ),
    );

    expect(find.text('Care & Costs summary'), findsOneWidget);
    expect(find.text('¥680.00'), findsOneWidget);
    expect(find.text('¥500.00'), findsOneWidget);
    expect(find.text('¥180.00'), findsOneWidget);
    expect(find.textContaining('demo credits'), findsNothing);

    await tester.ensureVisible(find.byKey(const Key('open-care-costs-button')));
    await tester.tap(find.byKey(const Key('open-care-costs-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('care-cost-ledger-list')), findsOneWidget);
    expect(find.text('¥680.00'), findsWidgets);
    expect(find.text('¥500.00'), findsWidgets);
    expect(find.text('¥180.00'), findsWidgets);
  });

  testWidgets('dashboard financial summary renders an empty state', (
    tester,
  ) async {
    _setViewport(tester, const Size(412, 917));
    await _pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
        careCostLedger: _emptyLedger(),
      ),
    );

    expect(
      find.text('No billable services or products have been recorded yet.'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('open-care-costs-button')), findsOneWidget);
  });

  testWidgets('dashboard financial summary renders pending costs explicitly', (
    tester,
  ) async {
    _setViewport(tester, const Size(412, 917));
    await _pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
        careCostLedger: _pendingLedger(),
      ),
    );

    expect(find.text('Costs still pending'), findsOneWidget);
    expect(find.text('1'), findsWidgets);
    expect(find.textContaining('demo credits'), findsNothing);
  });

  testWidgets(
    'dashboard financial summary renders and retries an error state',
    (tester) async {
      _setViewport(tester, const Size(412, 917));
      final repository = FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
        careCostError: const ApiError(
          code: 'service_unavailable',
          message: 'Unavailable',
          statusCode: 503,
        ),
      );
      await _pumpApp(tester, repository);

      expect(
        find.text('Care & Costs are temporarily unavailable.'),
        findsOneWidget,
      );
      expect(
        find.byKey(const Key('retry-dashboard-care-costs')),
        findsOneWidget,
      );
    },
  );

  testWidgets('dashboard financial summary renders a loading state', (
    tester,
  ) async {
    _setViewport(tester, const Size(412, 917));
    final completer = Completer<CareCostLedgerData>();
    await _pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        loginSession: patientSession,
        dashboard: patientDashboard,
        careCostCompleter: completer,
      ),
      settle: false,
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.byKey(const Key('open-care-costs-button')), findsOneWidget);
  });

  final destinations = <(String, String)>[
    ('imaging', '/doctor/patients?section=imaging'),
    ('medical-records', '/doctor/patients?section=medicalHistory'),
    ('recovery-plans', '/doctor/patients?section=recoveryPlans'),
    ('resources', '/doctor/resources'),
    ('payer-requests', '/doctor/payer-requests'),
  ];
  for (final destination in destinations) {
    testWidgets(
      'Quick Access ${destination.$1} reaches its exact destination',
      (tester) async {
        _setViewport(tester, const Size(1280, 1000));
        await _pumpApp(
          tester,
          FakeDrAiRepository(
            restoredSession: doctorSession,
            dashboard: doctorDashboard,
          ),
        );
        final card = find.byKey(Key('doctor-quick-access-${destination.$1}'));
        await tester.ensureVisible(card);
        tester.widget<InkWell>(card).onTap!();
        await tester.pumpAndSettle();

        expect(_location(tester), destination.$2);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('doctor mobile navigation uses compact single-line labels', (
    tester,
  ) async {
    _setViewport(tester, const Size(390, 844));
    await _pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: doctorSession,
        dashboard: doctorDashboard,
      ),
    );

    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Dashboard'), findsNothing);
    await tester.tap(find.byIcon(Icons.people_outline).last);
    await tester.pumpAndSettle();
    expect(find.text('Patients'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('imaging deep link without patient opens imaging selection', (
    tester,
  ) async {
    _setViewport(tester, const Size(412, 917));
    await _pumpApp(
      tester,
      FakeDrAiRepository(restoredSession: doctorSession),
      initialLocation: '/doctor/patients?section=imaging',
    );

    expect(find.byKey(const Key('patient-detail-empty')), findsOneWidget);
    expect(find.text('Select a patient'), findsOneWidget);
    expect(_location(tester), '/doctor/patients?section=imaging');
  });

  testWidgets('imaging patient selection persists context in the URL', (
    tester,
  ) async {
    _setViewport(tester, const Size(1280, 1000));
    await _pumpApp(
      tester,
      FakeDrAiRepository(restoredSession: doctorSession),
      initialLocation: '/doctor/patients?section=imaging',
    );

    await tester.tap(find.byKey(const Key('patient-row-SYN-PATIENT-001')));
    await tester.pumpAndSettle();

    expect(
      _location(tester),
      '/doctor/patients?section=imaging&patient=patient-profile-test-id',
    );
    expect(
      find.byKey(const Key('imaging-clinical-service-panel')),
      findsOneWidget,
    );
  });

  testWidgets('imaging deep link preserves selected patient and event context', (
    tester,
  ) async {
    _setViewport(tester, const Size(1280, 1000));
    const location =
        '/doctor/patients?section=imaging&patient=patient-profile-test-id&event=clinical-event-test-id';
    await _pumpApp(
      tester,
      FakeDrAiRepository(restoredSession: doctorSession),
      initialLocation: location,
    );

    expect(
      find.byKey(const Key('selected-patient-summary-header')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('imaging-clinical-service-panel')),
      findsOneWidget,
    );
    expect(_location(tester), location);
  });

  testWidgets('Quick Access imaging preserves browser Back to dashboard', (
    tester,
  ) async {
    _setViewport(tester, const Size(1280, 1000));
    await _pumpApp(
      tester,
      FakeDrAiRepository(
        restoredSession: doctorSession,
        dashboard: doctorDashboard,
      ),
    );
    final card = find.byKey(const Key('doctor-quick-access-imaging'));
    await tester.ensureVisible(card);
    tester.widget<InkWell>(card).onTap!();
    await tester.pumpAndSettle();
    expect(_location(tester), '/doctor/patients?section=imaging');

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(Uri.parse(_location(tester)).path, '/doctor');
    expect(
      find.byKey(const Key('doctor-quick-access-imaging')),
      findsOneWidget,
    );
  });
}
