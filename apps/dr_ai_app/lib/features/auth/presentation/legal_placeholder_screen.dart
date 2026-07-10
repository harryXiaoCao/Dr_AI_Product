import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/brand_mark.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class LegalPlaceholderScreen extends StatelessWidget {
  const LegalPlaceholderScreen({required this.title, super.key});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DrAiColors.white,
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: Padding(
              padding: const EdgeInsets.all(DrAiSpacing.xl),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  border: Border.all(color: DrAiColors.outline),
                  borderRadius: BorderRadius.circular(DrAiRadii.lg),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(DrAiSpacing.xl),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      const Center(child: DrAiBrandMark(size: 56)),
                      const SizedBox(height: DrAiSpacing.lg),
                      Text(
                        title,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.headlineMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      Text(
                        context.l10n.placeholder,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: DrAiColors.inkSecondary,
                          letterSpacing: 0,
                        ),
                      ),
                      const SizedBox(height: DrAiSpacing.lg),
                      OutlinedButton.icon(
                        onPressed: () => context.go('/register'),
                        icon: const Icon(Icons.arrow_back),
                        label: Text(context.l10n.backToRegistration),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
