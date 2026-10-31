// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Chinese (`zh`).
class AppLocalizationsZh extends AppLocalizations {
  AppLocalizationsZh([String locale = 'zh']) : super(locale);

  @override
  String get appName => 'Dr. AI';

  @override
  String get dashboard => '首页';

  @override
  String get patientManagement => '患者管理';

  @override
  String get account => '账户';

  @override
  String get contacts => '联系';

  @override
  String get connectedDoctors => '已连接医生';

  @override
  String get pendingPatientApproval => '等待您的批准';

  @override
  String get approve => '批准';

  @override
  String get reject => '拒绝';

  @override
  String get removeConnectedDoctor => '移除已连接医生';

  @override
  String get activatePlan => '启用已批准方案';

  @override
  String get authorLabel => '作者';

  @override
  String get reviewerLabel => '审阅医生';

  @override
  String get notAssigned => '未分配——尚未建立独立审阅';

  @override
  String get recoveryPlan => '康复计划';

  @override
  String get myAccount => '我的账户';

  @override
  String get doctorWorkspace => '医生工作台';

  @override
  String get patientWorkspace => '患者空间';

  @override
  String get restoringSession => '正在恢复安全会话';

  @override
  String get signIn => '登录';

  @override
  String get logIn => '登录';

  @override
  String get logOut => '退出登录';

  @override
  String get logOutQuestion => '退出登录？';

  @override
  String get logOutConfirmation => '确认要在此设备上退出 Dr. AI 账户吗？';

  @override
  String get cancel => '取消';

  @override
  String get saveChanges => '保存更改';

  @override
  String get language => '语言';

  @override
  String get languagePreferences => '语言偏好';

  @override
  String get interfaceLanguage => '界面语言';

  @override
  String get interfaceLanguageDescription => '选择此设备上标签、消息和通知使用的语言。';

  @override
  String get english => 'English';

  @override
  String get simplifiedChinese => '简体中文';

  @override
  String get systemLanguage => '跟随系统';

  @override
  String get doctorAccount => '医生账户';

  @override
  String get doctorAccountDescription => '管理个人资料、语言偏好和账户设置。';

  @override
  String get payerAccount => '支付方账户';

  @override
  String get payerAccountDescription => '管理审核员个人身份与账户安全；机构授权继续由管理员维护。';

  @override
  String get loadingPayerAccount => '正在加载支付方账户';

  @override
  String get payerAccountLoadFailed => '无法加载支付方账户，请检查网络连接后重试。';

  @override
  String get pageLoadFailed => '无法加载此页面，请重试。';

  @override
  String get actionFailedRetry => '操作未能完成，请重试。';

  @override
  String get payerAccessUnavailable => '当前支付机构访问权限不可用。如非预期，请联系管理员。';

  @override
  String get reviewerProfile => '审核员资料';

  @override
  String get reviewerProfileDescription => '这些个人身份字段属于您的审核员账户。';

  @override
  String get reviewerIdentityHint => '请使用审核工作区中的同事能够识别的姓名和专业职务。';

  @override
  String get professionalTitle => '专业职务';

  @override
  String get payerTitleTooShort => '请至少输入 2 个字符。';

  @override
  String get payerEmailDescription => '用于登录和账户联系；留空可移除邮箱。';

  @override
  String get payerProfileValidationFailed => '请检查审核员姓名和专业职务后重试。';

  @override
  String get organizationAndAccess => '机构与访问权限';

  @override
  String get organizationAndAccessDescription => '您当前的机构成员关系与审核权限边界。';

  @override
  String get organizationAccessManaged => '以下字段为只读。仅获授权的管理员可更改成员关系、访问范围或认证状态。';

  @override
  String get organizationType => '机构类型';

  @override
  String get jurisdiction => '适用地区';

  @override
  String get membershipStatus => '成员状态';

  @override
  String get accessScope => '访问范围';

  @override
  String get organizationVerification => '机构认证状态';

  @override
  String get publicPayer => '公共支付机构';

  @override
  String get commercialPayer => '商业支付机构';

  @override
  String get observerOrganization => '观察机构';

  @override
  String get activeMembership => '有效';

  @override
  String get suspended => '已暂停';

  @override
  String get revoked => '已撤销';

  @override
  String get syntheticReviewScope => '合成数据审核';

  @override
  String get syntheticOnlyVerification => '仅限合成数据';

  @override
  String get verified => '已认证';

  @override
  String get sessionActions => '会话操作';

  @override
  String get payerSessionActionsDescription => '完成受限审核信息相关工作后，请退出此设备上的账户。';

  @override
  String get saving => '正在保存';

  @override
  String get preferredLanguage => '偏好语言';

  @override
  String get security => '安全';

  @override
  String get changePassword => '修改密码';

  @override
  String get changePasswordDescription => '安全地修改密码。完成后，所有设备上的会话都将退出。';

  @override
  String get currentPassword => '当前密码';

  @override
  String get newPassword => '新密码';

  @override
  String get confirmNewPassword => '确认新密码';

  @override
  String get updatePassword => '更新密码';

  @override
  String get showPasswords => '显示密码';

  @override
  String get hidePasswords => '隐藏密码';

  @override
  String get uploadAvatar => '上传头像';

  @override
  String get editProfile => '编辑个人资料和病史';

  @override
  String patientId(String id) {
    return '患者 ID：$id';
  }

  @override
  String get birthDate => '出生日期';

  @override
  String get gender => '性别';

  @override
  String get phone => '手机号';

  @override
  String get emergencyContact => '紧急联系人';

  @override
  String get contactPreference => '联系偏好';

  @override
  String get location => '所在地';

  @override
  String get height => '身高';

  @override
  String get weight => '体重';

  @override
  String get clinicalEvents => '临床事件';

  @override
  String get medicalHistory => '病史';

  @override
  String get medicalRecordsAndImaging => '医疗记录与影像';

  @override
  String get medicationsAndPrescriptions => '用药与处方';

  @override
  String get clinicalEventsEmpty => '医生创建临床事件后，它会显示在这里。';

  @override
  String get medicalRecords => '医疗记录';

  @override
  String get imagingResults => '影像结果';

  @override
  String get today => '今日';

  @override
  String get overdue => '已逾期';

  @override
  String get upcoming => '即将到期';

  @override
  String get unscheduled => '未排期';

  @override
  String get noScheduledTasks => '此分区暂无任务。';

  @override
  String get careCostsSummary => '诊疗与费用摘要';

  @override
  String get loadingCareCostsSummary => '正在加载诊疗与费用摘要';

  @override
  String get loadCareCostsSummaryFailed => '诊疗与费用暂时无法加载。';

  @override
  String get noCareCostsYet => '尚未记录可计费服务或产品。';

  @override
  String get authoritativeLedgerSummary =>
      '人民币金额与“诊疗与费用”使用同一服务端账本。上传影像属于证据，不会单独计费。';

  @override
  String get estimatedAmounts => '估算金额';

  @override
  String get finalAmounts => '最终金额';

  @override
  String get requestedFromPayer => '向支付方申请';

  @override
  String get expectedPatientResponsibility => '预计个人承担';

  @override
  String get pendingCostItems => '费用待补充';

  @override
  String get askDrAi => '咨询 Dr. AI';

  @override
  String get careRecords => '照护记录';

  @override
  String get privacyPolicy => '隐私政策';

  @override
  String get termsOfService => '服务条款';

  @override
  String get returnToDashboard => '返回首页';

  @override
  String get unauthorized => '当前身份无法访问此页面。';

  @override
  String get tryAgain => '重试';

  @override
  String get notRecorded => '未记录';

  @override
  String get noneRecorded => '暂无记录';

  @override
  String get yes => '是';

  @override
  String get no => '否';

  @override
  String get done => '完成';

  @override
  String get next => '下一步';

  @override
  String get backToRegistration => '返回注册';

  @override
  String get privacySupport => '隐私、同意与支持';

  @override
  String get accountSaved => '账户更改已保存。';

  @override
  String get accountSaveFailed => '无法保存账户更改。请检查网络连接后重试。';

  @override
  String get accountEmailAlreadyInUse => '该邮箱已绑定其他账户。请使用其他邮箱，或将此项留空。';

  @override
  String get languageUpdated => '界面语言已更新。';

  @override
  String get systemLanguageDescription => '系统语言为中文或英文时自动跟随；其他语言默认使用英文。';

  @override
  String get welcome => '欢迎使用 Dr. AI';

  @override
  String get signInDescription => '使用账户绑定的手机号或邮箱登录。';

  @override
  String get forgotPassword => '忘记密码？';

  @override
  String get stagingNotice => '当前为预发布环境，请勿输入真实患者数据。';

  @override
  String get alreadyHaveAccount => '已有账户？';

  @override
  String get doctorRegistration => '医生注册';

  @override
  String get payerRegistration => '支付方注册';

  @override
  String get createAccount => '创建账户';

  @override
  String get createAccountDoctorDescription => '创建账户并加入 Dr. AI';

  @override
  String get createAccountPayerDescription => '创建授权审核账户，用于透明的诊疗与费用审核';

  @override
  String get createAccountPatientDescription => '设置账户后继续填写健康资料。';

  @override
  String get accountInformation => '账户信息';

  @override
  String get personalInformation => '个人信息';

  @override
  String get hospitalInformation => '医院信息';

  @override
  String get homeAddress => '家庭住址';

  @override
  String get code => '区号';

  @override
  String get emailOrPhone => '邮箱或手机号';

  @override
  String get phoneNumber => '手机号';

  @override
  String get enterPhoneNumber => '请输入手机号';

  @override
  String get emailOptional => '邮箱（选填）';

  @override
  String get password => '密码';

  @override
  String get passwordGuidance => '使用 8–20 个字符，可包含字母、数字和符号。';

  @override
  String get showPassword => '显示密码';

  @override
  String get hidePassword => '隐藏密码';

  @override
  String get confirmPassword => '确认密码';

  @override
  String get verificationCode => '验证码';

  @override
  String get enterVerificationCode => '请输入 6 位验证码';

  @override
  String get sendCode => '发送验证码';

  @override
  String get patient => '患者';

  @override
  String get doctor => '医生';

  @override
  String get payer => '支付方';

  @override
  String get organizationInformation => '机构信息';

  @override
  String get organizationName => '机构名称';

  @override
  String get firstName => '名';

  @override
  String get middleNameOptional => '中间名（选填）';

  @override
  String get lastName => '姓';

  @override
  String get dateOfBirth => '出生日期';

  @override
  String get selectDate => '选择日期';

  @override
  String get countryRegion => '国家或地区';

  @override
  String get province => '省／州';

  @override
  String get city => '城市';

  @override
  String get hospital => '医院';

  @override
  String get hospitalEmpty => '暂无可选医院';

  @override
  String get hospitalMissing => '找不到您的医院？';

  @override
  String get addHospital => '添加我的医院';

  @override
  String get hospitalName => '医院名称';

  @override
  String get termsConsentPrefix => '我已阅读并同意';

  @override
  String get termsConsentJoiner => '和';

  @override
  String get required => '必填项。';

  @override
  String get invalidAccount => '请输入有效的邮箱或手机号。';

  @override
  String get invalidPhone => '请输入有效的手机号。';

  @override
  String get phoneRequired => '手机号为必填项。';

  @override
  String get invalidEmail => '请输入有效的邮箱地址。';

  @override
  String get enterPassword => '请输入密码。';

  @override
  String get passwordLength => '密码需为 8–20 个字符。';

  @override
  String get passwordMismatch => '两次输入的密码不一致。';

  @override
  String get enterSixDigitCode => '请输入 6 位验证码。';

  @override
  String get enterPhoneFirst => '请先输入手机号。';

  @override
  String get alreadyHaveAccountLogIn => '已有账户？登录';

  @override
  String get createAnAccount => '创建账户';

  @override
  String get loading => '正在加载';

  @override
  String get loadingContacts => '正在加载联系人';

  @override
  String get loadContactsFailed => '无法加载联系人，请重试。';

  @override
  String get contactsDescription => '您的医疗团队和 Dr. AI 服务都集中在这里。';

  @override
  String get services => '服务';

  @override
  String get system => '系统';

  @override
  String get systemContactDescription => '接收康复计划、用药、费用和账户提醒';

  @override
  String get official => '官方';

  @override
  String get drAiContactDescription => '就一般健康问题进行教育性对话';

  @override
  String get comingLater => '即将推出';

  @override
  String get myDoctors => '我的医生';

  @override
  String get groups => '群组';

  @override
  String get careGroups => '照护群组';

  @override
  String get careGroupsDescription => '群组对话和创建功能将在后续版本开放';

  @override
  String get connected => '已连接';

  @override
  String get noDoctorConnected => '尚未连接医生';

  @override
  String get sharePatientIdDoctor => '将患者 ID 分享给医生。连接后，医生会显示在这里。';

  @override
  String get placeholder => '内容准备中';

  @override
  String get privacyAndDataNotice => '隐私与数据说明';

  @override
  String get privacyNoticeBody =>
      '本合成数据开发环境受此处列明的账户、同意、隐私和支持边界约束，未获准处理真实患者数据或用于真实临床场景。';

  @override
  String get privacyNoData => '请勿在预发布环境中输入姓名、联系方式、原始病历、影像或患者拥有的临床内容。';

  @override
  String get privacyBackendKeys =>
      'DeepSeek 仅由 FastAPI 后端调用，密钥不会进入 Flutter 应用。';

  @override
  String get privacyChatBoundary => '对话仅用于准备教育性问题，并会在调用任何大模型前经过危险信号安全检查。';

  @override
  String get consentChecklist => '同意确认清单';

  @override
  String get consentStagingData => '我了解预发布环境尚不适合输入真实患者数据。';

  @override
  String get consentNoEmergency => '我了解 Dr. AI 不用于急救、诊断或治疗决策。';

  @override
  String get consentNoRealData => '我了解不得提交真实患者数据。';

  @override
  String get consentReady => '本地同意确认已准备完成。';

  @override
  String get consentIncomplete => '请先完成所有确认项再使用此预发布页面。';

  @override
  String get accountDeletionRequest => '账户删除申请';

  @override
  String get deletionLocalOnly => '此页面仅在本地准备删除申请，不会删除数据、修改账户或联系测试人员。';

  @override
  String get deletionPrompt => '输入 REQUEST ACCOUNT DELETION';

  @override
  String get prepareRequest => '准备申请';

  @override
  String get deletionPrepared => '删除申请已在本地准备完成，未更改任何账户数据。';

  @override
  String get feedbackForm => '反馈表';

  @override
  String get feedbackPrivacy => '请勿包含患者信息、含有隐私数据的截图或账户密钥。';

  @override
  String get feedbackDraft => '反馈草稿';

  @override
  String get feedbackHint => '请描述问题、设备、浏览器和所在的账户步骤。';

  @override
  String get prepareFeedback => '准备反馈草稿';

  @override
  String get feedbackPrepared => '反馈草稿已在本地准备完成，未发送任何外部消息。';

  @override
  String get knownLimitations => '已知限制';

  @override
  String get limitationClinical => '临床模型推理、计费、预约以及视频或语音问诊尚未开放。';

  @override
  String get limitationUpload => '影像上传完成流程和存储政策需要另行通过生产审批。';

  @override
  String get limitationRecovery => '密码重置、账户恢复以及经验证的短信或邮件发送仍在后续范围内。';

  @override
  String get limitationRelease => '任何生产部署、应用商店分发或账户政策变更都需要明确的发布审批。';

  @override
  String get privacySupportTitle => 'Dr. AI 隐私与支持';

  @override
  String get privacySupportHero => '隐私与支持';

  @override
  String get accountPolicyStaging => 'Dr. AI 合成数据开发环境的账户与隐私边界。';

  @override
  String accountPolicyUser(String name) {
    return '$name 的合成数据开发账户与隐私边界。';
  }

  @override
  String get stagingPolicyPlaceholder => '合成数据开发政策';

  @override
  String get passwordUpdated => '密码已更新';

  @override
  String get resetPassword => '重置密码';

  @override
  String get passwordChangedSignIn => '密码已修改，请使用新密码重新登录。';

  @override
  String get verifyPhoneReset => '请验证账户绑定的手机号。验证码将在 10 分钟后失效。';

  @override
  String get enterYourPhone => '请输入手机号。';

  @override
  String get sendVerificationCode => '发送验证码';

  @override
  String get sixDigitVerificationCode => '6 位验证码';

  @override
  String get backToSignIn => '返回登录';

  @override
  String get resetPasswordFailed => '无法重置密码，请重试。';

  @override
  String get stepAccount => '1  账户';

  @override
  String get stepProfile => '2  资料';

  @override
  String get stepLocation => '3  所在地';

  @override
  String get stepComplete => '4  完成';

  @override
  String get profile => '个人资料';

  @override
  String get careHospitalDetails => '照护与医院信息';

  @override
  String get finishSetup => '完成设置';

  @override
  String get loadingAccount => '正在加载账户';

  @override
  String get loadAccountFailed => '无法加载账户，请重试。';

  @override
  String get loadingRecoveryPlans => '正在加载康复计划';

  @override
  String get loadRecoveryPlansFailed => '无法加载康复计划，请重试。';

  @override
  String get loadingProfile => '正在加载个人资料';

  @override
  String get loadProfileFailed => '无法加载个人资料，请重试。';

  @override
  String get prescriptions => '处方';

  @override
  String get medicationReminders => '用药提醒';

  @override
  String get noMedications => '尚未记录用药。';

  @override
  String get records => '记录';

  @override
  String get imaging => '影像';

  @override
  String get available => '可查看';

  @override
  String get noneYet => '暂无';

  @override
  String get loadingActivePlan => '正在加载当前计划';

  @override
  String get loadActivePlanFailed => '无法加载当前康复计划，请重试。';

  @override
  String get noActivePlan => '目前没有生效的康复计划。医生可在患者管理中批准计划。';

  @override
  String get planHistory => '计划历史';

  @override
  String get planHistoryEmpty => '康复计划历史会显示在这里。';

  @override
  String get completeHealthProfile => '完善健康资料';

  @override
  String get medicalIntake => '健康信息采集';

  @override
  String get medicalIntakeDescription =>
      '请完成一次填写，以便照护团队在首次临床事件前查看您的资料。标有 * 的字段为必填项，选填项可留空。';

  @override
  String get aboutYou => '关于您';

  @override
  String get aboutYouDescription => '填写照护团队用于识别和联系您的信息。';

  @override
  String get fullNameRequired => '姓名 *';

  @override
  String get homeAddressOptional => '家庭住址（选填）';

  @override
  String get streetBuilding => '街道和楼栋信息';

  @override
  String get unspecified => '未说明';

  @override
  String get female => '女';

  @override
  String get male => '男';

  @override
  String get other => '其他';

  @override
  String get emergencyContactOptional => '紧急联系人（选填）';

  @override
  String get fullName => '姓名';

  @override
  String get emergencyPhoneOptional => '紧急联系电话（选填）';

  @override
  String get includeCountryCode => '请包含国家区号';

  @override
  String get inApp => '应用内';

  @override
  String get email => '邮箱';

  @override
  String get healthMeasurements => '健康测量';

  @override
  String get healthMeasurementsDescription => '填写最近一次已知的测量值。如果不知道血压，可以留空。';

  @override
  String get heightCmRequired => '身高（厘米）*';

  @override
  String get weightKgRequired => '体重（千克）*';

  @override
  String get bloodType => '血型';

  @override
  String get bloodPressure => '血压';

  @override
  String get unknown => '未知';

  @override
  String get systolicBp => '收缩压';

  @override
  String get diastolicBp => '舒张压';

  @override
  String get smokingStatus => '吸烟情况';

  @override
  String get never => '从不';

  @override
  String get former => '已戒烟';

  @override
  String get current => '目前吸烟';

  @override
  String get alcohol => '饮酒情况';

  @override
  String get noneOrRare => '不饮酒或极少';

  @override
  String get occasional => '偶尔';

  @override
  String get weekly => '每周';

  @override
  String get daily => '每天';

  @override
  String get allergiesConditions => '过敏与健康状况';

  @override
  String get conditionsDescription => '仅在符合相应情况时选择“是”。选择后可填写发生时间、治疗或当前状态。';

  @override
  String get hasAllergies => '您是否有任何过敏？';

  @override
  String get allergy => '过敏原';

  @override
  String get reactionOptional => '反应（选填）';

  @override
  String get hasChronicCondition => '您是否有遗传性或长期疾病？';

  @override
  String get condition => '疾病';

  @override
  String get notesOptional => '备注（选填）';

  @override
  String get diagnosisTreatmentHint => '诊断日期、治疗方式或当前状态';

  @override
  String get heartHistory => '心脏或血管病史';

  @override
  String get heartHistoryDescription => '心肌梗死、中风、心律不齐、血栓或心力衰竭。';

  @override
  String get endocrineHistory => '糖尿病、甲状腺或骨骼健康';

  @override
  String get endocrineHistoryDescription => '糖尿病（包括妊娠糖尿病）、甲状腺疾病或骨质疏松。';

  @override
  String get neuroHistory => '神经、情绪或心理健康';

  @override
  String get neuroHistoryDescription => '抑郁、严重焦虑、癫痫、双相情感障碍或慢性偏头痛。';

  @override
  String get digestiveHistory => '胃肠或肝脏病史';

  @override
  String get digestiveHistoryDescription => '溃疡、克罗恩病、溃疡性结肠炎、肠易激综合征、肝炎或肝硬化。';

  @override
  String get respiratoryHistory => '肺部或呼吸病史';

  @override
  String get respiratoryHistoryDescription => '哮喘、慢阻肺、肺气肿或需要住院治疗的严重肺炎。';

  @override
  String get kidneyHistory => '肾脏或泌尿系统病史';

  @override
  String get kidneyHistoryDescription => '慢性肾病、肾功能下降或严重肾结石。';

  @override
  String get cancerHistory => '肿瘤或正在进行的治疗';

  @override
  String get cancerHistoryDescription => '任何肿瘤（包括皮肤癌）、化疗、放疗或免疫治疗。';

  @override
  String get medicalBackground => '医疗背景与日常生活';

  @override
  String get medicalBackgroundDescription => '请使用简短易懂的描述。之后可在“我的账户”中更新这些信息。';

  @override
  String get currentMedicationsOptional => '目前使用的药物和补充剂（选填）';

  @override
  String get medicationHint => '填写名称、剂量和服用频率';

  @override
  String get surgeriesOptional => '既往手术或住院经历（选填）';

  @override
  String get surgeriesHint => '填写手术或住院原因、年份和医院';

  @override
  String get familyHistoryOptional => '家族病史（选填）';

  @override
  String get familyHistoryHint => '填写疾病以及亲属关系，例如父母或兄弟姐妹';

  @override
  String get lifestyleOptional => '运动与睡眠备注（选填）';

  @override
  String get lifestyleHint => '填写通常每周的活动和睡眠情况';

  @override
  String get pregnancyStatus => '妊娠状态';

  @override
  String get preferNotToSay => '不愿说明';

  @override
  String get notApplicable => '不适用';

  @override
  String get unsure => '不确定';

  @override
  String get saveProfileFailed => '无法保存个人资料，请检查表单后重试。';

  @override
  String get useNumbersOnly => '请仅输入数字。';

  @override
  String get useDateFormat => '请使用 YYYY-MM-DD 格式。';

  @override
  String get provinceState => '省／州';

  @override
  String get loadingTodayTasks => '正在加载今日康复任务';

  @override
  String get loadTodayTasksFailed => '无法加载今日康复任务，请重试。';

  @override
  String get phase5MedicationNotificationsReadOnly =>
      '第五阶段不会安排系统用药通知。第六阶段需完成设备注册并接入受治理的通知投递服务；目前请使用已保存的应用内任务清单。';

  @override
  String get noTodayTasks => '今天没有待完成的康复任务。';

  @override
  String get taskSyncFailed => '完成状态未能同步。您的本地操作仍会显示，请在网络恢复后重试。';

  @override
  String get loadingMedicationReminders => '正在加载用药提醒…';

  @override
  String get medicationRemindersUnavailable => '用药提醒当前不可用。';

  @override
  String get noMedicationReminders => '目前没有到期的用药提醒。';

  @override
  String get refill => '续药';

  @override
  String get educationalDisclaimer => '仅供健康教育参考，不构成医疗建议。';

  @override
  String get prepareQuestion => '准备一个想向医生咨询的问题';

  @override
  String get sendEducationalQuestion => '发送教育性问题';

  @override
  String get streamingResponse => '正在生成回复…';

  @override
  String fallbackReason(String reason) {
    return '备用回复原因：$reason';
  }

  @override
  String get exercise => '运动';

  @override
  String get diet => '饮食';

  @override
  String get followUp => '随访';

  @override
  String get task => '任务';

  @override
  String get noClinicalEventUpdate => '当前没有可提交更新的临床事件';

  @override
  String updateEvent(String title) {
    return '更新：$title';
  }

  @override
  String latestPatientUpdate(String summary) {
    return '患者最近更新：$summary';
  }

  @override
  String get updateType => '更新类型';

  @override
  String get generalUpdate => '一般更新';

  @override
  String get symptomUpdate => '症状更新';

  @override
  String get medicationNote => '用药备注';

  @override
  String get recoveryCheckIn => '康复反馈';

  @override
  String get selfReportedUpdate => '患者自述更新';

  @override
  String updateSubmitted(String type) {
    return '已提交更新：$type';
  }

  @override
  String get sendUpdate => '发送更新';

  @override
  String get enterUpdate => '请先填写简短更新。';

  @override
  String get paymentUnavailable => '暂不支持付款';

  @override
  String get payNowUnavailable => '暂不支持立即付款';

  @override
  String get paymentDescription => '您可以在这里查看费用状态，目前尚未开放在线付款。';

  @override
  String get chatRateLimited => '教育性对话请求过于频繁，请稍后重试。';

  @override
  String get unableToReach => '无法连接 Dr. AI。';

  @override
  String get conditionDetailsHint => '补充诊断、日期、治疗方式或当前状态';

  @override
  String get china => '中国';

  @override
  String get guangdong => '广东省';

  @override
  String get shenzhen => '深圳市';

  @override
  String get active => '进行中';

  @override
  String get careRelationshipActive => '诊疗关系有效';

  @override
  String get paused => '已暂停';

  @override
  String get stopped => '已停止';

  @override
  String get monitoring => '观察中';

  @override
  String get resolved => '已解决';

  @override
  String get draft => '草稿';

  @override
  String get pendingReview => '待审核';

  @override
  String get approved => '已批准';

  @override
  String get completed => '已完成';

  @override
  String get pending => '待处理';

  @override
  String get completeProfileSetup => '完善个人资料';

  @override
  String get sharePatientCode => '分享患者代码';

  @override
  String get waitDoctorConnect => '等待医生连接';

  @override
  String get after => '之后';

  @override
  String get reviewMedicalHistory => '查看您的病史';

  @override
  String get confirmContactPreferences => '确认联系偏好';

  @override
  String get prepareDoctorQuestions => '准备想向医生咨询的问题';

  @override
  String get followCareTasks => '完成医生创建的照护任务';

  @override
  String get trackRecovery => '跟踪康复进展';

  @override
  String get checkMedicationsImaging => '查看用药和影像结果';

  @override
  String get doctorNotConnected => '尚未连接医生';

  @override
  String get sharePatientCodeAction => '分享患者代码';

  @override
  String get careAfterConnection => '连接医生后会显示照护详情。';

  @override
  String get consultation => '问诊';

  @override
  String get medicalRecord => '医疗记录';

  @override
  String get medication => '用药';

  @override
  String allergiesSummary(String value) {
    return '过敏：$value';
  }

  @override
  String chronicDiseasesSummary(String value) {
    return '慢性疾病：$value';
  }

  @override
  String visitHistorySummary(int count) {
    return '就诊记录：$count';
  }

  @override
  String diagnosesSummary(String value) {
    return '诊断：$value';
  }

  @override
  String get loadingDoctorAccount => '正在加载医生账户';

  @override
  String get noAccountChanges => '没有需要保存的账户更改。';

  @override
  String get doctorIdentityRequired => '保存前必须填写显示名称和职称。';

  @override
  String get verificationStatus => '认证状态';

  @override
  String get activeDoctorAccount => '医生账户已启用';

  @override
  String get inactiveDoctorAccount => '当前不活跃';

  @override
  String doctorLastOnline(String date) {
    return '当前不活跃 · 上次在线 $date';
  }

  @override
  String get accountContact => '账户联系方式';

  @override
  String get clinicalIdentity => '临床身份';

  @override
  String get displayName => '显示名称';

  @override
  String get specialty => '专科';

  @override
  String get title => '职称';

  @override
  String get hospitalLocation => '医院与所在地';

  @override
  String get hospitalManaged => '医院（由管理员维护）';

  @override
  String get department => '科室';

  @override
  String get contact => '联系方式';

  @override
  String get hospitalProfilePending => '医院资料待完善';

  @override
  String get completeHospitalDetails => '请完善医院信息';

  @override
  String get careWorkspaceReady => '照护工作台已可连接患者代码。';

  @override
  String get doctorProfile => '医生资料';

  @override
  String get clinician => '临床医生';

  @override
  String get connectPatientsEpisodes => '通过患者代码建立连接并开始照护事件';

  @override
  String get noPatientActivity => '暂无患者活动';

  @override
  String get xray => 'X 光';

  @override
  String get ultrasound => '超声';

  @override
  String get inviteTeamMember => '邀请团队成员';

  @override
  String get connectPatient => '连接患者';

  @override
  String get createEvent => '创建临床事件';

  @override
  String get quickAccess => '快捷入口';

  @override
  String get imagingRecordsManualReview => '影像记录与人工审核';

  @override
  String get imagingRecordsManualReviewDescription =>
      '选择患者后查看与临床事件关联的影像证据及医生填写的审核状态。';

  @override
  String get patientMedicalRecords => '患者医疗记录';

  @override
  String get patientMedicalRecordsDescription => '选择患者后查看获授权的临床病史与记录。';

  @override
  String get patientRecoveryPlans => '患者康复计划';

  @override
  String get patientRecoveryPlansDescription => '选择患者后打开康复计划工作区。';

  @override
  String get medicalResourcesReadOnly => '医疗资源（只读）';

  @override
  String get medicalResourcesReadOnlyDescription => '查看当前信息性资源概览；尚未开放预约。';

  @override
  String get payerRequests => '支付申请';

  @override
  String get payerRequestsDescription => '打开由人工审核的医生支付申请工作区。';

  @override
  String get teamManagement => '团队管理';

  @override
  String get recentActivities => '最近活动';

  @override
  String get resourceOverview => '资源概览';

  @override
  String get ok => '确定';

  @override
  String get medicalEquipment => '医疗设备';

  @override
  String resourceAvailable(int available, int total) {
    return '$available/$total 可用';
  }

  @override
  String get medicationStocks => '药品库存';

  @override
  String get staffingLevels => '人员配置';

  @override
  String get bedAvailability => '床位情况';

  @override
  String get operationalSummary => '诊所数据更新后，这里会显示运营概览。';

  @override
  String get overview => '概览';

  @override
  String get verifiedHistory => '已核实病史';

  @override
  String get activeClinicalEvents => '当前临床事件';

  @override
  String get activeRecoveryPlan => '当前康复计划';

  @override
  String get currentMedications => '目前用药';

  @override
  String get overviewSummary => '患者摘要与当前临床事件背景';

  @override
  String get profileSummary => '供医生查看的患者自主管理信息';

  @override
  String get medicalHistoryLower => '病史';

  @override
  String get medicalHistorySummary => '患者填写的病史与医生审核信息';

  @override
  String get clinicalEventsSummary => '按时间整理问题、就诊、诊断及关联照护';

  @override
  String get medicationsPrescriptions => '用药与处方';

  @override
  String get medicationsSummary => '与临床事件关联的医嘱、计划和自动提醒';

  @override
  String get recoveryPlans => '康复计划';

  @override
  String get recoveryPlansSummary => '与临床事件关联的计划创建、审核和完成记录';

  @override
  String get imagingSummary => '与临床事件关联的影像信息和人工审核状态';

  @override
  String get consultationActivity => '问诊与活动';

  @override
  String get consultationActivitySummary => '医生备注、专科审核和相关时间线';

  @override
  String get searchPatients => '搜索患者';

  @override
  String get collapsePatientList => '收起患者列表';

  @override
  String get expandPatientList => '展开患者列表';

  @override
  String get collapseSectionNavigation => '收起分区导航';

  @override
  String get expandSectionNavigation => '展开分区导航';

  @override
  String get namePatientId => '姓名或患者 ID';

  @override
  String get loadingPatients => '正在加载患者';

  @override
  String get noConnectedPatients => '暂无已连接患者';

  @override
  String get connectPatientEmpty => '向患者获取代码并在此建立连接，然后从零开始创建照护工作区。';

  @override
  String get connectPatientByCode => '通过代码连接患者';

  @override
  String get patientCode => '患者代码';

  @override
  String get patientCodeHelper => '注册后显示在患者首页';

  @override
  String get reviewPatientMatch => '查看匹配患者';

  @override
  String connectedPatient(String name) {
    return '已连接 $name。';
  }

  @override
  String get enterPatientCode => '请输入患者代码。';

  @override
  String get confirmPatientConnection => '确认连接患者';

  @override
  String get confirmPatientDescription => '创建患者照护工作区访问权限前，请确认这就是向您提供 ID 的患者。';

  @override
  String get confirmConnect => '确认并连接';

  @override
  String get patientNotFound => '没有与此 ID 匹配的患者，请检查后重试。';

  @override
  String get reviewPatientFailed => '无法查看此患者 ID，请重试。';

  @override
  String get patientProfile => '患者资料';

  @override
  String get choosePatient => '选择患者';

  @override
  String get selectPatient => '请选择患者';

  @override
  String get selectPatientDescription => '打开已分配患者以查看核心记录。';

  @override
  String get patientWorkspaceTitle => '患者工作区';

  @override
  String get loadingPatientProfile => '正在加载患者资料';

  @override
  String get changePatient => '更换患者';

  @override
  String get recoveryPlanLoading => '正在加载康复计划';

  @override
  String get recoveryPlanUnavailable => '康复计划当前不可用';

  @override
  String lastVisit(String value) {
    return '最近就诊：$value';
  }

  @override
  String get activeClinicalEvent => '当前临床事件';

  @override
  String get createEventFirst => '请先创建临床事件，再进行与事件关联的照护工作。';

  @override
  String get createEventBeforeCare => '请先创建临床事件，再添加与事件关联的处方、康复计划、影像、备注或问诊。';

  @override
  String get selectedCareEpisode => '所选照护事件';

  @override
  String get legacyRecordsNotice => '选择事件前，关联版块会显示原有的患者级记录。';

  @override
  String get workspaceSection => '工作区版块';

  @override
  String get clinicalEventReadiness => '临床事件准备状态';

  @override
  String activeEventStatus(String status) {
    return '当前事件：$status';
  }

  @override
  String get createSelectEventDescription =>
      '创建或选择临床事件，将处方、用药计划、康复计划、影像、备注和问诊整理到同一照护事件下。';

  @override
  String get doctorReviewOnly => '医生仅查看：患者自主管理的资料不能在此工作区直接编辑。';

  @override
  String get profileCorrectionNotice => '如需修改资料，应请患者自行更正；医生不能在此直接编辑。';

  @override
  String get historyAuditNotice => '病史由患者填写。医生的确认、更正请求和补充说明会以可见的审计记录保存。';

  @override
  String get allergies => '过敏';

  @override
  String get noAllergies => '未记录过敏';

  @override
  String get noReaction => '未记录过敏反应详情。';

  @override
  String get chronicDiseases => '慢性疾病';

  @override
  String get noChronicDiseases => '未记录慢性疾病';

  @override
  String get noConditionNote => '未记录疾病备注。';

  @override
  String get doctorAmendmentAdded => '医生已在查看患者病史后添加补充说明。';

  @override
  String get patientConfirmHistory => '请患者在个人资料中确认此项病史。';

  @override
  String get medicalHistoryReview => '病史审核';

  @override
  String get noPatientHistoryItem => '目前没有可供医生审核的患者过敏、慢性疾病或医疗记录。';

  @override
  String get patientEnteredItem => '患者填写项目';

  @override
  String get reviewAction => '审核操作';

  @override
  String get markVerified => '标记为已确认';

  @override
  String get addDoctorAmendment => '添加医生补充说明';

  @override
  String get requestPatientCorrection => '请求患者更正';

  @override
  String get doctorAmendment => '医生补充说明';

  @override
  String get patientCorrectionRequest => '患者更正请求';

  @override
  String get saveAuditedReview => '保存审核记录';

  @override
  String historyReviewSaved(String action) {
    return '病史审核已保存：$action。';
  }

  @override
  String get selectHistoryItem => '请先选择患者填写的项目。';

  @override
  String get enterDoctorAmendment => '请输入医生补充说明。';

  @override
  String get enterPatientCorrection => '请输入希望患者更正的内容。';

  @override
  String get encounterUpdates => '就诊更新';

  @override
  String get noEncounterUpdates => '暂无就诊更新';

  @override
  String clinicalEventLink(String title) {
    return '关联临床事件：$title';
  }

  @override
  String get doctorDiagnosisRecord => '医生诊断记录';

  @override
  String get noDiagnoses => '未记录诊断';

  @override
  String get noDiagnosisNote => '未记录诊断备注。';

  @override
  String get diagnosisReadOnly => '患者可以查看此记录，但不能编辑医生诊断。';

  @override
  String get doctorNotes => '医生备注';

  @override
  String get noDoctorNotes => '暂无医生备注';

  @override
  String linkedToEvent(String title) {
    return '关联至 $title';
  }

  @override
  String prescriptionContextNotice(String title) {
    return '处方医嘱和当前用药计划显示在 $title 下方。以下提醒由用药计划自动生成，不是独立的医生工作区。';
  }

  @override
  String imagingEvidenceNotice(String title) {
    return '影像作为 $title 的辅助证据供医生查看。检查结果仍由医生填写，应用不会自动作出临床判断。';
  }

  @override
  String get noEncounterUpdate => '未记录就诊更新';

  @override
  String get diagnosisNotRecorded => '未记录诊断';

  @override
  String get clinicalEventDescription =>
      '一个临床事件用于按时间整理同一医疗问题。事件由医生创建和更新；患者可以查看，但不能编辑医生诊断。';

  @override
  String latestUpdate(String value) {
    return '最近更新：$value';
  }

  @override
  String get eventTimeline => '事件时间线';

  @override
  String get clinicalEventEditor => '临床事件编辑器';

  @override
  String get createClinicalEvent => '创建临床事件';

  @override
  String get updateClinicalEvent => '更新临床事件';

  @override
  String get newEvent => '新建事件';

  @override
  String get noClinicalEvent => '尚未创建临床事件。请先创建事件，再添加关联的照护内容。';

  @override
  String get clinicalEventTitle => '临床事件标题';

  @override
  String get chiefComplaint => '主诉';

  @override
  String get onsetDate => '起始日期';

  @override
  String get dateOptional => 'YYYY-MM-DD 或留空';

  @override
  String get status => '状态';

  @override
  String get symptomSummary => '症状或更新摘要';

  @override
  String get doctorDiagnosis => '医生诊断或初步诊断';

  @override
  String get eventDiagnosisNotice => '患者可以查看临床事件，但医生诊断字段由医生管理并保留审计记录。';

  @override
  String get newCareEpisode => '新的照护事件';

  @override
  String get chiefComplaintMissing => '未记录主诉';

  @override
  String get eventValidation => '请填写标题、主诉，并可选择填写 YYYY-MM-DD 格式的起始日期。';

  @override
  String timelineEntry(String type) {
    return '临床事件时间线记录：$type。';
  }

  @override
  String prescriptionStatus(String status) {
    return '处方：$status';
  }

  @override
  String get generatedRefillReminder => '自动生成的续药提醒';

  @override
  String get generatedMedicationReminder => '自动生成的用药提醒';

  @override
  String imagingStatusTitle(String status) {
    return '影像：$status';
  }

  @override
  String manualReviewStatus(String title) {
    return '$title 的人工审核状态。';
  }

  @override
  String get activityTimeline => '活动时间线';

  @override
  String get noActivity => '暂无活动';

  @override
  String get noMedicalRecords => '暂无医疗记录';

  @override
  String get doctorReviewAmendments => '医生审核与补充说明';

  @override
  String get noDoctorReviews => '暂无医生审核记录';

  @override
  String get clinicianVerifiedHistory => '医生已确认患者填写的病史。';

  @override
  String get auditOverlayNotice => '此审计记录与原始患者填写项目关联；原始内容保持不变。';

  @override
  String allergyLabel(String value) {
    return '过敏：$value';
  }

  @override
  String chronicDiseaseLabel(String value) {
    return '慢性疾病：$value';
  }

  @override
  String medicalRecordLabel(String value) {
    return '医疗记录：$value';
  }

  @override
  String get clinicianVerified => '医生已确认';

  @override
  String get patientCorrectionRequested => '已请求患者更正';

  @override
  String get noImagingAssets => '暂无影像资料';

  @override
  String uploaded(String date) {
    return '上传时间：$date';
  }

  @override
  String findingResult(String value) {
    return '检查结果：$value';
  }

  @override
  String measurementObservation(String value) {
    return '测量或观察：$value';
  }

  @override
  String get pendingManualReview => '等待医生人工审核';

  @override
  String get medications => '用药';

  @override
  String get noMedicationsRecorded => '未记录用药';

  @override
  String get noPrescriptions => '暂无处方';

  @override
  String get medicationRemindersTitle => '用药提醒';

  @override
  String get noMedicationReminderRecords => '暂无用药提醒';

  @override
  String get refillReminder => '续药提醒';

  @override
  String get medicationReminder => '用药提醒';

  @override
  String get medicationScheduleEditor => '用药计划编辑器';

  @override
  String get prescriptionOrderWorkflow => '处方医嘱流程';

  @override
  String get scheduleNotRecorded => '未记录用药计划';

  @override
  String get saveMedicationFirst => '请先保存用药记录，再开具处方。';

  @override
  String get prescriptionWorkflowDescription => '处方将使用所选临床事件中的药物信息，并生成患者用药计划。';

  @override
  String get selectEventMedication => '请先选择或创建临床事件，再保存与事件关联的用药。';

  @override
  String get medicationName => '药物名称';

  @override
  String get dosage => '剂量';

  @override
  String get schedule => '用药计划';

  @override
  String get prescriptionNote => '处方备注';

  @override
  String get addMedication => '添加用药';

  @override
  String get updateMedication => '更新用药';

  @override
  String get issuePrescription => '开具处方';

  @override
  String get medicationValidation => '必须填写药物名称、剂量和用药计划。';

  @override
  String get asset => '资料';

  @override
  String bytesVia(int bytes, String provider) {
    return '$bytes 字节，存储服务：$provider';
  }

  @override
  String medicationLines(int count) {
    return '$count 条用药明细';
  }

  @override
  String nextDue(String date) {
    return '下次：$date';
  }

  @override
  String get manualFindingDefault => '医生在影像审核后填写的人工检查结果。';

  @override
  String get manualMeasurementDefault => '人工测量备注；未进行自动解释。';

  @override
  String get imagingUpload => '影像上传';

  @override
  String get imageFilename => '影像文件名';

  @override
  String get imageMetadataHelper => 'PNG、JPEG 或 DICOM 元数据';

  @override
  String get contentType => '内容类型';

  @override
  String get sizeBytes => '字节数';

  @override
  String get prepareUpload => '准备上传';

  @override
  String get imagingWorkflow => '影像工作流程';

  @override
  String get manualFinding => '医生填写的检查结果';

  @override
  String get manualMeasurement => '人工测量或观察';

  @override
  String get prepareImaging => '准备影像';

  @override
  String get finalizeUpload => '完成上传';

  @override
  String get markReviewed => '标记为已审核';

  @override
  String get selectEventImaging => '请先选择或创建临床事件，再准备与事件关联的影像信息。';

  @override
  String get assessmentForm => '评估表';

  @override
  String get assessmentFixture => '评估案例';

  @override
  String get runAssessment => '运行评估';

  @override
  String get loadingAssessmentHistory => '正在加载评估历史';

  @override
  String get noAssessmentResults => '暂无评估结果';

  @override
  String get assessmentEmptyDescription => '运行一个评估案例以生成结果。';

  @override
  String get imageUploadValidation => '请输入影像文件名和大于零的字节数。';

  @override
  String get uploadedBytesValidation => '请输入已上传的字节数以完成上传。';

  @override
  String get manualFindingValidation => '请在审核前填写人工影像检查结果。';

  @override
  String get assessmentSelectionValidation => '请选择评估案例。';

  @override
  String get recoveryPlanEditor => '康复计划编辑器';

  @override
  String get selectEventRecovery => '请先选择或创建临床事件，再创建与事件关联的康复计划。';

  @override
  String get noEventRecoveryPlan => '此临床事件尚无康复计划，请先保存草稿。';

  @override
  String planStatusReview(
    String status,
    String review,
    int completed,
    int total,
  ) {
    return '计划状态：$status；审核：$review；已完成 $completed/$total 项任务。';
  }

  @override
  String get noActiveEventPlan => '此临床事件没有生效的康复计划。';

  @override
  String get oneActiveEventPlan => '此临床事件关联了一个生效的康复计划。';

  @override
  String get multipleActivePlans => '此事件存在多个生效计划；请批准替代计划以解决此状态。';

  @override
  String get planTitle => '计划标题';

  @override
  String get planTitleLimit => '必填，3–160 个字符。';

  @override
  String get planTitleRequired => '请输入计划标题。';

  @override
  String get planTitleTooShort => '计划标题至少需要 3 个字符。';

  @override
  String get planTitleTooLong => '计划标题不得超过 160 个字符。';

  @override
  String get planTitleInvalidServer => '请检查计划标题，并确保不超过 160 个字符。';

  @override
  String get recoveryTaskTitleLimit => '填写时需为 3–160 个字符。';

  @override
  String get recoveryTaskTitleTooShort => '此任务标题至少需要 3 个字符。';

  @override
  String get recoveryTaskTitleTooLong => '此任务标题不得超过 160 个字符。';

  @override
  String get instructions => '说明';

  @override
  String get medicationTask => '用药任务';

  @override
  String get exerciseTask => '运动任务';

  @override
  String get dietTask => '饮食任务';

  @override
  String get followUpTask => '随访任务';

  @override
  String reviewStatus(String status) {
    return '审核状态：$status。';
  }

  @override
  String get saveDraft => '保存草稿';

  @override
  String get submitReview => '提交审核';

  @override
  String get requestChanges => '请求修改';

  @override
  String get reviewComment => '审核意见';

  @override
  String get reviewCommentHelp => '请求修改时必填；批准时可选。';

  @override
  String get reviewCommentRequired => '请求修改前请输入审核意见。';

  @override
  String get approvePatient => '批准并提供给患者';

  @override
  String get completePlan => '完成计划';

  @override
  String get medicationTaskDetail => '已与患者确认用药提醒。';

  @override
  String get exerciseTaskDetail => '已与患者确认运动任务。';

  @override
  String get dietTaskDetail => '已与患者确认营养或补水任务。';

  @override
  String get followUpTaskDetail => '已与患者确认随访准备。';

  @override
  String get planFieldsValidation => '每个计划字段至少填写三个字符。';

  @override
  String savePlanBeforeAction(String action) {
    return '请先保存康复计划，再执行“$action”。';
  }

  @override
  String get submitPlanFirst => '请先保存并提交康复计划。';

  @override
  String get specialistConsultation => '专科会诊';

  @override
  String get specialistDescription => '提交异步会诊请求。此流程不包含预约、计费、视频或语音功能。';

  @override
  String get selectEventConsultation => '请先选择或创建临床事件，再申请与事件关联的专科审核。';

  @override
  String get questionSummary => '问题摘要';

  @override
  String get routine => '常规';

  @override
  String get soon => '尽快';

  @override
  String get requestSpecialistReview => '申请专科审核';

  @override
  String get loadingConsultations => '正在加载会诊请求';

  @override
  String get noSpecialistRequest => '暂无专科会诊请求';

  @override
  String get specialistEmptyDescription => '提交请求后可异步跟踪状态。';

  @override
  String priority(String value) {
    return '优先级：$value';
  }

  @override
  String get consultationValidation => '请输入专科和简洁、相关的问题摘要。';

  @override
  String consultationSubmitted(String specialty, String status) {
    return '$specialty 会诊请求：$status。';
  }

  @override
  String bornYear(int year) {
    return '出生年份：$year';
  }

  @override
  String get demographicsMissing => '未记录人口统计信息';

  @override
  String ageYears(int age) {
    return '$age 岁';
  }

  @override
  String get ageSexMissing => '未记录年龄或性别';

  @override
  String get recoveryPlanNone => '康复计划：无';

  @override
  String recoveryPlanStatus(String status, String review) {
    return '康复计划：$status／$review';
  }

  @override
  String get workflowReviewReady => '工作流程：可查看';

  @override
  String get workflowSetupNeeded => '工作流程：待设置';

  @override
  String clinicalEventNamed(String title) {
    return '临床事件：$title';
  }

  @override
  String get clinicalEventSetup => '临床事件：待设置';

  @override
  String eventResourceSummary(
    int prescriptions,
    int medications,
    int plans,
    int imaging,
    int notes,
  ) {
    return '$prescriptions 个处方、$medications 个用药计划项目、$plans 个康复计划、$imaging 份影像资料、$notes 条备注';
  }

  @override
  String historyOverview(
    String allergies,
    String conditions,
    String visits,
    String diagnoses,
  ) {
    return '过敏：$allergies｜慢性疾病：$conditions｜就诊：$visits｜诊断：$diagnoses';
  }

  @override
  String get noPrescriptionNote => '无处方备注';

  @override
  String get notScheduled => '未安排';

  @override
  String get emptySectionDescription => '此版块尚未记录信息。';

  @override
  String get uploadPrepared => '上传已准备';

  @override
  String uploadMetadata(String method) {
    return '$method 元数据';
  }

  @override
  String objectKey(String key) {
    return '对象键：$key';
  }

  @override
  String expires(String value) {
    return '有效期至：$value';
  }

  @override
  String get imagingUploadPrepared => '影像上传已准备';

  @override
  String get imagingStatus => '影像状态';

  @override
  String reviewed(String date) {
    return '审核时间：$date';
  }

  @override
  String risk(String value) {
    return '风险：$value';
  }

  @override
  String assessmentScore(String score) {
    return '评估分数：$score';
  }

  @override
  String modelVersion(String version) {
    return '模型：$version';
  }

  @override
  String get sessionEnded => '会话已结束，请重新登录。';

  @override
  String get patientRecordUnavailable => '无法查看此患者记录。';

  @override
  String get checkInformation => '请检查输入的信息后重试。';

  @override
  String get unableToReachRetry => '无法连接 Dr. AI，请检查网络后重试。';

  @override
  String get dateUnknown => '日期未知';

  @override
  String eventSaved(String title, String status) {
    return '$title 已保存为$status。';
  }

  @override
  String contentAsset(String type) {
    return '$type 资料';
  }

  @override
  String get assessmentLimitationSynthetic => '此结果来自评估案例，未进行临床推理。';

  @override
  String get assessmentLimitationValidation => '未经过诊断、治疗或预后用途验证。';

  @override
  String get assessmentNextStep => '请与合格的临床医生共同查看此评估案例。';

  @override
  String get researchNotDiagnosis => '研究评估，不用于诊断。';

  @override
  String get low => '低';

  @override
  String get moderate => '中等';

  @override
  String get high => '高';

  @override
  String get partial => '部分完整';

  @override
  String get insufficient => '信息不足';

  @override
  String get sms => '短信';

  @override
  String get specificHomeAddress => '详细家庭住址';

  @override
  String get unableToRequestCode => '无法获取验证码，请重试。';

  @override
  String get acceptTermsValidation => '请接受条款和隐私政策。';

  @override
  String localDevelopmentCodeFilled(String message) {
    return '$message 本地开发验证码已自动填入。';
  }

  @override
  String clinicianNamed(String name) {
    return '临床医生：$name';
  }

  @override
  String medicationLinesLinked(int count, String event) {
    return '$count 条用药记录已关联至$event。';
  }

  @override
  String get createdFromMedicationSchedule => '根据用药计划创建。';

  @override
  String get setupNeeded => '待设置';

  @override
  String get secureInformationTitle => '您的信息受到安全保护';

  @override
  String get secureInformationBody => '我们会保护您的数据，并遵守医疗健康隐私法规。';

  @override
  String get unableToChangePassword => '无法修改密码，请重试。';

  @override
  String get signedOut => '您已退出登录。';

  @override
  String get signedOutLocally => '您已在本设备退出登录，但暂时无法连接服务器。';

  @override
  String get incorrectCredentials => '邮箱或密码不正确。';

  @override
  String get registrationRoleUnavailable => '当前所选角色暂不支持注册。';

  @override
  String get accountAlreadyExists => '此联系方式已关联现有账户。';

  @override
  String get registrationFieldsInvalid => '请检查手机号、邮箱、密码、角色和验证码。';

  @override
  String get unableToCreateAccount => '无法创建账户，请检查网络后重试。';

  @override
  String prescriptionCount(int count) {
    return '$count 个处方';
  }

  @override
  String generatedReminderCount(int count) {
    return '$count 条自动提醒';
  }

  @override
  String imagingAssetCount(int count) {
    return '$count 份影像资料';
  }

  @override
  String noteCount(int count) {
    return '$count 条备注';
  }

  @override
  String get patientIntakeSummary => '患者初诊信息摘要';

  @override
  String get imagingUploadFinalized => '影像上传已完成。';

  @override
  String get imagingReviewUpdated => '影像审核状态已更新。';

  @override
  String get doctorContactsDescription => '与已连接患者进行私密沟通，并使用 Dr. AI 服务。';

  @override
  String get systemReadOnlyDescription => '提醒与通知 · 只读';

  @override
  String get aiCareCompanion => 'AI 健康助手';

  @override
  String get myPatients => '我的患者';

  @override
  String get connectedPatientPrivateChat => '已连接患者 · 私聊';

  @override
  String get connectPatientToChat => '请先在患者管理中连接患者，再开始私密对话。';

  @override
  String get noGroupChats => '暂无群聊';

  @override
  String get groupChatsUnavailable => '群聊功能暂未开放。';

  @override
  String get contactsLoadFailed => '无法加载联系人。';

  @override
  String get systemNotifications => '系统通知';

  @override
  String get systemNotificationsSubtitle => '提醒和重要账户更新将显示在这里。';

  @override
  String get aiAssistant => 'Dr. AI 助手';

  @override
  String get aiAssistantSubtitle => 'AI 健康助手界面已准备好，将在下一阶段开放。';

  @override
  String get noSystemNotifications => '暂无系统通知';

  @override
  String get systemReadOnlyNotice => '此频道仅用于接收通知，无法向系统发送消息。';

  @override
  String get aiAvailablePhase3 => 'AI 对话将在第三阶段开放';

  @override
  String get aiPlaceholderNotice =>
      '在通过评估的 DeepSeek 发布版本启用前，生成式回复保持不可用；确定性安全控制和结构化回退仍然有效。';

  @override
  String get aiChatSubtitle => '提供实用健康信息，并清楚标明来源或一般 AI 信息模式。';

  @override
  String get aiChatSafetyNotice =>
      'Dr. AI 是 AI 助手，可能会出错。重要信息请通过权威来源或医生核实。它不能确认诊断、替代急救或更改药物。';

  @override
  String get aiChatWelcome => '今天想一起理清什么问题？';

  @override
  String get aiChatInputHint => '可询问症状、检查、药物或照护问题';

  @override
  String get aiChatSendFailed => '无法完成安全对话请求，请重试。';

  @override
  String get aiChatHistory => '对话记录';

  @override
  String get aiNewChat => '新对话';

  @override
  String get aiPreviousChats => '之前的对话';

  @override
  String get aiNoPreviousChats => '发出第一个问题后，你的健康对话会显示在这里。';

  @override
  String get aiHistoryRetentionNotice => '每个对话至少保留 60 天，且仅在你的账户中可见。';

  @override
  String get aiArchiveChat => '归档对话';

  @override
  String get aiReopenChat => '重新打开对话';

  @override
  String get aiDeleteChat => '从我的记录中删除';

  @override
  String get aiArchivedChat => '已归档';

  @override
  String get aiChatLifecycleFailed => '无法更新此对话，请重试。';

  @override
  String get retry => '重试';

  @override
  String get aiFollowUpQuestion => '补充一个信息会更有帮助';

  @override
  String get aiReviewMeasurementGuidance => '正确测量';

  @override
  String get aiTrackMeasurements => '记录读数';

  @override
  String get aiPrepareDoctorQuestions => '整理问医生的问题';

  @override
  String get aiPrepareSymptomSummary => '整理我的症状';

  @override
  String get aiPrepareSymptomSummaryPrompt => '请帮我整理症状、出现时间、变化情况，以及要问医生的重点。';

  @override
  String get aiMeasurementGuidancePrompt => '怎样才能正确测量？';

  @override
  String get aiTrackMeasurementsPrompt => '请帮我做一个简单的记录计划。';

  @override
  String get aiSuggestionEducation => '记录血压有什么作用？';

  @override
  String get aiSuggestionSymptoms => '我最近头晕，可能有哪些原因？什么情况需要及时就医？';

  @override
  String get aiSuggestionMedication => '我应该向医生询问哪些处方药问题？';

  @override
  String get aiSuggestionDoctor => '帮我整理下次看医生时要问的问题。';

  @override
  String get aiSources => '经审核来源';

  @override
  String get aiApprovedEvidenceBanner => '有来源支持的回答——基于 Dr. AI 已审核资料。';

  @override
  String get aiGeneralKnowledgeBanner => '一般 AI 生成信息——未找到支持此回答的 Dr. AI 来源。';

  @override
  String get aiFixedSafetyBanner => '由服务器控制的安全回复。';

  @override
  String get aiOpenOfficialSource => '打开官方来源';

  @override
  String get aiImportantUncertainty => '需要注意的不确定性';

  @override
  String get aiContextUsed => '已结合你的记录进行说明';

  @override
  String get aiContextProfile => '个人资料';

  @override
  String get aiContextMeasurements => '健康测量';

  @override
  String get aiContextConditions => '已记录病情';

  @override
  String get aiContextMedications => '用药信息';

  @override
  String get aiContextClinicalEvents => '当前就诊事件';

  @override
  String get aiContextRecoveryPlan => '康复计划';

  @override
  String get aiContextFromProfile => '你的个人资料';

  @override
  String get aiContextPatientReported => '你报告的病史';

  @override
  String get aiContextDoctorRecord => '医生记录';

  @override
  String get aiContextCurrentPrescription => '当前处方';

  @override
  String get aiContextMedicationSchedule => '当前用药安排';

  @override
  String get aiContextCurrentRecoveryPlan => '当前康复计划';

  @override
  String get aiContactDoctor => '联系我的医生';

  @override
  String get aiCall120Now => '立即拨打120';

  @override
  String get privateCareConversation => '私密照护对话';

  @override
  String get loadingConversation => '正在加载对话…';

  @override
  String get conversationLoadFailed => '无法加载此对话。';

  @override
  String get messageSendFailed => '消息发送失败，请重试。';

  @override
  String get writeMessage => '输入消息';

  @override
  String get sendMessage => '发送消息';

  @override
  String get noPrivateMessages => '暂无消息。您可以就持续照护发起私密对话。';

  @override
  String get patientFallbackName => '患者';

  @override
  String get doctorFallbackName => '医生';

  @override
  String get resources => '医疗资源';

  @override
  String get medicalResources => '医疗资源';

  @override
  String get medicalResourcesSubtitle => '检索经审核的临床资料，核验来源，并保存以便后续查阅。';

  @override
  String get resourceCatalogPreviewTitle => '权威来源目录';

  @override
  String get resourceCatalogPreviewBody =>
      '247 项世卫组织实况报道覆盖 240 个官方中文页面和 244 个官方英文页面。原文已依据许可请求 202609681 存储，审核完成前不进入医生或患者检索版本。';

  @override
  String get resourceSearchHint => '用中文或英文搜索医疗资源';

  @override
  String get resourceSearchTab => '搜索';

  @override
  String get savedResourcesTab => '已保存';

  @override
  String get recentUpdatesTab => '近期更新';

  @override
  String get sourceRegistryTab => '来源登记';

  @override
  String get resourceFilters => '筛选条件';

  @override
  String get showFilters => '显示筛选';

  @override
  String get hideFilters => '收起筛选';

  @override
  String get clearFilters => '清除筛选';

  @override
  String get allOptions => '全部';

  @override
  String get topicFilter => '主题';

  @override
  String get documentTypeFilter => '文档类型';

  @override
  String get organizationFilter => '机构';

  @override
  String get jurisdictionFilter => '适用地区';

  @override
  String get originalLanguageFilter => '原始语言';

  @override
  String get intendedAudienceFilter => '适用对象';

  @override
  String get publicationReviewDateFilter => '发布／目录日期';

  @override
  String get versionStatusFilter => '现行／已被取代';

  @override
  String get topicRespiratoryCare => '呼吸系统照护';

  @override
  String get topicCardiovascularCare => '心血管照护';

  @override
  String get topicDiabetesCare => '糖尿病照护';

  @override
  String get topicRehabilitation => '康复';

  @override
  String get documentClinicalGuide => '临床指南';

  @override
  String get documentCarePathway => '照护路径';

  @override
  String get documentSafetyBulletin => '安全通报';

  @override
  String get documentPatientEducation => '患者教育';

  @override
  String get organizationPrimaryCareCouncil => '基层照护审核委员会';

  @override
  String get organizationMedicinesSafetyCenter => '药物安全审核中心';

  @override
  String get organizationRehabilitationCollaborative => '连续照护与康复协作组';

  @override
  String get jurisdictionMainlandChina => '中国大陆';

  @override
  String get jurisdictionInternational => '国际';

  @override
  String get jurisdictionChina => '中国';

  @override
  String get audienceDoctors => '医生';

  @override
  String get audienceDoctorsAndPatients => '医生与患者';

  @override
  String get dateAny => '不限日期';

  @override
  String get datePast12Months => '近 12 个月';

  @override
  String get datePast24Months => '近 24 个月';

  @override
  String get statusCurrent => '现行';

  @override
  String get statusSuperseded => '已被取代';

  @override
  String get searchSuggestions => '建议搜索';

  @override
  String get resourceSuggestionOne => '高血压随访';

  @override
  String get resourceSuggestionTwo => '呼吸道感染用药安全';

  @override
  String get serviceCategoryLabel => '服务类别';

  @override
  String get chooseSyntheticImage => '选择合成影像';

  @override
  String get movePhaseEarlier => '将阶段前移';

  @override
  String get movePhaseLater => '将阶段后移';

  @override
  String get removePhase => '移除阶段';

  @override
  String get codeLaboratory => '实验室检查';

  @override
  String get codeProcedure => '医疗操作';

  @override
  String get codeSurgery => '手术';

  @override
  String get codeImplantDevice => '植入物或医疗器械';

  @override
  String get codeAnesthesia => '麻醉';

  @override
  String get codeTreatment => '治疗';

  @override
  String get codeRehabilitation => '康复治疗';

  @override
  String get codeOtherService => '其他服务';

  @override
  String get codeOrdered => '已开单';

  @override
  String get codeRequested => '已申请';

  @override
  String get codeScheduled => '已安排';

  @override
  String get codeInProgress => '进行中';

  @override
  String get codePerformed => '已实施';

  @override
  String get codeCancelled => '已取消';

  @override
  String get codeNotCompleted => '未完成';

  @override
  String get codeInPerson => '线下会诊';

  @override
  String get codeVideo => '视频会诊';

  @override
  String get codeTelephone => '电话会诊';

  @override
  String get codeRecordReview => '病历审阅';

  @override
  String get codeEnteredInError => '误录入';

  @override
  String get codeDemoVisit => '演示就诊';

  @override
  String get codeDemoFollowUp => '演示复诊';

  @override
  String get codeSyntheticHistory => '合成病史';

  @override
  String get equipmentVentilators => '呼吸机';

  @override
  String get statusPendingUpload => '等待上传';

  @override
  String get statusUploaded => '已上传';

  @override
  String get statusFailed => '失败';

  @override
  String get statusExpired => '已过期';

  @override
  String get statusNotReady => '尚不可审核';

  @override
  String get statusReviewed => '已审核';

  @override
  String get statusRejected => '已驳回';

  @override
  String get statusPlanned => '已计划';

  @override
  String get resourceSuggestionThree => '糖尿病生病期间健康教育';

  @override
  String resourceResultCount(int count) {
    return '$count 项资源';
  }

  @override
  String get currentAndReviewed => '现行且已审核';

  @override
  String get supersededDoNotRely => '已被取代——请勿作为现行指导依据';

  @override
  String get rightsLimitedLinkOnly => '权利受限——仅提供链接／不存储全文';

  @override
  String get doctorOnlyResource => '仅限医生';

  @override
  String get patientEducationApproved => '已批准用于患者教育';

  @override
  String get patientUseNotApproved => '未批准用于患者';

  @override
  String get publisherLabel => '发布机构';

  @override
  String get sourceTypeLabel => '来源类型';

  @override
  String get publishedLabel => '发布日期';

  @override
  String get lastMedicalReviewLabel => '最近医学审核';

  @override
  String get openSourceDetails => '查看来源详情';

  @override
  String get saveResource => '保存资源';

  @override
  String get removeSavedResource => '取消保存';

  @override
  String get resourceSavedConfirmation => '资源已保存。';

  @override
  String get resourceRemovedConfirmation => '已取消保存资源。';

  @override
  String get officialLocator => '原始来源定位';

  @override
  String get provenance => '来源与流转记录';

  @override
  String get provenanceBody =>
      '于 2026 年 7 月 14 日从世界卫生组织官方中英文实况报道索引配对采集。仅存储标题和定位信息，正文仍保留在世卫组织网站。';

  @override
  String get versionHistory => '版本历史';

  @override
  String get versionCurrentEntry => '当前已审核版本 · 在本目录中有效';

  @override
  String get versionSupersededEntry => '历史版本 · 仅为追溯而保留';

  @override
  String get relevantPassages => '相关段落';

  @override
  String get relatedSources => '相关来源';

  @override
  String get stableInternalReference => '稳定内部引用';

  @override
  String get copyCitation => '复制引用';

  @override
  String get citationCopied => '引用已复制。';

  @override
  String get copyOfficialLocator => '复制原始来源定位';

  @override
  String get officialLocatorCopied => '原始来源定位已复制。';

  @override
  String resourceCitation(
    String title,
    String publisher,
    String year,
    String locator,
  ) {
    return '$title。$publisher。$year。$locator';
  }

  @override
  String get noResourceResultsTitle => '未找到匹配资源';

  @override
  String get noResourceResultsBody => '请尝试其他关键词，或清除一个或多个筛选条件。';

  @override
  String get noSavedResourcesTitle => '暂无已保存资源';

  @override
  String get noSavedResourcesBody => '可在“搜索”中保存来源，之后在此快速查阅。';

  @override
  String get noRecentUpdatesTitle => '暂无近期更新';

  @override
  String get noRecentUpdatesBody => '经审核的来源更新会在可用时显示在这里。';

  @override
  String get sourceRegistrySubtitle => '当前本地目录中收录的机构。';

  @override
  String get viewOrganizationSources => '查看来源';

  @override
  String reviewedSourceCount(int count) {
    return '$count 个目录来源';
  }

  @override
  String get loadingMedicalResources => '正在加载医疗资源';

  @override
  String get resourceOfflineTitle => '离线状态下无法使用医疗资源';

  @override
  String get resourceOfflineBody => '请重新联网以核实现行来源状态。已保存的引用仍会列出，但不会缓存全文。';

  @override
  String get resourceServiceFailureTitle => '无法加载医疗资源';

  @override
  String get resourceServiceFailureBody => '来源服务未响应。未发送任何患者信息或查询内容。';

  @override
  String get resourcePartialIndexTitle => '部分已审核来源暂时不可用';

  @override
  String get resourcePartialIndexBody => '在恢复当前来源索引期间，搜索结果可能不完整。';

  @override
  String get resourceRetry => '重试';

  @override
  String resourceUpdatedLabel(String date) {
    return '目录核验于 $date';
  }

  @override
  String get resourceTitleRespiratory => '单纯呼吸道症状的安全抗菌药物决策';

  @override
  String get resourcePassageRespiratory =>
      '考虑抗菌治疗前，应核查症状持续时间、严重程度、危险信号及可能的病毒感染特征。';

  @override
  String get resourcePassageRespiratoryDetail =>
      '如暂不需要立即使用抗菌药物，应记录临床依据，并向患者说明明确的复诊阈值。';

  @override
  String get resourceTitleHypertension => '稳定期高血压基层随访路径';

  @override
  String get resourcePassageHypertension =>
      '应采用一致的血压测量方法，复核依从性和不良反应，并共同确定可行的随访间隔。';

  @override
  String get resourcePassageHypertensionDetail =>
      '当血压严重升高并伴有警示症状或急性器官损伤证据时，应及时升级处置。';

  @override
  String get resourceTitleDiabetes => '2 型糖尿病成人生病期间的安全教育';

  @override
  String get resourcePassageDiabetes => '说明补充水分、监测、危险信号及何时联系医生，不应擅自更改已开具的药物。';

  @override
  String get resourcePassageDiabetesDetail => '面向患者的表述应与现行处方及已连接医生的指导进行核对。';

  @override
  String get resourceTitleStroke => '卒中康复出院后的照护衔接清单';

  @override
  String get resourcePassageStroke => '此早期清单涵盖药物核对、行动支持、照护者沟通及随访责任。';

  @override
  String get resourcePassageStrokeDetail => '该版本已由更新的衔接标准取代，仅应保留用于理解既往记录。';

  @override
  String get resourceOfficialMetadataStatus => '官方目录元数据';

  @override
  String get rightsReviewPending => '权利审核待完成——仅提供官方链接';

  @override
  String get resourceCatalogMetadataNote =>
      '请打开任一世界卫生组织官方语言页面阅读原文。Dr. AI 仅存储配对后的标题和定位信息；目前不得用于摘录、向量化或 AI 检索。';

  @override
  String get catalogVerifiedLabel => '目录核验日期';

  @override
  String get documentFactSheet => '实况报道';

  @override
  String get documentClinicalGuideline => '临床诊疗指南';

  @override
  String get documentClinicalProtocol => '诊疗方案与技术规范';

  @override
  String get documentPracticeGuideline => '实践指南';

  @override
  String get documentGuidance => '工作指导';

  @override
  String get organizationWorldHealthOrganization => '世界卫生组织';

  @override
  String get topicInfectiousDisease => '传染病';

  @override
  String get topicChronicDisease => '慢性病';

  @override
  String get topicMaternalChildHealth => '妇幼健康';

  @override
  String get topicMentalHealth => '心理健康和精神卫生';

  @override
  String get topicInjuryEmergency => '伤害与急救';

  @override
  String get topicEnvironmentalHealth => '环境健康';

  @override
  String get topicNutritionLifestyle => '营养与生活方式';

  @override
  String get topicHealthSystems => '卫生系统与安全';

  @override
  String get showMoreResources => '再显示 20 项资源';

  @override
  String get catalogUseStatus => '目录与检索状态';

  @override
  String get bilingualChineseEnglish => '双语：中文与英文';

  @override
  String get languageChinese => '中文';

  @override
  String get languageEnglish => '英文';

  @override
  String get organizationNationalHealthCommission => '中华人民共和国国家卫生健康委员会';

  @override
  String get chineseOfficialSource => '官方中文页面';

  @override
  String get englishOfficialSource => '官方英文页面';

  @override
  String get copyEnglishOfficialLocator => '复制英文官方定位';

  @override
  String get englishOfficialLocatorCopied => '英文官方定位已复制。';

  @override
  String get close => '关闭';

  @override
  String get readOriginalText => '阅读原文';

  @override
  String get openOfficialSource => '打开官方来源';

  @override
  String get originalEnglish => '英文原文';

  @override
  String get backToResources => '返回资源库';

  @override
  String get resourceReaderTitle => '原始文档';

  @override
  String get resourceReaderReviewPending => '医学审核待完成';

  @override
  String get resourceReaderReviewApproved => '医学审核已通过';

  @override
  String get resourceReaderNotice =>
      '此处展示发布方英文原文，仅供医生参考。该境外资料当前不用于 AI 检索或面向患者的回答。';

  @override
  String get resourceReaderUnavailableTitle => '暂无可阅读的原文';

  @override
  String get resourceReaderUnavailableBody => '该来源当前没有已获准展示的存储原文。请查看发布方官方来源。';

  @override
  String get resourceReaderLoadFailedTitle => '无法加载原始文档';

  @override
  String get resourceReaderLoadFailedBody => '请检查网络后重试。未发送任何患者信息。';

  @override
  String get resourceReaderRetry => '重试';

  @override
  String get publicationDateLabel => '发布日期';

  @override
  String get captureDateLabel => '采集日期';

  @override
  String get rightsAndAttribution => '权利与署名';

  @override
  String get copyDocumentCitation => '复制文档引用';

  @override
  String get reviewedChineseTranslation => '已审核中文译文';

  @override
  String get unofficialAiTranslationNotice =>
      '这是经医学与中文审核的非官方 AI 生成中文译文。权威核验请以发布方英文原文为准。译文审核与检索准入仍为独立门槛。';

  @override
  String get financialDetails => '费用信息';

  @override
  String get financialDetailsDescription => '费用信息应归属于产生该费用的服务或产品。';

  @override
  String get billableClinicalItem => '此临床项目需要计费';

  @override
  String get billableClinicalItemDescription => '如果此记录仅用于临床文档，请勿启用。';

  @override
  String get costStatus => '费用状态';

  @override
  String get costPending => '费用待补充';

  @override
  String get costEstimate => '预估';

  @override
  String get costFinal => '最终';

  @override
  String get currency => '币种';

  @override
  String get pendingCostSubmissionBlocked =>
      '现在可以先保存临床记录；完整记录费用分配前，不能选择此项目提交支付申请。';

  @override
  String get totalCostCny => '总费用（人民币）';

  @override
  String get requestedFromPayerCny => '向支付方申请（人民币）';

  @override
  String get expectedPatientResponsibilityCny => '预计患者承担（人民币）';

  @override
  String get financialAllocationNotice => '“向支付方申请”不代表付款保证；“预计患者承担”也不是最终审定责任。';

  @override
  String get financialAllocationValidation =>
      '请输入非负金额；向支付方申请金额与预计患者承担金额之和必须等于总费用。';

  @override
  String get imagingArtifactNotBillable =>
      '上传的影像和报告属于临床证据，不应形成第二笔费用。只有独立的影像检查项目记录才能承载检查费用。';

  @override
  String get editConsultationCost => '补充或编辑费用';

  @override
  String get saveConsultationCost => '保存会诊费用';

  @override
  String get financialStatus => '费用状态';

  @override
  String get noCostRecorded => '尚未记录费用';

  @override
  String estimatedCost(String amount) {
    return '预估 ¥$amount';
  }

  @override
  String finalCost(String amount) {
    return '最终 ¥$amount';
  }

  @override
  String get alreadySubmitted => '已提交支付申请';

  @override
  String get addCost => '添加费用';

  @override
  String get completeCost => '补全费用';

  @override
  String get editCost => '编辑费用';

  @override
  String get saveCost => '保存费用';

  @override
  String get imagingProcedure => '影像检查项目';

  @override
  String get imagingProcedures => '影像检查项目';

  @override
  String get imagingProcedureDescription =>
      '请先创建已开立、已预约或已完成的检查服务。预约信息、影像证据和费用记录保持分离。';

  @override
  String get clinicalDetails => '临床信息';

  @override
  String get procedureName => '检查项目名称';

  @override
  String get modality => '影像方式或检查类型';

  @override
  String get bodyRegion => '检查部位';

  @override
  String get clinicalIndication => '临床指征或摘要（可选）';

  @override
  String get schedulingServiceDetails => '预约与服务信息';

  @override
  String get scheduledDateTime => '预约日期与时间';

  @override
  String get performedDateTime => '实际检查日期与时间';

  @override
  String get createImagingProcedure => '创建影像检查项目';

  @override
  String get updateImagingProcedure => '更新影像检查项目';

  @override
  String get editClinicalService => '编辑详情';

  @override
  String imagingProcedureSaved(String name) {
    return '已保存$name。';
  }

  @override
  String get noImagingProcedures => '此临床事件下尚未创建影像检查项目。';

  @override
  String get imagingEvidence => '影像证据与结果';

  @override
  String get selectImagingProcedure => '影像检查项目';

  @override
  String get attachEvidence => '关联证据';

  @override
  String evidenceFileCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count 个关联文件',
      one: '1 个关联文件',
      zero: '无关联文件',
    );
    return '$_temp0';
  }

  @override
  String get imagingProcedureValidation =>
      '请输入检查项目名称、影像方式和检查部位。已预约项目需要预约时间；已执行或已完成项目需要实际检查时间。';

  @override
  String get accountRequestsTitle => '支持、反馈与账户申请';

  @override
  String get accountRequestsDescription =>
      '提交并跟踪已持久化的申请。回执、状态变更、重试和撤回都会在此保留可追溯记录。';

  @override
  String get requestTypeLabel => '申请类型';

  @override
  String get supportRequestType => '支持请求';

  @override
  String get feedbackRequestType => '产品反馈';

  @override
  String get deletionRequestType => '账户删除审核';

  @override
  String get requestSubjectLabel => '主题';

  @override
  String get requestSubjectValidation => '请至少输入 3 个字符。';

  @override
  String get requestMessageLabel => '您需要什么帮助？';

  @override
  String get requestMessageValidation => '请至少输入 8 个字符。';

  @override
  String get requestPrivacyHelper => '请勿填写患者身份、联系方式、临床文本、影像内容或支付方保密备注。';

  @override
  String get deletionRetentionBoundary =>
      '此操作提交删除审核申请，不会立即删除账户，也不会立即删除依法或因安全、财务、临床及审计要求需保留的记录。身份核验和适用的保留期限仍然有效。';

  @override
  String get standardSupportRetentionBoundary => '此支持或反馈申请将按照标准支持记录政策保留。';

  @override
  String get unknownRetentionBoundary =>
      '适用的保留边界暂不可用。在据此判断删除或保留情况前，请联系获授权的支持人员。';

  @override
  String get deletionRequestOnlyEffect => '这只是删除审核申请；不会立即删除账户或需保留的记录。';

  @override
  String get notDeletionRequestEffect => '此申请不要求删除账户或记录。';

  @override
  String get unknownDeletionEffect => '删除效果暂不可用；请勿假定任何内容会被立即删除。';

  @override
  String get deletionBoundaryConfirmation => '我理解这是一项审核申请，适用记录可能仍需依法或依规保留。';

  @override
  String get submitRequest => '提交申请';

  @override
  String get submittingRequest => '正在提交';

  @override
  String get retryRequest => '安全重试';

  @override
  String requestSubmitted(String reference) {
    return '申请 $reference 已提交并持久化。';
  }

  @override
  String requestReplayConfirmed(String reference) {
    return '申请 $reference 已被接收，未创建重复申请。';
  }

  @override
  String get requestConflict => '此次重试与另一份已保存申请冲突。您的文本已保留；请查看更新后的记录再重试。';

  @override
  String get requestNetworkFailure => '暂时无法连接 Dr. AI。您的文本已保留；重试不会创建重复申请。';

  @override
  String get requestSafeContentFailure => '请移除联系方式、患者信息、临床文本或保密备注后重试。';

  @override
  String get requestAuthorizationFailure => '此账户无权使用该申请。';

  @override
  String get requestGenericFailure => '暂时无法完成申请。您的文本已保留，可安全重试。';

  @override
  String get requestHistoryTitle => '申请记录';

  @override
  String get loadingAccountRequests => '正在加载账户申请记录';

  @override
  String get loadAccountRequestsFailed => '申请记录暂时不可用。';

  @override
  String get noAccountRequests => '此账户尚未提交支持、反馈或删除申请。';

  @override
  String get startAccountRequest => '开始申请';

  @override
  String requestReceipt(String reference) {
    return '回执编号：$reference';
  }

  @override
  String get requestTimelineTitle => '状态时间线';

  @override
  String get requestTimelineUnavailable => '此较早申请暂无详细状态变更记录。';

  @override
  String get requestStatusQueued => '已排队';

  @override
  String get requestStatusReviewing => '审核中';

  @override
  String get requestStatusResolved => '已处理';

  @override
  String get requestStatusFailed => '需要处理';

  @override
  String get requestStatusCancelled => '已撤回';

  @override
  String get requestStatusUnavailable => '状态不可用';

  @override
  String get requestNextQueued => '下一步：由获授权的工作人员审核此申请。';

  @override
  String get requestNextReviewing => '下一步：等待当前审核完成；申请会继续显示在此处。';

  @override
  String get requestNextResolved => '此申请已结束，请在时间线查看记录结果。';

  @override
  String get requestNextFailed => '申请未能继续处理。请查看时间线；如仍无可执行操作，请提交新申请。';

  @override
  String get requestNextCancelled => '此申请已撤回；回执和必要审计记录仍会保留。';

  @override
  String get requestNextUnavailable => '当前没有可执行的下一步。';

  @override
  String get timelineRequestSubmitted => '申请已提交';

  @override
  String get timelineRequestWithdrawn => '申请已撤回';

  @override
  String get timelineReviewStarted => '已开始审核';

  @override
  String get timelineRequestResolved => '审核已完成';

  @override
  String get timelineActorYou => '您';

  @override
  String get timelineActorAuthorizedOperator => '获授权工作人员';

  @override
  String get timelineActorSystem => '受治理系统';

  @override
  String get withdrawRequest => '撤回申请';

  @override
  String get withdrawRequestQuestion => '撤回此申请？';

  @override
  String get withdrawRequestDescription => '在合同允许的情况下，撤回会停止后续处理；回执和必要审计记录仍会保留。';

  @override
  String requestWithdrawn(String reference) {
    return '申请 $reference 已撤回。';
  }

  @override
  String get withdrawalReplayConfirmed => '此撤回操作已被接收，未创建重复状态变更。';

  @override
  String get withdrawalConflict => '申请在撤回前已发生变化。记录已刷新，请查看当前状态。';

  @override
  String get signInForAccountRequests => '请登录并打开“账户”，提交或跟踪支持、反馈及删除审核申请。';

  @override
  String get openAccountForRequests => '请打开“账户”，提交或跟踪支持、反馈及删除审核申请。';

  @override
  String get ceiTitle => '临床事件智能';

  @override
  String get ceiPatientTitle => '您的诊疗与费用智能';

  @override
  String get ceiDoctorTitle => '临床事件智能审核';

  @override
  String get ceiPayerTitle => '已授权申请智能';

  @override
  String get ceiLoading => '正在加载已冻结的临床事件智能';

  @override
  String get ceiUnavailableTitle => '智能信息暂不可用';

  @override
  String get ceiUnavailableValue => '暂无';

  @override
  String get ceiRequestedItem => '申请项目';

  @override
  String get ceiSourceWithheld => '来源未提供';

  @override
  String get ceiUnitItem => '项';

  @override
  String get ceiUnavailableBody => '该申请仍可继续用于常规临床记录、待补费用、澄清及人工审核。';

  @override
  String get ceiEmptyTitle => '尚无经验证的智能产物';

  @override
  String get ceiEmptyPatientBody => '在负责的诊疗团队审核下一步期间，您的申请和诊疗记录仍可使用。';

  @override
  String get ceiEmptyDoctorBody => '受治理版本可用时可生成有界产物。临床和待补费用工作无需等待。';

  @override
  String get ceiEmptyPayerBody => '请继续人工审核或请求澄清。获准的决定不以 AI 产物为前提。';

  @override
  String get ceiRefresh => '刷新';

  @override
  String get ceiGenerate => '生成智能产物';

  @override
  String get ceiGenerating => '正在生成智能产物';

  @override
  String get ceiArtifact => '不可变产物';

  @override
  String get ceiSnapshot => '已冻结快照';

  @override
  String get ceiHumanReview => '人工审核';

  @override
  String get ceiLocation => '确定性地点';

  @override
  String get ceiLocationSource => '来自临床事件、提供方机构及设施记录，不来自 IP 或模型推断。';

  @override
  String get ceiHumanOnlyNotice => 'AI 支持分数仅供人员参考，绝不会自动批准、拒绝、减少、延误、移除或开具诊疗。';

  @override
  String get ceiRequestedItems => '申请中的可计费项目';

  @override
  String get ceiRequestedItemsDescription => '每条申请项目仅出现一次，并与预测路径项目保持分离。';

  @override
  String get ceiRequested => '申请值';

  @override
  String get ceiEstimated => '估算范围';

  @override
  String get ceiUsefulness => '用途说明';

  @override
  String get ceiConfidence => '置信度';

  @override
  String get ceiAiSupportScore => 'AI 支持分数';

  @override
  String get ceiScoreVersion => '聚合规则';

  @override
  String get ceiClinicalFit => '临床匹配度';

  @override
  String get ceiEvidenceSupport => '证据支持度';

  @override
  String get ceiTimingSequence => '时机／顺序';

  @override
  String get ceiQuantityIntensity => '数量／强度';

  @override
  String get ceiDocumentationCompleteness => '文档完整度';

  @override
  String get ceiCostAlignment => '费用匹配度';

  @override
  String get ceiTier => '溯源层级';

  @override
  String get ceiTier5Title => '仅模型探索性估算';

  @override
  String get ceiTier5Body => '没有可准入的价格参考。该范围有意保持较宽，不能成为权威价格，费用匹配权重会显著降低或归零。';

  @override
  String get ceiSources => '已准入来源';

  @override
  String get ceiNoAdmittedPriceSource => '无已准入价格来源';

  @override
  String get ceiSupportingFacts => '支持事实';

  @override
  String get ceiContradictingFacts => '矛盾事实';

  @override
  String get ceiMissingInformation => '缺失信息';

  @override
  String get ceiAlternatives => '替代方案';

  @override
  String get ceiPredictedPathways => '可能的预测路径';

  @override
  String get ceiPredictedBoundary => '预测路径项目并非医生申请项目，也不会改变原申请。';

  @override
  String get ceiTypicalPathway => '典型／一线';

  @override
  String get ceiAlternativePathway => '合理替代';

  @override
  String get ceiEscalatedPathway => '升级路径';

  @override
  String get ceiMissingDocumentation => '缺失文档助手';

  @override
  String get ceiMissingDocumentationEmpty => '此冻结产物未发现缺失文档。';

  @override
  String get ceiCounterfactuals => '反事实比较';

  @override
  String get ceiCounterfactualBoundary => '可能的替代方案用于辅助讨论，不会替代医生申请项目。';

  @override
  String get ceiCritic => '主模型与审查模型';

  @override
  String get ceiAgreement => '一致';

  @override
  String get ceiPartialDisagreement => '部分分歧';

  @override
  String get ceiMaterialDisagreement => '重大分歧';

  @override
  String get ceiCriticUnavailable => '审查模型不可用';

  @override
  String get ceiCriticUnavailableBody => '经验证的主产物仍保持可见，但不表示双方一致。';

  @override
  String get ceiLineage => '不可变结果沿袭';

  @override
  String get ceiFallbackTitle => '结构化后备内容已启用';

  @override
  String get ceiFallbackBody => '即使没有生成的角色解释，经验证的结构化事实仍保持可见。';

  @override
  String get ceiProviderUnavailableTitle => 'AI 提供方不可用';

  @override
  String get ceiProviderUnavailableBody => '此冻结产物仍可使用。临床记录、待补费用、澄清和人工审核流程可继续。';

  @override
  String get ceiAcknowledge => '确认阅读';

  @override
  String get ceiConcur => '同意';

  @override
  String get ceiDisagree => '不同意';

  @override
  String get ceiException => '记录例外';

  @override
  String get ceiResponseRecorded => '临床响应已追加，产物未被更改。';

  @override
  String get ceiResponseFailed => '无法追加响应。手动临床记录仍可使用。';

  @override
  String get ceiRationale => '可归属理由';

  @override
  String get ceiCancel => '取消';

  @override
  String get ceiAppendResponse => '追加响应';

  @override
  String get ceiValidated => '已验证';

  @override
  String get ceiValidatedWithUncertainty => '已验证但存在不确定性';

  @override
  String get ceiValidatedWithResults => '已验证并记录检查结果';

  @override
  String get ceiAwaitingHumanReview => '等待人工审核';

  @override
  String get ceiHumanReviewRequired => '需要人工审核';

  @override
  String get ceiStronglySupported => '当前信息强力支持';

  @override
  String get ceiPlausible => '具有合理性';

  @override
  String get ceiMateriallyUncertain => '存在重大不确定性，建议澄清';

  @override
  String get ceiWeaklySupported => '当前信息支持较弱，需要人工审核';

  @override
  String get aiPossibleCauses => '可能原因';

  @override
  String get aiPossibleCausesNotDiagnosis => '以下是可能性，并非确诊。';

  @override
  String get aiWarningSigns => '重要警示症状';

  @override
  String get aiNextSteps => '实用的下一步';
}
