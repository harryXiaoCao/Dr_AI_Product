import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SignOutButton extends ConsumerWidget {
  const SignOutButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return OutlinedButton.icon(
      key: const Key('account-sign-out-button'),
      onPressed: auth.isLoading ? null : () => _confirmSignOut(context, ref),
      icon: auth.isLoading
          ? const SizedBox.square(
              dimension: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.logout),
      label: Text(context.l10n.logOut),
      style: OutlinedButton.styleFrom(
        foregroundColor: DrAiColors.danger,
        side: const BorderSide(color: DrAiColors.danger),
      ),
    );
  }

  Future<void> _confirmSignOut(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.l10n.logOutQuestion),
        content: Text(context.l10n.logOutConfirmation),
        actions: <Widget>[
          TextButton(
            key: const Key('sign-out-cancel-button'),
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            key: const Key('sign-out-confirm-button'),
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(context.l10n.logOut),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await ref.read(authControllerProvider.notifier).logout();
    }
  }
}
