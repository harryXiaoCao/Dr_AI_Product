import 'package:flutter/material.dart';

class DrAiBrandMark extends StatelessWidget {
  const DrAiBrandMark({
    this.size = 40,
    this.semanticLabel = 'Dr. AI logo',
    super.key,
  });

  final double size;
  final String semanticLabel;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: semanticLabel,
      image: true,
      child: Image.asset(
        'assets/brand/dr_ai_mark.png',
        width: size,
        height: size,
        fit: BoxFit.contain,
        filterQuality: FilterQuality.high,
      ),
    );
  }
}
