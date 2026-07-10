import 'package:dr_ai_app/l10n/generated/app_localizations.dart';
import 'package:dr_ai_app/l10n/generated/app_localizations_en.dart';
import 'package:flutter/widgets.dart';

export 'package:dr_ai_app/l10n/generated/app_localizations.dart';

extension AppLocalizationsContext on BuildContext {
  AppLocalizations get l10n =>
      Localizations.of<AppLocalizations>(this, AppLocalizations) ??
      AppLocalizationsEn();
}

extension AppLocalizationsValues on AppLocalizations {
  String stableValue(String value) {
    final normalized = value.trim().toLowerCase();
    if (localeName.startsWith('zh')) {
      final geographicLabel = _zhGeographicLabels[normalized];
      if (geographicLabel != null) {
        return geographicLabel;
      }
    }
    return switch (normalized) {
      'english' => english,
      'simplified chinese' => simplifiedChinese,
      'unspecified' => unspecified,
      'female' => female,
      'male' => male,
      'other' => other,
      'phone' => phone,
      'in-app' => inApp,
      'email' => email,
      'unknown' => unknown,
      'never' => never,
      'former' => former,
      'current' => current,
      'none or rare' => noneOrRare,
      'occasional' => occasional,
      'weekly' => weekly,
      'daily' => daily,
      'prefer not to say' => preferNotToSay,
      'not applicable' => notApplicable,
      'no' => no,
      'yes' => yes,
      'unsure' => unsure,
      'china' => china,
      'guangdong' => guangdong,
      'shenzhen' => shenzhen,
      'active' => active,
      'paused' => paused,
      'stopped' => stopped,
      'monitoring' => monitoring,
      'resolved' => resolved,
      'draft' => draft,
      'pending_review' || 'pending review' => pendingReview,
      'approved' => approved,
      'completed' => completed,
      'pending' => pending,
      'low' => low,
      'moderate' => moderate,
      'high' => high,
      'complete' => completed,
      'partial' => partial,
      'insufficient' => insufficient,
      'sms' => sms,
      'research simulation - not for diagnosis.' => researchNotDiagnosis,
      'synthetic fixture result; no clinical inference was performed.' =>
        assessmentLimitationSynthetic,
      'not validated for diagnosis, treatment, or prognosis.' =>
        assessmentLimitationValidation,
      'review the synthetic case with a qualified clinician.' =>
        assessmentNextStep,
      'hospital profile pending' => hospitalProfilePending,
      'complete hospital details' => completeHospitalDetails,
      'doctor profile' => doctorProfile,
      'clinician' => clinician,
      'ai supported ct image diagnose' ||
      'ai-supported ct image review' => ctImageReview,
      'ai supported x-ray image diagnose' ||
      'ai-supported x-ray image review' => xrayImageReview,
      'ai supported mri image diagnose' ||
      'ai-supported mri image review' => mriImageReview,
      'check patient medical records' => checkMedicalRecords,
      'check patient recovery plans' => checkRecoveryPlans,
      'check imaging results' => checkImagingResults,
      'book medical equipment' => bookEquipment,
      'no patient activity yet' => noPatientActivity,
      'x-ray' => xray,
      'ultrasound' => ultrasound,
      'invite team member' => inviteTeamMember,
      'connect patient' => connectPatient,
      'create event' => createEvent,
      'you have signed out.' => signedOut,
      'you have signed out locally. the server could not be reached.' =>
        signedOutLocally,
      'the email or password is incorrect.' => incorrectCredentials,
      'registration is not available for the selected role.' =>
        registrationRoleUnavailable,
      'an account already exists for this contact.' => accountAlreadyExists,
      'check the phone number, email, password, role, and verification code.' =>
        registrationFieldsInvalid,
      'unable to create the account. check your connection and try again.' =>
        unableToCreateAccount,
      'unable to reach dr. ai. check your connection and try again.' =>
        unableToReachRetry,
      'your session has ended. please sign in again.' => sessionEnded,
      'patient intake summary' => patientIntakeSummary,
      'imaging upload prepared.' => uploadPrepared,
      'imaging upload finalized.' => imagingUploadFinalized,
      'imaging review status updated.' => imagingReviewUpdated,
      _ => value,
    };
  }
}

// Geographic names are structured reference data rather than interface copy.
// Keeping their Chinese display labels here avoids duplicating the stored
// English values used by API payloads and dropdown selection state.
const Map<String, String> _zhGeographicLabels = <String, String>{
  'china': '中国',
  'united states': '美国',
  'canada': '加拿大',
  'united kingdom': '英国',
  'australia': '澳大利亚',
  'japan': '日本',
  'singapore': '新加坡',
  'germany': '德国',
  'france': '法国',
  'india': '印度',
  'beijing': '北京',
  'shanghai': '上海',
  'guangdong': '广东',
  'guangzhou': '广州',
  'shenzhen': '深圳',
  'foshan': '佛山',
  'dongguan': '东莞',
  'zhuhai': '珠海',
  'jiangsu': '江苏',
  'nanjing': '南京',
  'suzhou': '苏州',
  'wuxi': '无锡',
  'changzhou': '常州',
  'zhejiang': '浙江',
  'hangzhou': '杭州',
  'ningbo': '宁波',
  'wenzhou': '温州',
  'jiaxing': '嘉兴',
  'sichuan': '四川',
  'chengdu': '成都',
  'mianyang': '绵阳',
  'deyang': '德阳',
  'hubei': '湖北',
  'wuhan': '武汉',
  'yichang': '宜昌',
  'xiangyang': '襄阳',
  'shandong': '山东',
  'jinan': '济南',
  'qingdao': '青岛',
  'yantai': '烟台',
  'henan': '河南',
  'zhengzhou': '郑州',
  'luoyang': '洛阳',
  'kaifeng': '开封',
  'hunan': '湖南',
  'changsha': '长沙',
  'zhuzhou': '株洲',
  'xiangtan': '湘潭',
  'fujian': '福建',
  'fuzhou': '福州',
  'xiamen': '厦门',
  'quanzhou': '泉州',
  'shaanxi': '陕西',
  'xi’an': '西安',
  'xianyang': '咸阳',
  'baoji': '宝鸡',
};

Locale resolveDrAiLocale(Locale? locale, Iterable<Locale> supportedLocales) {
  if (locale?.languageCode == 'zh') {
    return const Locale('zh');
  }
  return const Locale('en');
}
