import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:flutter/material.dart';

class FoundationNotice extends StatelessWidget {
  const FoundationNotice({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(DrAiSpacing.md),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceMuted,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: const Text(
        'Foundation preview using synthetic content only. '
        'No clinical features or real patient data are enabled.',
      ),
    );
  }
}
