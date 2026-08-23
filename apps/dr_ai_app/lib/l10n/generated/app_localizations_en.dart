// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'Dr. AI';

  @override
  String get dashboard => 'Dashboard';

  @override
  String get patientManagement => 'Patient Management';

  @override
  String get account => 'Account';

  @override
  String get contacts => 'Contacts';

  @override
  String get connectedDoctors => 'Connected Doctors';

  @override
  String get pendingPatientApproval => 'Pending approval';

  @override
  String get approve => 'Approve';

  @override
  String get reject => 'Reject';

  @override
  String get removeConnectedDoctor => 'Remove connected doctor';

  @override
  String get activatePlan => 'Activate approved plan';

  @override
  String get authorLabel => 'Author';

  @override
  String get reviewerLabel => 'Reviewer';

  @override
  String get notAssigned =>
      'Not assigned — independent review is not established';

  @override
  String get recoveryPlan => 'Recovery Plan';

  @override
  String get myAccount => 'My Account';

  @override
  String get doctorWorkspace => 'Doctor workspace';

  @override
  String get patientWorkspace => 'Patient workspace';

  @override
  String get restoringSession => 'Restoring secure session';

  @override
  String get signIn => 'Sign in';

  @override
  String get logIn => 'Log in';

  @override
  String get logOut => 'Log out';

  @override
  String get logOutQuestion => 'Log out?';

  @override
  String get logOutConfirmation =>
      'Confirm that you want to leave your Dr. AI account on this device.';

  @override
  String get cancel => 'Cancel';

  @override
  String get saveChanges => 'Save changes';

  @override
  String get language => 'Language';

  @override
  String get languagePreferences => 'Language preferences';

  @override
  String get interfaceLanguage => 'Interface language';

  @override
  String get interfaceLanguageDescription =>
      'Choose the language used for labels, messages, and notifications on this device.';

  @override
  String get english => 'English';

  @override
  String get simplifiedChinese => '简体中文';

  @override
  String get systemLanguage => 'System language';

  @override
  String get doctorAccount => 'Doctor Account';

  @override
  String get doctorAccountDescription =>
      'Manage your profile, language preferences, and account settings.';

  @override
  String get payerAccount => 'Payer Account';

  @override
  String get payerAccountDescription =>
      'Manage your reviewer identity and account security while keeping organization authorization administrator-controlled.';

  @override
  String get loadingPayerAccount => 'Loading payer account';

  @override
  String get payerAccountLoadFailed =>
      'Unable to load the payer account. Check your connection and try again.';

  @override
  String get payerAccessUnavailable =>
      'Your payer organization access is unavailable. Contact an administrator if this is unexpected.';

  @override
  String get reviewerProfile => 'Reviewer profile';

  @override
  String get reviewerProfileDescription =>
      'These personal identity fields belong to your reviewer account.';

  @override
  String get reviewerIdentityHint =>
      'Use the name and professional title colleagues should recognize in the review workspace.';

  @override
  String get professionalTitle => 'Professional title';

  @override
  String get payerTitleTooShort => 'Use at least 2 characters.';

  @override
  String get payerEmailDescription =>
      'Used to sign in and for account communication. Leave empty to remove it.';

  @override
  String get payerProfileValidationFailed =>
      'Check the reviewer name and professional title, then try again.';

  @override
  String get organizationAndAccess => 'Organization & access';

  @override
  String get organizationAndAccessDescription =>
      'Your current institutional membership and review boundary.';

  @override
  String get organizationAccessManaged =>
      'These fields are read-only. Only an authorized administrator can change membership, scope, or verification.';

  @override
  String get organizationType => 'Organization type';

  @override
  String get jurisdiction => 'Jurisdiction';

  @override
  String get membershipStatus => 'Membership status';

  @override
  String get accessScope => 'Access scope';

  @override
  String get organizationVerification => 'Organization verification';

  @override
  String get publicPayer => 'Public payer';

  @override
  String get commercialPayer => 'Commercial payer';

  @override
  String get observerOrganization => 'Observer organization';

  @override
  String get activeMembership => 'Active';

  @override
  String get suspended => 'Suspended';

  @override
  String get revoked => 'Revoked';

  @override
  String get syntheticReviewScope => 'Synthetic review';

  @override
  String get syntheticOnlyVerification => 'Synthetic-only';

  @override
  String get verified => 'Verified';

  @override
  String get sessionActions => 'Session actions';

  @override
  String get payerSessionActionsDescription =>
      'Sign out of this device when you have finished working with restricted review information.';

  @override
  String get saving => 'Saving';

  @override
  String get preferredLanguage => 'Preferred language';

  @override
  String get security => 'Security';

  @override
  String get changePassword => 'Change password';

  @override
  String get changePasswordDescription =>
      'Change your password securely. You will be signed out on all devices afterward.';

  @override
  String get currentPassword => 'Current password';

  @override
  String get newPassword => 'New password';

  @override
  String get confirmNewPassword => 'Confirm new password';

  @override
  String get updatePassword => 'Update password';

  @override
  String get showPasswords => 'Show passwords';

  @override
  String get hidePasswords => 'Hide passwords';

  @override
  String get uploadAvatar => 'Upload avatar';

  @override
  String get editProfile => 'Edit profile and medical history';

  @override
  String patientId(String id) {
    return 'Patient ID: $id';
  }

  @override
  String get birthDate => 'Birth date';

  @override
  String get gender => 'Gender';

  @override
  String get phone => 'Phone';

  @override
  String get emergencyContact => 'Emergency contact';

  @override
  String get contactPreference => 'Contact preference';

  @override
  String get location => 'Location';

  @override
  String get height => 'Height';

  @override
  String get weight => 'Weight';

  @override
  String get clinicalEvents => 'Clinical Events';

  @override
  String get medicalHistory => 'Medical History';

  @override
  String get medicalRecordsAndImaging => 'Medical Records And Imaging';

  @override
  String get medicationsAndPrescriptions => 'Medications And Prescriptions';

  @override
  String get clinicalEventsEmpty =>
      'Clinical Events appear after your doctor creates one.';

  @override
  String get medicalRecords => 'Medical records';

  @override
  String get imagingResults => 'Imaging results';

  @override
  String get today => 'Today';

  @override
  String get overdue => 'Overdue';

  @override
  String get upcoming => 'Upcoming';

  @override
  String get unscheduled => 'Unscheduled';

  @override
  String get noScheduledTasks => 'No tasks in this section.';

  @override
  String get careCostsSummary => 'Care & Costs summary';

  @override
  String get loadingCareCostsSummary => 'Loading Care & Costs summary';

  @override
  String get loadCareCostsSummaryFailed =>
      'Care & Costs are temporarily unavailable.';

  @override
  String get noCareCostsYet =>
      'No billable services or products have been recorded yet.';

  @override
  String get authoritativeLedgerSummary =>
      'CNY amounts from the same server ledger as Care & Costs. Uploaded images are evidence, not separate charges.';

  @override
  String get estimatedAmounts => 'Estimated amounts';

  @override
  String get finalAmounts => 'Final amounts';

  @override
  String get requestedFromPayer => 'Requested from payer';

  @override
  String get expectedPatientResponsibility => 'Expected patient responsibility';

  @override
  String get pendingCostItems => 'Costs still pending';

  @override
  String get askDrAi => 'Ask Dr. AI';

  @override
  String get careRecords => 'Care Records';

  @override
  String get privacyPolicy => 'Privacy Policy';

  @override
  String get termsOfService => 'Terms of Service';

  @override
  String get returnToDashboard => 'Return to dashboard';

  @override
  String get unauthorized => 'This route is not available for your role.';

  @override
  String get tryAgain => 'Try again';

  @override
  String get notRecorded => 'Not recorded';

  @override
  String get noneRecorded => 'None recorded';

  @override
  String get yes => 'Yes';

  @override
  String get no => 'No';

  @override
  String get done => 'Done';

  @override
  String get next => 'Next';

  @override
  String get backToRegistration => 'Back to registration';

  @override
  String get privacySupport => 'Privacy, consent, and support';

  @override
  String get accountSaved => 'Account changes saved.';

  @override
  String get accountSaveFailed =>
      'Unable to save account changes. Check your connection and try again.';

  @override
  String get accountEmailAlreadyInUse =>
      'This email is already linked to another account. Use a different email or leave this field empty.';

  @override
  String get languageUpdated => 'Interface language updated.';

  @override
  String get systemLanguageDescription =>
      'Chinese and English follow your device setting. Other system languages use English.';

  @override
  String get welcome => 'Welcome to Dr. AI';

  @override
  String get signInDescription =>
      'Sign in with the phone number or email on your account.';

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get stagingNotice =>
      'Staging environment: do not enter real patient data.';

  @override
  String get alreadyHaveAccount => 'Already have an account?';

  @override
  String get doctorRegistration => 'Doctor Registration';

  @override
  String get payerRegistration => 'Payer Registration';

  @override
  String get createAccount => 'Create your account';

  @override
  String get createAccountDoctorDescription =>
      'Create your account to join Dr. AI';

  @override
  String get createAccountPayerDescription =>
      'Create an authorized reviewer account for transparent care and cost review';

  @override
  String get createAccountPatientDescription =>
      'Set up your account and continue to medical intake.';

  @override
  String get accountInformation => 'Account Information';

  @override
  String get personalInformation => 'Personal Information';

  @override
  String get hospitalInformation => 'Hospital Information';

  @override
  String get homeAddress => 'Home Address';

  @override
  String get code => 'Code';

  @override
  String get emailOrPhone => 'Email or phone number';

  @override
  String get phoneNumber => 'Phone number';

  @override
  String get enterPhoneNumber => 'Enter phone number';

  @override
  String get emailOptional => 'Email (optional)';

  @override
  String get password => 'Password';

  @override
  String get passwordGuidance =>
      '8-20 characters. Letters, numbers, and symbols are okay.';

  @override
  String get showPassword => 'Show password';

  @override
  String get hidePassword => 'Hide password';

  @override
  String get confirmPassword => 'Confirm password';

  @override
  String get verificationCode => 'Verification code';

  @override
  String get enterVerificationCode => 'Enter 6-digit code';

  @override
  String get sendCode => 'Send code';

  @override
  String get patient => 'Patient';

  @override
  String get doctor => 'Doctor';

  @override
  String get payer => 'Payer';

  @override
  String get organizationInformation => 'Organization information';

  @override
  String get organizationName => 'Organization name';

  @override
  String get firstName => 'First name';

  @override
  String get middleNameOptional => 'Middle name (optional)';

  @override
  String get lastName => 'Last name';

  @override
  String get dateOfBirth => 'Date of birth';

  @override
  String get selectDate => 'Select date';

  @override
  String get countryRegion => 'Country/Region';

  @override
  String get province => 'Province';

  @override
  String get city => 'City';

  @override
  String get hospital => 'Hospital';

  @override
  String get hospitalEmpty => 'No hospitals listed yet';

  @override
  String get hospitalMissing => 'Can’t find your hospital?';

  @override
  String get addHospital => 'Add my hospital';

  @override
  String get hospitalName => 'Hospital name';

  @override
  String get termsConsentPrefix => 'I have read and agree to the ';

  @override
  String get termsConsentJoiner => ' and ';

  @override
  String get required => 'Required.';

  @override
  String get invalidAccount => 'Enter a valid email address or phone number.';

  @override
  String get invalidPhone => 'Enter a valid phone number.';

  @override
  String get phoneRequired => 'Phone number is required.';

  @override
  String get invalidEmail => 'Enter a valid email address.';

  @override
  String get enterPassword => 'Enter your password.';

  @override
  String get passwordLength => 'Use 8-20 characters.';

  @override
  String get passwordMismatch => 'Passwords do not match.';

  @override
  String get enterSixDigitCode => 'Enter the 6-digit code.';

  @override
  String get enterPhoneFirst => 'Enter your phone number first.';

  @override
  String get alreadyHaveAccountLogIn => 'Already have an account? Log in';

  @override
  String get createAnAccount => 'Create an account';

  @override
  String get loading => 'Loading';

  @override
  String get loadingContacts => 'Loading your contacts';

  @override
  String get loadContactsFailed => 'Unable to load your contacts. Try again.';

  @override
  String get contactsDescription =>
      'Your care team and Dr. AI services are kept together here.';

  @override
  String get services => 'Services';

  @override
  String get system => 'System';

  @override
  String get systemContactDescription =>
      'Care-plan, medication, fee, and account reminders';

  @override
  String get official => 'Official';

  @override
  String get drAiContactDescription =>
      'Educational AI chat will be available in Phase 3';

  @override
  String get comingLater => 'Coming later';

  @override
  String get myDoctors => 'My doctors';

  @override
  String get groups => 'Groups';

  @override
  String get careGroups => 'Care groups';

  @override
  String get careGroupsDescription =>
      'Group conversations and creation are planned for a later release';

  @override
  String get connected => 'Connected';

  @override
  String get noDoctorConnected => 'No doctor connected yet';

  @override
  String get sharePatientIdDoctor =>
      'Share your patient ID with a doctor. Once they connect, they will appear here.';

  @override
  String get placeholder => 'PLACEHOLDER';

  @override
  String get privacyAndDataNotice => 'Privacy and data notice';

  @override
  String get privacyNoticeBody =>
      'This synthetic-development environment is governed by the account, consent, privacy, and support boundaries shown here. It is not authorized for real patient data or live clinical use.';

  @override
  String get privacyNoData =>
      'Do not enter names, contact information, raw records, images, or patient-owned clinical content in staging.';

  @override
  String get privacyBackendKeys =>
      'DeepSeek is reached only through the FastAPI backend; keys never enter the Flutter app.';

  @override
  String get privacyChatBoundary =>
      'Chat is educational question preparation only and is blocked by red-flag safety checks before any LLM call.';

  @override
  String get consentChecklist => 'Consent checklist';

  @override
  String get consentStagingData =>
      'I understand staging is not ready for real patient data.';

  @override
  String get consentNoEmergency =>
      'I understand Dr. AI is not for emergencies, diagnosis, or treatment decisions.';

  @override
  String get consentNoRealData =>
      'I understand I must not submit real patient data.';

  @override
  String get consentReady => 'Consent readiness prepared locally.';

  @override
  String get consentIncomplete =>
      'Complete all items before using this staging surface.';

  @override
  String get accountDeletionRequest => 'Account deletion request';

  @override
  String get deletionLocalOnly =>
      'This local surface prepares a deletion request only. It does not delete data, alter accounts, or contact testers.';

  @override
  String get deletionPrompt => 'Type REQUEST ACCOUNT DELETION';

  @override
  String get prepareRequest => 'Prepare request';

  @override
  String get deletionPrepared =>
      'Deletion request prepared locally. No account data was changed.';

  @override
  String get feedbackForm => 'Feedback form';

  @override
  String get feedbackPrivacy =>
      'Do not include patient details, screenshots containing private data, or account secrets.';

  @override
  String get feedbackDraft => 'Feedback draft';

  @override
  String get feedbackHint =>
      'Describe the issue, device, browser, and account step.';

  @override
  String get prepareFeedback => 'Prepare feedback draft';

  @override
  String get feedbackPrepared =>
      'Feedback draft prepared locally. No external message was sent.';

  @override
  String get knownLimitations => 'Known limitations';

  @override
  String get limitationClinical =>
      'Clinical model inference, billing, appointments, and video or voice consultation are not enabled yet.';

  @override
  String get limitationUpload =>
      'Image upload completion and storage policy require a separate production approval path.';

  @override
  String get limitationRecovery =>
      'Password reset, account recovery, and verified SMS/email delivery remain deferred.';

  @override
  String get limitationRelease =>
      'Any production deployment, store distribution, or account policy change requires explicit release approval.';

  @override
  String get privacySupportTitle => 'Dr. AI privacy and support';

  @override
  String get privacySupportHero => 'Privacy and support';

  @override
  String get accountPolicyStaging =>
      'Synthetic-development account and privacy boundaries for Dr. AI.';

  @override
  String accountPolicyUser(String name) {
    return 'Synthetic-development account and privacy boundaries for $name.';
  }

  @override
  String get stagingPolicyPlaceholder => 'Synthetic-development policy';

  @override
  String get passwordUpdated => 'Password updated';

  @override
  String get resetPassword => 'Reset password';

  @override
  String get passwordChangedSignIn =>
      'Your password has been changed. Sign in again with your new password.';

  @override
  String get verifyPhoneReset =>
      'Verify the phone number on your account. The code expires after 10 minutes.';

  @override
  String get enterYourPhone => 'Enter your phone number.';

  @override
  String get sendVerificationCode => 'Send verification code';

  @override
  String get sixDigitVerificationCode => '6-digit verification code';

  @override
  String get backToSignIn => 'Back to sign in';

  @override
  String get resetPasswordFailed => 'Unable to reset your password. Try again.';

  @override
  String get stepAccount => '1  Account';

  @override
  String get stepProfile => '2  Profile';

  @override
  String get stepLocation => '3  Location';

  @override
  String get stepComplete => '4  Complete';

  @override
  String get profile => 'Profile';

  @override
  String get careHospitalDetails => 'Care and hospital details';

  @override
  String get finishSetup => 'Finish setup';

  @override
  String get loadingAccount => 'Loading your account';

  @override
  String get loadAccountFailed => 'Unable to load your account. Try again.';

  @override
  String get loadingRecoveryPlans => 'Loading recovery plans';

  @override
  String get loadRecoveryPlansFailed =>
      'Unable to load recovery plans. Try again.';

  @override
  String get loadingProfile => 'Loading your profile';

  @override
  String get loadProfileFailed => 'Unable to load your profile. Try again.';

  @override
  String get prescriptions => 'Prescriptions';

  @override
  String get medicationReminders => 'Medication reminders';

  @override
  String get noMedications => 'No medications recorded yet.';

  @override
  String get records => 'Records';

  @override
  String get imaging => 'Imaging';

  @override
  String get available => 'Available';

  @override
  String get noneYet => 'None yet';

  @override
  String get loadingActivePlan => 'Loading active plan';

  @override
  String get loadActivePlanFailed =>
      'Unable to load active recovery plan. Try again.';

  @override
  String get noActivePlan =>
      'No active recovery plan yet. Your doctor can approve one from Patient Management.';

  @override
  String get planHistory => 'Plan History';

  @override
  String get planHistoryEmpty => 'Recovery plan history will appear here.';

  @override
  String get completeHealthProfile => 'Complete your health profile';

  @override
  String get medicalIntake => 'Medical intake';

  @override
  String get medicalIntakeDescription =>
      'Complete this once so your care team can review your profile before the first Clinical Event. Required fields are marked with *. Optional fields can be left blank.';

  @override
  String get aboutYou => 'About you';

  @override
  String get aboutYouDescription =>
      'Enter the identity and contact information your care team should use.';

  @override
  String get fullNameRequired => 'First and last name *';

  @override
  String get homeAddressOptional => 'Home address (optional)';

  @override
  String get streetBuilding => 'Street and building information';

  @override
  String get unspecified => 'Unspecified';

  @override
  String get female => 'Female';

  @override
  String get male => 'Male';

  @override
  String get other => 'Other';

  @override
  String get emergencyContactOptional => 'Emergency contact (optional)';

  @override
  String get fullName => 'Full name';

  @override
  String get emergencyPhoneOptional => 'Emergency phone (optional)';

  @override
  String get includeCountryCode => 'Include country code';

  @override
  String get inApp => 'In-app';

  @override
  String get email => 'Email';

  @override
  String get healthMeasurements => 'Health measurements';

  @override
  String get healthMeasurementsDescription =>
      'Add your latest known measurements. Leave blood pressure blank if you do not know it.';

  @override
  String get heightCmRequired => 'Height (cm) *';

  @override
  String get weightKgRequired => 'Weight (kg) *';

  @override
  String get bloodType => 'Blood type';

  @override
  String get bloodPressure => 'Blood pressure';

  @override
  String get unknown => 'Unknown';

  @override
  String get systolicBp => 'Systolic BP';

  @override
  String get diastolicBp => 'Diastolic BP';

  @override
  String get smokingStatus => 'Smoking status';

  @override
  String get never => 'Never';

  @override
  String get former => 'Former';

  @override
  String get current => 'Current';

  @override
  String get alcohol => 'Alcohol';

  @override
  String get noneOrRare => 'None or rare';

  @override
  String get occasional => 'Occasional';

  @override
  String get weekly => 'Weekly';

  @override
  String get daily => 'Daily';

  @override
  String get allergiesConditions => 'Allergies and health conditions';

  @override
  String get conditionsDescription =>
      'Choose Yes only when a condition applies. A details box will open for dates, treatment, or current status.';

  @override
  String get hasAllergies => 'Do you have any allergies?';

  @override
  String get allergy => 'Allergy';

  @override
  String get reactionOptional => 'Reaction (optional)';

  @override
  String get hasChronicCondition =>
      'Do you have hereditary or long-term medical conditions?';

  @override
  String get condition => 'Condition';

  @override
  String get notesOptional => 'Notes (optional)';

  @override
  String get diagnosisTreatmentHint =>
      'Diagnosis date, treatment, or current status';

  @override
  String get heartHistory => 'Heart or blood vessel history';

  @override
  String get heartHistoryDescription =>
      'Heart attack, stroke, irregular heartbeat, blood clots, or heart failure.';

  @override
  String get endocrineHistory => 'Diabetes, thyroid, or bone health';

  @override
  String get endocrineHistoryDescription =>
      'Diabetes including gestational diabetes, thyroid disorders, or osteoporosis.';

  @override
  String get neuroHistory => 'Brain, mood, or nervous system';

  @override
  String get neuroHistoryDescription =>
      'Depression, severe anxiety, seizures, epilepsy, bipolar disorder, or chronic migraines.';

  @override
  String get digestiveHistory => 'Stomach, bowel, or liver history';

  @override
  String get digestiveHistoryDescription =>
      'Ulcers, Crohn disease, ulcerative colitis, irritable bowel disease, hepatitis, or cirrhosis.';

  @override
  String get respiratoryHistory => 'Lung or breathing history';

  @override
  String get respiratoryHistoryDescription =>
      'Asthma, COPD, emphysema, or severe pneumonia requiring hospitalization.';

  @override
  String get kidneyHistory => 'Kidney or urinary history';

  @override
  String get kidneyHistoryDescription =>
      'Chronic kidney disease, reduced kidney function, or severe kidney stones.';

  @override
  String get cancerHistory => 'Cancer or active treatment';

  @override
  String get cancerHistoryDescription =>
      'Any cancer including skin cancer, chemotherapy, radiation, or immunotherapy.';

  @override
  String get medicalBackground => 'Medical background and daily life';

  @override
  String get medicalBackgroundDescription =>
      'Use short, plain-language summaries. You can update this information later from My Account.';

  @override
  String get currentMedicationsOptional =>
      'Current medications and supplements (optional)';

  @override
  String get medicationHint => 'Name, dose, and how often you take each one';

  @override
  String get surgeriesOptional =>
      'Past surgeries or hospitalizations (optional)';

  @override
  String get surgeriesHint =>
      'Procedure or reason, year, and hospital if known';

  @override
  String get familyHistoryOptional => 'Family medical history (optional)';

  @override
  String get familyHistoryHint =>
      'Condition and relationship, such as parent or sibling';

  @override
  String get lifestyleOptional => 'Exercise and sleep notes (optional)';

  @override
  String get lifestyleHint => 'Typical weekly activity and sleep pattern';

  @override
  String get pregnancyStatus => 'Pregnancy status';

  @override
  String get preferNotToSay => 'Prefer not to say';

  @override
  String get notApplicable => 'Not applicable';

  @override
  String get unsure => 'Unsure';

  @override
  String get saveProfileFailed =>
      'Unable to save your profile. Check the form and try again.';

  @override
  String get useNumbersOnly => 'Use numbers only.';

  @override
  String get useDateFormat => 'Use YYYY-MM-DD.';

  @override
  String get provinceState => 'Province / State';

  @override
  String get loadingTodayTasks => 'Loading today recovery tasks';

  @override
  String get loadTodayTasksFailed =>
      'Unable to load today recovery tasks. Try again.';

  @override
  String get phase5MedicationNotificationsReadOnly =>
      'System medication notifications are not scheduled in Phase 5. Phase 6 requires device registration and a governed delivery service; use the persisted in-product task list for now.';

  @override
  String get noTodayTasks => 'No active recovery tasks for today.';

  @override
  String get taskSyncFailed =>
      'Completion could not sync. Your local tap is still visible; try again when the connection recovers.';

  @override
  String get loadingMedicationReminders => 'Loading medication reminders...';

  @override
  String get medicationRemindersUnavailable =>
      'Medication reminders unavailable.';

  @override
  String get noMedicationReminders => 'No medication reminders due.';

  @override
  String get refill => 'Refill';

  @override
  String get educationalDisclaimer =>
      'Educational information only - not medical advice.';

  @override
  String get prepareQuestion => 'Prepare a question for your clinician';

  @override
  String get sendEducationalQuestion => 'Send educational question';

  @override
  String get streamingResponse => 'Streaming response...';

  @override
  String fallbackReason(String reason) {
    return 'Fallback: $reason';
  }

  @override
  String get exercise => 'Exercise';

  @override
  String get diet => 'Diet';

  @override
  String get followUp => 'Follow-up';

  @override
  String get task => 'Task';

  @override
  String get noClinicalEventUpdate =>
      'No Clinical Event available for patient update';

  @override
  String updateEvent(String title) {
    return 'Update: $title';
  }

  @override
  String latestPatientUpdate(String summary) {
    return 'Latest patient update: $summary';
  }

  @override
  String get updateType => 'Update type';

  @override
  String get generalUpdate => 'General update';

  @override
  String get symptomUpdate => 'Symptom update';

  @override
  String get medicationNote => 'Medication note';

  @override
  String get recoveryCheckIn => 'Recovery check-in';

  @override
  String get selfReportedUpdate => 'Self-reported update';

  @override
  String updateSubmitted(String type) {
    return 'Update submitted: $type';
  }

  @override
  String get sendUpdate => 'Send update';

  @override
  String get enterUpdate => 'Enter a short update first.';

  @override
  String get paymentUnavailable => 'Payment unavailable';

  @override
  String get payNowUnavailable => 'Pay now unavailable';

  @override
  String get paymentDescription =>
      'You can review fee status here. Online payment is not enabled yet.';

  @override
  String get chatRateLimited => 'Educational chat is temporarily rate limited.';

  @override
  String get unableToReach => 'Unable to reach Dr. AI.';

  @override
  String get conditionDetailsHint =>
      'Add diagnosis, date, treatment, or current status';

  @override
  String get china => 'China';

  @override
  String get guangdong => 'Guangdong';

  @override
  String get shenzhen => 'Shenzhen';

  @override
  String get active => 'Active';

  @override
  String get paused => 'Paused';

  @override
  String get stopped => 'Stopped';

  @override
  String get monitoring => 'Monitoring';

  @override
  String get resolved => 'Resolved';

  @override
  String get draft => 'Draft';

  @override
  String get pendingReview => 'Pending review';

  @override
  String get approved => 'Approved';

  @override
  String get completed => 'Completed';

  @override
  String get pending => 'Pending';

  @override
  String get completeProfileSetup => 'Complete profile setup';

  @override
  String get sharePatientCode => 'Share your patient code';

  @override
  String get waitDoctorConnect => 'Wait for your doctor to connect';

  @override
  String get after => 'After';

  @override
  String get reviewMedicalHistory => 'Review your medical history';

  @override
  String get confirmContactPreferences => 'Confirm contact preferences';

  @override
  String get prepareDoctorQuestions => 'Prepare questions for your doctor';

  @override
  String get followCareTasks => 'Follow doctor-created care tasks';

  @override
  String get trackRecovery => 'Track recovery progress';

  @override
  String get checkMedicationsImaging => 'Check medications and imaging results';

  @override
  String get doctorNotConnected => 'Doctor not connected';

  @override
  String get sharePatientCodeAction => 'Share patient code';

  @override
  String get careAfterConnection => 'Care details appear after connection.';

  @override
  String get consultation => 'Consultation';

  @override
  String get medicalRecord => 'Medical record';

  @override
  String get medication => 'Medication';

  @override
  String allergiesSummary(String value) {
    return 'Allergies: $value';
  }

  @override
  String chronicDiseasesSummary(String value) {
    return 'Chronic diseases: $value';
  }

  @override
  String visitHistorySummary(int count) {
    return 'Visit history: $count';
  }

  @override
  String diagnosesSummary(String value) {
    return 'Diagnoses: $value';
  }

  @override
  String get loadingDoctorAccount => 'Loading doctor account';

  @override
  String get noAccountChanges => 'No account changes to save.';

  @override
  String get doctorIdentityRequired =>
      'Display name and title are required before saving.';

  @override
  String get verificationStatus => 'Verification status';

  @override
  String get activeDoctorAccount => 'Active doctor account';

  @override
  String get inactiveDoctorAccount => 'Not active';

  @override
  String doctorLastOnline(String date) {
    return 'Not active · Last online $date';
  }

  @override
  String get accountContact => 'Account contact';

  @override
  String get clinicalIdentity => 'Clinical identity';

  @override
  String get displayName => 'Display name';

  @override
  String get specialty => 'Specialty';

  @override
  String get title => 'Title';

  @override
  String get hospitalLocation => 'Hospital & location';

  @override
  String get hospitalManaged => 'Hospital (managed by administrator)';

  @override
  String get department => 'Department';

  @override
  String get contact => 'Contact';

  @override
  String get hospitalProfilePending => 'Hospital profile pending';

  @override
  String get completeHospitalDetails => 'Complete hospital details';

  @override
  String get careWorkspaceReady =>
      'Your care workspace is ready for patient-code connection.';

  @override
  String get doctorProfile => 'Doctor profile';

  @override
  String get clinician => 'Clinician';

  @override
  String get connectPatientsEpisodes =>
      'Connect patients by code to start care episodes';

  @override
  String get noPatientActivity => 'No patient activity yet';

  @override
  String get xray => 'X-ray';

  @override
  String get ultrasound => 'Ultrasound';

  @override
  String get inviteTeamMember => 'Invite team member';

  @override
  String get connectPatient => 'Connect patient';

  @override
  String get createEvent => 'Create event';

  @override
  String get quickAccess => 'Quick Access';

  @override
  String get imagingRecordsManualReview => 'Imaging records & manual review';

  @override
  String get imagingRecordsManualReviewDescription =>
      'Select a patient to view event-linked imaging evidence and doctor-entered review status.';

  @override
  String get patientMedicalRecords => 'Patient medical records';

  @override
  String get patientMedicalRecordsDescription =>
      'Select a patient to review their authorized clinical history and records.';

  @override
  String get patientRecoveryPlans => 'Patient recovery plans';

  @override
  String get patientRecoveryPlansDescription =>
      'Select a patient to open the recovery-plan workspace.';

  @override
  String get medicalResourcesReadOnly => 'Medical resources (read-only)';

  @override
  String get medicalResourcesReadOnlyDescription =>
      'View the current informational resource overview; booking is not enabled.';

  @override
  String get payerRequests => 'Payer requests';

  @override
  String get payerRequestsDescription =>
      'Open the doctor workspace for human-reviewed payer requests.';

  @override
  String get teamManagement => 'Team Management';

  @override
  String get recentActivities => 'Recent Activities';

  @override
  String get resourceOverview => 'Resource Overview';

  @override
  String get ok => 'OK';

  @override
  String get medicalEquipment => 'Medical Equipment';

  @override
  String resourceAvailable(int available, int total) {
    return '$available/$total Available';
  }

  @override
  String get medicationStocks => 'Medication Stocks';

  @override
  String get staffingLevels => 'Staffing Levels';

  @override
  String get bedAvailability => 'Bed Availability';

  @override
  String get operationalSummary =>
      'Operational summaries update as clinic data becomes available.';

  @override
  String get overview => 'Overview';

  @override
  String get verifiedHistory => 'Verified History';

  @override
  String get activeClinicalEvents => 'Active Clinical Events';

  @override
  String get activeRecoveryPlan => 'Active Recovery Plan';

  @override
  String get currentMedications => 'Current Medications';

  @override
  String get overviewSummary => 'Patient snapshot and active event context';

  @override
  String get profileSummary =>
      'Patient-controlled information for doctor review';

  @override
  String get medicalHistoryLower => 'Medical history';

  @override
  String get medicalHistorySummary =>
      'Patient-entered history with clinician review context';

  @override
  String get clinicalEventsSummary =>
      'Problems over time with visits, diagnosis, and linked care';

  @override
  String get medicationsPrescriptions => 'Medications & Prescriptions';

  @override
  String get medicationsSummary =>
      'Event-linked orders, schedules, and generated reminders';

  @override
  String get recoveryPlans => 'Recovery Plans';

  @override
  String get recoveryPlansSummary =>
      'Event-linked timeline creation, review, and completion';

  @override
  String get imagingSummary =>
      'Event-linked upload metadata and manual review status';

  @override
  String get consultationActivity => 'Consultation & Activity';

  @override
  String get consultationActivitySummary =>
      'Notes, specialist review, and supporting timeline';

  @override
  String get searchPatients => 'Search patients';

  @override
  String get collapsePatientList => 'Collapse patient list';

  @override
  String get expandPatientList => 'Expand patient list';

  @override
  String get collapseSectionNavigation => 'Collapse section navigation';

  @override
  String get expandSectionNavigation => 'Expand section navigation';

  @override
  String get namePatientId => 'Name or patient ID';

  @override
  String get loadingPatients => 'Loading patients';

  @override
  String get noConnectedPatients => 'No connected patients';

  @override
  String get connectPatientEmpty =>
      'Ask the patient for their code, connect them here, then build the care workspace from zero.';

  @override
  String get connectPatientByCode => 'Connect patient by code';

  @override
  String get patientCode => 'Patient code';

  @override
  String get patientCodeHelper =>
      'Shown on the patient dashboard after sign-up';

  @override
  String get reviewPatientMatch => 'Review patient match';

  @override
  String connectedPatient(String name) {
    return 'Connected $name.';
  }

  @override
  String get enterPatientCode => 'Enter the patient code.';

  @override
  String get confirmPatientConnection => 'Confirm patient connection';

  @override
  String get confirmPatientDescription =>
      'Check that this is the patient who gave you the ID before creating access to their care workspace.';

  @override
  String get confirmConnect => 'Confirm and connect';

  @override
  String get patientNotFound =>
      'No patient matches this ID. Check it and try again.';

  @override
  String get reviewPatientFailed =>
      'Unable to review this patient ID. Try again.';

  @override
  String get patientProfile => 'Patient Profile';

  @override
  String get choosePatient => 'Choose patient';

  @override
  String get selectPatient => 'Select a patient';

  @override
  String get selectPatientDescription =>
      'Open an assigned patient to review core records.';

  @override
  String get patientWorkspaceTitle => 'Patient Workspace';

  @override
  String get loadingPatientProfile => 'Loading patient profile';

  @override
  String get changePatient => 'Change patient';

  @override
  String get recoveryPlanLoading => 'Recovery plan loading';

  @override
  String get recoveryPlanUnavailable => 'Recovery plan unavailable';

  @override
  String lastVisit(String value) {
    return 'Last visit: $value';
  }

  @override
  String get activeClinicalEvent => 'Active Clinical Event';

  @override
  String get createEventFirst =>
      'Create a Clinical Event before event-linked care work.';

  @override
  String get createEventBeforeCare =>
      'Create a Clinical Event before authoring event-linked prescriptions, recovery plans, imaging, notes, or consultation.';

  @override
  String get selectedCareEpisode => 'Selected care episode';

  @override
  String get legacyRecordsNotice =>
      'Linked sections will show legacy patient-wide records until an event is selected.';

  @override
  String get workspaceSection => 'Workspace section';

  @override
  String get clinicalEventReadiness => 'Clinical event readiness';

  @override
  String activeEventStatus(String status) {
    return 'Active event: $status';
  }

  @override
  String get createSelectEventDescription =>
      'Create or select a Clinical Event to organize prescriptions, medication schedules, recovery plans, imaging, notes, and consultation around one care episode.';

  @override
  String get doctorReviewOnly =>
      'Doctor review only: patient-controlled profile fields are not edited from this workspace.';

  @override
  String get profileCorrectionNotice =>
      'Profile corrections should be requested from the patient; direct doctor editing is intentionally unavailable here.';

  @override
  String get historyAuditNotice =>
      'Medical history is patient-entered. Doctor verification, correction requests, and amendments are stored as visible audited overlays.';

  @override
  String get allergies => 'Allergies';

  @override
  String get noAllergies => 'No allergies recorded';

  @override
  String get noReaction => 'No reaction detail recorded.';

  @override
  String get chronicDiseases => 'Chronic diseases';

  @override
  String get noChronicDiseases => 'No chronic diseases recorded';

  @override
  String get noConditionNote => 'No condition note recorded.';

  @override
  String get doctorAmendmentAdded =>
      'Doctor amendment added after reviewing the patient history.';

  @override
  String get patientConfirmHistory =>
      'Please confirm this history item in your profile.';

  @override
  String get medicalHistoryReview => 'Medical History Review';

  @override
  String get noPatientHistoryItem =>
      'No patient-entered allergy, chronic disease, or record is available for doctor review yet.';

  @override
  String get patientEnteredItem => 'Patient-entered item';

  @override
  String get reviewAction => 'Review action';

  @override
  String get markVerified => 'Mark verified';

  @override
  String get addDoctorAmendment => 'Add doctor amendment';

  @override
  String get requestPatientCorrection => 'Request patient correction';

  @override
  String get doctorAmendment => 'Doctor amendment';

  @override
  String get patientCorrectionRequest => 'Patient correction request';

  @override
  String get saveAuditedReview => 'Save audited review';

  @override
  String historyReviewSaved(String action) {
    return 'Medical history review saved: $action.';
  }

  @override
  String get selectHistoryItem => 'Select a patient-entered item first.';

  @override
  String get enterDoctorAmendment => 'Enter a doctor amendment.';

  @override
  String get enterPatientCorrection => 'Enter a patient correction request.';

  @override
  String get encounterUpdates => 'Encounter updates';

  @override
  String get noEncounterUpdates => 'No encounter updates recorded';

  @override
  String clinicalEventLink(String title) {
    return 'Clinical Event link: $title';
  }

  @override
  String get doctorDiagnosisRecord => 'Doctor diagnosis record';

  @override
  String get noDiagnoses => 'No diagnoses recorded';

  @override
  String get noDiagnosisNote => 'No diagnosis note recorded.';

  @override
  String get diagnosisReadOnly =>
      'Patient can read this record but cannot edit doctor diagnosis.';

  @override
  String get doctorNotes => 'Doctor notes';

  @override
  String get noDoctorNotes => 'No doctor notes';

  @override
  String linkedToEvent(String title) {
    return 'Linked to $title';
  }

  @override
  String prescriptionContextNotice(String title) {
    return 'Prescription orders and active medication schedules are shown under $title. Reminder rows below are generated schedule outputs, not a standalone doctor workspace.';
  }

  @override
  String imagingEvidenceNotice(String title) {
    return 'Imaging is reviewed as supporting evidence for $title. Findings remain doctor-entered; the app does not make automated clinical claims.';
  }

  @override
  String get noEncounterUpdate => 'No encounter update recorded';

  @override
  String get diagnosisNotRecorded => 'Diagnosis not recorded';

  @override
  String get clinicalEventDescription =>
      'Clinical Event groups one medical problem over time. Doctors create and update it; patients can read it but cannot edit doctor diagnosis.';

  @override
  String latestUpdate(String value) {
    return 'Latest update: $value';
  }

  @override
  String get eventTimeline => 'Event timeline';

  @override
  String get clinicalEventEditor => 'Clinical Event Editor';

  @override
  String get createClinicalEvent => 'Create Clinical Event';

  @override
  String get updateClinicalEvent => 'Update Clinical Event';

  @override
  String get newEvent => 'New event';

  @override
  String get noClinicalEvent =>
      'No Clinical Event exists yet. Create one before authoring linked care outputs.';

  @override
  String get clinicalEventTitle => 'Clinical Event title';

  @override
  String get chiefComplaint => 'Chief complaint';

  @override
  String get onsetDate => 'Onset date';

  @override
  String get dateOptional => 'YYYY-MM-DD or blank';

  @override
  String get status => 'Status';

  @override
  String get symptomSummary => 'Symptom/update summary';

  @override
  String get doctorDiagnosis => 'Doctor diagnosis or provisional diagnosis';

  @override
  String get eventDiagnosisNotice =>
      'Patients can read Clinical Events, but doctor diagnosis fields are doctor-managed and audited.';

  @override
  String get newCareEpisode => 'New care episode';

  @override
  String get chiefComplaintMissing => 'Chief complaint not recorded';

  @override
  String get eventValidation =>
      'Use a title, chief complaint, and optional YYYY-MM-DD onset date.';

  @override
  String timelineEntry(String type) {
    return 'Clinical Event timeline entry: $type.';
  }

  @override
  String prescriptionStatus(String status) {
    return 'Prescription $status';
  }

  @override
  String get generatedRefillReminder => 'Generated refill reminder';

  @override
  String get generatedMedicationReminder => 'Generated medication reminder';

  @override
  String imagingStatusTitle(String status) {
    return 'Imaging $status';
  }

  @override
  String manualReviewStatus(String title) {
    return 'Manual review status for $title.';
  }

  @override
  String get activityTimeline => 'Activity timeline';

  @override
  String get noActivity => 'No activity yet';

  @override
  String get noMedicalRecords => 'No Medical Records';

  @override
  String get doctorReviewAmendments => 'Doctor review and amendments';

  @override
  String get noDoctorReviews => 'No doctor review records';

  @override
  String get clinicianVerifiedHistory =>
      'Clinician verified patient-entered history.';

  @override
  String get auditOverlayNotice =>
      'Audit-linked overlay; original patient-entered item is preserved.';

  @override
  String allergyLabel(String value) {
    return 'Allergy: $value';
  }

  @override
  String chronicDiseaseLabel(String value) {
    return 'Chronic disease: $value';
  }

  @override
  String medicalRecordLabel(String value) {
    return 'Medical record: $value';
  }

  @override
  String get clinicianVerified => 'Clinician verified';

  @override
  String get patientCorrectionRequested => 'Patient correction requested';

  @override
  String get noImagingAssets => 'No imaging assets';

  @override
  String uploaded(String date) {
    return 'Uploaded: $date';
  }

  @override
  String findingResult(String value) {
    return 'Finding/result: $value';
  }

  @override
  String measurementObservation(String value) {
    return 'Measurement/observation: $value';
  }

  @override
  String get pendingManualReview => 'Pending manual doctor review';

  @override
  String get medications => 'Medications';

  @override
  String get noMedicationsRecorded => 'No medications recorded';

  @override
  String get noPrescriptions => 'No prescriptions';

  @override
  String get medicationRemindersTitle => 'Medication Reminders';

  @override
  String get noMedicationReminderRecords => 'No medication reminders';

  @override
  String get refillReminder => 'Refill reminder';

  @override
  String get medicationReminder => 'Medication reminder';

  @override
  String get medicationScheduleEditor => 'Medication Schedule Editor';

  @override
  String get prescriptionOrderWorkflow => 'Prescription Order Workflow';

  @override
  String get scheduleNotRecorded => 'Schedule not recorded';

  @override
  String get saveMedicationFirst =>
      'Save a medication before issuing a prescription.';

  @override
  String get prescriptionWorkflowDescription =>
      'Prescription lines use the selected event medication values and feed the patient medication schedule.';

  @override
  String get selectEventMedication =>
      'Select or create a Clinical Event before saving new event-linked medication work.';

  @override
  String get medicationName => 'Medication name';

  @override
  String get dosage => 'Dosage';

  @override
  String get schedule => 'Schedule';

  @override
  String get prescriptionNote => 'Prescription note';

  @override
  String get addMedication => 'Add medication';

  @override
  String get updateMedication => 'Update medication';

  @override
  String get issuePrescription => 'Issue prescription';

  @override
  String get medicationValidation =>
      'Medication name, dosage, and schedule are required.';

  @override
  String get asset => 'asset';

  @override
  String bytesVia(int bytes, String provider) {
    return '$bytes bytes via $provider';
  }

  @override
  String medicationLines(int count) {
    return '$count medication line(s)';
  }

  @override
  String nextDue(String date) {
    return 'Next: $date';
  }

  @override
  String get manualFindingDefault =>
      'Manual finding entered by doctor after imaging review.';

  @override
  String get manualMeasurementDefault =>
      'Manual measurement note; no automated interpretation.';

  @override
  String get imagingUpload => 'Imaging Upload';

  @override
  String get imageFilename => 'Image filename';

  @override
  String get imageMetadataHelper => 'PNG, JPEG, or DICOM metadata';

  @override
  String get contentType => 'Content type';

  @override
  String get sizeBytes => 'Size in bytes';

  @override
  String get prepareUpload => 'Prepare upload';

  @override
  String get imagingWorkflow => 'Imaging Workflow';

  @override
  String get manualFinding => 'Manual doctor-entered finding/result';

  @override
  String get manualMeasurement => 'Manual measurement or observation';

  @override
  String get prepareImaging => 'Prepare imaging';

  @override
  String get finalizeUpload => 'Finalize upload';

  @override
  String get markReviewed => 'Mark reviewed';

  @override
  String get selectEventImaging =>
      'Select or create a Clinical Event before preparing event-linked imaging metadata.';

  @override
  String get assessmentForm => 'Assessment Form';

  @override
  String get assessmentFixture => 'Assessment case';

  @override
  String get runAssessment => 'Run assessment';

  @override
  String get loadingAssessmentHistory => 'Loading assessment history';

  @override
  String get noAssessmentResults => 'No assessment results yet';

  @override
  String get assessmentEmptyDescription =>
      'Run an assessment case to create a result.';

  @override
  String get imageUploadValidation =>
      'Enter an image filename and a positive byte size.';

  @override
  String get uploadedBytesValidation =>
      'Enter the uploaded byte size to finalize.';

  @override
  String get manualFindingValidation =>
      'Enter a manual imaging finding/result before review.';

  @override
  String get assessmentSelectionValidation => 'Select an assessment case.';

  @override
  String get recoveryPlanEditor => 'Recovery Plan Editor';

  @override
  String get selectEventRecovery =>
      'Select or create a Clinical Event before creating an event-linked recovery plan.';

  @override
  String get noEventRecoveryPlan =>
      'No recovery plan for this Clinical Event yet. Save a draft first.';

  @override
  String planStatusReview(
    String status,
    String review,
    int completed,
    int total,
  ) {
    return 'Plan $status; review $review; $completed/$total tasks complete.';
  }

  @override
  String get noActiveEventPlan =>
      'No active Recovery Plan for this Clinical Event.';

  @override
  String get oneActiveEventPlan =>
      'One active Recovery Plan is linked to this Clinical Event.';

  @override
  String get multipleActivePlans =>
      'Multiple active plans are visible for this event; approve a replacement to resolve the workflow.';

  @override
  String get planTitle => 'Plan title';

  @override
  String get planTitleLimit => 'Required, 3–160 characters.';

  @override
  String get planTitleRequired => 'Enter a plan title.';

  @override
  String get planTitleTooShort =>
      'Use at least 3 characters for the plan title.';

  @override
  String get planTitleTooLong =>
      'Use no more than 160 characters for the plan title.';

  @override
  String get planTitleInvalidServer =>
      'Check the plan title and keep it within 160 characters.';

  @override
  String get recoveryTaskTitleLimit => '3–160 characters when provided.';

  @override
  String get recoveryTaskTitleTooShort =>
      'Use at least 3 characters for this task title.';

  @override
  String get recoveryTaskTitleTooLong =>
      'Use no more than 160 characters for this task title.';

  @override
  String get instructions => 'Instructions';

  @override
  String get medicationTask => 'Medication task';

  @override
  String get exerciseTask => 'Exercise task';

  @override
  String get dietTask => 'Diet task';

  @override
  String get followUpTask => 'Follow-up task';

  @override
  String reviewStatus(String status) {
    return 'Review $status.';
  }

  @override
  String get saveDraft => 'Save draft';

  @override
  String get submitReview => 'Submit review';

  @override
  String get requestChanges => 'Request changes';

  @override
  String get reviewComment => 'Review comment';

  @override
  String get reviewCommentHelp =>
      'Required when requesting changes; optional when approving.';

  @override
  String get reviewCommentRequired =>
      'Enter a review comment before requesting changes.';

  @override
  String get approvePatient => 'Approve for patient';

  @override
  String get completePlan => 'Complete plan';

  @override
  String get medicationTaskDetail =>
      'Medication reminder reviewed with the patient.';

  @override
  String get exerciseTaskDetail =>
      'Movement or exercise task reviewed with the patient.';

  @override
  String get dietTaskDetail =>
      'Nutrition or hydration task reviewed with the patient.';

  @override
  String get followUpTaskDetail =>
      'Follow-up preparation reviewed with the patient.';

  @override
  String get planFieldsValidation =>
      'Use at least three characters for every plan field.';

  @override
  String savePlanBeforeAction(String action) {
    return 'Save the recovery plan before $action.';
  }

  @override
  String get submitPlanFirst => 'Save and submit the recovery plan first.';

  @override
  String get specialistConsultation => 'Specialist Consultation';

  @override
  String get specialistDescription =>
      'Asynchronous consultation request. Appointments, billing, video, and voice are not included in this workflow.';

  @override
  String get selectEventConsultation =>
      'Select or create a Clinical Event before requesting event-linked specialist review.';

  @override
  String get questionSummary => 'Question summary';

  @override
  String get routine => 'Routine';

  @override
  String get soon => 'Soon';

  @override
  String get requestSpecialistReview => 'Request specialist review';

  @override
  String get loadingConsultations => 'Loading consultation requests';

  @override
  String get noSpecialistRequest => 'No specialist request yet';

  @override
  String get specialistEmptyDescription =>
      'Submit a request for asynchronous status tracking.';

  @override
  String priority(String value) {
    return 'Priority: $value';
  }

  @override
  String get consultationValidation =>
      'Enter a specialty and a concise, relevant summary.';

  @override
  String consultationSubmitted(String specialty, String status) {
    return '$specialty consultation $status.';
  }

  @override
  String bornYear(int year) {
    return 'Born $year';
  }

  @override
  String get demographicsMissing => 'Demographics not recorded';

  @override
  String ageYears(int age) {
    return 'Age $age';
  }

  @override
  String get ageSexMissing => 'Age/sex not recorded';

  @override
  String get recoveryPlanNone => 'Recovery plan: none';

  @override
  String recoveryPlanStatus(String status, String review) {
    return 'Recovery plan: $status / $review';
  }

  @override
  String get workflowReviewReady => 'Workflow: review ready';

  @override
  String get workflowSetupNeeded => 'Workflow: setup needed';

  @override
  String clinicalEventNamed(String title) {
    return 'Clinical Event: $title';
  }

  @override
  String get clinicalEventSetup => 'Clinical Event: setup needed';

  @override
  String eventResourceSummary(
    int prescriptions,
    int medications,
    int plans,
    int imaging,
    int notes,
  ) {
    return '$prescriptions prescription(s), $medications medication schedule item(s), $plans recovery plan(s), $imaging imaging asset(s), $notes note(s)';
  }

  @override
  String historyOverview(
    String allergies,
    String conditions,
    String visits,
    String diagnoses,
  ) {
    return 'Allergies: $allergies | Chronic diseases: $conditions | Visits: $visits | Diagnoses: $diagnoses';
  }

  @override
  String get noPrescriptionNote => 'No prescription note';

  @override
  String get notScheduled => 'Not scheduled';

  @override
  String get emptySectionDescription =>
      'No information has been recorded for this section yet.';

  @override
  String get uploadPrepared => 'Upload prepared';

  @override
  String uploadMetadata(String method) {
    return '$method metadata';
  }

  @override
  String objectKey(String key) {
    return 'Object key: $key';
  }

  @override
  String expires(String value) {
    return 'Expires: $value';
  }

  @override
  String get imagingUploadPrepared => 'Imaging upload prepared';

  @override
  String get imagingStatus => 'Imaging status';

  @override
  String reviewed(String date) {
    return 'Reviewed: $date';
  }

  @override
  String risk(String value) {
    return 'Risk: $value';
  }

  @override
  String assessmentScore(String score) {
    return 'Assessment score: $score';
  }

  @override
  String modelVersion(String version) {
    return 'Model: $version';
  }

  @override
  String get sessionEnded => 'Your session has ended. Please sign in again.';

  @override
  String get patientRecordUnavailable =>
      'This patient record is not available.';

  @override
  String get checkInformation => 'Check the entered information and try again.';

  @override
  String get unableToReachRetry =>
      'Unable to reach Dr. AI. Check your connection and try again.';

  @override
  String get dateUnknown => 'date unknown';

  @override
  String eventSaved(String title, String status) {
    return '$title saved as $status.';
  }

  @override
  String contentAsset(String type) {
    return '$type asset';
  }

  @override
  String get assessmentLimitationSynthetic =>
      'Assessment case result; no clinical inference was performed.';

  @override
  String get assessmentLimitationValidation =>
      'Not validated for diagnosis, treatment, or prognosis.';

  @override
  String get assessmentNextStep =>
      'Review the assessment case with a qualified clinician.';

  @override
  String get researchNotDiagnosis => 'Research assessment - not for diagnosis.';

  @override
  String get low => 'Low';

  @override
  String get moderate => 'Moderate';

  @override
  String get high => 'High';

  @override
  String get partial => 'Partial';

  @override
  String get insufficient => 'Insufficient';

  @override
  String get sms => 'SMS';

  @override
  String get specificHomeAddress => 'Specific home address';

  @override
  String get unableToRequestCode => 'Unable to request a code. Try again.';

  @override
  String get acceptTermsValidation => 'Accept the terms and policy.';

  @override
  String localDevelopmentCodeFilled(String message) {
    return '$message The local development code was filled automatically.';
  }

  @override
  String clinicianNamed(String name) {
    return 'Clinician: $name';
  }

  @override
  String medicationLinesLinked(int count, String event) {
    return '$count medication line(s) linked to $event.';
  }

  @override
  String get createdFromMedicationSchedule =>
      'Created from medication schedule context.';

  @override
  String get setupNeeded => 'Setup needed';

  @override
  String get secureInformationTitle => 'Your information is secure';

  @override
  String get secureInformationBody =>
      'We protect your data and comply with healthcare privacy regulations.';

  @override
  String get unableToChangePassword =>
      'Unable to change your password. Try again.';

  @override
  String get signedOut => 'You have signed out.';

  @override
  String get signedOutLocally =>
      'You have signed out locally. The server could not be reached.';

  @override
  String get incorrectCredentials => 'The email or password is incorrect.';

  @override
  String get registrationRoleUnavailable =>
      'Registration is not available for the selected role.';

  @override
  String get accountAlreadyExists =>
      'An account already exists for this contact.';

  @override
  String get registrationFieldsInvalid =>
      'Check the phone number, email, password, role, and verification code.';

  @override
  String get unableToCreateAccount =>
      'Unable to create the account. Check your connection and try again.';

  @override
  String prescriptionCount(int count) {
    return '$count prescription(s)';
  }

  @override
  String generatedReminderCount(int count) {
    return '$count generated reminder(s)';
  }

  @override
  String imagingAssetCount(int count) {
    return '$count imaging asset(s)';
  }

  @override
  String noteCount(int count) {
    return '$count note(s)';
  }

  @override
  String get patientIntakeSummary => 'Patient intake summary';

  @override
  String get imagingUploadFinalized => 'Imaging upload finalized.';

  @override
  String get imagingReviewUpdated => 'Imaging review status updated.';

  @override
  String get doctorContactsDescription =>
      'Private conversations with your connected patients and Dr. AI services.';

  @override
  String get systemReadOnlyDescription =>
      'Reminders and notifications · read-only';

  @override
  String get aiCareCompanion => 'AI care companion';

  @override
  String get myPatients => 'My patients';

  @override
  String get connectedPatientPrivateChat => 'Connected patient · private chat';

  @override
  String get connectPatientToChat =>
      'Connect a patient from Patient Management to start a private conversation.';

  @override
  String get noGroupChats => 'No group chats';

  @override
  String get groupChatsUnavailable =>
      'Group conversations are not available yet.';

  @override
  String get contactsLoadFailed => 'Contacts could not be loaded.';

  @override
  String get systemNotifications => 'System notifications';

  @override
  String get systemNotificationsSubtitle =>
      'Reminders and important account updates will appear here.';

  @override
  String get aiAssistant => 'Dr. AI assistant';

  @override
  String get aiAssistantSubtitle =>
      'Your AI care companion interface is ready for the next phase.';

  @override
  String get noSystemNotifications => 'No system notifications yet';

  @override
  String get systemReadOnlyNotice =>
      'This channel is read-only. You cannot send messages to the system.';

  @override
  String get aiAvailablePhase3 =>
      'AI conversations will become available in Phase 3';

  @override
  String get aiPlaceholderNotice =>
      'Generative replies stay unavailable until an evaluated DeepSeek release is activated. Deterministic safety and structured fallback remain active.';

  @override
  String get aiChatSubtitle =>
      'Practical health guidance with a clear source or general-AI label.';

  @override
  String get aiChatSafetyNotice =>
      'Dr. AI is an AI assistant and can make mistakes. Verify important details with authoritative sources or a doctor. It cannot confirm a diagnosis, replace emergency care, or change medication.';

  @override
  String get aiChatWelcome => 'What can I help you work through?';

  @override
  String get aiChatInputHint =>
      'Ask about symptoms, tests, medicines, or your care';

  @override
  String get aiChatSendFailed =>
      'The secure chat request could not be completed. Try again.';

  @override
  String get aiChatHistory => 'Conversation history';

  @override
  String get aiNewChat => 'New chat';

  @override
  String get aiPreviousChats => 'Previous chats';

  @override
  String get aiNoPreviousChats =>
      'Your health conversations will appear here after you send the first question.';

  @override
  String get aiHistoryRetentionNotice =>
      'Each conversation is kept for at least 60 days and is visible only in your account.';

  @override
  String get aiArchiveChat => 'Archive conversation';

  @override
  String get aiReopenChat => 'Reopen conversation';

  @override
  String get aiDeleteChat => 'Delete from my history';

  @override
  String get aiArchivedChat => 'Archived';

  @override
  String get aiChatLifecycleFailed =>
      'The conversation could not be updated. Try again.';

  @override
  String get retry => 'Retry';

  @override
  String get aiFollowUpQuestion => 'One detail would help';

  @override
  String get aiReviewMeasurementGuidance => 'Measure correctly';

  @override
  String get aiTrackMeasurements => 'Track readings';

  @override
  String get aiPrepareDoctorQuestions => 'Prepare doctor questions';

  @override
  String get aiPrepareSymptomSummary => 'Organize my symptoms';

  @override
  String get aiPrepareSymptomSummaryPrompt =>
      'Help me organize my symptoms, timeline, and key questions for a clinician.';

  @override
  String get aiMeasurementGuidancePrompt => 'How can I measure this correctly?';

  @override
  String get aiTrackMeasurementsPrompt =>
      'Help me make a simple record-tracking plan.';

  @override
  String get aiSuggestionEducation =>
      'What should I understand about recording blood pressure?';

  @override
  String get aiSuggestionSymptoms =>
      'I feel dizzy. What could explain it, and when should I seek care?';

  @override
  String get aiSuggestionMedication =>
      'What questions should I ask my doctor about a prescribed medicine?';

  @override
  String get aiSuggestionDoctor =>
      'Help me prepare questions for my next doctor visit.';

  @override
  String get aiSources => 'Reviewed sources';

  @override
  String get aiApprovedEvidenceBanner =>
      'Source-grounded answer — supported by reviewed Dr. AI passages.';

  @override
  String get aiGeneralKnowledgeBanner =>
      'General AI-generated information — no supporting Dr. AI source was found.';

  @override
  String get aiFixedSafetyBanner => 'Server-controlled safety response.';

  @override
  String get aiOpenOfficialSource => 'Open official source';

  @override
  String get aiImportantUncertainty => 'Important uncertainty';

  @override
  String get aiContextUsed => 'Personalized with your records';

  @override
  String get aiContextProfile => 'Profile basics';

  @override
  String get aiContextMeasurements => 'Health measurements';

  @override
  String get aiContextConditions => 'Recorded conditions';

  @override
  String get aiContextMedications => 'Medication information';

  @override
  String get aiContextClinicalEvents => 'Current care episode';

  @override
  String get aiContextRecoveryPlan => 'Recovery plan';

  @override
  String get aiContextFromProfile => 'Your profile records';

  @override
  String get aiContextPatientReported => 'Your reported history';

  @override
  String get aiContextDoctorRecord => 'Doctor\'s record';

  @override
  String get aiContextCurrentPrescription => 'Current prescription';

  @override
  String get aiContextMedicationSchedule => 'Current medication schedule';

  @override
  String get aiContextCurrentRecoveryPlan => 'Current recovery plan';

  @override
  String get aiContactDoctor => 'Contact my doctor';

  @override
  String get aiCall120Now => 'Call 120 now';

  @override
  String get privateCareConversation => 'Private care conversation';

  @override
  String get loadingConversation => 'Loading conversation…';

  @override
  String get conversationLoadFailed => 'This conversation could not be loaded.';

  @override
  String get messageSendFailed =>
      'Message could not be sent. Please try again.';

  @override
  String get writeMessage => 'Write a message';

  @override
  String get sendMessage => 'Send message';

  @override
  String get noPrivateMessages =>
      'No messages yet. Start a private conversation about ongoing care.';

  @override
  String get patientFallbackName => 'Patient';

  @override
  String get doctorFallbackName => 'Doctor';

  @override
  String get resources => 'Resources';

  @override
  String get medicalResources => 'Medical Resources';

  @override
  String get medicalResourcesSubtitle =>
      'Search reviewed clinical sources, verify provenance, and keep guidance for later.';

  @override
  String get resourceCatalogPreviewTitle => 'Authoritative source catalog';

  @override
  String get resourceCatalogPreviewBody =>
      '247 WHO fact sheets cover 240 official Chinese and 244 official English pages. Licensed text is stored under request 202609681 but remains outside doctor and patient retrieval pending review.';

  @override
  String get resourceSearchHint =>
      'Search medical resources in Chinese or English';

  @override
  String get resourceSearchTab => 'Search';

  @override
  String get savedResourcesTab => 'Saved';

  @override
  String get recentUpdatesTab => 'Recent updates';

  @override
  String get sourceRegistryTab => 'Source registry';

  @override
  String get resourceFilters => 'Filters';

  @override
  String get showFilters => 'Show filters';

  @override
  String get hideFilters => 'Hide filters';

  @override
  String get clearFilters => 'Clear filters';

  @override
  String get allOptions => 'All';

  @override
  String get topicFilter => 'Topic';

  @override
  String get documentTypeFilter => 'Document type';

  @override
  String get organizationFilter => 'Organization';

  @override
  String get jurisdictionFilter => 'Jurisdiction';

  @override
  String get originalLanguageFilter => 'Original language';

  @override
  String get intendedAudienceFilter => 'Intended audience';

  @override
  String get publicationReviewDateFilter => 'Publication / catalog date';

  @override
  String get versionStatusFilter => 'Current / superseded';

  @override
  String get topicRespiratoryCare => 'Respiratory care';

  @override
  String get topicCardiovascularCare => 'Cardiovascular care';

  @override
  String get topicDiabetesCare => 'Diabetes care';

  @override
  String get topicRehabilitation => 'Rehabilitation';

  @override
  String get documentClinicalGuide => 'Clinical guide';

  @override
  String get documentCarePathway => 'Care pathway';

  @override
  String get documentSafetyBulletin => 'Safety bulletin';

  @override
  String get documentPatientEducation => 'Patient education';

  @override
  String get organizationPrimaryCareCouncil => 'Primary Care Review Council';

  @override
  String get organizationMedicinesSafetyCenter =>
      'Medicines Safety Review Center';

  @override
  String get organizationRehabilitationCollaborative =>
      'Continuity and Rehabilitation Collaborative';

  @override
  String get jurisdictionMainlandChina => 'Mainland China';

  @override
  String get jurisdictionInternational => 'International';

  @override
  String get jurisdictionChina => 'China';

  @override
  String get audienceDoctors => 'Doctors';

  @override
  String get audienceDoctorsAndPatients => 'Doctors and patients';

  @override
  String get dateAny => 'Any date';

  @override
  String get datePast12Months => 'Past 12 months';

  @override
  String get datePast24Months => 'Past 24 months';

  @override
  String get statusCurrent => 'Current';

  @override
  String get statusSuperseded => 'Superseded';

  @override
  String get searchSuggestions => 'Suggested searches';

  @override
  String get resourceSuggestionOne => 'Hypertension follow-up';

  @override
  String get resourceSuggestionTwo => '呼吸道感染用药安全';

  @override
  String get resourceSuggestionThree => 'Diabetes sick-day education';

  @override
  String resourceResultCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count resources',
      one: '1 resource',
      zero: 'No resources',
    );
    return '$_temp0';
  }

  @override
  String get currentAndReviewed => 'Current and reviewed';

  @override
  String get supersededDoNotRely =>
      'Superseded—do not rely on as current guidance';

  @override
  String get rightsLimitedLinkOnly =>
      'Rights-limited—link only / no stored full text';

  @override
  String get doctorOnlyResource => 'Doctor-only';

  @override
  String get patientEducationApproved => 'Patient education approved';

  @override
  String get patientUseNotApproved => 'Not approved for patient use';

  @override
  String get publisherLabel => 'Publisher';

  @override
  String get sourceTypeLabel => 'Source type';

  @override
  String get publishedLabel => 'Published';

  @override
  String get lastMedicalReviewLabel => 'Last medical review';

  @override
  String get openSourceDetails => 'Open source details';

  @override
  String get saveResource => 'Save resource';

  @override
  String get removeSavedResource => 'Remove from saved';

  @override
  String get resourceSavedConfirmation => 'Resource saved.';

  @override
  String get resourceRemovedConfirmation => 'Resource removed from saved.';

  @override
  String get officialLocator => 'Official locator';

  @override
  String get provenance => 'Provenance';

  @override
  String get provenanceBody =>
      'Paired from the official WHO Chinese and English fact-sheet indexes on 14 July 2026. Only titles and locators are stored; source bodies remain on WHO\'s website.';

  @override
  String get versionHistory => 'Version history';

  @override
  String get versionCurrentEntry =>
      'Current reviewed version · active in this catalog';

  @override
  String get versionSupersededEntry =>
      'Previous version · retained only for traceability';

  @override
  String get relevantPassages => 'Relevant passages';

  @override
  String get relatedSources => 'Related sources';

  @override
  String get stableInternalReference => 'Stable internal reference';

  @override
  String get copyCitation => 'Copy citation';

  @override
  String get citationCopied => 'Citation copied.';

  @override
  String get copyOfficialLocator => 'Copy official locator';

  @override
  String get officialLocatorCopied => 'Official locator copied.';

  @override
  String resourceCitation(
    String title,
    String publisher,
    String year,
    String locator,
  ) {
    return '$title. $publisher. $year. $locator';
  }

  @override
  String get noResourceResultsTitle => 'No matching resources';

  @override
  String get noResourceResultsBody =>
      'Try another term or clear one or more filters.';

  @override
  String get noSavedResourcesTitle => 'No saved resources';

  @override
  String get noSavedResourcesBody =>
      'Save a source from Search to keep it available here.';

  @override
  String get noRecentUpdatesTitle => 'No recent updates';

  @override
  String get noRecentUpdatesBody =>
      'Reviewed source updates will appear here when available.';

  @override
  String get sourceRegistrySubtitle =>
      'Organizations represented in the current local catalog.';

  @override
  String get viewOrganizationSources => 'View sources';

  @override
  String reviewedSourceCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count catalog sources',
      one: '1 catalog source',
      zero: 'No catalog sources',
    );
    return '$_temp0';
  }

  @override
  String get loadingMedicalResources => 'Loading medical resources';

  @override
  String get resourceOfflineTitle => 'Resources are unavailable offline';

  @override
  String get resourceOfflineBody =>
      'Reconnect to verify current source status. Saved references remain listed without cached full text.';

  @override
  String get resourceServiceFailureTitle =>
      'Medical resources could not be loaded';

  @override
  String get resourceServiceFailureBody =>
      'The source service did not respond. No patient or query content was sent.';

  @override
  String get resourcePartialIndexTitle =>
      'Some reviewed sources are temporarily unavailable';

  @override
  String get resourcePartialIndexBody =>
      'Results may be incomplete while the current source index is restored.';

  @override
  String get resourceRetry => 'Retry';

  @override
  String resourceUpdatedLabel(String date) {
    return 'Catalog verified $date';
  }

  @override
  String get resourceTitleRespiratory =>
      'Safe antibiotic decisions for uncomplicated respiratory symptoms';

  @override
  String get resourcePassageRespiratory =>
      'Review symptom duration, severity, red flags, and likely viral features before considering antimicrobial treatment.';

  @override
  String get resourcePassageRespiratoryDetail =>
      'Document the clinical rationale and give a clear follow-up threshold when immediate antibiotics are not indicated.';

  @override
  String get resourceTitleHypertension =>
      'Primary-care follow-up pathway for stable hypertension';

  @override
  String get resourcePassageHypertension =>
      'Use consistent blood-pressure technique, review adherence and adverse effects, and agree on a practical follow-up interval.';

  @override
  String get resourcePassageHypertensionDetail =>
      'Escalate promptly when severe readings occur with concerning symptoms or evidence of acute organ injury.';

  @override
  String get resourceTitleDiabetes =>
      'Sick-day safety education for adults living with type 2 diabetes';

  @override
  String get resourcePassageDiabetes =>
      'Explain hydration, monitoring, warning signs, and when to contact a clinician without independently changing prescribed medicines.';

  @override
  String get resourcePassageDiabetesDetail =>
      'Patient-facing wording should be checked against the current prescription and the connected clinician\'s instructions.';

  @override
  String get resourceTitleStroke =>
      'Transition checklist after stroke rehabilitation discharge';

  @override
  String get resourcePassageStroke =>
      'This earlier checklist covered medication reconciliation, mobility support, caregiver communication, and follow-up ownership.';

  @override
  String get resourcePassageStrokeDetail =>
      'A newer transition standard replaces this version; retain it only to understand prior documentation.';

  @override
  String get resourceOfficialMetadataStatus => 'Official catalog metadata';

  @override
  String get rightsReviewPending => 'Rights review pending—official link only';

  @override
  String get resourceCatalogMetadataNote =>
      'Open either official WHO language page to read the source. Dr. AI stores only paired titles and locators; the content is not yet eligible for excerpts, embeddings, or AI retrieval.';

  @override
  String get catalogVerifiedLabel => 'Catalog verified';

  @override
  String get documentFactSheet => 'Fact sheet';

  @override
  String get documentClinicalGuideline => 'Clinical guideline';

  @override
  String get documentClinicalProtocol => 'Clinical protocol';

  @override
  String get documentPracticeGuideline => 'Practice guideline';

  @override
  String get documentGuidance => 'Guidance';

  @override
  String get organizationWorldHealthOrganization => 'World Health Organization';

  @override
  String get topicInfectiousDisease => 'Infectious diseases';

  @override
  String get topicChronicDisease => 'Chronic diseases';

  @override
  String get topicMaternalChildHealth => 'Maternal and child health';

  @override
  String get topicMentalHealth => 'Mental health';

  @override
  String get topicInjuryEmergency => 'Injury and emergency care';

  @override
  String get topicEnvironmentalHealth => 'Environmental health';

  @override
  String get topicNutritionLifestyle => 'Nutrition and lifestyle';

  @override
  String get topicHealthSystems => 'Health systems and safety';

  @override
  String get showMoreResources => 'Show 20 more resources';

  @override
  String get catalogUseStatus => 'Catalog and retrieval status';

  @override
  String get bilingualChineseEnglish => 'Bilingual: Chinese and English';

  @override
  String get languageChinese => 'Chinese';

  @override
  String get languageEnglish => 'English';

  @override
  String get organizationNationalHealthCommission =>
      'National Health Commission of China';

  @override
  String get chineseOfficialSource => 'Official Chinese page';

  @override
  String get englishOfficialSource => 'Official English page';

  @override
  String get copyEnglishOfficialLocator => 'Copy English official locator';

  @override
  String get englishOfficialLocatorCopied => 'English official locator copied.';

  @override
  String get close => 'Close';

  @override
  String get readOriginalText => 'Read original text';

  @override
  String get openOfficialSource => 'Open official source';

  @override
  String get originalEnglish => 'Original English';

  @override
  String get backToResources => 'Back to resources';

  @override
  String get resourceReaderTitle => 'Original document';

  @override
  String get resourceReaderReviewPending => 'Medical review pending';

  @override
  String get resourceReaderReviewApproved => 'Medical review approved';

  @override
  String get resourceReaderNotice =>
      'Publisher-authored original text for doctor reference. This foreign-jurisdiction document is not currently used for AI retrieval or patient-facing answers.';

  @override
  String get resourceReaderUnavailableTitle => 'Original text is not available';

  @override
  String get resourceReaderUnavailableBody =>
      'This source does not currently have stored text approved for display. Use the official publisher source instead.';

  @override
  String get resourceReaderLoadFailedTitle =>
      'The original document could not be loaded';

  @override
  String get resourceReaderLoadFailedBody =>
      'Check your connection and try again. No patient information was sent.';

  @override
  String get resourceReaderRetry => 'Retry';

  @override
  String get publicationDateLabel => 'Published';

  @override
  String get captureDateLabel => 'Captured';

  @override
  String get rightsAndAttribution => 'Rights and attribution';

  @override
  String get copyDocumentCitation => 'Copy document citation';

  @override
  String get reviewedChineseTranslation => 'Reviewed Chinese translation';

  @override
  String get unofficialAiTranslationNotice =>
      'This is an unofficial AI-generated Chinese translation that has completed medical and native-Chinese review. Use the publisher\'s English original for authoritative verification. The translation remains separate from retrieval approval.';

  @override
  String get financialDetails => 'Financial details';

  @override
  String get financialDetailsDescription =>
      'Financial information belongs to the billable service or product that produced it.';

  @override
  String get billableClinicalItem => 'This clinical item is billable';

  @override
  String get billableClinicalItemDescription =>
      'Leave this off when the record is clinical documentation only.';

  @override
  String get costStatus => 'Cost status';

  @override
  String get costPending => 'Cost pending';

  @override
  String get costEstimate => 'Estimate';

  @override
  String get costFinal => 'Final';

  @override
  String get currency => 'Currency';

  @override
  String get pendingCostSubmissionBlocked =>
      'You can save the clinical record now. It cannot be selected for a payer request until the full allocation is recorded.';

  @override
  String get totalCostCny => 'Total cost (CNY)';

  @override
  String get requestedFromPayerCny => 'Requested from payer (CNY)';

  @override
  String get expectedPatientResponsibilityCny =>
      'Expected patient responsibility (CNY)';

  @override
  String get financialAllocationNotice =>
      'Requested from payer is not a payment guarantee. Expected patient responsibility is not a final adjudicated obligation.';

  @override
  String get financialAllocationValidation =>
      'Enter non-negative amounts. Requested payer amount plus expected patient responsibility must equal the total.';

  @override
  String get imagingArtifactNotBillable =>
      'The uploaded image and report are clinical evidence, not a second charge. A distinct imaging-procedure record is required before procedure costs can be captured.';

  @override
  String get editConsultationCost => 'Complete or edit cost';

  @override
  String get saveConsultationCost => 'Save consultation cost';

  @override
  String get financialStatus => 'Financial status';

  @override
  String get noCostRecorded => 'No cost recorded';

  @override
  String estimatedCost(String amount) {
    return 'Estimated ¥$amount';
  }

  @override
  String finalCost(String amount) {
    return 'Final ¥$amount';
  }

  @override
  String get alreadySubmitted => 'Already submitted';

  @override
  String get addCost => 'Add cost';

  @override
  String get completeCost => 'Complete cost';

  @override
  String get editCost => 'Edit cost';

  @override
  String get saveCost => 'Save cost';

  @override
  String get imagingProcedure => 'Imaging procedure';

  @override
  String get imagingProcedures => 'Imaging procedures';

  @override
  String get imagingProcedureDescription =>
      'Create the ordered, scheduled, or performed service first. Scheduling and evidence remain separate from its financial companion.';

  @override
  String get clinicalDetails => 'Clinical details';

  @override
  String get procedureName => 'Procedure name';

  @override
  String get modality => 'Modality or procedure type';

  @override
  String get bodyRegion => 'Body region';

  @override
  String get clinicalIndication => 'Clinical indication or summary (optional)';

  @override
  String get schedulingServiceDetails => 'Scheduling and service details';

  @override
  String get scheduledDateTime => 'Scheduled date and time';

  @override
  String get performedDateTime => 'Performed date and time';

  @override
  String get createImagingProcedure => 'Create imaging procedure';

  @override
  String get updateImagingProcedure => 'Update imaging procedure';

  @override
  String get editClinicalService => 'Edit details';

  @override
  String imagingProcedureSaved(String name) {
    return '$name saved.';
  }

  @override
  String get noImagingProcedures =>
      'No imaging procedure has been created for this Clinical Event.';

  @override
  String get imagingEvidence => 'Imaging evidence and results';

  @override
  String get selectImagingProcedure => 'Imaging procedure';

  @override
  String get attachEvidence => 'Attach evidence';

  @override
  String evidenceFileCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count linked files',
      one: '1 linked file',
      zero: 'No linked files',
    );
    return '$_temp0';
  }

  @override
  String get imagingProcedureValidation =>
      'Enter a procedure name, modality, and body region. Scheduled services need a scheduled time; performed or completed services need a performed time.';

  @override
  String get accountRequestsTitle => 'Support, feedback & account requests';

  @override
  String get accountRequestsDescription =>
      'Submit and track a persisted request. Each receipt, status change, retry, and withdrawal remains attributable and visible here.';

  @override
  String get requestTypeLabel => 'Request type';

  @override
  String get supportRequestType => 'Support';

  @override
  String get feedbackRequestType => 'Product feedback';

  @override
  String get deletionRequestType => 'Account deletion review';

  @override
  String get requestSubjectLabel => 'Subject';

  @override
  String get requestSubjectValidation => 'Enter at least 3 characters.';

  @override
  String get requestMessageLabel => 'What do you need help with?';

  @override
  String get requestMessageValidation => 'Enter at least 8 characters.';

  @override
  String get requestPrivacyHelper =>
      'Do not include patient identities, contact details, clinical text, images, or confidential reviewer notes.';

  @override
  String get deletionRetentionBoundary =>
      'This submits a deletion review request; it does not immediately delete the account or regulated, security, financial, clinical, or audit-retained records. Authorized retention and identity checks still apply.';

  @override
  String get standardSupportRetentionBoundary =>
      'This support or feedback request is retained under the standard support record policy.';

  @override
  String get unknownRetentionBoundary =>
      'The applicable retention boundary is unavailable. Contact authorized support before relying on deletion or retention assumptions.';

  @override
  String get deletionRequestOnlyEffect =>
      'This is a deletion review request only; it does not immediately delete the account or retained records.';

  @override
  String get notDeletionRequestEffect =>
      'This request does not ask for account or record deletion.';

  @override
  String get unknownDeletionEffect =>
      'The deletion effect is unavailable. No immediate deletion should be assumed.';

  @override
  String get deletionBoundaryConfirmation =>
      'I understand that this is a review request and that applicable records may need to be retained.';

  @override
  String get submitRequest => 'Submit request';

  @override
  String get submittingRequest => 'Submitting';

  @override
  String get retryRequest => 'Retry safely';

  @override
  String requestSubmitted(String reference) {
    return 'Request $reference was submitted and persisted.';
  }

  @override
  String requestReplayConfirmed(String reference) {
    return 'Request $reference was already received. No duplicate request was created.';
  }

  @override
  String get requestConflict =>
      'This retry conflicts with a different saved request. Your text is preserved; review the updated history before retrying.';

  @override
  String get requestNetworkFailure =>
      'The request could not reach Dr. AI. Your text is preserved; retrying will not create a duplicate.';

  @override
  String get requestSafeContentFailure =>
      'Remove contact details, patient information, clinical text, or confidential notes, then retry.';

  @override
  String get requestAuthorizationFailure =>
      'This account is not authorized to use that request.';

  @override
  String get requestGenericFailure =>
      'The request could not be completed. Your text is preserved for a safe retry.';

  @override
  String get requestHistoryTitle => 'Request history';

  @override
  String get loadingAccountRequests => 'Loading account request history';

  @override
  String get loadAccountRequestsFailed =>
      'Request history is temporarily unavailable.';

  @override
  String get noAccountRequests =>
      'No support, feedback, or deletion requests have been submitted from this account.';

  @override
  String get startAccountRequest => 'Start a request';

  @override
  String requestReceipt(String reference) {
    return 'Receipt: $reference';
  }

  @override
  String get requestTimelineTitle => 'Status timeline';

  @override
  String get requestTimelineUnavailable =>
      'Detailed transition history is unavailable for this older request.';

  @override
  String get requestStatusQueued => 'Queued';

  @override
  String get requestStatusReviewing => 'Under review';

  @override
  String get requestStatusResolved => 'Resolved';

  @override
  String get requestStatusFailed => 'Needs attention';

  @override
  String get requestStatusCancelled => 'Withdrawn';

  @override
  String get requestStatusUnavailable => 'Status unavailable';

  @override
  String get requestNextQueued =>
      'Next: an authorized operator will review this request.';

  @override
  String get requestNextReviewing =>
      'Next: wait for the current review to finish. The request remains visible here.';

  @override
  String get requestNextResolved =>
      'This request is final. Review its timeline for the recorded outcome.';

  @override
  String get requestNextFailed =>
      'The request could not advance. Review the timeline and submit a new request if the next action remains unavailable.';

  @override
  String get requestNextCancelled =>
      'This request was withdrawn. Its receipt and audit history remain available.';

  @override
  String get requestNextUnavailable => 'No next action is currently available.';

  @override
  String get timelineRequestSubmitted => 'Request submitted';

  @override
  String get timelineRequestWithdrawn => 'Request withdrawn';

  @override
  String get timelineReviewStarted => 'Review started';

  @override
  String get timelineRequestResolved => 'Review completed';

  @override
  String get timelineActorYou => 'You';

  @override
  String get timelineActorAuthorizedOperator => 'Authorized operator';

  @override
  String get timelineActorSystem => 'Governed system';

  @override
  String get withdrawRequest => 'Withdraw request';

  @override
  String get withdrawRequestQuestion => 'Withdraw this request?';

  @override
  String get withdrawRequestDescription =>
      'Withdrawal stops further work where the contract permits it. The receipt and required audit history are retained.';

  @override
  String requestWithdrawn(String reference) {
    return 'Request $reference was withdrawn.';
  }

  @override
  String get withdrawalReplayConfirmed =>
      'This withdrawal was already received. No duplicate transition was created.';

  @override
  String get withdrawalConflict =>
      'The request changed before withdrawal. History was refreshed; review its current status.';

  @override
  String get signInForAccountRequests =>
      'Sign in and open Account to submit or track support, feedback, and deletion-review requests.';

  @override
  String get openAccountForRequests =>
      'Open Account to submit or track support, feedback, and deletion-review requests.';

  @override
  String get ceiTitle => 'Clinical Event intelligence';

  @override
  String get ceiPatientTitle => 'Your care and cost intelligence';

  @override
  String get ceiDoctorTitle => 'Clinical Event intelligence review';

  @override
  String get ceiPayerTitle => 'Authorized request intelligence';

  @override
  String get ceiLoading => 'Loading frozen Clinical Event intelligence';

  @override
  String get ceiUnavailableTitle => 'Intelligence is unavailable';

  @override
  String get ceiUnavailableBody =>
      'The request remains usable for ordinary clinical documentation, pending-cost work, clarification, and human review.';

  @override
  String get ceiEmptyTitle => 'No validated intelligence artifact yet';

  @override
  String get ceiEmptyPatientBody =>
      'Your request and care records remain available while the responsible care team reviews the next step.';

  @override
  String get ceiEmptyDoctorBody =>
      'Generate a bounded artifact when the governed release is available. Clinical and pending-cost work does not need to wait.';

  @override
  String get ceiEmptyPayerBody =>
      'Continue human review or request clarification. No AI artifact is required for a permitted decision.';

  @override
  String get ceiRefresh => 'Refresh';

  @override
  String get ceiGenerate => 'Generate intelligence';

  @override
  String get ceiGenerating => 'Generating intelligence';

  @override
  String get ceiArtifact => 'Immutable artifact';

  @override
  String get ceiSnapshot => 'Frozen snapshot';

  @override
  String get ceiHumanReview => 'Human review';

  @override
  String get ceiLocation => 'Deterministic location';

  @override
  String get ceiLocationSource =>
      'From Clinical Event, provider organization, and facility records—not IP or model inference.';

  @override
  String get ceiHumanOnlyNotice =>
      'AI support scores inform people only. They never approve, deny, reduce, delay, remove, or prescribe care.';

  @override
  String get ceiRequestedItems => 'Requested billable items';

  @override
  String get ceiRequestedItemsDescription =>
      'Every requested line appears exactly once and stays separate from predicted pathway items.';

  @override
  String get ceiRequested => 'Requested';

  @override
  String get ceiEstimated => 'Estimated range';

  @override
  String get ceiUsefulness => 'Usefulness';

  @override
  String get ceiConfidence => 'Confidence';

  @override
  String get ceiAiSupportScore => 'AI support score';

  @override
  String get ceiScoreVersion => 'Aggregation rule';

  @override
  String get ceiClinicalFit => 'Clinical fit';

  @override
  String get ceiEvidenceSupport => 'Evidence support';

  @override
  String get ceiTimingSequence => 'Timing / sequence';

  @override
  String get ceiQuantityIntensity => 'Quantity / intensity';

  @override
  String get ceiDocumentationCompleteness => 'Documentation completeness';

  @override
  String get ceiCostAlignment => 'Cost alignment';

  @override
  String get ceiTier => 'Provenance tier';

  @override
  String get ceiTier5Title => 'Model-only exploratory estimate';

  @override
  String get ceiTier5Body =>
      'No admitted price reference was available. This range is intentionally wide, cannot become authoritative pricing, and receives reduced or zero cost-alignment weight.';

  @override
  String get ceiSources => 'Admitted sources';

  @override
  String get ceiNoAdmittedPriceSource => 'No admitted price source';

  @override
  String get ceiSupportingFacts => 'Supporting facts';

  @override
  String get ceiContradictingFacts => 'Contradicting facts';

  @override
  String get ceiMissingInformation => 'Missing information';

  @override
  String get ceiAlternatives => 'Alternatives';

  @override
  String get ceiPredictedPathways => 'Plausible predicted pathways';

  @override
  String get ceiPredictedBoundary =>
      'Predicted pathway items are not doctor-requested items and do not change the request.';

  @override
  String get ceiTypicalPathway => 'Typical / first-line';

  @override
  String get ceiAlternativePathway => 'Reasonable alternative';

  @override
  String get ceiEscalatedPathway => 'Escalated';

  @override
  String get ceiMissingDocumentation => 'Missing-documentation assistant';

  @override
  String get ceiMissingDocumentationEmpty =>
      'No missing documentation was identified in this frozen artifact.';

  @override
  String get ceiCounterfactuals => 'Counterfactual comparisons';

  @override
  String get ceiCounterfactualBoundary =>
      'Plausible alternatives support discussion; they do not replace the doctor-requested items.';

  @override
  String get ceiCritic => 'Primary and critic';

  @override
  String get ceiAgreement => 'Agreement';

  @override
  String get ceiPartialDisagreement => 'Partial disagreement';

  @override
  String get ceiMaterialDisagreement => 'Material disagreement';

  @override
  String get ceiCriticUnavailable => 'Critic unavailable';

  @override
  String get ceiCriticUnavailableBody =>
      'The validated primary artifact remains visible; no agreement is implied.';

  @override
  String get ceiLineage => 'Immutable outcome lineage';

  @override
  String get ceiFallbackTitle => 'Structured fallback is active';

  @override
  String get ceiFallbackBody =>
      'Validated structured facts remain visible without generated role-specific prose.';

  @override
  String get ceiProviderUnavailableTitle => 'AI provider unavailable';

  @override
  String get ceiProviderUnavailableBody =>
      'This frozen artifact remains usable. Clinical documentation, pending-cost, clarification, and human-review workflows continue.';

  @override
  String get ceiAcknowledge => 'Acknowledge';

  @override
  String get ceiConcur => 'Concur';

  @override
  String get ceiDisagree => 'Disagree';

  @override
  String get ceiException => 'Record exception';

  @override
  String get ceiResponseRecorded =>
      'Clinician response appended. The artifact was not changed.';

  @override
  String get ceiResponseFailed =>
      'The response could not be appended. Manual clinical documentation remains available.';

  @override
  String get ceiRationale => 'Attributable rationale';

  @override
  String get ceiCancel => 'Cancel';

  @override
  String get ceiAppendResponse => 'Append response';

  @override
  String get ceiValidated => 'Validated';

  @override
  String get ceiValidatedWithUncertainty => 'Validated with uncertainty';

  @override
  String get ceiValidatedWithResults => 'Validated with recorded checks';

  @override
  String get ceiAwaitingHumanReview => 'Awaiting human review';

  @override
  String get ceiHumanReviewRequired => 'Human review required';

  @override
  String get ceiStronglySupported =>
      'Strongly supported by current information';

  @override
  String get ceiPlausible => 'Plausible';

  @override
  String get ceiMateriallyUncertain =>
      'Materially uncertain; clarification recommended';

  @override
  String get ceiWeaklySupported => 'Weakly supported; human review required';

  @override
  String get aiPossibleCauses => 'Possible causes';

  @override
  String get aiPossibleCausesNotDiagnosis =>
      'These are possibilities, not a confirmed diagnosis.';

  @override
  String get aiWarningSigns => 'Important warning signs';

  @override
  String get aiNextSteps => 'Practical next steps';
}
