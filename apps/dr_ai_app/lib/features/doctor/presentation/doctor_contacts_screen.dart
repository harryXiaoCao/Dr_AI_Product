import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/avatar/avatar_upload.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class DoctorContactsScreen extends ConsumerWidget {
  const DoctorContactsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final contacts = ref.watch(doctorPatientContactsProvider);
    return ResponsiveAppShell(
      role: AppRole.doctor,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 760),
            child: contacts.when(
              loading: () =>
                  DashboardLoadingView(label: context.l10n.loadingContacts),
              error: (error, stackTrace) => DashboardErrorView(
                message: context.l10n.contactsLoadFailed,
                onRetry: () => ref.invalidate(doctorPatientContactsProvider),
              ),
              data: (data) => _DoctorContactList(patients: data.items),
            ),
          ),
        ),
      ),
    );
  }
}

class _DoctorContactList extends StatelessWidget {
  const _DoctorContactList({required this.patients});
  final List<DoctorPatientContact> patients;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('doctor-contact-list'),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      children: <Widget>[
        Text(
          context.l10n.contacts,
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            color: DrAiColors.ink,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        Text(
          context.l10n.doctorContactsDescription,
          style: const TextStyle(color: DrAiColors.inkSecondary),
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _Label(context.l10n.services),
        const SizedBox(height: DrAiSpacing.sm),
        _ContactRow(
          icon: Icons.notifications_active_outlined,
          title: context.l10n.system,
          subtitle: context.l10n.systemReadOnlyDescription,
          onTap: () => context.push('/doctor/contact/system'),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ContactRow(
          icon: Icons.auto_awesome_outlined,
          title: context.l10n.appName,
          subtitle: context.l10n.aiCareCompanion,
          onTap: () => context.push('/doctor/contact/ai'),
        ),
        const SizedBox(height: DrAiSpacing.lg),
        Row(
          children: <Widget>[
            Expanded(child: _Label(context.l10n.myPatients)),
            Text(
              '${patients.length}',
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: DrAiSpacing.sm),
        if (patients.isEmpty)
          const _EmptyPatients()
        else
          for (final patient in patients) ...<Widget>[
            _PatientRow(patient: patient),
            const SizedBox(height: DrAiSpacing.sm),
          ],
        const SizedBox(height: DrAiSpacing.md),
        _Label(context.l10n.groups),
        const SizedBox(height: DrAiSpacing.sm),
        const _EmptyGroups(),
        const SizedBox(height: DrAiSpacing.lg),
      ],
    );
  }
}

class _PatientRow extends StatelessWidget {
  const _PatientRow({required this.patient});
  final DoctorPatientContact patient;
  @override
  Widget build(BuildContext context) {
    final avatar = avatarImageProvider(patient.avatarUrl);
    return _ContactRow(
      key: Key('patient-contact-${patient.patientId}'),
      leading: CircleAvatar(
        radius: 24,
        backgroundColor: const Color(0xFFE8ECFB),
        backgroundImage: avatar,
        child: avatar == null
            ? Text(
                patient.displayName.characters.first.toUpperCase(),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontWeight: FontWeight.w800,
                ),
              )
            : null,
      ),
      title: patient.displayName,
      subtitle: context.l10n.connectedPatientPrivateChat,
      onTap: () => context.push(
        Uri(
          path: '/doctor/contact/private',
          queryParameters: {
            'id': patient.patientId,
            'name': patient.displayName,
          },
        ).toString(),
      ),
    );
  }
}

class _Label extends StatelessWidget {
  const _Label(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Container(
    decoration: BoxDecoration(
      color: DrAiColors.sectionHeader,
      borderRadius: BorderRadius.circular(DrAiRadii.md),
    ),
    padding: const EdgeInsets.symmetric(
      horizontal: DrAiSpacing.md,
      vertical: DrAiSpacing.sm,
    ),
    child: Text(
      text,
      style: Theme.of(context).textTheme.titleMedium?.copyWith(
        color: DrAiColors.white,
        fontWeight: FontWeight.w700,
      ),
    ),
  );
}

class _ContactRow extends StatelessWidget {
  const _ContactRow({
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.icon,
    this.leading,
    super.key,
  });
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final IconData? icon;
  final Widget? leading;
  @override
  Widget build(BuildContext context) => Material(
    color: DrAiColors.white,
    shape: RoundedRectangleBorder(
      side: const BorderSide(color: DrAiColors.outline),
      borderRadius: BorderRadius.circular(DrAiRadii.lg),
    ),
    child: InkWell(
      borderRadius: BorderRadius.circular(DrAiRadii.lg),
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Row(
          children: <Widget>[
            leading ??
                CircleAvatar(
                  radius: 24,
                  backgroundColor: const Color(0xFFE7EEFF),
                  child: Icon(icon, color: DrAiColors.brand),
                ),
            const SizedBox(width: DrAiSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: const TextStyle(
                      color: DrAiColors.ink,
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    subtitle,
                    style: const TextStyle(color: DrAiColors.inkSecondary),
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.chevron_right_rounded,
              color: DrAiColors.inkSecondary,
            ),
          ],
        ),
      ),
    ),
  );
}

class _EmptyPatients extends StatelessWidget {
  const _EmptyPatients();
  @override
  Widget build(BuildContext context) => _EmptyPanel(
    icon: Icons.person_add_alt_1_outlined,
    title: context.l10n.noConnectedPatients,
    detail: context.l10n.connectPatientToChat,
  );
}

class _EmptyGroups extends StatelessWidget {
  const _EmptyGroups();
  @override
  Widget build(BuildContext context) => _EmptyPanel(
    icon: Icons.groups_2_outlined,
    title: context.l10n.noGroupChats,
    detail: context.l10n.groupChatsUnavailable,
  );
}

class _EmptyPanel extends StatelessWidget {
  const _EmptyPanel({
    required this.icon,
    required this.title,
    required this.detail,
  });
  final IconData icon;
  final String title;
  final String detail;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(DrAiSpacing.lg),
    decoration: BoxDecoration(
      color: DrAiColors.white,
      border: Border.all(color: DrAiColors.outline),
      borderRadius: BorderRadius.circular(DrAiRadii.lg),
    ),
    child: Column(
      children: <Widget>[
        Icon(icon, color: DrAiColors.brand, size: 30),
        const SizedBox(height: DrAiSpacing.sm),
        Text(
          title,
          style: const TextStyle(
            color: DrAiColors.ink,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          detail,
          textAlign: TextAlign.center,
          style: const TextStyle(color: DrAiColors.inkSecondary, height: 1.4),
        ),
      ],
    ),
  );
}
