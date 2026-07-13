import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:flutter/material.dart';

class SectionCard extends StatelessWidget {
  const SectionCard({required this.title, required this.child, super.key});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Container(
            color: DrAiColors.sectionHeader,
            padding: const EdgeInsets.symmetric(
              horizontal: DrAiSpacing.md,
              vertical: DrAiSpacing.sm,
            ),
            child: Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: DrAiColors.white,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          Padding(padding: const EdgeInsets.all(DrAiSpacing.md), child: child),
        ],
      ),
    );
  }
}
