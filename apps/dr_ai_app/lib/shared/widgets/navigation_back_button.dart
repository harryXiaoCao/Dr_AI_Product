import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Returns to the previous in-app page, or to a safe section on a deep link.
class NavigationBackButton extends StatelessWidget {
  const NavigationBackButton({required this.fallbackPath, super.key});

  final String fallbackPath;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: Localizations.localeOf(context).languageCode == 'zh'
          ? '返回'
          : 'Back',
      onPressed: () {
        if (context.canPop()) {
          context.pop();
        } else {
          context.go(fallbackPath);
        }
      },
      icon: const Icon(Icons.arrow_back_rounded),
    );
  }
}

/// Keeps the return control visible for loading, empty, and error states.
class NavigationPageFrame extends StatelessWidget {
  const NavigationPageFrame({
    required this.fallbackPath,
    required this.child,
    super.key,
  });

  final String fallbackPath;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        Align(
          alignment: Alignment.centerLeft,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
            child: NavigationBackButton(fallbackPath: fallbackPath),
          ),
        ),
        Expanded(child: child),
      ],
    );
  }
}
