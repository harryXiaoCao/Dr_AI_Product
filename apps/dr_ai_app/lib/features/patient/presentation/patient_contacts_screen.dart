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

class PatientContactsScreen extends ConsumerWidget {
  const PatientContactsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final contacts = ref.watch(patientDoctorContactsProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 1,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 720),
            child: contacts.when(
              loading: () =>
                  DashboardLoadingView(label: context.l10n.loadingContacts),
              error: (error, stackTrace) => DashboardErrorView(
                message: context.l10n.loadContactsFailed,
                onRetry: () => ref.invalidate(patientDoctorContactsProvider),
              ),
              data: (data) => _ContactList(doctors: data.items),
            ),
          ),
        ),
      ),
    );
  }
}

class _ContactList extends StatelessWidget {
  const _ContactList({required this.doctors});

  final List<PatientDoctorContact> doctors;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('patient-contact-list'),
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
          context.l10n.contactsDescription,
          style: TextStyle(color: DrAiColors.inkSecondary),
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _SectionLabel(context.l10n.services),
        const SizedBox(height: DrAiSpacing.sm),
        _ContactTile(
          key: Key('system-contact'),
          icon: Icons.notifications_active_outlined,
          iconBackground: Color(0xFFE7F6F1),
          iconColor: Color(0xFF087F5B),
          title: context.l10n.system,
          subtitle: context.l10n.systemContactDescription,
          badge: context.l10n.official,
          onTap: () => context.push('/patient/notifications', extra: 1),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ContactTile(
          key: Key('dr-ai-contact'),
          icon: Icons.auto_awesome_outlined,
          iconBackground: Color(0xFFEDEBFF),
          iconColor: DrAiColors.accentIndigo,
          title: context.l10n.appName,
          subtitle: context.l10n.drAiContactDescription,
          badge: context.l10n.available,
          onTap: () => context.push('/patient/contact/ai'),
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _SectionLabel(context.l10n.connectedDoctors, count: doctors.length),
        const SizedBox(height: DrAiSpacing.sm),
        if (doctors.isEmpty)
          const _EmptyDoctors()
        else
          for (final doctor in doctors) ...<Widget>[
            _DoctorContactTile(doctor: doctor),
            const SizedBox(height: DrAiSpacing.sm),
          ],
        const SizedBox(height: DrAiSpacing.lg),
      ],
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.label, {this.count});

  final String label;
  final int? count;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: DrAiColors.sectionHeader,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      padding: const EdgeInsets.symmetric(
        horizontal: DrAiSpacing.md,
        vertical: DrAiSpacing.sm,
      ),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: DrAiColors.white,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          if (count != null)
            Text(
              '$count',
              key: const Key('doctor-contact-count'),
              style: const TextStyle(
                color: DrAiColors.white,
                fontWeight: FontWeight.w700,
              ),
            ),
        ],
      ),
    );
  }
}

class _ContactTile extends StatelessWidget {
  const _ContactTile({
    required this.icon,
    required this.iconBackground,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.badge,
    this.onTap,
    super.key,
  });

  final IconData icon;
  final Color iconBackground;
  final Color iconColor;
  final String title;
  final String subtitle;
  final String badge;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return _ContactCard(
      leading: CircleAvatar(
        radius: 24,
        backgroundColor: iconBackground,
        child: Icon(icon, color: iconColor),
      ),
      title: title,
      subtitle: subtitle,
      badge: badge,
      onTap: onTap,
    );
  }
}

class _DoctorContactTile extends ConsumerWidget {
  const _DoctorContactTile({required this.doctor});

  final PatientDoctorContact doctor;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final avatar = avatarImageProvider(doctor.avatarUrl);
    final clinicalRole = <String?>[
      doctor.specialty,
      doctor.department,
    ].whereType<String>().where((value) => value.trim().isNotEmpty).join(' · ');
    final pending = doctor.relationshipStatus == 'pending_patient_approval';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        _ContactCard(
          key: Key('doctor-contact-${doctor.doctorId}'),
          leading: CircleAvatar(
            radius: 24,
            backgroundColor: const Color(0xFFE8ECFB),
            backgroundImage: avatar,
            child: avatar == null
                ? Text(
                    _initials(doctor.displayName),
                    style: const TextStyle(
                      color: DrAiColors.brand,
                      fontWeight: FontWeight.w800,
                    ),
                  )
                : null,
          ),
          title: doctor.displayName,
          subtitle: clinicalRole.isEmpty
              ? '${doctor.title} · ${doctor.hospitalName}'
              : '$clinicalRole\n${doctor.hospitalName}',
          badge: pending
              ? context.l10n.pendingPatientApproval
              : context.l10n.connected,
          onTap: pending
              ? null
              : () => context.push(
                  Uri(
                    path: '/patient/contact/private',
                    queryParameters: <String, String>{
                      'id': doctor.doctorId,
                      'name': doctor.displayName,
                    },
                  ).toString(),
                ),
        ),
        Align(
          alignment: Alignment.centerRight,
          child: Wrap(
            spacing: DrAiSpacing.xs,
            children: pending
                ? <Widget>[
                    OutlinedButton(
                      key: Key('reject-doctor-${doctor.doctorId}'),
                      onPressed: () => ref
                          .read(doctorRelationshipActionProvider.notifier)
                          .act(doctor, 'reject'),
                      child: Text(context.l10n.reject),
                    ),
                    FilledButton(
                      key: Key('approve-doctor-${doctor.doctorId}'),
                      onPressed: () => ref
                          .read(doctorRelationshipActionProvider.notifier)
                          .act(doctor, 'approve'),
                      child: Text(context.l10n.approve),
                    ),
                  ]
                : <Widget>[
                    TextButton.icon(
                      key: Key('remove-doctor-${doctor.doctorId}'),
                      onPressed: () => ref
                          .read(doctorRelationshipActionProvider.notifier)
                          .act(doctor, 'revoke'),
                      icon: const Icon(Icons.person_remove_outlined),
                      label: Text(context.l10n.removeConnectedDoctor),
                    ),
                  ],
          ),
        ),
      ],
    );
  }
}

class _ContactCard extends StatelessWidget {
  const _ContactCard({
    required this.leading,
    required this.title,
    required this.subtitle,
    required this.badge,
    this.onTap,
    super.key,
  });

  final Widget leading;
  final String title;
  final String subtitle;
  final String badge;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      label: '$title. $subtitle. $badge.',
      child: Material(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(DrAiRadii.lg),
          child: Container(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            decoration: BoxDecoration(
              border: Border.all(color: DrAiColors.outline),
              borderRadius: BorderRadius.circular(DrAiRadii.lg),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: <Widget>[
                leading,
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
                        style: const TextStyle(
                          color: DrAiColors.inkSecondary,
                          height: 1.35,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: DrAiSpacing.sm),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE7EEFF),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    badge,
                    style: const TextStyle(
                      color: DrAiColors.brand,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                if (onTap != null) ...<Widget>[
                  const SizedBox(width: DrAiSpacing.xs),
                  const Icon(
                    Icons.chevron_right_rounded,
                    color: DrAiColors.inkSecondary,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EmptyDoctors extends StatelessWidget {
  const _EmptyDoctors();

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('doctor-contact-empty-state'),
      padding: const EdgeInsets.all(DrAiSpacing.lg),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        border: Border.all(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
      ),
      child: Column(
        children: <Widget>[
          const Icon(
            Icons.person_add_alt_1_outlined,
            color: DrAiColors.brand,
            size: 30,
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Text(
            context.l10n.noDoctorConnected,
            style: const TextStyle(
              color: DrAiColors.ink,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            context.l10n.sharePatientIdDoctor,
            textAlign: TextAlign.center,
            style: const TextStyle(color: DrAiColors.inkSecondary, height: 1.4),
          ),
        ],
      ),
    );
  }
}

String _initials(String name) {
  final parts = name
      .replaceAll(RegExp(r'^Dr\.?\s+', caseSensitive: false), '')
      .trim()
      .split(RegExp(r'\s+'));
  if (parts.isEmpty || parts.first.isEmpty) {
    return 'DR';
  }
  return parts.take(2).map((part) => part[0].toUpperCase()).join();
}
