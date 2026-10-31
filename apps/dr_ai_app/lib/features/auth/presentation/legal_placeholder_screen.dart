import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/brand_mark.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class LegalPlaceholderScreen extends StatelessWidget {
  const LegalPlaceholderScreen({
    required this.title,
    required this.isPrivacy,
    super.key,
  });

  final String title;
  final bool isPrivacy;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DrAiColors.white,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(DrAiSpacing.xl),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
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
                        _copy(
                          context,
                          'Early synthetic-development notice',
                          '早期合成数据开发说明',
                        ),
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: DrAiColors.inkSecondary,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      ..._sections(context).map(
                        (section) => Padding(
                          padding: const EdgeInsets.only(
                            bottom: DrAiSpacing.sm,
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              const Padding(
                                padding: EdgeInsets.only(top: 3),
                                child: Icon(
                                  Icons.check_circle_outline,
                                  size: 18,
                                  color: DrAiColors.brand,
                                ),
                              ),
                              const SizedBox(width: DrAiSpacing.xs),
                              Expanded(child: Text(section)),
                            ],
                          ),
                        ),
                      ),
                      Text(
                        _copy(
                          context,
                          'This development notice is not a claim of clinical, legal, regulatory, payer, or commercial approval.',
                          '本开发说明不代表已取得临床、法律、监管、支付方或商业批准。',
                        ),
                        style: const TextStyle(
                          color: DrAiColors.inkSecondary,
                          fontSize: 12,
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: DrAiSpacing.lg),
                      OutlinedButton.icon(
                        onPressed: () {
                          if (context.canPop()) {
                            context.pop();
                          } else {
                            context.go('/register');
                          }
                        },
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

  List<String> _sections(BuildContext context) {
    if (isPrivacy) {
      return <String>[
        _copy(
          context,
          'Use synthetic identities, clinical records, images, prices, organizations, and reviewer data only. Do not enter real patient information.',
          '仅使用合成身份、临床记录、影像、价格、机构和审核数据。请勿输入真实患者信息。',
        ),
        _copy(
          context,
          'Role and care-relationship checks limit records to the authorized patient, doctor, or payer request.',
          '角色及医患关系校验会将记录限制在获授权的患者、医生或支付申请范围内。',
        ),
        _copy(
          context,
          'Security and audit logs retain content-minimized metadata; secrets and unnecessary clinical text are excluded.',
          '安全与审计日志仅保留最少必要元数据，不记录密钥或不必要的临床文本。',
        ),
        _copy(
          context,
          'Account deletion, privacy, feedback, and support requests are persisted and can be tracked from the account surface.',
          '账户删除、隐私、反馈和支持请求会被持久化，并可在账户页面跟踪。',
        ),
      ];
    }
    return <String>[
      _copy(
        context,
        'Dr. AI currently operates only with synthetic data in local development and controlled staging.',
        'Dr. AI 当前仅在本地开发和受控预发布环境中使用合成数据。',
      ),
      _copy(
        context,
        'AI output may explain, estimate, or warn. It does not diagnose, prescribe, change medication, or make a payer decision.',
        'AI 可用于解释、估算或提示，但不会进行诊断、开处方、改变用药或作出支付决定。',
      ),
      _copy(
        context,
        'Doctors own recorded diagnoses and clinical plans. Authorized payer reviewers make every acceptance or rejection manually.',
        '医生负责已记录的诊断和临床计划；获授权的支付方审核员手动作出每项接受或拒绝决定。',
      ),
      _copy(
        context,
        'Use only the role and synthetic account assigned to you, and do not attempt to access another user or organization.',
        '仅使用分配给您的角色和合成账户，不得尝试访问其他用户或机构。',
      ),
    ];
  }
}

String _copy(BuildContext context, String en, String zh) {
  return Localizations.localeOf(context).languageCode == 'zh' ? zh : en;
}
