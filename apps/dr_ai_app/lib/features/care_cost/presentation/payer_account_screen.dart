import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/application/care_cost_providers.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/account_request_center.dart';
import 'package:dr_ai_app/shared/widgets/account_security.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:dr_ai_app/shared/widgets/sign_out_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PayerAccountScreen extends ConsumerStatefulWidget {
  const PayerAccountScreen({super.key});

  @override
  ConsumerState<PayerAccountScreen> createState() => _PayerAccountScreenState();
}

class _PayerAccountScreenState extends ConsumerState<PayerAccountScreen> {
  String? _savedMessage;

  @override
  Widget build(BuildContext context) {
    final profile = ref.watch(payerProfileProvider);
    final email =
        ref.watch(authControllerProvider).value?.user?.email.trim() ?? '';
    return ResponsiveAppShell(
      role: AppRole.payer,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: profile.when(
          loading: () => ListView(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            children: <Widget>[
              SizedBox(
                height: 180,
                child: DashboardLoadingView(
                  label: context.l10n.loadingPayerAccount,
                ),
              ),
              const AccountRequestCenter(role: AppRole.payer),
            ],
          ),
          error: (error, stackTrace) => ListView(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            children: <Widget>[
              SizedBox(
                height: 220,
                child: DashboardErrorView(
                  message: _payerAccountLoadError(context, error),
                  onRetry: () => ref.invalidate(payerProfileProvider),
                ),
              ),
              const AccountRequestCenter(role: AppRole.payer),
            ],
          ),
          data: (data) => _PayerAccountView(
            profile: data,
            email: email,
            savedMessage: _savedMessage,
            onEditing: () {
              if (_savedMessage != null) {
                setState(() => _savedMessage = null);
              }
            },
            onSaved: () {
              setState(() => _savedMessage = context.l10n.accountSaved);
            },
          ),
        ),
      ),
    );
  }
}

class _PayerAccountView extends ConsumerStatefulWidget {
  const _PayerAccountView({
    required this.profile,
    required this.email,
    required this.savedMessage,
    required this.onEditing,
    required this.onSaved,
  });

  final PayerProfileData profile;
  final String email;
  final String? savedMessage;
  final VoidCallback onEditing;
  final VoidCallback onSaved;

  @override
  ConsumerState<_PayerAccountView> createState() => _PayerAccountViewState();
}

class _PayerAccountViewState extends ConsumerState<_PayerAccountView> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _displayNameController;
  late final TextEditingController _titleController;
  late final TextEditingController _emailController;
  late String _persistedDisplayName;
  late String _persistedTitle;
  late String _persistedEmail;
  bool _saving = false;
  bool _statusIsError = false;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _displayNameController = TextEditingController(
      text: widget.profile.displayName,
    );
    _titleController = TextEditingController(text: widget.profile.title);
    _emailController = TextEditingController(text: widget.email);
    _persistedDisplayName = widget.profile.displayName;
    _persistedTitle = widget.profile.title;
    _persistedEmail = widget.email;
    _statusMessage = widget.savedMessage;
  }

  @override
  void dispose() {
    _displayNameController.dispose();
    _titleController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  void _clearStatus() {
    if (_statusMessage == null && widget.savedMessage == null) {
      return;
    }
    setState(() {
      _statusMessage = null;
      _statusIsError = false;
    });
    widget.onEditing();
  }

  void _cancelChanges() {
    setState(() {
      _displayNameController.text = _persistedDisplayName;
      _titleController.text = _persistedTitle;
      _emailController.text = _persistedEmail;
      _statusMessage = null;
      _statusIsError = false;
    });
    widget.onEditing();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    final displayName = _displayNameController.text.trim();
    final title = _titleController.text.trim();
    final email = _emailController.text.trim().toLowerCase();
    final profileChanged =
        displayName != _persistedDisplayName || title != _persistedTitle;
    final emailChanged = email != _persistedEmail;
    if (!profileChanged && !emailChanged) {
      setState(() {
        _statusMessage = context.l10n.noAccountChanges;
        _statusIsError = false;
      });
      return;
    }

    setState(() {
      _saving = true;
      _statusMessage = null;
      _statusIsError = false;
    });
    var displayNameChanged = false;
    try {
      if (profileChanged) {
        final updated = await ref
            .read(repositoryProvider)
            .updatePayerProfile(displayName: displayName, title: title);
        _persistedDisplayName = updated.displayName;
        _persistedTitle = updated.title;
        displayNameChanged = updated.displayName != widget.profile.displayName;
      }
      if (emailChanged) {
        await ref
            .read(authControllerProvider.notifier)
            .updateAccountEmail(email);
        _persistedEmail = email;
      }
      if (!mounted) {
        return;
      }
      widget.onSaved();
      if (displayNameChanged) {
        ref
            .read(authControllerProvider.notifier)
            .syncAccountDisplayName(_persistedDisplayName);
      }
      ref.invalidate(payerProfileProvider);
      ref.invalidate(payerDashboardProvider);
      setState(() {
        _saving = false;
        _statusMessage = context.l10n.accountSaved;
      });
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _saving = false;
          _statusIsError = true;
          _statusMessage = _payerAccountSaveError(context, error);
        });
      }
    } on Exception {
      if (mounted) {
        setState(() {
          _saving = false;
          _statusIsError = true;
          _statusMessage = context.l10n.accountSaveFailed;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = widget.profile;
    return ListView(
      key: const Key('payer-account-list'),
      padding: EdgeInsets.fromLTRB(
        MediaQuery.sizeOf(context).width >= DrAiBreakpoints.desktop
            ? DrAiSpacing.xl
            : DrAiSpacing.md,
        DrAiSpacing.lg,
        MediaQuery.sizeOf(context).width >= DrAiBreakpoints.desktop
            ? DrAiSpacing.xl
            : DrAiSpacing.md,
        DrAiSpacing.xxl,
      ),
      children: <Widget>[
        Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1180),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  context.l10n.payerAccount,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.brandDark,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: DrAiSpacing.xs),
                Text(
                  context.l10n.payerAccountDescription,
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    height: 1.45,
                  ),
                ),
                const SizedBox(height: DrAiSpacing.lg),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final sideBySide = constraints.maxWidth >= 860;
                    final identity = _identityCard();
                    final governance = _governanceCard(profile);
                    if (!sideBySide) {
                      return Column(
                        children: <Widget>[
                          identity,
                          const SizedBox(height: DrAiSpacing.md),
                          governance,
                        ],
                      );
                    }
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Expanded(child: identity),
                        const SizedBox(width: DrAiSpacing.lg),
                        Expanded(child: governance),
                      ],
                    );
                  },
                ),
                const SizedBox(height: DrAiSpacing.lg),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final sideBySide = constraints.maxWidth >= 760;
                    const security = _PayerAccountCard(
                      key: Key('payer-account-security-card'),
                      child: AccountSecuritySection(keyPrefix: 'payer-account'),
                    );
                    final session = _PayerAccountCard(
                      key: const Key('payer-account-session-card'),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: <Widget>[
                          _SectionHeading(
                            icon: Icons.logout,
                            title: context.l10n.sessionActions,
                            description:
                                context.l10n.payerSessionActionsDescription,
                          ),
                          const SizedBox(height: DrAiSpacing.md),
                          const Align(
                            alignment: Alignment.centerLeft,
                            child: SignOutButton(),
                          ),
                        ],
                      ),
                    );
                    if (!sideBySide) {
                      return Column(
                        children: <Widget>[
                          security,
                          const SizedBox(height: DrAiSpacing.md),
                          session,
                        ],
                      );
                    }
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        const Expanded(child: security),
                        const SizedBox(width: DrAiSpacing.lg),
                        Expanded(child: session),
                      ],
                    );
                  },
                ),
                const SizedBox(height: DrAiSpacing.lg),
                const AccountRequestCenter(role: AppRole.payer),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _identityCard() {
    final effectiveStatus = _statusMessage ?? widget.savedMessage;
    return _PayerAccountCard(
      key: const Key('payer-account-identity-card'),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            _SectionHeading(
              icon: Icons.badge_outlined,
              title: context.l10n.reviewerProfile,
              description: context.l10n.reviewerProfileDescription,
            ),
            const SizedBox(height: DrAiSpacing.lg),
            Row(
              children: <Widget>[
                CircleAvatar(
                  radius: 28,
                  backgroundColor: DrAiColors.brandSoft,
                  child: Text(
                    _initials(_displayNameController.text),
                    style: const TextStyle(
                      color: DrAiColors.brand,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.md),
                Expanded(
                  child: Text(
                    context.l10n.reviewerIdentityHint,
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.lg),
            TextFormField(
              key: const Key('payer-account-display-name-field'),
              controller: _displayNameController,
              enabled: !_saving,
              textInputAction: TextInputAction.next,
              autofillHints: const <String>[AutofillHints.name],
              decoration: InputDecoration(
                labelText: context.l10n.displayName,
                border: const OutlineInputBorder(),
              ),
              validator: (value) =>
                  (value ?? '').trim().isEmpty ? context.l10n.required : null,
              onChanged: (_) {
                _clearStatus();
                setState(() {});
              },
            ),
            const SizedBox(height: DrAiSpacing.md),
            TextFormField(
              key: const Key('payer-account-title-field'),
              controller: _titleController,
              enabled: !_saving,
              textInputAction: TextInputAction.next,
              decoration: InputDecoration(
                labelText: context.l10n.professionalTitle,
                border: const OutlineInputBorder(),
              ),
              validator: (value) {
                final title = (value ?? '').trim();
                if (title.isEmpty) {
                  return context.l10n.required;
                }
                if (title.length < 2) {
                  return context.l10n.payerTitleTooShort;
                }
                return null;
              },
              onChanged: (_) => _clearStatus(),
            ),
            const SizedBox(height: DrAiSpacing.md),
            TextFormField(
              key: const Key('payer-account-email-field'),
              controller: _emailController,
              enabled: !_saving,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.done,
              autofillHints: const <String>[AutofillHints.email],
              decoration: InputDecoration(
                labelText: context.l10n.emailOptional,
                helperText: context.l10n.payerEmailDescription,
                border: const OutlineInputBorder(),
              ),
              validator: (value) {
                final email = (value ?? '').trim();
                return email.isNotEmpty && !_looksLikeEmail(email)
                    ? context.l10n.invalidEmail
                    : null;
              },
              onFieldSubmitted: (_) {
                if (!_saving) {
                  _save();
                }
              },
              onChanged: (_) => _clearStatus(),
            ),
            if (effectiveStatus != null) ...<Widget>[
              const SizedBox(height: DrAiSpacing.md),
              Semantics(
                liveRegion: true,
                child: Container(
                  key: const Key('payer-account-save-status'),
                  padding: const EdgeInsets.all(DrAiSpacing.sm),
                  decoration: BoxDecoration(
                    color: _statusIsError
                        ? const Color(0xFFFFEDEA)
                        : const Color(0xFFEAF8F3),
                    borderRadius: BorderRadius.circular(DrAiRadii.md),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Icon(
                        _statusIsError
                            ? Icons.error_outline
                            : Icons.check_circle_outline,
                        color: _statusIsError
                            ? DrAiColors.danger
                            : const Color(0xFF087B62),
                        size: 20,
                      ),
                      const SizedBox(width: DrAiSpacing.xs),
                      Expanded(
                        child: Text(
                          effectiveStatus,
                          style: TextStyle(
                            color: _statusIsError
                                ? DrAiColors.danger
                                : const Color(0xFF08614F),
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            const SizedBox(height: DrAiSpacing.lg),
            Wrap(
              alignment: WrapAlignment.end,
              spacing: DrAiSpacing.sm,
              runSpacing: DrAiSpacing.sm,
              children: <Widget>[
                TextButton(
                  key: const Key('payer-account-cancel-button'),
                  onPressed: _saving ? null : _cancelChanges,
                  child: Text(context.l10n.cancel),
                ),
                FilledButton.icon(
                  key: const Key('payer-account-save-button'),
                  onPressed: _saving ? null : _save,
                  icon: _saving
                      ? const SizedBox.square(
                          dimension: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: DrAiColors.white,
                          ),
                        )
                      : const Icon(Icons.save_outlined),
                  label: Text(
                    _saving ? context.l10n.saving : context.l10n.saveChanges,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _governanceCard(PayerProfileData profile) {
    return _PayerAccountCard(
      key: const Key('payer-account-governance-card'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _SectionHeading(
            icon: Icons.admin_panel_settings_outlined,
            title: context.l10n.organizationAndAccess,
            description: context.l10n.organizationAndAccessDescription,
          ),
          const SizedBox(height: DrAiSpacing.md),
          Container(
            padding: const EdgeInsets.all(DrAiSpacing.sm),
            decoration: BoxDecoration(
              color: DrAiColors.brandSoft.withValues(alpha: 0.55),
              borderRadius: BorderRadius.circular(DrAiRadii.md),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Icon(
                  Icons.lock_outline,
                  color: DrAiColors.brand,
                  size: 20,
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    context.l10n.organizationAccessManaged,
                    style: const TextStyle(
                      color: DrAiColors.brandDark,
                      height: 1.4,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          _ReadOnlyDetail(
            label: context.l10n.organizationName,
            value: profile.organization.name,
          ),
          _ReadOnlyDetail(
            label: context.l10n.organizationType,
            value: _organizationTypeLabel(
              context,
              profile.organization.organizationType,
            ),
          ),
          _ReadOnlyDetail(
            label: context.l10n.jurisdiction,
            value: profile.organization.jurisdictionCode,
          ),
          _ReadOnlyDetail(
            label: context.l10n.membershipStatus,
            value: _membershipStatusLabel(context, profile.status),
            valueColor: profile.status == 'active'
                ? const Color(0xFF087B62)
                : DrAiColors.ink,
          ),
          _ReadOnlyDetail(
            label: context.l10n.accessScope,
            value: _scopeLabel(context, profile.scope),
          ),
          _ReadOnlyDetail(
            label: context.l10n.organizationVerification,
            value: _verificationLabel(
              context,
              profile.organization.verificationStatus,
            ),
            showDivider: false,
          ),
        ],
      ),
    );
  }
}

class _PayerAccountCard extends StatelessWidget {
  const _PayerAccountCard({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(DrAiSpacing.lg),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        border: Border.all(color: DrAiColors.outline),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x0A0A0076),
            blurRadius: 18,
            offset: Offset(0, 6),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _SectionHeading extends StatelessWidget {
  const _SectionHeading({
    required this.icon,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: DrAiColors.brandSoft,
            borderRadius: BorderRadius.circular(DrAiRadii.md),
          ),
          child: Icon(icon, color: DrAiColors.brand, size: 22),
        ),
        const SizedBox(width: DrAiSpacing.sm),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xxs),
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
    );
  }
}

class _ReadOnlyDetail extends StatelessWidget {
  const _ReadOnlyDetail({
    required this.label,
    required this.value,
    this.valueColor,
    this.showDivider = true,
  });

  final String label;
  final String value;
  final Color? valueColor;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      readOnly: true,
      label: '$label: $value',
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.sm),
        decoration: BoxDecoration(
          border: showDivider
              ? const Border(bottom: BorderSide(color: DrAiColors.outline))
              : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(
              flex: 4,
              child: Text(
                label,
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
            ),
            const SizedBox(width: DrAiSpacing.sm),
            Expanded(
              flex: 5,
              child: Text(
                value,
                textAlign: TextAlign.end,
                style: TextStyle(
                  color: valueColor ?? DrAiColors.ink,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

String _initials(String name) {
  final words = name.trim().split(RegExp(r'\s+'));
  if (words.isEmpty || words.first.isEmpty) {
    return 'DR';
  }
  if (words.length == 1) {
    final characters = words.first.characters;
    return characters.take(2).toString().toUpperCase();
  }
  return '${words.first.characters.first}${words.last.characters.first}'
      .toUpperCase();
}

bool _looksLikeEmail(String value) {
  return RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value);
}

String _payerAccountLoadError(BuildContext context, Object error) {
  if (error is ApiError) {
    return switch (error.code) {
      'unauthenticated' => context.l10n.sessionEnded,
      'not_found' => context.l10n.payerAccessUnavailable,
      _ => context.l10n.payerAccountLoadFailed,
    };
  }
  return context.l10n.payerAccountLoadFailed;
}

String _payerAccountSaveError(BuildContext context, ApiError error) {
  return switch (error.code) {
    'email_already_in_use' => context.l10n.accountEmailAlreadyInUse,
    'unauthenticated' => context.l10n.sessionEnded,
    'not_found' => context.l10n.payerAccessUnavailable,
    'validation_failed' => context.l10n.payerProfileValidationFailed,
    _ => context.l10n.accountSaveFailed,
  };
}

String _organizationTypeLabel(BuildContext context, String value) {
  return switch (value) {
    'public_payer' => context.l10n.publicPayer,
    'commercial_payer' => context.l10n.commercialPayer,
    'observer' => context.l10n.observerOrganization,
    _ => value.replaceAll('_', ' '),
  };
}

String _membershipStatusLabel(BuildContext context, String value) {
  return switch (value) {
    'active' => context.l10n.activeMembership,
    'suspended' => context.l10n.suspended,
    'revoked' => context.l10n.revoked,
    _ => value.replaceAll('_', ' '),
  };
}

String _scopeLabel(BuildContext context, String value) {
  return switch (value) {
    'synthetic_review' => context.l10n.syntheticReviewScope,
    _ => value.replaceAll('_', ' '),
  };
}

String _verificationLabel(BuildContext context, String value) {
  return switch (value) {
    'synthetic_only' => context.l10n.syntheticOnlyVerification,
    'verified' => context.l10n.verified,
    'pending' => context.l10n.pending,
    _ => value.replaceAll('_', ' '),
  };
}
