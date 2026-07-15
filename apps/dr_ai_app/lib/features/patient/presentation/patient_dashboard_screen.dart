import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/presentation/signup_reference_data.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/l10n/locale_controller.dart';
import 'package:dr_ai_app/shared/avatar/avatar_upload.dart';
import 'package:dr_ai_app/shared/widgets/account_security.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:dr_ai_app/shared/widgets/sign_out_button.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PatientDashboardScreen extends ConsumerWidget {
  const PatientDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      child: dashboard.when(
        loading: () => const DashboardLoadingView(),
        error: (error, stackTrace) => DashboardErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(dashboardProvider),
        ),
        data: (data) => _PatientDashboard(data: data),
      ),
    );
  }
}

class PatientAccountScreen extends ConsumerWidget {
  const PatientAccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final care = ref.watch(ownPatientCareProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 3,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: care.when(
              loading: () =>
                  DashboardLoadingView(label: context.l10n.loadingAccount),
              error: (error, stackTrace) => DashboardErrorView(
                message: context.l10n.loadAccountFailed,
                onRetry: () => ref.invalidate(ownPatientCareProvider),
              ),
              data: (bundle) => _PatientAccountView(bundle: bundle),
            ),
          ),
        ),
      ),
    );
  }
}

class PatientRecoveryPlanScreen extends ConsumerWidget {
  const PatientRecoveryPlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final care = ref.watch(ownPatientCareProvider);
    final today = ref.watch(patientTodayProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: care.when(
              loading: () => DashboardLoadingView(
                label: context.l10n.loadingRecoveryPlans,
              ),
              error: (error, stackTrace) => DashboardErrorView(
                message: context.l10n.loadRecoveryPlansFailed,
                onRetry: () {
                  ref.invalidate(ownPatientCareProvider);
                  ref.invalidate(patientTodayProvider);
                },
              ),
              data: (bundle) => _PatientRecoveryPlanView(
                bundle: bundle,
                today: today,
                onRetry: () {
                  ref.invalidate(ownPatientCareProvider);
                  ref.invalidate(patientTodayProvider);
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PatientDashboard extends ConsumerWidget {
  const _PatientDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final care = ref.watch(ownPatientCareProvider);
    switch (care) {
      case AsyncData(:final value)
          when !value.patient.medicalHistorySetupCompleted:
        return _PatientMedicalSurveyScreen(
          care: care,
          onRetry: () => ref.invalidate(ownPatientCareProvider),
        );
      case AsyncLoading():
        return DashboardLoadingView(label: context.l10n.loadingProfile);
      case AsyncError():
        return DashboardErrorView(
          message: context.l10n.loadProfileFailed,
          onRetry: () => ref.invalidate(ownPatientCareProvider),
        );
      case _:
        break;
    }
    final dashboardData = _patientDashboardData(context, data.data);
    final fees = List<Map<String, dynamic>>.from(
      (dashboardData['fee_items'] as List).map(
        (item) => Map<String, dynamic>.from(item as Map),
      ),
    );
    final hasRecords = (dashboardData['medical_records'] as List).isNotEmpty;
    final hasImages = (dashboardData['imaging_results'] as List).isNotEmpty;
    final today = ref.watch(patientTodayProvider);
    final notifications = ref.watch(medicationNotificationShellProvider);
    final textScale = MediaQuery.textScalerOf(context).scale(1);
    final cardScale = textScale.clamp(1.0, 1.6).toDouble();

    return ColoredBox(
      color: DrAiColors.pageBackground,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: ListView(
            key: const Key('patient-dashboard-list'),
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 5),
            children: <Widget>[
              SizedBox(
                height: 420 * cardScale,
                child: _PatientSection(
                  title: context.l10n.today,
                  child: _PatientTodayCard(
                    today: today,
                    care: care,
                    notifications: notifications,
                    onRetry: () {
                      ref.invalidate(patientTodayProvider);
                      ref.invalidate(medicationNotificationShellProvider);
                      ref.invalidate(ownPatientCareProvider);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 300 * cardScale,
                child: _PatientSection(
                  title: context.l10n.medicalFee,
                  child: _MedicalFee(items: fees),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 334 * cardScale,
                child: _PatientSection(
                  title: context.l10n.askDrAi,
                  child: const _EducationalChatCard(),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 118 * cardScale,
                child: _PatientSection(
                  title: context.l10n.careRecords,
                  child: _CareRecordStatus(
                    hasRecords: hasRecords,
                    hasImages: hasImages,
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Text(
                dashboardData['safety_label'] as String,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 6),
            ],
          ),
        ),
      ),
    );
  }
}

Map<String, dynamic> _patientDashboardData(
  BuildContext context,
  Map<String, dynamic> source,
) {
  if (source.containsKey('recovery_days') &&
      source.containsKey('doctor') &&
      source.containsKey('fee_items')) {
    return source;
  }
  return <String, dynamic>{
    'safety_label': context.l10n.stagingNotice,
    'recovery_days': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': context.l10n.today,
        'tasks': <String>[
          context.l10n.completeProfileSetup,
          context.l10n.sharePatientCode,
          context.l10n.waitDoctorConnect,
        ],
      },
      <String, dynamic>{
        'label': context.l10n.next,
        'tasks': <String>[
          context.l10n.reviewMedicalHistory,
          context.l10n.confirmContactPreferences,
          context.l10n.prepareDoctorQuestions,
        ],
      },
      <String, dynamic>{
        'label': context.l10n.after,
        'tasks': <String>[
          context.l10n.followCareTasks,
          context.l10n.trackRecovery,
          context.l10n.checkMedicationsImaging,
        ],
      },
    ],
    'doctor': <String, dynamic>{
      'name': context.l10n.doctorNotConnected,
      'title': context.l10n.sharePatientCodeAction,
      'expertise': context.l10n.careAfterConnection,
    },
    'fee_items': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': context.l10n.consultation,
        'amount': context.l10n.pending,
        'selected': false,
      },
      <String, dynamic>{
        'label': context.l10n.medicalRecord,
        'amount': context.l10n.pending,
        'selected': false,
      },
      <String, dynamic>{
        'label': context.l10n.medication,
        'amount': context.l10n.pending,
        'selected': false,
      },
      <String, dynamic>{
        'label': context.l10n.imaging,
        'amount': context.l10n.pending,
        'selected': false,
      },
    ],
    'medical_records': <Object>[],
    'imaging_results': <Object>[],
    ...source,
  };
}

class _PatientAccountView extends ConsumerWidget {
  const _PatientAccountView({required this.bundle});

  final PatientCareBundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final avatar = avatarImageProvider(bundle.patient.avatarUrl);
    final accountEmail =
        ref.watch(authControllerProvider).value?.user?.email ?? '';
    return ListView(
      key: const Key('patient-account-list'),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      children: <Widget>[
        _PatientOnboardingPanel(
          title: context.l10n.myAccount,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Center(
                child: Stack(
                  clipBehavior: Clip.none,
                  children: <Widget>[
                    CircleAvatar(
                      radius: 48,
                      backgroundColor: const Color(0xFFE9EDF8),
                      backgroundImage: avatar,
                      child: avatar == null
                          ? const Icon(
                              Icons.person_outline,
                              size: 44,
                              color: DrAiColors.brand,
                            )
                          : null,
                    ),
                    Positioned(
                      right: -4,
                      bottom: 0,
                      child: IconButton.filled(
                        key: const Key('patient-account-avatar-upload-button'),
                        tooltip: context.l10n.uploadAvatar,
                        onPressed: () =>
                            _savePatientAvatar(context, ref, bundle),
                        icon: const Icon(Icons.photo_camera_outlined, size: 16),
                        style: IconButton.styleFrom(
                          backgroundColor: DrAiColors.accentIndigo,
                          foregroundColor: DrAiColors.white,
                          side: const BorderSide(
                            color: DrAiColors.white,
                            width: 2,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: DrAiSpacing.md),
              Text(
                bundle.patient.displayName,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 4),
              SelectableText(
                context.l10n.patientId(bundle.patient.syntheticIdentifier),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _AccountLine(
                label: context.l10n.birthDate,
                value: bundle.patient.birthDate,
              ),
              _AccountLine(
                label: context.l10n.gender,
                value: bundle.patient.gender == null
                    ? null
                    : context.l10n.stableValue(bundle.patient.gender!),
              ),
              _AccountLine(
                label: context.l10n.phone,
                value: bundle.patient.contactPhone,
              ),
              _AccountLine(label: context.l10n.email, value: accountEmail),
              _AccountLine(
                label: context.l10n.emergencyContact,
                value: _compactContact(
                  context,
                  bundle.patient.emergencyContactName,
                  bundle.patient.emergencyContactPhone,
                ),
              ),
              _AccountLine(
                label: context.l10n.language,
                value: bundle.patient.preferredLanguage == 'Simplified Chinese'
                    ? context.l10n.simplifiedChinese
                    : bundle.patient.preferredLanguage == 'English'
                    ? context.l10n.english
                    : bundle.patient.preferredLanguage,
              ),
              _AccountLine(
                label: context.l10n.contactPreference,
                value: bundle.patient.contactPreference == null
                    ? null
                    : context.l10n.stableValue(
                        bundle.patient.contactPreference!,
                      ),
              ),
              _AccountLine(
                label: context.l10n.location,
                value: _compactLocation(context, bundle.patient),
              ),
              _AccountLine(
                label: context.l10n.height,
                value: bundle.patient.heightCm == null
                    ? null
                    : '${_formatProfileNumber(bundle.patient.heightCm!)} cm',
              ),
              _AccountLine(
                label: context.l10n.weight,
                value: bundle.patient.weightKg == null
                    ? null
                    : '${_formatProfileNumber(bundle.patient.weightKg!)} kg',
              ),
              _AccountLine(
                label: context.l10n.bloodType,
                value: bundle.patient.bloodType == null
                    ? null
                    : context.l10n.stableValue(bundle.patient.bloodType!),
              ),
              _AccountLine(
                label: context.l10n.bloodPressure,
                value:
                    bundle.patient.systolicBloodPressure == null ||
                        bundle.patient.diastolicBloodPressure == null
                    ? null
                    : '${bundle.patient.systolicBloodPressure}/'
                          '${bundle.patient.diastolicBloodPressure} mmHg',
              ),
              const SizedBox(height: DrAiSpacing.sm),
              FilledButton.icon(
                key: const Key('patient-account-edit-profile-button'),
                onPressed: () => _showPatientSurveyEditor(context, bundle),
                icon: const Icon(Icons.edit_outlined),
                label: Text(context.l10n.editProfile),
              ),
              const SizedBox(height: DrAiSpacing.sm),
              const SignOutButton(),
            ],
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: context.l10n.security,
          child: const AccountSecuritySection(keyPrefix: 'patient-account'),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: context.l10n.medicalHistory,
          child: Text(
            _patientHistorySummary(context, bundle),
            key: const Key('patient-account-history-summary'),
          ),
        ),
      ],
    );
  }

  Future<void> _savePatientAvatar(
    BuildContext context,
    WidgetRef ref,
    PatientCareBundle bundle,
  ) async {
    try {
      final result = await pickAvatarImage();
      if (result == null) {
        return;
      }
      await ref
          .read(repositoryProvider)
          .updateOwnPatientProfile(
            displayName: bundle.patient.displayName,
            birthDate: bundle.patient.birthDate ?? '',
            gender: bundle.patient.gender ?? bundle.patient.sex ?? '',
            contactPhone: bundle.patient.contactPhone ?? '',
            emergencyContactName: bundle.patient.emergencyContactName ?? '',
            emergencyContactPhone: bundle.patient.emergencyContactPhone ?? '',
            preferredLanguage: bundle.patient.preferredLanguage ?? '',
            contactPreference: bundle.patient.contactPreference ?? '',
            avatarUrl: result.dataUrl,
            country: bundle.patient.country ?? '',
            province: bundle.patient.province ?? '',
            city: bundle.patient.city ?? '',
            homeAddress: bundle.patient.homeAddress ?? '',
            heightCm: _nullableProfileNumber(bundle.patient.heightCm),
            weightKg: _nullableProfileNumber(bundle.patient.weightKg),
            bloodType: bundle.patient.bloodType ?? 'Unknown',
            systolicBloodPressure:
                bundle.patient.systolicBloodPressure?.toString() ?? '',
            diastolicBloodPressure:
                bundle.patient.diastolicBloodPressure?.toString() ?? '',
            smokingStatus: bundle.patient.smokingStatus ?? 'Never',
            alcoholConsumption:
                bundle.patient.alcoholConsumption ?? 'None or rare',
            heartHistory: bundle.patient.heartHistory ?? '',
            endocrineHistory: bundle.patient.endocrineHistory ?? '',
            neuroHistory: bundle.patient.neuroHistory ?? '',
            digestiveHistory: bundle.patient.digestiveHistory ?? '',
            respiratoryHistory: bundle.patient.respiratoryHistory ?? '',
            kidneyHistory: bundle.patient.kidneyHistory ?? '',
            cancerHistory: bundle.patient.cancerHistory ?? '',
            patientReportedMedications:
                bundle.patient.patientReportedMedications ?? '',
            surgeryHistory: bundle.patient.surgeryHistory ?? '',
            familyHistory: bundle.patient.familyHistory ?? '',
            lifestyleNotes: bundle.patient.lifestyleNotes ?? '',
            pregnancyStatus:
                bundle.patient.pregnancyStatus ?? 'Prefer not to say',
            medicalHistorySetupCompleted:
                bundle.patient.medicalHistorySetupCompleted,
          );
      ref.invalidate(ownPatientCareProvider);
      ref.invalidate(dashboardProvider);
    } on AvatarUploadException catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.message)));
      }
    }
  }

  Future<void> _showPatientSurveyEditor(
    BuildContext context,
    PatientCareBundle bundle,
  ) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: DrAiColors.black.withValues(alpha: 0.22),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.62,
        maxChildSize: 0.96,
        expand: false,
        builder: (context, _) {
          return ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            child: _PatientMedicalSurveyScreen(
              care: AsyncData<PatientCareBundle>(bundle),
              onRetry: () {},
              closeOnSave: true,
            ),
          );
        },
      ),
    );
  }
}

class _AccountLine extends StatelessWidget {
  const _AccountLine({required this.label, required this.value});

  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: <Widget>[
          SizedBox(
            width: 132,
            child: Text(
              label,
              style: const TextStyle(color: DrAiColors.mutedInk),
            ),
          ),
          Expanded(
            child: Text(
              value == null || value!.trim().isEmpty
                  ? context.l10n.notRecorded
                  : value!,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _AccountListTile extends StatelessWidget {
  const _AccountListTile({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: DrAiColors.brand),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                Text(
                  subtitle,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: DrAiColors.mutedInk,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyAccountState extends StatelessWidget {
  const _EmptyAccountState({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.sm),
      child: Row(
        children: <Widget>[
          Icon(icon, color: DrAiColors.mutedInk),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: DrAiColors.mutedInk),
            ),
          ),
        ],
      ),
    );
  }
}

class _CareRecordStatus extends StatelessWidget {
  const _CareRecordStatus({required this.hasRecords, required this.hasImages});

  final bool hasRecords;
  final bool hasImages;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Expanded(
          child: _CareStatusPill(
            icon: Icons.description_outlined,
            label: context.l10n.records,
            value: hasRecords ? context.l10n.available : context.l10n.noneYet,
          ),
        ),
        const SizedBox(width: DrAiSpacing.xs),
        Expanded(
          child: _CareStatusPill(
            icon: Icons.document_scanner_outlined,
            label: context.l10n.imaging,
            value: hasImages ? context.l10n.available : context.l10n.noneYet,
          ),
        ),
      ],
    );
  }
}

class _CareStatusPill extends StatelessWidget {
  const _CareStatusPill({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        child: Row(
          children: <Widget>[
            Icon(icon, color: DrAiColors.brand, size: 20),
            const SizedBox(width: DrAiSpacing.xs),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    label,
                    style: const TextStyle(
                      color: DrAiColors.mutedInk,
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    value,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

String _compactContact(BuildContext context, String? name, String? phone) {
  final parts = <String>[
    if (name != null && name.trim().isNotEmpty) name.trim(),
    if (phone != null && phone.trim().isNotEmpty) phone.trim(),
  ];
  return parts.isEmpty ? context.l10n.notRecorded : parts.join(' - ');
}

class _PatientRecoveryPlanView extends StatelessWidget {
  const _PatientRecoveryPlanView({
    required this.bundle,
    required this.today,
    required this.onRetry,
  });

  final PatientCareBundle bundle;
  final AsyncValue<PatientTodayData> today;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('patient-recovery-plan-list'),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      children: <Widget>[
        _PatientOnboardingPanel(
          title: context.l10n.recoveryPlan,
          child: today.when(
            loading: () =>
                DashboardLoadingView(label: context.l10n.loadingActivePlan),
            error: (error, stackTrace) => DashboardErrorView(
              message: context.l10n.loadActivePlanFailed,
              onRetry: onRetry,
            ),
            data: (data) {
              if (data.activePlan == null) {
                return _EmptyAccountState(
                  icon: Icons.assignment_outlined,
                  text: context.l10n.noActivePlan,
                );
              }
              return _PatientRecoveryTasks(data: data);
            },
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: context.l10n.planHistory,
          child: bundle.recoveryPlans.isEmpty
              ? _EmptyAccountState(
                  icon: Icons.history_outlined,
                  text: context.l10n.planHistoryEmpty,
                )
              : Column(
                  children: <Widget>[
                    for (final plan in bundle.recoveryPlans)
                      _AccountListTile(
                        icon: Icons.assignment_outlined,
                        title: plan.title,
                        subtitle:
                            '${plan.status} - ${plan.reviewStatus} - ${plan.progressSummary.completionPercent}% complete',
                      ),
                  ],
                ),
        ),
      ],
    );
  }
}

class _PatientRecoveryTasks extends ConsumerWidget {
  const _PatientRecoveryTasks({required this.data});

  final PatientTodayData data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final completionState = ref.watch(recoveryTaskCompletionControllerProvider);
    final locallyCompleted = completionState.hasValue
        ? completionState.value ?? const <String>{}
        : const <String>{};
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          data.activePlan!.title,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 4),
        Text(
          data.activePlan!.instructions,
          style: const TextStyle(color: DrAiColors.mutedInk),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        Text(
          '${data.progressSummary.completedTaskCount}/${data.progressSummary.taskCount} complete - ${data.progressSummary.completionPercent}%',
          style: const TextStyle(
            color: DrAiColors.brand,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        for (final task in data.tasks)
          _TodayTaskTile(
            task: task,
            locallyCompleted: locallyCompleted.contains(task.taskId),
            isPending: completionState.isLoading,
            onChanged: (completed) => ref
                .read(recoveryTaskCompletionControllerProvider.notifier)
                .setCompleted(task.taskId, completed: completed),
          ),
      ],
    );
  }
}

class _PatientMedicalSurveyScreen extends ConsumerStatefulWidget {
  const _PatientMedicalSurveyScreen({
    required this.care,
    required this.onRetry,
    this.closeOnSave = false,
  });

  final AsyncValue<PatientCareBundle> care;
  final VoidCallback onRetry;
  final bool closeOnSave;

  @override
  ConsumerState<_PatientMedicalSurveyScreen> createState() =>
      _PatientMedicalSurveyScreenState();
}

class _PatientMedicalSurveyScreenState
    extends ConsumerState<_PatientMedicalSurveyScreen> {
  final _formKey = GlobalKey<FormState>();
  final _displayNameController = TextEditingController();
  final _birthDateController = TextEditingController();
  final _contactPhoneController = TextEditingController();
  final _accountEmailController = TextEditingController();
  final _emergencyNameController = TextEditingController();
  final _emergencyPhoneController = TextEditingController();
  final _homeAddressController = TextEditingController();
  final _heightController = TextEditingController();
  final _weightController = TextEditingController();
  final _systolicController = TextEditingController();
  final _diastolicController = TextEditingController();
  final _allergyLabelController = TextEditingController();
  final _allergyReactionController = TextEditingController();
  final _conditionNameController = TextEditingController();
  final _conditionNotesController = TextEditingController();
  final _heartDetailsController = TextEditingController();
  final _endocrineDetailsController = TextEditingController();
  final _neuroDetailsController = TextEditingController();
  final _digestiveDetailsController = TextEditingController();
  final _respiratoryDetailsController = TextEditingController();
  final _kidneyDetailsController = TextEditingController();
  final _cancerDetailsController = TextEditingController();
  final _currentMedicationsController = TextEditingController();
  final _surgeryHistoryController = TextEditingController();
  final _familyHistoryController = TextEditingController();
  final _lifestyleNotesController = TextEditingController();
  String _gender = 'Unspecified';
  String _bloodType = 'Unknown';
  String _pregnancyStatus = 'Prefer not to say';
  String _preferredLanguage = 'Simplified Chinese';
  String _contactPreference = 'Phone';
  String _country = 'China';
  String _province = 'Guangdong';
  String _city = 'Shenzhen';
  String _smokingStatus = 'Never';
  String _alcoholConsumption = 'None or rare';
  bool _hasAllergies = false;
  bool _hasChronicCondition = false;
  bool _hasHeartIssue = false;
  bool _hasEndocrineIssue = false;
  bool _hasNeuroIssue = false;
  bool _hasDigestiveIssue = false;
  bool _hasRespiratoryIssue = false;
  bool _hasKidneyIssue = false;
  bool _hasCancerIssue = false;
  bool _seededFromBundle = false;
  String? _accountSaveError;

  @override
  void dispose() {
    _displayNameController.dispose();
    _birthDateController.dispose();
    _contactPhoneController.dispose();
    _accountEmailController.dispose();
    _emergencyNameController.dispose();
    _emergencyPhoneController.dispose();
    _homeAddressController.dispose();
    _heightController.dispose();
    _weightController.dispose();
    _systolicController.dispose();
    _diastolicController.dispose();
    _allergyLabelController.dispose();
    _allergyReactionController.dispose();
    _conditionNameController.dispose();
    _conditionNotesController.dispose();
    _heartDetailsController.dispose();
    _endocrineDetailsController.dispose();
    _neuroDetailsController.dispose();
    _digestiveDetailsController.dispose();
    _respiratoryDetailsController.dispose();
    _kidneyDetailsController.dispose();
    _cancerDetailsController.dispose();
    _currentMedicationsController.dispose();
    _surgeryHistoryController.dispose();
    _familyHistoryController.dispose();
    _lifestyleNotesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final onboardingState = ref.watch(patientOnboardingControllerProvider);
    return ColoredBox(
      color: DrAiColors.pageBackground,
      child: LayoutBuilder(
        builder: (context, constraints) {
          return Center(
            child: SizedBox(
              height: constraints.maxHeight,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 640),
                child: ListView(
                  key: const Key('patient-onboarding-list'),
                  padding: const EdgeInsets.all(DrAiSpacing.md),
                  children: <Widget>[
                    _PatientOnboardingPanel(
                      title: context.l10n.completeHealthProfile,
                      child: widget.care.when(
                        loading: () => DashboardLoadingView(
                          label: context.l10n.loadingProfile,
                        ),
                        error: (error, stackTrace) => DashboardErrorView(
                          message: context.l10n.loadProfileFailed,
                          onRetry: widget.onRetry,
                        ),
                        data: (bundle) {
                          _seedFields(bundle);
                          return _surveyForm(context, bundle, onboardingState);
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  void _seedFields(PatientCareBundle bundle) {
    if (_seededFromBundle) {
      return;
    }
    _seededFromBundle = true;
    final patient = bundle.patient;
    _displayNameController.text = patient.displayName == 'New Patient'
        ? ''
        : patient.displayName;
    _birthDateController.text = patient.birthDate ?? '';
    _contactPhoneController.text = patient.contactPhone ?? '';
    _accountEmailController.text =
        ref.read(authControllerProvider).value?.user?.email ?? '';
    _emergencyNameController.text = patient.emergencyContactName ?? '';
    _emergencyPhoneController.text = patient.emergencyContactPhone ?? '';
    _homeAddressController.text = patient.homeAddress ?? '';
    _heightController.text = _nullableProfileNumber(patient.heightCm);
    _weightController.text = _nullableProfileNumber(patient.weightKg);
    _bloodType = _knownOption(patient.bloodType, <String>[
      'Unknown',
      'A+',
      'A-',
      'B+',
      'B-',
      'AB+',
      'AB-',
      'O+',
      'O-',
    ], _bloodType);
    _systolicController.text = patient.systolicBloodPressure?.toString() ?? '';
    _diastolicController.text =
        patient.diastolicBloodPressure?.toString() ?? '';
    _smokingStatus = _knownOption(patient.smokingStatus, <String>[
      'Never',
      'Former',
      'Current',
    ], _smokingStatus);
    _alcoholConsumption = _knownOption(patient.alcoholConsumption, <String>[
      'None or rare',
      'Occasional',
      'Weekly',
      'Daily',
    ], _alcoholConsumption);
    _seedCondition(
      patient.heartHistory,
      _heartDetailsController,
      (value) => _hasHeartIssue = value,
    );
    _seedCondition(
      patient.endocrineHistory,
      _endocrineDetailsController,
      (value) => _hasEndocrineIssue = value,
    );
    _seedCondition(
      patient.neuroHistory,
      _neuroDetailsController,
      (value) => _hasNeuroIssue = value,
    );
    _seedCondition(
      patient.digestiveHistory,
      _digestiveDetailsController,
      (value) => _hasDigestiveIssue = value,
    );
    _seedCondition(
      patient.respiratoryHistory,
      _respiratoryDetailsController,
      (value) => _hasRespiratoryIssue = value,
    );
    _seedCondition(
      patient.kidneyHistory,
      _kidneyDetailsController,
      (value) => _hasKidneyIssue = value,
    );
    _seedCondition(
      patient.cancerHistory,
      _cancerDetailsController,
      (value) => _hasCancerIssue = value,
    );
    _currentMedicationsController.text =
        patient.patientReportedMedications ?? '';
    _surgeryHistoryController.text = patient.surgeryHistory ?? '';
    _familyHistoryController.text = patient.familyHistory ?? '';
    _lifestyleNotesController.text = patient.lifestyleNotes ?? '';
    _pregnancyStatus = _knownOption(patient.pregnancyStatus, <String>[
      'Prefer not to say',
      'Not applicable',
      'No',
      'Yes',
      'Unsure',
    ], _pregnancyStatus);
    _country = _knownLocationCountry(patient.country);
    _province = _knownLocationProvince(_country, patient.province);
    _city = _knownLocationCity(_country, _province, patient.city);
    final savedGender = patient.gender ?? patient.sex;
    _gender =
        savedGender == null || savedGender.toLowerCase() == 'not specified'
        ? 'Unspecified'
        : savedGender;
    _preferredLanguage = _knownOption(patient.preferredLanguage, <String>[
      'Simplified Chinese',
      'English',
    ], _preferredLanguage);
    _contactPreference = _knownOption(patient.contactPreference, <String>[
      'Phone',
      'In-app',
      'Email',
    ], _contactPreference);
    final activeAllergies = bundle.allergies.where(
      (item) => item.status.toLowerCase() == 'active',
    );
    if (activeAllergies.isNotEmpty) {
      final allergy = activeAllergies.first;
      _hasAllergies = true;
      _allergyLabelController.text = allergy.label;
      _allergyReactionController.text = allergy.reaction ?? '';
    }
    final activeConditions = bundle.chronicDiseases.where(
      (item) => item.status.toLowerCase() == 'active',
    );
    if (activeConditions.isNotEmpty) {
      final condition = activeConditions.first;
      _hasChronicCondition = true;
      _conditionNameController.text = condition.name;
      _conditionNotesController.text = condition.notes ?? '';
    }
  }

  void _seedCondition(
    String? detail,
    TextEditingController controller,
    ValueChanged<bool> setEnabled,
  ) {
    final normalized = detail?.trim() ?? '';
    setEnabled(normalized.isNotEmpty);
    controller.text = normalized;
  }

  Widget _surveyForm(
    BuildContext context,
    PatientCareBundle bundle,
    AsyncValue<void> onboardingState,
  ) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          DecoratedBox(
            decoration: BoxDecoration(
              color: DrAiColors.pageBackground,
              borderRadius: BorderRadius.circular(DrAiRadii.md),
            ),
            child: Padding(
              padding: const EdgeInsets.all(DrAiSpacing.md),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    context.l10n.medicalIntake,
                    style: TextStyle(
                      color: DrAiColors.brandDark,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    context.l10n.medicalIntakeDescription,
                    style: TextStyle(color: DrAiColors.mutedInk),
                  ),
                  const SizedBox(height: DrAiSpacing.xs),
                  SelectableText(
                    context.l10n.patientId(bundle.patient.syntheticIdentifier),
                    key: const Key('patient-onboarding-code'),
                    style: const TextStyle(
                      color: DrAiColors.brand,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: DrAiSpacing.md),
          _surveySectionHeader(
            keyName: 'onboarding-about-you-section',
            icon: Icons.person_outline,
            title: context.l10n.aboutYou,
            description: context.l10n.aboutYouDescription,
          ),
          const SizedBox(height: DrAiSpacing.sm),
          _requiredTextField(
            controller: _displayNameController,
            label: context.l10n.fullNameRequired,
            keyName: 'onboarding-name-field',
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(child: _countryField()),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(child: _provinceField()),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(child: _cityField()),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: _optionalTextField(
                  controller: _homeAddressController,
                  label: context.l10n.homeAddressOptional,
                  keyName: 'onboarding-home-address-field',
                  hint: context.l10n.streetBuilding,
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(child: _birthDateField()),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-gender-field'),
                  initialValue: _gender,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: InputDecoration(
                    labelText: context.l10n.gender,
                    border: const OutlineInputBorder(),
                  ),
                  items: _localizedOptionItems(context, <String>[
                    'Unspecified',
                    'Female',
                    'Male',
                    'Other',
                  ]),
                  onChanged: (value) =>
                      setState(() => _gender = value ?? _gender),
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _contactPhoneController,
            label: context.l10n.phoneNumber,
            keyName: 'onboarding-phone-field',
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _accountEmailController,
            label: context.l10n.emailOptional,
            keyName: 'onboarding-email-field',
            validator: (value) {
              final email = value?.trim() ?? '';
              return email.isNotEmpty && !_isValidEmail(email)
                  ? context.l10n.invalidEmail
                  : null;
            },
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: _optionalTextField(
                  controller: _emergencyNameController,
                  label: context.l10n.emergencyContactOptional,
                  keyName: 'onboarding-emergency-name-field',
                  hint: context.l10n.fullName,
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: _optionalTextField(
                  controller: _emergencyPhoneController,
                  label: context.l10n.emergencyPhoneOptional,
                  keyName: 'onboarding-emergency-phone-field',
                  hint: context.l10n.includeCountryCode,
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-language-field'),
                  initialValue: _preferredLanguage,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: InputDecoration(
                    labelText: context.l10n.preferredLanguage,
                    border: OutlineInputBorder(),
                  ),
                  items: <DropdownMenuItem<String>>[
                    DropdownMenuItem<String>(
                      value: 'Simplified Chinese',
                      child: Text(context.l10n.simplifiedChinese),
                    ),
                    DropdownMenuItem<String>(
                      value: 'English',
                      child: Text(context.l10n.english),
                    ),
                  ],
                  onChanged: (value) {
                    if (value == null) {
                      return;
                    }
                    setState(() => _preferredLanguage = value);
                    ref
                        .read(localeControllerProvider.notifier)
                        .applyProfilePreference(value);
                  },
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-contact-preference-field'),
                  initialValue: _contactPreference,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: InputDecoration(
                    labelText: context.l10n.contactPreference,
                    border: const OutlineInputBorder(),
                  ),
                  items: _localizedOptionItems(context, <String>[
                    'Phone',
                    'In-app',
                    'Email',
                  ]),
                  onChanged: (value) => setState(
                    () => _contactPreference = value ?? _contactPreference,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          _surveySectionHeader(
            keyName: 'onboarding-measurements-section',
            icon: Icons.monitor_weight_outlined,
            title: context.l10n.healthMeasurements,
            description: context.l10n.healthMeasurementsDescription,
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Row(
            children: <Widget>[
              Expanded(
                child: _decimalTextField(
                  controller: _heightController,
                  label: context.l10n.heightCmRequired,
                  keyName: 'onboarding-height-field',
                  required: true,
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: _decimalTextField(
                  controller: _weightController,
                  label: context.l10n.weightKgRequired,
                  keyName: 'onboarding-weight-field',
                  required: true,
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          DropdownButtonFormField<String>(
            key: const Key('onboarding-blood-type-field'),
            initialValue: _bloodType,
            isExpanded: true,
            menuMaxHeight: _menuMaxHeight,
            borderRadius: _menuBorderRadius,
            dropdownColor: DrAiColors.white,
            icon: const Icon(Icons.keyboard_arrow_down_rounded),
            style: _menuTextStyle,
            decoration: InputDecoration(
              labelText: context.l10n.bloodType,
              border: const OutlineInputBorder(),
            ),
            items: _localizedOptionItems(context, <String>[
              'Unknown',
              'A+',
              'A-',
              'B+',
              'B-',
              'AB+',
              'AB-',
              'O+',
              'O-',
            ]),
            onChanged: (value) =>
                setState(() => _bloodType = value ?? _bloodType),
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: _integerTextField(
                  controller: _systolicController,
                  label: context.l10n.systolicBp,
                  keyName: 'onboarding-systolic-field',
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: _integerTextField(
                  controller: _diastolicController,
                  label: context.l10n.diastolicBp,
                  keyName: 'onboarding-diastolic-field',
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-smoking-field'),
                  initialValue: _smokingStatus,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: InputDecoration(
                    labelText: context.l10n.smokingStatus,
                    border: const OutlineInputBorder(),
                  ),
                  items: _localizedOptionItems(context, <String>[
                    'Never',
                    'Former',
                    'Current',
                  ]),
                  onChanged: (value) =>
                      setState(() => _smokingStatus = value ?? _smokingStatus),
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-alcohol-field'),
                  initialValue: _alcoholConsumption,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: InputDecoration(
                    labelText: context.l10n.alcohol,
                    border: const OutlineInputBorder(),
                  ),
                  items: _localizedOptionItems(context, <String>[
                    'None or rare',
                    'Occasional',
                    'Weekly',
                    'Daily',
                  ]),
                  onChanged: (value) => setState(
                    () => _alcoholConsumption = value ?? _alcoholConsumption,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          _surveySectionHeader(
            keyName: 'onboarding-conditions-section',
            icon: Icons.medical_information_outlined,
            title: context.l10n.allergiesConditions,
            description: context.l10n.conditionsDescription,
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Material(
            color: DrAiColors.white,
            child: SwitchListTile(
              key: const Key('onboarding-allergy-switch'),
              contentPadding: EdgeInsets.zero,
              title: Text(context.l10n.hasAllergies),
              value: _hasAllergies,
              onChanged: (value) => setState(() => _hasAllergies = value),
            ),
          ),
          if (_hasAllergies) ...<Widget>[
            _requiredTextField(
              controller: _allergyLabelController,
              label: context.l10n.allergy,
              keyName: 'onboarding-allergy-field',
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _optionalTextField(
              controller: _allergyReactionController,
              label: context.l10n.reactionOptional,
              keyName: 'onboarding-allergy-reaction-field',
              hint: 'e.g. rash, swelling, breathing difficulty',
            ),
          ],
          Material(
            color: DrAiColors.white,
            child: SwitchListTile(
              key: const Key('onboarding-chronic-switch'),
              contentPadding: EdgeInsets.zero,
              title: Text(context.l10n.hasChronicCondition),
              value: _hasChronicCondition,
              onChanged: (value) =>
                  setState(() => _hasChronicCondition = value),
            ),
          ),
          if (_hasChronicCondition) ...<Widget>[
            _requiredTextField(
              controller: _conditionNameController,
              label: context.l10n.condition,
              keyName: 'onboarding-condition-field',
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _optionalTextField(
              controller: _conditionNotesController,
              label: context.l10n.notesOptional,
              keyName: 'onboarding-condition-notes-field',
              hint: context.l10n.diagnosisTreatmentHint,
            ),
          ],
          const SizedBox(height: DrAiSpacing.md),
          _conditionQuestion(
            keyName: 'onboarding-heart-switch',
            title: context.l10n.heartHistory,
            detail: context.l10n.heartHistoryDescription,
            value: _hasHeartIssue,
            onChanged: (value) => setState(() => _hasHeartIssue = value),
            controller: _heartDetailsController,
            fieldKey: 'onboarding-heart-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-endocrine-switch',
            title: context.l10n.endocrineHistory,
            detail: context.l10n.endocrineHistoryDescription,
            value: _hasEndocrineIssue,
            onChanged: (value) => setState(() => _hasEndocrineIssue = value),
            controller: _endocrineDetailsController,
            fieldKey: 'onboarding-endocrine-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-neuro-switch',
            title: context.l10n.neuroHistory,
            detail: context.l10n.neuroHistoryDescription,
            value: _hasNeuroIssue,
            onChanged: (value) => setState(() => _hasNeuroIssue = value),
            controller: _neuroDetailsController,
            fieldKey: 'onboarding-neuro-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-digestive-switch',
            title: context.l10n.digestiveHistory,
            detail: context.l10n.digestiveHistoryDescription,
            value: _hasDigestiveIssue,
            onChanged: (value) => setState(() => _hasDigestiveIssue = value),
            controller: _digestiveDetailsController,
            fieldKey: 'onboarding-digestive-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-respiratory-switch',
            title: context.l10n.respiratoryHistory,
            detail: context.l10n.respiratoryHistoryDescription,
            value: _hasRespiratoryIssue,
            onChanged: (value) => setState(() => _hasRespiratoryIssue = value),
            controller: _respiratoryDetailsController,
            fieldKey: 'onboarding-respiratory-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-kidney-switch',
            title: context.l10n.kidneyHistory,
            detail: context.l10n.kidneyHistoryDescription,
            value: _hasKidneyIssue,
            onChanged: (value) => setState(() => _hasKidneyIssue = value),
            controller: _kidneyDetailsController,
            fieldKey: 'onboarding-kidney-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-cancer-switch',
            title: context.l10n.cancerHistory,
            detail: context.l10n.cancerHistoryDescription,
            value: _hasCancerIssue,
            onChanged: (value) => setState(() => _hasCancerIssue = value),
            controller: _cancerDetailsController,
            fieldKey: 'onboarding-cancer-details-field',
          ),
          const SizedBox(height: DrAiSpacing.md),
          _surveySectionHeader(
            keyName: 'onboarding-background-section',
            icon: Icons.history_edu_outlined,
            title: context.l10n.medicalBackground,
            description: context.l10n.medicalBackgroundDescription,
          ),
          const SizedBox(height: DrAiSpacing.sm),
          _optionalTextField(
            controller: _currentMedicationsController,
            label: context.l10n.currentMedicationsOptional,
            keyName: 'onboarding-current-medications-field',
            hint: context.l10n.medicationHint,
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _surgeryHistoryController,
            label: context.l10n.surgeriesOptional,
            keyName: 'onboarding-surgery-history-field',
            hint: context.l10n.surgeriesHint,
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _familyHistoryController,
            label: context.l10n.familyHistoryOptional,
            keyName: 'onboarding-family-history-field',
            hint: context.l10n.familyHistoryHint,
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _lifestyleNotesController,
            label: context.l10n.lifestyleOptional,
            keyName: 'onboarding-lifestyle-field',
            hint: context.l10n.lifestyleHint,
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          DropdownButtonFormField<String>(
            key: const Key('onboarding-pregnancy-field'),
            initialValue: _pregnancyStatus,
            isExpanded: true,
            menuMaxHeight: _menuMaxHeight,
            borderRadius: _menuBorderRadius,
            dropdownColor: DrAiColors.white,
            icon: const Icon(Icons.keyboard_arrow_down_rounded),
            style: _menuTextStyle,
            decoration: InputDecoration(
              labelText: context.l10n.pregnancyStatus,
              border: const OutlineInputBorder(),
            ),
            items: _localizedOptionItems(context, <String>[
              'Prefer not to say',
              'Not applicable',
              'No',
              'Yes',
              'Unsure',
            ]),
            onChanged: (value) =>
                setState(() => _pregnancyStatus = value ?? _pregnancyStatus),
          ),
          if (onboardingState.hasError) ...<Widget>[
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              context.l10n.saveProfileFailed,
              key: Key('patient-onboarding-error'),
              style: TextStyle(color: DrAiColors.danger),
            ),
          ],
          if (_accountSaveError != null) ...<Widget>[
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              _accountSaveError!,
              key: const Key('patient-account-email-error'),
              style: TextStyle(color: DrAiColors.danger),
            ),
          ],
          const SizedBox(height: DrAiSpacing.md),
          FilledButton.icon(
            key: const Key('patient-onboarding-submit'),
            onPressed: onboardingState.isLoading ? null : () => _submit(bundle),
            icon: onboardingState.isLoading
                ? const SizedBox.square(
                    dimension: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: DrAiColors.white,
                    ),
                  )
                : const Icon(Icons.check_circle_outline),
            label: Text(context.l10n.finishSetup),
          ),
        ],
      ),
    );
  }

  Future<void> _submit(PatientCareBundle bundle) async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    setState(() => _accountSaveError = null);
    final email = _accountEmailController.text.trim().toLowerCase();
    final currentEmail =
        ref.read(authControllerProvider).value?.user?.email ?? '';
    final activeAllergies = bundle.allergies
        .where((item) => item.status.toLowerCase() == 'active')
        .toList();
    final activeConditions = bundle.chronicDiseases
        .where((item) => item.status.toLowerCase() == 'active')
        .toList();
    try {
      if (email != currentEmail) {
        await ref
            .read(authControllerProvider.notifier)
            .updateAccountEmail(email);
      }
    } on Exception {
      if (mounted) {
        setState(() => _accountSaveError = context.l10n.accountSaveFailed);
      }
      return;
    }
    await ref
        .read(patientOnboardingControllerProvider.notifier)
        .complete(
          patientId: bundle.patient.patientId,
          displayName: _displayNameController.text,
          birthDate: _birthDateController.text,
          gender: _gender,
          contactPhone: _contactPhoneController.text,
          emergencyContactName: _emergencyNameController.text,
          emergencyContactPhone: _emergencyPhoneController.text,
          preferredLanguage: _preferredLanguage,
          contactPreference: _contactPreference,
          country: _country,
          province: _province,
          city: _city,
          homeAddress: _homeAddressController.text,
          hasAllergies: _hasAllergies,
          existingAllergy: activeAllergies.isEmpty
              ? null
              : activeAllergies.first,
          allergyLabel: _allergyLabelController.text,
          allergyReaction: _allergyReactionController.text,
          hasChronicCondition: _hasChronicCondition,
          existingChronicCondition: activeConditions.isEmpty
              ? null
              : activeConditions.first,
          chronicConditionName: _conditionNameController.text,
          chronicConditionNotes: _conditionNotesController.text,
          heightCm: _heightController.text,
          weightKg: _weightController.text,
          bloodType: _bloodType,
          systolicBloodPressure: _systolicController.text,
          diastolicBloodPressure: _diastolicController.text,
          smokingStatus: _smokingStatus,
          alcoholConsumption: _alcoholConsumption,
          conditionDetails: <String, String>{
            if (_hasHeartIssue)
              'Heart or blood vessel history': _conditionDetail(
                _heartDetailsController,
              ),
            if (_hasEndocrineIssue)
              'Diabetes, thyroid, or bone health': _conditionDetail(
                _endocrineDetailsController,
              ),
            if (_hasNeuroIssue)
              'Brain, mood, or nervous system': _conditionDetail(
                _neuroDetailsController,
              ),
            if (_hasDigestiveIssue)
              'Stomach, bowel, or liver history': _conditionDetail(
                _digestiveDetailsController,
              ),
            if (_hasRespiratoryIssue)
              'Lung or breathing history': _conditionDetail(
                _respiratoryDetailsController,
              ),
            if (_hasKidneyIssue)
              'Kidney or urinary history': _conditionDetail(
                _kidneyDetailsController,
              ),
            if (_hasCancerIssue)
              'Cancer or active treatment': _conditionDetail(
                _cancerDetailsController,
              ),
          },
          currentMedications: _currentMedicationsController.text,
          surgeryHistory: _surgeryHistoryController.text,
          familyHistory: _familyHistoryController.text,
          lifestyleNotes: _lifestyleNotesController.text,
          pregnancyStatus: _pregnancyStatus,
        );
    if (!mounted) {
      return;
    }
    final saved = ref.read(patientOnboardingControllerProvider);
    if (saved.hasValue) {
      await ref
          .read(localeControllerProvider.notifier)
          .applyProfilePreference(_preferredLanguage);
      if (widget.closeOnSave && mounted && Navigator.of(context).canPop()) {
        Navigator.of(context).pop();
      }
    }
  }

  String _conditionDetail(TextEditingController controller) {
    final text = controller.text.trim();
    return text.isEmpty ? 'Yes' : text;
  }

  Widget _requiredTextField({
    required TextEditingController controller,
    required String label,
    required String keyName,
  }) {
    return _optionalTextField(
      controller: controller,
      label: label,
      keyName: keyName,
      validator: (value) {
        if ((value?.trim() ?? '').isEmpty) {
          return context.l10n.required;
        }
        return null;
      },
    );
  }

  Widget _surveySectionHeader({
    required String keyName,
    required IconData icon,
    required String title,
    required String description,
  }) {
    return DecoratedBox(
      key: Key(keyName),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Icon(icon, color: DrAiColors.brand),
            const SizedBox(width: DrAiSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: const TextStyle(
                      color: DrAiColors.brandDark,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    description,
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _decimalTextField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    bool required = false,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
      ),
      validator: (value) {
        final text = value?.trim() ?? '';
        if (required && text.isEmpty) {
          return context.l10n.required;
        }
        if (text.isNotEmpty && double.tryParse(text) == null) {
          return context.l10n.useNumbersOnly;
        }
        return null;
      },
    );
  }

  Widget _integerTextField({
    required TextEditingController controller,
    required String label,
    required String keyName,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      keyboardType: TextInputType.number,
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
      ),
      validator: (value) {
        final text = value?.trim() ?? '';
        if (text.isNotEmpty && int.tryParse(text) == null) {
          return context.l10n.useNumbersOnly;
        }
        return null;
      },
    );
  }

  Widget _conditionQuestion({
    required String keyName,
    required String title,
    required String detail,
    required bool value,
    required ValueChanged<bool> onChanged,
    required TextEditingController controller,
    required String fieldKey,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.sm),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: DrAiColors.surfaceSubtle,
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.xs),
          child: Column(
            children: <Widget>[
              Material(
                color: Colors.transparent,
                child: SwitchListTile(
                  key: Key(keyName),
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(detail),
                  value: value,
                  onChanged: onChanged,
                ),
              ),
              if (value) ...<Widget>[
                _optionalTextField(
                  controller: controller,
                  label: context.l10n.conditionDetailsHint,
                  keyName: fieldKey,
                  maxLines: 2,
                ),
                const SizedBox(height: DrAiSpacing.xs),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _birthDateField() {
    return TextFormField(
      key: const Key('onboarding-birth-date-field'),
      controller: _birthDateController,
      keyboardType: TextInputType.datetime,
      decoration: InputDecoration(
        labelText: context.l10n.birthDate,
        hintText: 'YYYY-MM-DD',
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: context.l10n.selectDate,
          onPressed: () => _showBirthDatePicker(_birthDateController),
          icon: const Icon(Icons.calendar_today_outlined),
        ),
      ),
      validator: _dateValidator,
    );
  }

  Widget _countryField() {
    return DropdownButtonFormField<String>(
      key: const Key('onboarding-country-field'),
      initialValue: _country,
      isExpanded: true,
      menuMaxHeight: _menuMaxHeight,
      borderRadius: _menuBorderRadius,
      dropdownColor: DrAiColors.white,
      icon: const Icon(Icons.keyboard_arrow_down_rounded),
      style: _menuTextStyle,
      decoration: InputDecoration(
        labelText: context.l10n.countryRegion,
        border: const OutlineInputBorder(),
      ),
      items: _localizedOptionItems(context, _locationCountryOptions(_country)),
      onChanged: (value) {
        if (value == null) {
          return;
        }
        final province = _knownLocationProvince(value, null);
        setState(() {
          _country = value;
          _province = province;
          _city = _knownLocationCity(value, province, null);
        });
      },
    );
  }

  Widget _provinceField() {
    return DropdownButtonFormField<String>(
      key: const Key('onboarding-province-field'),
      initialValue: _province,
      isExpanded: true,
      menuMaxHeight: _menuMaxHeight,
      borderRadius: _menuBorderRadius,
      dropdownColor: DrAiColors.white,
      icon: const Icon(Icons.keyboard_arrow_down_rounded),
      style: _menuTextStyle,
      decoration: InputDecoration(
        labelText: context.l10n.provinceState,
        border: const OutlineInputBorder(),
      ),
      items: _localizedOptionItems(
        context,
        _locationProvinceOptions(_country, _province),
      ),
      onChanged: (value) {
        if (value == null) {
          return;
        }
        setState(() {
          _province = value;
          _city = _knownLocationCity(_country, value, null);
        });
      },
    );
  }

  Widget _cityField() {
    return DropdownButtonFormField<String>(
      key: const Key('onboarding-city-field'),
      initialValue: _city,
      isExpanded: true,
      menuMaxHeight: _menuMaxHeight,
      borderRadius: _menuBorderRadius,
      dropdownColor: DrAiColors.white,
      icon: const Icon(Icons.keyboard_arrow_down_rounded),
      style: _menuTextStyle,
      decoration: InputDecoration(
        labelText: context.l10n.city,
        border: const OutlineInputBorder(),
      ),
      items: _localizedOptionItems(
        context,
        _locationCityOptions(_country, _province, _city),
      ),
      onChanged: (value) {
        if (value != null) {
          setState(() => _city = value);
        }
      },
    );
  }

  Widget _optionalTextField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    String? hint,
    String? Function(String?)? validator,
    ValueChanged<String>? onChanged,
    int maxLines = 1,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: const OutlineInputBorder(),
      ),
      validator: validator,
      onChanged: onChanged,
    );
  }

  List<DropdownMenuItem<String>> _localizedOptionItems(
    BuildContext context,
    List<String> values,
  ) {
    return values
        .map(
          (value) => DropdownMenuItem<String>(
            value: value,
            child: Text(context.l10n.stableValue(value)),
          ),
        )
        .toList();
  }

  String _knownOption(
    String? savedValue,
    List<String> values,
    String fallback,
  ) {
    final text = savedValue?.trim();
    if (text == null || text.isEmpty) {
      return fallback;
    }
    for (final value in values) {
      if (value.toLowerCase() == text.toLowerCase()) {
        return value;
      }
    }
    return fallback;
  }

  String? _dateValidator(String? value) {
    final text = value?.trim() ?? '';
    if (text.isEmpty) {
      return null;
    }
    if (_parseDate(text) == null) {
      return context.l10n.useDateFormat;
    }
    return null;
  }

  Future<void> _showBirthDatePicker(TextEditingController controller) async {
    var selected =
        _parseDate(controller.text) ?? DateTime(DateTime.now().year - 25, 1, 1);
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.transparent,
      barrierColor: DrAiColors.black.withValues(alpha: 0.18),
      builder: (context) => SafeArea(
        top: false,
        child: DecoratedBox(
          decoration: const BoxDecoration(
            color: DrAiColors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: Color(0x240A0076),
                blurRadius: 30,
                offset: Offset(0, -10),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFFD8E1EF),
                  borderRadius: BorderRadius.circular(DrAiRadii.pill),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  DrAiSpacing.md,
                  DrAiSpacing.sm,
                  DrAiSpacing.md,
                  DrAiSpacing.xs,
                ),
                child: Row(
                  children: <Widget>[
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: Text(context.l10n.cancel),
                    ),
                    const Spacer(),
                    Text(
                      context.l10n.birthDate,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: DrAiColors.brandDark,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const Spacer(),
                    FilledButton(
                      style: FilledButton.styleFrom(
                        minimumSize: const Size(76, 38),
                        visualDensity: VisualDensity.compact,
                      ),
                      onPressed: () {
                        controller.text = _formatDate(selected);
                        Navigator.of(context).pop();
                      },
                      child: Text(context.l10n.done),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1, color: Color(0xFFE3E8F2)),
              SizedBox(
                height: 244,
                child: CupertinoTheme(
                  data: const CupertinoThemeData(
                    brightness: Brightness.light,
                    textTheme: CupertinoTextThemeData(
                      dateTimePickerTextStyle: TextStyle(
                        color: DrAiColors.ink,
                        fontSize: 21,
                        height: 1.25,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  child: CupertinoDatePicker(
                    mode: CupertinoDatePickerMode.date,
                    initialDateTime: selected,
                    minimumYear: 1900,
                    maximumDate: DateTime.now(),
                    backgroundColor: DrAiColors.white,
                    onDateTimeChanged: (value) => selected = value,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PatientOnboardingPanel extends StatelessWidget {
  const _PatientOnboardingPanel({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x0A030025),
            blurRadius: 16,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Container(
            height: 40,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: DrAiColors.sectionHeader,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Text(
              title,
              style: const TextStyle(
                color: DrAiColors.white,
                fontSize: 16,
                height: 1.4,
              ),
            ),
          ),
          Padding(padding: const EdgeInsets.all(DrAiSpacing.md), child: child),
        ],
      ),
    );
  }
}

class _PatientTodayCard extends ConsumerWidget {
  const _PatientTodayCard({
    required this.today,
    required this.care,
    required this.notifications,
    required this.onRetry,
  });

  final AsyncValue<PatientTodayData> today;
  final AsyncValue<PatientCareBundle> care;
  final AsyncValue<MedicationNotificationScheduleResult> notifications;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final completionState = ref.watch(recoveryTaskCompletionControllerProvider);
    final locallyCompleted = completionState.hasValue
        ? completionState.value ?? const <String>{}
        : const <String>{};
    return today.when(
      loading: () =>
          DashboardLoadingView(label: context.l10n.loadingTodayTasks),
      error: (error, stackTrace) => DashboardErrorView(
        message: context.l10n.loadTodayTasksFailed,
        onRetry: onRetry,
      ),
      data: (data) {
        return ListView(
          key: const Key('patient-today-task-list'),
          children: <Widget>[
            if (data.activePlan != null) ...<Widget>[
              Text(
                data.activePlan!.title,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 2),
              Text(
                data.activePlan!.instructions,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '${data.progressSummary.completedTaskCount}/'
                '${data.progressSummary.taskCount} tasks complete - '
                '${data.progressSummary.completionPercent}%',
                key: const Key('patient-today-progress-summary'),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
            ],
            notifications.when(
              loading: () => Text(
                context.l10n.preparingNotifications,
                style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
              ),
              error: (error, stackTrace) => Text(
                context.l10n.notificationsUnavailable,
                style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
              ),
              data: (result) => Text(
                result.label,
                key: const Key('patient-medication-notification-shell'),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            _MedicationReminderTodayList(care: care),
            if (data.tasks.isEmpty)
              Padding(
                padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
                child: Text(context.l10n.noTodayTasks),
              ),
            completionState.when(
              data: (_) => const SizedBox.shrink(),
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) => Padding(
                padding: EdgeInsets.only(top: DrAiSpacing.xs),
                child: Text(
                  context.l10n.taskSyncFailed,
                  style: TextStyle(color: DrAiColors.danger, fontSize: 12),
                ),
              ),
            ),
            for (final task in data.tasks)
              _TodayTaskTile(
                task: task,
                locallyCompleted: locallyCompleted.contains(task.taskId),
                isPending: completionState.isLoading,
                onChanged: (completed) => ref
                    .read(recoveryTaskCompletionControllerProvider.notifier)
                    .setCompleted(task.taskId, completed: completed),
              ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              context.l10n.stableValue(data.safetyLabel),
              style: const TextStyle(color: DrAiColors.mutedInk, fontSize: 11),
            ),
          ],
        );
      },
    );
  }
}

class _MedicationReminderTodayList extends StatelessWidget {
  const _MedicationReminderTodayList({required this.care});

  final AsyncValue<PatientCareBundle> care;

  @override
  Widget build(BuildContext context) {
    return care.when(
      loading: () => Padding(
        padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
        child: Text(
          context.l10n.loadingMedicationReminders,
          style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
        ),
      ),
      error: (error, stackTrace) => Padding(
        padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
        child: Text(
          context.l10n.medicationRemindersUnavailable,
          style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
        ),
      ),
      data: (bundle) {
        final active = bundle.medicationReminders
            .where((item) => item.status == 'active')
            .toList();
        if (active.isEmpty) {
          return Padding(
            padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
            child: Text(
              context.l10n.noMedicationReminders,
              key: Key('patient-today-medication-reminders-empty'),
              style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
            ),
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              context.l10n.medicationReminders,
              style: TextStyle(
                color: DrAiColors.brandDark,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 4),
            for (final reminder in active.take(3))
              Container(
                key: Key('patient-today-reminder-${reminder.id}'),
                margin: const EdgeInsets.only(bottom: 4),
                padding: const EdgeInsets.all(DrAiSpacing.xs),
                decoration: BoxDecoration(
                  color: DrAiColors.surfaceSubtle,
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Row(
                  children: <Widget>[
                    Icon(
                      reminder.reminderType == 'refill'
                          ? Icons.inventory_2_outlined
                          : Icons.medication_outlined,
                      color: DrAiColors.brand,
                      size: 18,
                    ),
                    const SizedBox(width: DrAiSpacing.xs),
                    Expanded(
                      child: Text(
                        '${reminder.reminderType == 'refill' ? context.l10n.refill : context.l10n.medication} - ${reminder.scheduleLabel}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: DrAiSpacing.xs),
          ],
        );
      },
    );
  }
}

class _EducationalChatCard extends ConsumerStatefulWidget {
  const _EducationalChatCard();

  @override
  ConsumerState<_EducationalChatCard> createState() =>
      _EducationalChatCardState();
}

class _EducationalChatCardState extends ConsumerState<_EducationalChatCard> {
  final _messageController = TextEditingController();
  final _chatScrollController = ScrollController();

  @override
  void dispose() {
    _messageController.dispose();
    _chatScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(educationalChatControllerProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_chatScrollController.hasClients) {
        _chatScrollController.jumpTo(
          _chatScrollController.position.maxScrollExtent,
        );
      }
    });
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          context.l10n.educationalDisclaimer,
          style: TextStyle(
            color: DrAiColors.danger,
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        Expanded(
          child: ListView.builder(
            key: const Key('educational-chat-message-list'),
            controller: _chatScrollController,
            padding: const EdgeInsets.only(bottom: 2),
            itemCount: chat.messages.length,
            itemBuilder: (context, index) {
              final message = chat.messages[index];
              return _ChatBubble(message: message);
            },
          ),
        ),
        if (chat.errorMessage != null)
          Padding(
            padding: const EdgeInsets.only(top: DrAiSpacing.xs),
            child: Text(
              chat.errorMessage!,
              style: const TextStyle(color: DrAiColors.danger, fontSize: 12),
            ),
          ),
        const SizedBox(height: DrAiSpacing.xs),
        Row(
          children: <Widget>[
            Expanded(
              child: TextField(
                key: const Key('educational-chat-input'),
                controller: _messageController,
                minLines: 1,
                maxLines: 2,
                maxLength: 800,
                keyboardType: TextInputType.text,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: InputDecoration(
                  counterText: '',
                  isDense: true,
                  hintText: context.l10n.prepareQuestion,
                  prefixIcon: Icon(Icons.chat_bubble_outline),
                ),
              ),
            ),
            const SizedBox(width: DrAiSpacing.xs),
            IconButton.filled(
              key: const Key('educational-chat-send-button'),
              tooltip: context.l10n.sendEducationalQuestion,
              onPressed: chat.isSending ? null : _send,
              icon: chat.isSending
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send_outlined),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _send() async {
    final sent = await ref
        .read(educationalChatControllerProvider.notifier)
        .send(_messageController.text);
    if (sent && mounted) {
      _messageController.clear();
    }
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.message});

  final ChatDisplayMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        key: Key('educational-chat-${message.role}-${message.id}'),
        constraints: const BoxConstraints(maxWidth: 520),
        margin: const EdgeInsets.only(bottom: DrAiSpacing.xs),
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        decoration: BoxDecoration(
          color: message.isRedFlag
              ? DrAiColors.patientAccent
              : isUser
              ? DrAiColors.brand
              : DrAiColors.surfaceSubtle,
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            if (message.content.isEmpty)
              Text(
                context.l10n.streamingResponse,
                style: TextStyle(color: DrAiColors.mutedInk),
              )
            else
              Text(
                message.content,
                style: TextStyle(
                  color: isUser ? DrAiColors.white : DrAiColors.ink,
                  fontSize: 12,
                ),
              ),
            if (message.safetyLabel != null) ...<Widget>[
              const SizedBox(height: 2),
              Text(
                context.l10n.stableValue(message.safetyLabel!),
                style: const TextStyle(
                  color: DrAiColors.danger,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
            if (message.fallbackReason != null) ...<Widget>[
              const SizedBox(height: 2),
              Text(
                context.l10n.fallbackReason(message.fallbackReason!),
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 10,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _TodayTaskTile extends StatelessWidget {
  const _TodayTaskTile({
    required this.task,
    required this.locallyCompleted,
    required this.isPending,
    required this.onChanged,
  });

  final RecoveryTaskItem task;
  final bool locallyCompleted;
  final bool isPending;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final completed = task.isCompleted || locallyCompleted;
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      child: Material(
        color: completed ? DrAiColors.patientAccent : DrAiColors.surfaceSubtle,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          side: const BorderSide(color: DrAiColors.outline),
        ),
        child: CheckboxListTile(
          key: Key('today-task-${task.category}'),
          value: completed,
          onChanged: isPending
              ? null
              : (value) => onChanged(value ?? !completed),
          controlAffinity: ListTileControlAffinity.leading,
          secondary: Icon(_taskIcon(task.category), color: DrAiColors.brand),
          title: Text(
            task.title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          subtitle: Text(
            '${_taskLabel(context, task.category)} - ${task.dueLabel}'
            '${task.notificationTime == null ? '' : ' - ${task.notificationTime}'}\n'
            '${task.detail}',
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ),
    );
  }
}

IconData _taskIcon(String category) {
  return switch (category) {
    'medication' => Icons.medication_outlined,
    'exercise' => Icons.directions_walk_outlined,
    'diet' => Icons.restaurant_outlined,
    'follow_up' => Icons.event_available_outlined,
    _ => Icons.check_circle_outline,
  };
}

String _taskLabel(BuildContext context, String category) {
  return switch (category) {
    'medication' => context.l10n.medicationNote,
    'exercise' => context.l10n.exercise,
    'diet' => context.l10n.diet,
    'follow_up' => context.l10n.followUp,
    _ => context.l10n.task,
  };
}

class _PatientEventUpdatePanel extends ConsumerStatefulWidget {
  const _PatientEventUpdatePanel({required this.bundle});

  final PatientCareBundle bundle;

  @override
  ConsumerState<_PatientEventUpdatePanel> createState() =>
      _PatientEventUpdatePanelState();
}

class _PatientEventUpdatePanelState
    extends ConsumerState<_PatientEventUpdatePanel> {
  final _summaryController = TextEditingController();
  String _updateType = 'general_update';
  String? _validationError;

  @override
  void dispose() {
    _summaryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final event = widget.bundle.clinicalEvents.isEmpty
        ? null
        : widget.bundle.clinicalEvents.first;
    final state = ref.watch(clinicalEventUpdateControllerProvider);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              event == null
                  ? context.l10n.noClinicalEventUpdate
                  : context.l10n.updateEvent(event.title),
              key: const Key('patient-event-update-title'),
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            if (widget.bundle.clinicalEventUpdates.isNotEmpty)
              Text(
                context.l10n.latestPatientUpdate(
                  widget.bundle.clinicalEventUpdates.first.summary,
                ),
                key: const Key('patient-event-latest-update'),
              ),
            if (event != null) ...<Widget>[
              const SizedBox(height: 4),
              DropdownButtonFormField<String>(
                key: const Key('patient-event-update-type-field'),
                initialValue: _updateType,
                isExpanded: true,
                decoration: InputDecoration(
                  labelText: context.l10n.updateType,
                  isDense: true,
                ),
                items: <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'general_update',
                    child: Text(context.l10n.generalUpdate),
                  ),
                  DropdownMenuItem(
                    value: 'symptom_update',
                    child: Text(context.l10n.symptomUpdate),
                  ),
                  DropdownMenuItem(
                    value: 'medication_note',
                    child: Text(context.l10n.medicationNote),
                  ),
                  DropdownMenuItem(
                    value: 'recovery_check_in',
                    child: Text(context.l10n.recoveryCheckIn),
                  ),
                ],
                onChanged: (value) =>
                    setState(() => _updateType = value ?? 'general_update'),
              ),
              const SizedBox(height: 4),
              TextField(
                key: const Key('patient-event-update-summary-field'),
                controller: _summaryController,
                maxLength: 1200,
                minLines: 1,
                maxLines: 2,
                decoration: InputDecoration(
                  counterText: '',
                  labelText: context.l10n.selfReportedUpdate,
                  isDense: true,
                ),
              ),
              if (_validationError != null)
                Text(
                  _validationError!,
                  style: const TextStyle(color: DrAiColors.danger),
                ),
              state.when(
                loading: () => const LinearProgressIndicator(),
                error: (error, stackTrace) =>
                    Text(_patientSafeErrorMessage(context, error)),
                data: (update) => update == null
                    ? const SizedBox.shrink()
                    : Text(
                        context.l10n.updateSubmitted(
                          context.l10n.stableValue(update.updateType),
                        ),
                      ),
              ),
              const SizedBox(height: 4),
              FilledButton.icon(
                key: const Key('patient-event-update-submit-button'),
                onPressed: state.isLoading ? null : () => _submit(event.id),
                icon: const Icon(Icons.send_outlined),
                label: Text(context.l10n.sendUpdate),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _submit(String eventId) {
    if (_summaryController.text.trim().length < 3) {
      setState(() => _validationError = context.l10n.enterUpdate);
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(clinicalEventUpdateControllerProvider.notifier)
        .submit(
          clinicalEventId: eventId,
          updateType: _updateType,
          summary: _summaryController.text.trim(),
        );
  }
}

String _patientHistorySummary(BuildContext context, PatientCareBundle bundle) {
  return <String>[
    context.l10n.allergiesSummary(
      _patientLabelsOrEmpty(context, bundle.allergies),
    ),
    context.l10n.chronicDiseasesSummary(
      _patientConditionsOrEmpty(context, bundle.chronicDiseases),
    ),
    context.l10n.visitHistorySummary(bundle.visitHistory.length),
    context.l10n.diagnosesSummary(
      _patientDiagnosesOrEmpty(context, bundle.diagnoses),
    ),
  ].join('\n');
}

String _patientLabelsOrEmpty(
  BuildContext context,
  List<PatientAllergyItem> items,
) {
  if (items.isEmpty) {
    return context.l10n.noneRecorded;
  }
  return items.map((item) => item.label).join(', ');
}

String _patientConditionsOrEmpty(
  BuildContext context,
  List<ChronicDiseaseItem> items,
) {
  if (items.isEmpty) {
    return context.l10n.noneRecorded;
  }
  return items.map((item) => item.name).join(', ');
}

String _patientDiagnosesOrEmpty(
  BuildContext context,
  List<DiagnosisItem> items,
) {
  if (items.isEmpty) {
    return context.l10n.noneRecorded;
  }
  return items.map((item) => item.label).join(', ');
}

String _compactLocation(BuildContext context, PatientProfile patient) {
  final parts = <String>[
    if (patient.city != null && patient.city!.trim().isNotEmpty)
      context.l10n.stableValue(patient.city!.trim()),
    if (patient.province != null && patient.province!.trim().isNotEmpty)
      context.l10n.stableValue(patient.province!.trim()),
    if (patient.country != null && patient.country!.trim().isNotEmpty)
      context.l10n.stableValue(patient.country!.trim()),
    if (patient.homeAddress != null && patient.homeAddress!.trim().isNotEmpty)
      patient.homeAddress!.trim(),
  ];
  return parts.isEmpty ? context.l10n.notRecorded : parts.join(', ');
}

String _nullableProfileNumber(double? value) {
  return value == null ? '' : _formatProfileNumber(value);
}

String _formatProfileNumber(double value) {
  return value == value.roundToDouble()
      ? value.round().toString()
      : value.toStringAsFixed(1);
}

String _knownLocationCountry(String? saved) {
  final value = _emptyLocationValue(saved);
  return value ?? locationCountries.first.name;
}

String _knownLocationProvince(String country, String? saved) {
  final value = _emptyLocationValue(saved);
  final regions = _locationRegions(country);
  return value ?? (regions.isEmpty ? '' : regions.first.name);
}

String _knownLocationCity(String country, String province, String? saved) {
  final value = _emptyLocationValue(saved);
  final cities = _locationCities(country, province);
  return value ?? (cities.isEmpty ? '' : cities.first);
}

List<String> _locationCountryOptions(String selected) {
  return _withSelectedLocation(
    locationCountries.map((country) => country.name),
    selected,
  );
}

List<String> _locationProvinceOptions(String country, String selected) {
  return _withSelectedLocation(
    _locationRegions(country).map((region) => region.name),
    selected,
  );
}

List<String> _locationCityOptions(
  String country,
  String province,
  String selected,
) {
  return _withSelectedLocation(_locationCities(country, province), selected);
}

List<LocationRegion> _locationRegions(String country) {
  for (final item in locationCountries) {
    if (item.name == country) {
      return item.regions;
    }
  }
  return const <LocationRegion>[];
}

List<String> _locationCities(String country, String province) {
  for (final region in _locationRegions(country)) {
    if (region.name == province) {
      return region.cities;
    }
  }
  return const <String>[];
}

List<String> _withSelectedLocation(Iterable<String> values, String selected) {
  final options = values.toList();
  if (selected.trim().isNotEmpty && !options.contains(selected)) {
    options.add(selected);
  }
  if (options.isEmpty) {
    options.add('');
  }
  return options;
}

String? _emptyLocationValue(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

class _PatientSection extends StatelessWidget {
  const _PatientSection({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Container(
            height: 40,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: DrAiColors.brand,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Text(
              title,
              style: const TextStyle(
                color: DrAiColors.white,
                fontSize: 16,
                height: 1.4,
              ),
            ),
          ),
          Expanded(
            child: Padding(padding: const EdgeInsets.all(5), child: child),
          ),
        ],
      ),
    );
  }
}

class _MedicalFee extends StatelessWidget {
  const _MedicalFee({required this.items});

  final List<Map<String, dynamic>> items;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(DrAiSpacing.md),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        border: Border.all(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          LayoutBuilder(
            builder: (context, constraints) {
              final itemWidth = (constraints.maxWidth - DrAiSpacing.sm) / 2;
              return Wrap(
                spacing: DrAiSpacing.sm,
                runSpacing: DrAiSpacing.sm,
                children: <Widget>[
                  for (final item in items)
                    SizedBox(
                      width: itemWidth,
                      child: _FeeSummaryItem(item: item),
                    ),
                ],
              );
            },
          ),
          const Spacer(),
          Semantics(
            key: const Key('payment-disabled-control'),
            container: true,
            excludeSemantics: true,
            button: true,
            enabled: false,
            label: context.l10n.payNowUnavailable,
            child: Container(
              constraints: const BoxConstraints(minHeight: 42),
              padding: const EdgeInsets.symmetric(
                horizontal: DrAiSpacing.md,
                vertical: 9,
              ),
              decoration: BoxDecoration(
                color: const Color(0xFFE1E3E8),
                borderRadius: BorderRadius.circular(DrAiRadii.md),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  Icon(
                    Icons.lock_outline,
                    size: 17,
                    color: DrAiColors.inkSecondary,
                  ),
                  SizedBox(width: 7),
                  Flexible(
                    child: Text(
                      context.l10n.paymentUnavailable,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: DrAiColors.inkSecondary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 5),
          Text(
            context.l10n.paymentDescription,
            textAlign: TextAlign.center,
            style: TextStyle(color: DrAiColors.inkSecondary, fontSize: 11),
          ),
        ],
      ),
    );
  }
}

class _FeeSummaryItem extends StatelessWidget {
  const _FeeSummaryItem({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final active = item['selected'] as bool;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
      decoration: BoxDecoration(
        color: active ? const Color(0xFFF2FBF8) : const Color(0xFFF7F8FA),
        borderRadius: BorderRadius.circular(DrAiRadii.sm),
      ),
      child: Row(
        children: <Widget>[
          Icon(
            active ? Icons.receipt_long_outlined : Icons.schedule_outlined,
            size: 17,
            color: active ? const Color(0xFF087F5B) : DrAiColors.inkSecondary,
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  item['label'] as String,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: DrAiColors.ink,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  item['amount'] as String,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

DateTime? _parseDate(String value) {
  final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(value.trim());
  if (match == null) {
    return null;
  }
  final year = int.tryParse(match.group(1)!);
  final month = int.tryParse(match.group(2)!);
  final day = int.tryParse(match.group(3)!);
  if (year == null || month == null || day == null) {
    return null;
  }
  final parsed = DateTime(year, month, day);
  if (parsed.year != year || parsed.month != month || parsed.day != day) {
    return null;
  }
  if (year < 1900 || parsed.isAfter(DateTime.now())) {
    return null;
  }
  return parsed;
}

bool _isValidEmail(String value) {
  return RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value);
}

String _formatDate(DateTime date) {
  return '${date.year.toString().padLeft(4, '0')}-'
      '${date.month.toString().padLeft(2, '0')}-'
      '${date.day.toString().padLeft(2, '0')}';
}

const double _menuMaxHeight = 320;
const BorderRadius _menuBorderRadius = BorderRadius.all(
  Radius.circular(DrAiRadii.md),
);
const TextStyle _menuTextStyle = TextStyle(
  color: DrAiColors.ink,
  fontSize: 14,
  height: 20 / 14,
  fontWeight: FontWeight.w500,
);

String _patientSafeErrorMessage(BuildContext context, Object error) {
  if (error is ApiError) {
    if (error.code == 'rate_limited') {
      return context.l10n.chatRateLimited;
    }
    if (error.code == 'service_unavailable') {
      return context.l10n.unableToReach;
    }
    return error.message;
  }
  return context.l10n.unableToReach;
}
