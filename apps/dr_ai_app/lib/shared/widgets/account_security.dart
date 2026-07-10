import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AccountSecuritySection extends ConsumerWidget {
  const AccountSecuritySection({required this.keyPrefix, super.key});

  final String keyPrefix;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          context.l10n.security,
          style: TextStyle(
            color: DrAiColors.brandDark,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        Text(
          context.l10n.changePasswordDescription,
          style: TextStyle(color: DrAiColors.inkSecondary, height: 1.4),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        OutlinedButton.icon(
          key: Key('$keyPrefix-change-password-button'),
          onPressed: () => showDialog<void>(
            context: context,
            builder: (context) => _ChangePasswordDialog(keyPrefix: keyPrefix),
          ),
          icon: const Icon(Icons.password_outlined),
          label: Text(context.l10n.changePassword),
        ),
      ],
    );
  }
}

class _ChangePasswordDialog extends ConsumerStatefulWidget {
  const _ChangePasswordDialog({required this.keyPrefix});

  final String keyPrefix;

  @override
  ConsumerState<_ChangePasswordDialog> createState() =>
      _ChangePasswordDialogState();
}

class _ChangePasswordDialogState extends ConsumerState<_ChangePasswordDialog> {
  final _formKey = GlobalKey<FormState>();
  final _currentController = TextEditingController();
  final _newController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _saving = false;
  bool _obscure = true;
  String? _errorMessage;

  @override
  void dispose() {
    _currentController.dispose();
    _newController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(context.l10n.changePassword),
      content: SizedBox(
        width: 420,
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              _passwordField(
                controller: _currentController,
                label: context.l10n.currentPassword,
                keyName: '${widget.keyPrefix}-current-password-field',
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _passwordField(
                controller: _newController,
                label: context.l10n.newPassword,
                keyName: '${widget.keyPrefix}-new-password-field',
                validateNewPassword: true,
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _passwordField(
                controller: _confirmController,
                label: context.l10n.confirmNewPassword,
                keyName: '${widget.keyPrefix}-confirm-password-field',
                validator: (value) => value != _newController.text
                    ? context.l10n.passwordMismatch
                    : null,
              ),
              if (_errorMessage != null) ...<Widget>[
                const SizedBox(height: DrAiSpacing.sm),
                Text(
                  context.l10n.stableValue(_errorMessage!),
                  key: Key('${widget.keyPrefix}-change-password-error'),
                  style: const TextStyle(color: DrAiColors.danger),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: _saving ? null : () => Navigator.of(context).pop(),
          child: Text(context.l10n.cancel),
        ),
        FilledButton(
          key: Key('${widget.keyPrefix}-change-password-confirm'),
          onPressed: _saving ? null : _submit,
          child: _saving
              ? const SizedBox.square(
                  dimension: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: DrAiColors.white,
                  ),
                )
              : Text(context.l10n.updatePassword),
        ),
      ],
    );
  }

  TextFormField _passwordField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    bool validateNewPassword = false,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      obscureText: _obscure,
      autofillHints: <String>[
        validateNewPassword
            ? AutofillHints.newPassword
            : AutofillHints.password,
      ],
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: _obscure
              ? context.l10n.showPasswords
              : context.l10n.hidePasswords,
          onPressed: () => setState(() => _obscure = !_obscure),
          icon: Icon(
            _obscure
                ? Icons.visibility_outlined
                : Icons.visibility_off_outlined,
          ),
        ),
      ),
      validator:
          validator ??
          (value) {
            final password = value ?? '';
            if (password.isEmpty) {
              return context.l10n.required;
            }
            if (validateNewPassword &&
                (password.length < 8 || password.length > 20)) {
              return context.l10n.passwordLength;
            }
            return null;
          },
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    setState(() {
      _saving = true;
      _errorMessage = null;
    });
    try {
      await ref
          .read(repositoryProvider)
          .changePassword(
            currentPassword: _currentController.text,
            newPassword: _newController.text,
          );
      if (!mounted) {
        return;
      }
      Navigator.of(context).pop();
      await ref.read(authControllerProvider.notifier).logout();
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _saving = false;
          _errorMessage = error.message;
        });
      }
    } on Exception {
      if (mounted) {
        setState(() {
          _saving = false;
          _errorMessage = context.l10n.unableToChangePassword;
        });
      }
    }
  }
}
