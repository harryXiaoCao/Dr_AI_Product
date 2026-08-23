import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

RecoveryPlanData planWithTasks(
  List<RecoveryTaskItem> tasks, {
  String planId = 'recovery-plan-test-id',
  String title = 'Synthetic Week 3 Recovery Plan',
}) {
  final completed = tasks.where((task) => task.isCompleted).length;
  final percent = tasks.isEmpty ? 0 : (completed * 100 / tasks.length).round();
  return RecoveryPlanData(
    planId: planId,
    patientId: demoRecoveryPlan.patientId,
    clinicalEventId: demoRecoveryPlan.clinicalEventId,
    title: title,
    instructions: demoRecoveryPlan.instructions,
    status: 'active',
    reviewStatus: 'approved',
    safetyLabel: demoRecoveryPlan.safetyLabel,
    createdAt: demoRecoveryPlan.createdAt,
    updatedAt: demoRecoveryPlan.updatedAt,
    approvedAt: demoRecoveryPlan.approvedAt,
    activatedAt: demoRecoveryPlan.activatedAt,
    progressSummary: RecoveryPlanProgressData(
      taskCount: tasks.length,
      completedTaskCount: completed,
      remainingTaskCount: tasks.length - completed,
      completionPercent: percent,
    ),
    tasks: tasks,
  );
}

PatientTodayData todayFor(RecoveryPlanData plan) => PatientTodayData(
  safetyLabel: plan.safetyLabel,
  activePlan: plan,
  progressSummary: plan.progressSummary,
  tasks: plan.tasks,
);

Future<void> pumpRecovery(
  WidgetTester tester,
  FakeDrAiRepository repository,
) async {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = const Size(1280, 1400);
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: const DrAiApp(initialLocation: '/patient/recovery-plan'),
    ),
  );
  await tester.pumpAndSettle();
}

void expectProgress(
  WidgetTester tester, {
  required String active,
  required String history,
}) {
  expect(
    tester
        .widget<Text>(find.byKey(const Key('patient-recovery-active-progress')))
        .data,
    active,
  );
  expect(
    tester
        .widget<Text>(
          find.byKey(
            const Key(
              'patient-recovery-history-progress-recovery-plan-test-id',
            ),
          ),
        )
        .data,
    contains(history),
  );
}

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues(<String, String>{});
  });

  testWidgets('active plan and history stay consistent through completion', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      patientCareBundle: patientCareBundleWithRecoveryPlans([demoRecoveryPlan]),
      patientToday: demoPatientToday,
    );
    await pumpRecovery(tester, repository);
    expectProgress(tester, active: '0/4 complete - 0%', history: '0% complete');

    await tester.tap(find.byKey(const Key('today-task-medication')));
    await tester.pumpAndSettle();
    expectProgress(
      tester,
      active: '1/4 complete - 25%',
      history: '25% complete',
    );
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const Key('today-task-medication')),
          )
          .value,
      isTrue,
    );

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    await pumpRecovery(tester, repository);
    expectProgress(
      tester,
      active: '1/4 complete - 25%',
      history: '25% complete',
    );

    await tester.tap(find.byKey(const Key('today-task-medication')));
    await tester.pumpAndSettle();
    expectProgress(tester, active: '0/4 complete - 0%', history: '0% complete');
  });

  testWidgets('failed completion rolls back coherently and allows retry', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      patientCareBundle: patientCareBundleWithRecoveryPlans([demoRecoveryPlan]),
      patientToday: demoPatientToday,
      completionError: const ApiError(
        code: 'service_unavailable',
        message: 'Synthetic failure',
        statusCode: 503,
      ),
    );
    await pumpRecovery(tester, repository);

    await tester.tap(find.byKey(const Key('today-task-medication')));
    await tester.pumpAndSettle();

    expectProgress(tester, active: '0/4 complete - 0%', history: '0% complete');
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const Key('today-task-medication')),
          )
          .value,
      isFalse,
    );
    expect(
      find.byKey(const Key('patient-recovery-sync-error')),
      findsOneWidget,
    );

    repository.completionError = null;
    await tester.tap(find.byKey(const Key('today-task-medication')));
    await tester.pumpAndSettle();
    expectProgress(
      tester,
      active: '1/4 complete - 25%',
      history: '25% complete',
    );
  });

  testWidgets('zero-task and fully complete plans render persisted progress', (
    tester,
  ) async {
    final empty = planWithTasks(const <RecoveryTaskItem>[]);
    await pumpRecovery(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        patientCareBundle: patientCareBundleWithRecoveryPlans([empty]),
        patientToday: todayFor(empty),
      ),
    );
    expectProgress(tester, active: '0/0 complete - 0%', history: '0% complete');

    final completedTasks = demoRecoveryPlan.tasks
        .map(
          (task) => RecoveryTaskItem(
            taskId: task.taskId,
            planId: task.planId,
            category: task.category,
            title: task.title,
            detail: task.detail,
            dueLabel: task.dueLabel,
            notificationTime: task.notificationTime,
            medicationId: task.medicationId,
            isCompleted: true,
            completedAt: DateTime(2026, 8, 13),
            notificationStatus: task.notificationStatus,
          ),
        )
        .toList();
    final complete = planWithTasks(completedTasks);
    await pumpRecovery(
      tester,
      FakeDrAiRepository(
        restoredSession: patientSession,
        patientCareBundle: patientCareBundleWithRecoveryPlans([complete]),
        patientToday: todayFor(complete),
      ),
    );
    expectProgress(
      tester,
      active: '4/4 complete - 100%',
      history: '100% complete',
    );
  });

  testWidgets('multiple history plans retain independent percentages', (
    tester,
  ) async {
    final older = planWithTasks(
      demoRecoveryPlan.tasks.take(1).toList(),
      planId: 'older-plan',
      title: 'Older synthetic plan',
    );
    final repository = FakeDrAiRepository(
      restoredSession: patientSession,
      patientCareBundle: patientCareBundleWithRecoveryPlans([
        demoRecoveryPlan,
        older,
      ]),
      patientToday: demoPatientToday,
    );
    await pumpRecovery(tester, repository);

    expectProgress(tester, active: '0/4 complete - 0%', history: '0% complete');
    expect(
      tester
          .widget<Text>(
            find.byKey(
              const Key('patient-recovery-history-progress-older-plan'),
            ),
          )
          .data,
      contains('0% complete'),
    );
  });
}
