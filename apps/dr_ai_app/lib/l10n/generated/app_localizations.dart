import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_zh.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('zh'),
  ];

  /// No description provided for @appName.
  ///
  /// In en, this message translates to:
  /// **'Dr. AI'**
  String get appName;

  /// No description provided for @dashboard.
  ///
  /// In en, this message translates to:
  /// **'Dashboard'**
  String get dashboard;

  /// No description provided for @patientManagement.
  ///
  /// In en, this message translates to:
  /// **'Patient Management'**
  String get patientManagement;

  /// No description provided for @account.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get account;

  /// No description provided for @contacts.
  ///
  /// In en, this message translates to:
  /// **'Contacts'**
  String get contacts;

  /// No description provided for @recoveryPlan.
  ///
  /// In en, this message translates to:
  /// **'Recovery Plan'**
  String get recoveryPlan;

  /// No description provided for @myAccount.
  ///
  /// In en, this message translates to:
  /// **'My Account'**
  String get myAccount;

  /// No description provided for @doctorWorkspace.
  ///
  /// In en, this message translates to:
  /// **'Doctor workspace'**
  String get doctorWorkspace;

  /// No description provided for @patientWorkspace.
  ///
  /// In en, this message translates to:
  /// **'Patient workspace'**
  String get patientWorkspace;

  /// No description provided for @restoringSession.
  ///
  /// In en, this message translates to:
  /// **'Restoring secure session'**
  String get restoringSession;

  /// No description provided for @signIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signIn;

  /// No description provided for @logIn.
  ///
  /// In en, this message translates to:
  /// **'Log in'**
  String get logIn;

  /// No description provided for @logOut.
  ///
  /// In en, this message translates to:
  /// **'Log out'**
  String get logOut;

  /// No description provided for @logOutQuestion.
  ///
  /// In en, this message translates to:
  /// **'Log out?'**
  String get logOutQuestion;

  /// No description provided for @logOutConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Confirm that you want to leave your Dr. AI account on this device.'**
  String get logOutConfirmation;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @saveChanges.
  ///
  /// In en, this message translates to:
  /// **'Save changes'**
  String get saveChanges;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @languagePreferences.
  ///
  /// In en, this message translates to:
  /// **'Language preferences'**
  String get languagePreferences;

  /// No description provided for @interfaceLanguage.
  ///
  /// In en, this message translates to:
  /// **'Interface language'**
  String get interfaceLanguage;

  /// No description provided for @interfaceLanguageDescription.
  ///
  /// In en, this message translates to:
  /// **'Choose the language used for labels, messages, and notifications on this device.'**
  String get interfaceLanguageDescription;

  /// No description provided for @english.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get english;

  /// No description provided for @simplifiedChinese.
  ///
  /// In en, this message translates to:
  /// **'简体中文'**
  String get simplifiedChinese;

  /// No description provided for @systemLanguage.
  ///
  /// In en, this message translates to:
  /// **'System language'**
  String get systemLanguage;

  /// No description provided for @doctorAccount.
  ///
  /// In en, this message translates to:
  /// **'Doctor Account'**
  String get doctorAccount;

  /// No description provided for @doctorAccountDescription.
  ///
  /// In en, this message translates to:
  /// **'Manage your profile, language preferences, and account settings.'**
  String get doctorAccountDescription;

  /// No description provided for @payerAccount.
  ///
  /// In en, this message translates to:
  /// **'Payer Account'**
  String get payerAccount;

  /// No description provided for @payerAccountDescription.
  ///
  /// In en, this message translates to:
  /// **'Manage your reviewer identity and account security while keeping organization authorization administrator-controlled.'**
  String get payerAccountDescription;

  /// No description provided for @loadingPayerAccount.
  ///
  /// In en, this message translates to:
  /// **'Loading payer account'**
  String get loadingPayerAccount;

  /// No description provided for @payerAccountLoadFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to load the payer account. Check your connection and try again.'**
  String get payerAccountLoadFailed;

  /// No description provided for @payerAccessUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Your payer organization access is unavailable. Contact an administrator if this is unexpected.'**
  String get payerAccessUnavailable;

  /// No description provided for @reviewerProfile.
  ///
  /// In en, this message translates to:
  /// **'Reviewer profile'**
  String get reviewerProfile;

  /// No description provided for @reviewerProfileDescription.
  ///
  /// In en, this message translates to:
  /// **'These personal identity fields belong to your reviewer account.'**
  String get reviewerProfileDescription;

  /// No description provided for @reviewerIdentityHint.
  ///
  /// In en, this message translates to:
  /// **'Use the name and professional title colleagues should recognize in the review workspace.'**
  String get reviewerIdentityHint;

  /// No description provided for @professionalTitle.
  ///
  /// In en, this message translates to:
  /// **'Professional title'**
  String get professionalTitle;

  /// No description provided for @payerTitleTooShort.
  ///
  /// In en, this message translates to:
  /// **'Use at least 2 characters.'**
  String get payerTitleTooShort;

  /// No description provided for @payerEmailDescription.
  ///
  /// In en, this message translates to:
  /// **'Used to sign in and for account communication. Leave empty to remove it.'**
  String get payerEmailDescription;

  /// No description provided for @payerProfileValidationFailed.
  ///
  /// In en, this message translates to:
  /// **'Check the reviewer name and professional title, then try again.'**
  String get payerProfileValidationFailed;

  /// No description provided for @organizationAndAccess.
  ///
  /// In en, this message translates to:
  /// **'Organization & access'**
  String get organizationAndAccess;

  /// No description provided for @organizationAndAccessDescription.
  ///
  /// In en, this message translates to:
  /// **'Your current institutional membership and review boundary.'**
  String get organizationAndAccessDescription;

  /// No description provided for @organizationAccessManaged.
  ///
  /// In en, this message translates to:
  /// **'These fields are read-only. Only an authorized administrator can change membership, scope, or verification.'**
  String get organizationAccessManaged;

  /// No description provided for @organizationType.
  ///
  /// In en, this message translates to:
  /// **'Organization type'**
  String get organizationType;

  /// No description provided for @jurisdiction.
  ///
  /// In en, this message translates to:
  /// **'Jurisdiction'**
  String get jurisdiction;

  /// No description provided for @membershipStatus.
  ///
  /// In en, this message translates to:
  /// **'Membership status'**
  String get membershipStatus;

  /// No description provided for @accessScope.
  ///
  /// In en, this message translates to:
  /// **'Access scope'**
  String get accessScope;

  /// No description provided for @organizationVerification.
  ///
  /// In en, this message translates to:
  /// **'Organization verification'**
  String get organizationVerification;

  /// No description provided for @publicPayer.
  ///
  /// In en, this message translates to:
  /// **'Public payer'**
  String get publicPayer;

  /// No description provided for @commercialPayer.
  ///
  /// In en, this message translates to:
  /// **'Commercial payer'**
  String get commercialPayer;

  /// No description provided for @observerOrganization.
  ///
  /// In en, this message translates to:
  /// **'Observer organization'**
  String get observerOrganization;

  /// No description provided for @activeMembership.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get activeMembership;

  /// No description provided for @suspended.
  ///
  /// In en, this message translates to:
  /// **'Suspended'**
  String get suspended;

  /// No description provided for @revoked.
  ///
  /// In en, this message translates to:
  /// **'Revoked'**
  String get revoked;

  /// No description provided for @syntheticReviewScope.
  ///
  /// In en, this message translates to:
  /// **'Synthetic review'**
  String get syntheticReviewScope;

  /// No description provided for @syntheticOnlyVerification.
  ///
  /// In en, this message translates to:
  /// **'Synthetic-only'**
  String get syntheticOnlyVerification;

  /// No description provided for @verified.
  ///
  /// In en, this message translates to:
  /// **'Verified'**
  String get verified;

  /// No description provided for @sessionActions.
  ///
  /// In en, this message translates to:
  /// **'Session actions'**
  String get sessionActions;

  /// No description provided for @payerSessionActionsDescription.
  ///
  /// In en, this message translates to:
  /// **'Sign out of this device when you have finished working with restricted review information.'**
  String get payerSessionActionsDescription;

  /// No description provided for @saving.
  ///
  /// In en, this message translates to:
  /// **'Saving'**
  String get saving;

  /// No description provided for @preferredLanguage.
  ///
  /// In en, this message translates to:
  /// **'Preferred language'**
  String get preferredLanguage;

  /// No description provided for @security.
  ///
  /// In en, this message translates to:
  /// **'Security'**
  String get security;

  /// No description provided for @changePassword.
  ///
  /// In en, this message translates to:
  /// **'Change password'**
  String get changePassword;

  /// No description provided for @changePasswordDescription.
  ///
  /// In en, this message translates to:
  /// **'Change your password securely. You will be signed out on all devices afterward.'**
  String get changePasswordDescription;

  /// No description provided for @currentPassword.
  ///
  /// In en, this message translates to:
  /// **'Current password'**
  String get currentPassword;

  /// No description provided for @newPassword.
  ///
  /// In en, this message translates to:
  /// **'New password'**
  String get newPassword;

  /// No description provided for @confirmNewPassword.
  ///
  /// In en, this message translates to:
  /// **'Confirm new password'**
  String get confirmNewPassword;

  /// No description provided for @updatePassword.
  ///
  /// In en, this message translates to:
  /// **'Update password'**
  String get updatePassword;

  /// No description provided for @showPasswords.
  ///
  /// In en, this message translates to:
  /// **'Show passwords'**
  String get showPasswords;

  /// No description provided for @hidePasswords.
  ///
  /// In en, this message translates to:
  /// **'Hide passwords'**
  String get hidePasswords;

  /// No description provided for @uploadAvatar.
  ///
  /// In en, this message translates to:
  /// **'Upload avatar'**
  String get uploadAvatar;

  /// No description provided for @editProfile.
  ///
  /// In en, this message translates to:
  /// **'Edit profile and medical history'**
  String get editProfile;

  /// No description provided for @patientId.
  ///
  /// In en, this message translates to:
  /// **'Patient ID: {id}'**
  String patientId(String id);

  /// No description provided for @birthDate.
  ///
  /// In en, this message translates to:
  /// **'Birth date'**
  String get birthDate;

  /// No description provided for @gender.
  ///
  /// In en, this message translates to:
  /// **'Gender'**
  String get gender;

  /// No description provided for @phone.
  ///
  /// In en, this message translates to:
  /// **'Phone'**
  String get phone;

  /// No description provided for @emergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Emergency contact'**
  String get emergencyContact;

  /// No description provided for @contactPreference.
  ///
  /// In en, this message translates to:
  /// **'Contact preference'**
  String get contactPreference;

  /// No description provided for @location.
  ///
  /// In en, this message translates to:
  /// **'Location'**
  String get location;

  /// No description provided for @height.
  ///
  /// In en, this message translates to:
  /// **'Height'**
  String get height;

  /// No description provided for @weight.
  ///
  /// In en, this message translates to:
  /// **'Weight'**
  String get weight;

  /// No description provided for @clinicalEvents.
  ///
  /// In en, this message translates to:
  /// **'Clinical Events'**
  String get clinicalEvents;

  /// No description provided for @medicalHistory.
  ///
  /// In en, this message translates to:
  /// **'Medical History'**
  String get medicalHistory;

  /// No description provided for @medicalRecordsAndImaging.
  ///
  /// In en, this message translates to:
  /// **'Medical Records And Imaging'**
  String get medicalRecordsAndImaging;

  /// No description provided for @medicationsAndPrescriptions.
  ///
  /// In en, this message translates to:
  /// **'Medications And Prescriptions'**
  String get medicationsAndPrescriptions;

  /// No description provided for @clinicalEventsEmpty.
  ///
  /// In en, this message translates to:
  /// **'Clinical Events appear after your doctor creates one.'**
  String get clinicalEventsEmpty;

  /// No description provided for @medicalRecords.
  ///
  /// In en, this message translates to:
  /// **'Medical records'**
  String get medicalRecords;

  /// No description provided for @imagingResults.
  ///
  /// In en, this message translates to:
  /// **'Imaging results'**
  String get imagingResults;

  /// No description provided for @today.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get today;

  /// No description provided for @medicalFee.
  ///
  /// In en, this message translates to:
  /// **'Medical Fee'**
  String get medicalFee;

  /// No description provided for @askDrAi.
  ///
  /// In en, this message translates to:
  /// **'Ask Dr. AI'**
  String get askDrAi;

  /// No description provided for @careRecords.
  ///
  /// In en, this message translates to:
  /// **'Care Records'**
  String get careRecords;

  /// No description provided for @privacyPolicy.
  ///
  /// In en, this message translates to:
  /// **'Privacy Policy'**
  String get privacyPolicy;

  /// No description provided for @termsOfService.
  ///
  /// In en, this message translates to:
  /// **'Terms of Service'**
  String get termsOfService;

  /// No description provided for @returnToDashboard.
  ///
  /// In en, this message translates to:
  /// **'Return to dashboard'**
  String get returnToDashboard;

  /// No description provided for @unauthorized.
  ///
  /// In en, this message translates to:
  /// **'This route is not available for your role.'**
  String get unauthorized;

  /// No description provided for @tryAgain.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get tryAgain;

  /// No description provided for @notRecorded.
  ///
  /// In en, this message translates to:
  /// **'Not recorded'**
  String get notRecorded;

  /// No description provided for @noneRecorded.
  ///
  /// In en, this message translates to:
  /// **'None recorded'**
  String get noneRecorded;

  /// No description provided for @yes.
  ///
  /// In en, this message translates to:
  /// **'Yes'**
  String get yes;

  /// No description provided for @no.
  ///
  /// In en, this message translates to:
  /// **'No'**
  String get no;

  /// No description provided for @done.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get done;

  /// No description provided for @next.
  ///
  /// In en, this message translates to:
  /// **'Next'**
  String get next;

  /// No description provided for @backToRegistration.
  ///
  /// In en, this message translates to:
  /// **'Back to registration'**
  String get backToRegistration;

  /// No description provided for @privacySupport.
  ///
  /// In en, this message translates to:
  /// **'Privacy, consent, and support'**
  String get privacySupport;

  /// No description provided for @accountSaved.
  ///
  /// In en, this message translates to:
  /// **'Account changes saved.'**
  String get accountSaved;

  /// No description provided for @accountSaveFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to save account changes. Check your connection and try again.'**
  String get accountSaveFailed;

  /// No description provided for @accountEmailAlreadyInUse.
  ///
  /// In en, this message translates to:
  /// **'This email is already linked to another account. Use a different email or leave this field empty.'**
  String get accountEmailAlreadyInUse;

  /// No description provided for @languageUpdated.
  ///
  /// In en, this message translates to:
  /// **'Interface language updated.'**
  String get languageUpdated;

  /// No description provided for @systemLanguageDescription.
  ///
  /// In en, this message translates to:
  /// **'Chinese and English follow your device setting. Other system languages use English.'**
  String get systemLanguageDescription;

  /// No description provided for @welcome.
  ///
  /// In en, this message translates to:
  /// **'Welcome to Dr. AI'**
  String get welcome;

  /// No description provided for @signInDescription.
  ///
  /// In en, this message translates to:
  /// **'Sign in with the phone number or email on your account.'**
  String get signInDescription;

  /// No description provided for @forgotPassword.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get forgotPassword;

  /// No description provided for @stagingNotice.
  ///
  /// In en, this message translates to:
  /// **'Staging environment: do not enter real patient data.'**
  String get stagingNotice;

  /// No description provided for @alreadyHaveAccount.
  ///
  /// In en, this message translates to:
  /// **'Already have an account?'**
  String get alreadyHaveAccount;

  /// No description provided for @doctorRegistration.
  ///
  /// In en, this message translates to:
  /// **'Doctor Registration'**
  String get doctorRegistration;

  /// No description provided for @payerRegistration.
  ///
  /// In en, this message translates to:
  /// **'Payer Registration'**
  String get payerRegistration;

  /// No description provided for @createAccount.
  ///
  /// In en, this message translates to:
  /// **'Create your account'**
  String get createAccount;

  /// No description provided for @createAccountDoctorDescription.
  ///
  /// In en, this message translates to:
  /// **'Create your account to join Dr. AI'**
  String get createAccountDoctorDescription;

  /// No description provided for @createAccountPayerDescription.
  ///
  /// In en, this message translates to:
  /// **'Create an authorized reviewer account for transparent care and cost review'**
  String get createAccountPayerDescription;

  /// No description provided for @createAccountPatientDescription.
  ///
  /// In en, this message translates to:
  /// **'Set up your account and continue to medical intake.'**
  String get createAccountPatientDescription;

  /// No description provided for @accountInformation.
  ///
  /// In en, this message translates to:
  /// **'Account Information'**
  String get accountInformation;

  /// No description provided for @personalInformation.
  ///
  /// In en, this message translates to:
  /// **'Personal Information'**
  String get personalInformation;

  /// No description provided for @hospitalInformation.
  ///
  /// In en, this message translates to:
  /// **'Hospital Information'**
  String get hospitalInformation;

  /// No description provided for @homeAddress.
  ///
  /// In en, this message translates to:
  /// **'Home Address'**
  String get homeAddress;

  /// No description provided for @code.
  ///
  /// In en, this message translates to:
  /// **'Code'**
  String get code;

  /// No description provided for @emailOrPhone.
  ///
  /// In en, this message translates to:
  /// **'Email or phone number'**
  String get emailOrPhone;

  /// No description provided for @phoneNumber.
  ///
  /// In en, this message translates to:
  /// **'Phone number'**
  String get phoneNumber;

  /// No description provided for @enterPhoneNumber.
  ///
  /// In en, this message translates to:
  /// **'Enter phone number'**
  String get enterPhoneNumber;

  /// No description provided for @emailOptional.
  ///
  /// In en, this message translates to:
  /// **'Email (optional)'**
  String get emailOptional;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @passwordGuidance.
  ///
  /// In en, this message translates to:
  /// **'8-20 characters. Letters, numbers, and symbols are okay.'**
  String get passwordGuidance;

  /// No description provided for @showPassword.
  ///
  /// In en, this message translates to:
  /// **'Show password'**
  String get showPassword;

  /// No description provided for @hidePassword.
  ///
  /// In en, this message translates to:
  /// **'Hide password'**
  String get hidePassword;

  /// No description provided for @confirmPassword.
  ///
  /// In en, this message translates to:
  /// **'Confirm password'**
  String get confirmPassword;

  /// No description provided for @verificationCode.
  ///
  /// In en, this message translates to:
  /// **'Verification code'**
  String get verificationCode;

  /// No description provided for @enterVerificationCode.
  ///
  /// In en, this message translates to:
  /// **'Enter 6-digit code'**
  String get enterVerificationCode;

  /// No description provided for @sendCode.
  ///
  /// In en, this message translates to:
  /// **'Send code'**
  String get sendCode;

  /// No description provided for @patient.
  ///
  /// In en, this message translates to:
  /// **'Patient'**
  String get patient;

  /// No description provided for @doctor.
  ///
  /// In en, this message translates to:
  /// **'Doctor'**
  String get doctor;

  /// No description provided for @payer.
  ///
  /// In en, this message translates to:
  /// **'Payer'**
  String get payer;

  /// No description provided for @organizationInformation.
  ///
  /// In en, this message translates to:
  /// **'Organization information'**
  String get organizationInformation;

  /// No description provided for @organizationName.
  ///
  /// In en, this message translates to:
  /// **'Organization name'**
  String get organizationName;

  /// No description provided for @firstName.
  ///
  /// In en, this message translates to:
  /// **'First name'**
  String get firstName;

  /// No description provided for @middleNameOptional.
  ///
  /// In en, this message translates to:
  /// **'Middle name (optional)'**
  String get middleNameOptional;

  /// No description provided for @lastName.
  ///
  /// In en, this message translates to:
  /// **'Last name'**
  String get lastName;

  /// No description provided for @dateOfBirth.
  ///
  /// In en, this message translates to:
  /// **'Date of birth'**
  String get dateOfBirth;

  /// No description provided for @selectDate.
  ///
  /// In en, this message translates to:
  /// **'Select date'**
  String get selectDate;

  /// No description provided for @countryRegion.
  ///
  /// In en, this message translates to:
  /// **'Country/Region'**
  String get countryRegion;

  /// No description provided for @province.
  ///
  /// In en, this message translates to:
  /// **'Province'**
  String get province;

  /// No description provided for @city.
  ///
  /// In en, this message translates to:
  /// **'City'**
  String get city;

  /// No description provided for @hospital.
  ///
  /// In en, this message translates to:
  /// **'Hospital'**
  String get hospital;

  /// No description provided for @hospitalEmpty.
  ///
  /// In en, this message translates to:
  /// **'No hospitals listed yet'**
  String get hospitalEmpty;

  /// No description provided for @hospitalMissing.
  ///
  /// In en, this message translates to:
  /// **'Can’t find your hospital?'**
  String get hospitalMissing;

  /// No description provided for @addHospital.
  ///
  /// In en, this message translates to:
  /// **'Add my hospital'**
  String get addHospital;

  /// No description provided for @hospitalName.
  ///
  /// In en, this message translates to:
  /// **'Hospital name'**
  String get hospitalName;

  /// No description provided for @termsConsentPrefix.
  ///
  /// In en, this message translates to:
  /// **'I have read and agree to the '**
  String get termsConsentPrefix;

  /// No description provided for @termsConsentJoiner.
  ///
  /// In en, this message translates to:
  /// **' and '**
  String get termsConsentJoiner;

  /// No description provided for @required.
  ///
  /// In en, this message translates to:
  /// **'Required.'**
  String get required;

  /// No description provided for @invalidAccount.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid email address or phone number.'**
  String get invalidAccount;

  /// No description provided for @invalidPhone.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid phone number.'**
  String get invalidPhone;

  /// No description provided for @phoneRequired.
  ///
  /// In en, this message translates to:
  /// **'Phone number is required.'**
  String get phoneRequired;

  /// No description provided for @invalidEmail.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid email address.'**
  String get invalidEmail;

  /// No description provided for @enterPassword.
  ///
  /// In en, this message translates to:
  /// **'Enter your password.'**
  String get enterPassword;

  /// No description provided for @passwordLength.
  ///
  /// In en, this message translates to:
  /// **'Use 8-20 characters.'**
  String get passwordLength;

  /// No description provided for @passwordMismatch.
  ///
  /// In en, this message translates to:
  /// **'Passwords do not match.'**
  String get passwordMismatch;

  /// No description provided for @enterSixDigitCode.
  ///
  /// In en, this message translates to:
  /// **'Enter the 6-digit code.'**
  String get enterSixDigitCode;

  /// No description provided for @enterPhoneFirst.
  ///
  /// In en, this message translates to:
  /// **'Enter your phone number first.'**
  String get enterPhoneFirst;

  /// No description provided for @alreadyHaveAccountLogIn.
  ///
  /// In en, this message translates to:
  /// **'Already have an account? Log in'**
  String get alreadyHaveAccountLogIn;

  /// No description provided for @createAnAccount.
  ///
  /// In en, this message translates to:
  /// **'Create an account'**
  String get createAnAccount;

  /// No description provided for @loading.
  ///
  /// In en, this message translates to:
  /// **'Loading'**
  String get loading;

  /// No description provided for @loadingContacts.
  ///
  /// In en, this message translates to:
  /// **'Loading your contacts'**
  String get loadingContacts;

  /// No description provided for @loadContactsFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to load your contacts. Try again.'**
  String get loadContactsFailed;

  /// No description provided for @contactsDescription.
  ///
  /// In en, this message translates to:
  /// **'Your care team and Dr. AI services are kept together here.'**
  String get contactsDescription;

  /// No description provided for @services.
  ///
  /// In en, this message translates to:
  /// **'Services'**
  String get services;

  /// No description provided for @system.
  ///
  /// In en, this message translates to:
  /// **'System'**
  String get system;

  /// No description provided for @systemContactDescription.
  ///
  /// In en, this message translates to:
  /// **'Care-plan, medication, fee, and account reminders'**
  String get systemContactDescription;

  /// No description provided for @official.
  ///
  /// In en, this message translates to:
  /// **'Official'**
  String get official;

  /// No description provided for @drAiContactDescription.
  ///
  /// In en, this message translates to:
  /// **'Educational AI chat will be available in Phase 3'**
  String get drAiContactDescription;

  /// No description provided for @comingLater.
  ///
  /// In en, this message translates to:
  /// **'Coming later'**
  String get comingLater;

  /// No description provided for @myDoctors.
  ///
  /// In en, this message translates to:
  /// **'My doctors'**
  String get myDoctors;

  /// No description provided for @groups.
  ///
  /// In en, this message translates to:
  /// **'Groups'**
  String get groups;

  /// No description provided for @careGroups.
  ///
  /// In en, this message translates to:
  /// **'Care groups'**
  String get careGroups;

  /// No description provided for @careGroupsDescription.
  ///
  /// In en, this message translates to:
  /// **'Group conversations and creation are planned for a later release'**
  String get careGroupsDescription;

  /// No description provided for @connected.
  ///
  /// In en, this message translates to:
  /// **'Connected'**
  String get connected;

  /// No description provided for @noDoctorConnected.
  ///
  /// In en, this message translates to:
  /// **'No doctor connected yet'**
  String get noDoctorConnected;

  /// No description provided for @sharePatientIdDoctor.
  ///
  /// In en, this message translates to:
  /// **'Share your patient ID with a doctor. Once they connect, they will appear here.'**
  String get sharePatientIdDoctor;

  /// No description provided for @placeholder.
  ///
  /// In en, this message translates to:
  /// **'PLACEHOLDER'**
  String get placeholder;

  /// No description provided for @privacyAndDataNotice.
  ///
  /// In en, this message translates to:
  /// **'Privacy and data notice'**
  String get privacyAndDataNotice;

  /// No description provided for @privacyNoticeBody.
  ///
  /// In en, this message translates to:
  /// **'This synthetic-development environment is governed by the account, consent, privacy, and support boundaries shown here. It is not authorized for real patient data or live clinical use.'**
  String get privacyNoticeBody;

  /// No description provided for @privacyNoData.
  ///
  /// In en, this message translates to:
  /// **'Do not enter names, contact information, raw records, images, or patient-owned clinical content in staging.'**
  String get privacyNoData;

  /// No description provided for @privacyBackendKeys.
  ///
  /// In en, this message translates to:
  /// **'DeepSeek is reached only through the FastAPI backend; keys never enter the Flutter app.'**
  String get privacyBackendKeys;

  /// No description provided for @privacyChatBoundary.
  ///
  /// In en, this message translates to:
  /// **'Chat is educational question preparation only and is blocked by red-flag safety checks before any LLM call.'**
  String get privacyChatBoundary;

  /// No description provided for @consentChecklist.
  ///
  /// In en, this message translates to:
  /// **'Consent checklist'**
  String get consentChecklist;

  /// No description provided for @consentStagingData.
  ///
  /// In en, this message translates to:
  /// **'I understand staging is not ready for real patient data.'**
  String get consentStagingData;

  /// No description provided for @consentNoEmergency.
  ///
  /// In en, this message translates to:
  /// **'I understand Dr. AI is not for emergencies, diagnosis, or treatment decisions.'**
  String get consentNoEmergency;

  /// No description provided for @consentNoRealData.
  ///
  /// In en, this message translates to:
  /// **'I understand I must not submit real patient data.'**
  String get consentNoRealData;

  /// No description provided for @consentReady.
  ///
  /// In en, this message translates to:
  /// **'Consent readiness prepared locally.'**
  String get consentReady;

  /// No description provided for @consentIncomplete.
  ///
  /// In en, this message translates to:
  /// **'Complete all items before using this staging surface.'**
  String get consentIncomplete;

  /// No description provided for @accountDeletionRequest.
  ///
  /// In en, this message translates to:
  /// **'Account deletion request'**
  String get accountDeletionRequest;

  /// No description provided for @deletionLocalOnly.
  ///
  /// In en, this message translates to:
  /// **'This local surface prepares a deletion request only. It does not delete data, alter accounts, or contact testers.'**
  String get deletionLocalOnly;

  /// No description provided for @deletionPrompt.
  ///
  /// In en, this message translates to:
  /// **'Type REQUEST ACCOUNT DELETION'**
  String get deletionPrompt;

  /// No description provided for @prepareRequest.
  ///
  /// In en, this message translates to:
  /// **'Prepare request'**
  String get prepareRequest;

  /// No description provided for @deletionPrepared.
  ///
  /// In en, this message translates to:
  /// **'Deletion request prepared locally. No account data was changed.'**
  String get deletionPrepared;

  /// No description provided for @feedbackForm.
  ///
  /// In en, this message translates to:
  /// **'Feedback form'**
  String get feedbackForm;

  /// No description provided for @feedbackPrivacy.
  ///
  /// In en, this message translates to:
  /// **'Do not include patient details, screenshots containing private data, or account secrets.'**
  String get feedbackPrivacy;

  /// No description provided for @feedbackDraft.
  ///
  /// In en, this message translates to:
  /// **'Feedback draft'**
  String get feedbackDraft;

  /// No description provided for @feedbackHint.
  ///
  /// In en, this message translates to:
  /// **'Describe the issue, device, browser, and account step.'**
  String get feedbackHint;

  /// No description provided for @prepareFeedback.
  ///
  /// In en, this message translates to:
  /// **'Prepare feedback draft'**
  String get prepareFeedback;

  /// No description provided for @feedbackPrepared.
  ///
  /// In en, this message translates to:
  /// **'Feedback draft prepared locally. No external message was sent.'**
  String get feedbackPrepared;

  /// No description provided for @knownLimitations.
  ///
  /// In en, this message translates to:
  /// **'Known limitations'**
  String get knownLimitations;

  /// No description provided for @limitationClinical.
  ///
  /// In en, this message translates to:
  /// **'Clinical model inference, billing, appointments, and video or voice consultation are not enabled yet.'**
  String get limitationClinical;

  /// No description provided for @limitationUpload.
  ///
  /// In en, this message translates to:
  /// **'Image upload completion and storage policy require a separate production approval path.'**
  String get limitationUpload;

  /// No description provided for @limitationRecovery.
  ///
  /// In en, this message translates to:
  /// **'Password reset, account recovery, and verified SMS/email delivery remain deferred.'**
  String get limitationRecovery;

  /// No description provided for @limitationRelease.
  ///
  /// In en, this message translates to:
  /// **'Any production deployment, store distribution, or account policy change requires explicit release approval.'**
  String get limitationRelease;

  /// No description provided for @privacySupportTitle.
  ///
  /// In en, this message translates to:
  /// **'Dr. AI privacy and support'**
  String get privacySupportTitle;

  /// No description provided for @privacySupportHero.
  ///
  /// In en, this message translates to:
  /// **'Privacy and support'**
  String get privacySupportHero;

  /// No description provided for @accountPolicyStaging.
  ///
  /// In en, this message translates to:
  /// **'Synthetic-development account and privacy boundaries for Dr. AI.'**
  String get accountPolicyStaging;

  /// No description provided for @accountPolicyUser.
  ///
  /// In en, this message translates to:
  /// **'Synthetic-development account and privacy boundaries for {name}.'**
  String accountPolicyUser(String name);

  /// No description provided for @stagingPolicyPlaceholder.
  ///
  /// In en, this message translates to:
  /// **'Synthetic-development policy'**
  String get stagingPolicyPlaceholder;

  /// No description provided for @passwordUpdated.
  ///
  /// In en, this message translates to:
  /// **'Password updated'**
  String get passwordUpdated;

  /// No description provided for @resetPassword.
  ///
  /// In en, this message translates to:
  /// **'Reset password'**
  String get resetPassword;

  /// No description provided for @passwordChangedSignIn.
  ///
  /// In en, this message translates to:
  /// **'Your password has been changed. Sign in again with your new password.'**
  String get passwordChangedSignIn;

  /// No description provided for @verifyPhoneReset.
  ///
  /// In en, this message translates to:
  /// **'Verify the phone number on your account. The code expires after 10 minutes.'**
  String get verifyPhoneReset;

  /// No description provided for @enterYourPhone.
  ///
  /// In en, this message translates to:
  /// **'Enter your phone number.'**
  String get enterYourPhone;

  /// No description provided for @sendVerificationCode.
  ///
  /// In en, this message translates to:
  /// **'Send verification code'**
  String get sendVerificationCode;

  /// No description provided for @sixDigitVerificationCode.
  ///
  /// In en, this message translates to:
  /// **'6-digit verification code'**
  String get sixDigitVerificationCode;

  /// No description provided for @backToSignIn.
  ///
  /// In en, this message translates to:
  /// **'Back to sign in'**
  String get backToSignIn;

  /// No description provided for @resetPasswordFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to reset your password. Try again.'**
  String get resetPasswordFailed;

  /// No description provided for @stepAccount.
  ///
  /// In en, this message translates to:
  /// **'1  Account'**
  String get stepAccount;

  /// No description provided for @stepProfile.
  ///
  /// In en, this message translates to:
  /// **'2  Profile'**
  String get stepProfile;

  /// No description provided for @stepLocation.
  ///
  /// In en, this message translates to:
  /// **'3  Location'**
  String get stepLocation;

  /// No description provided for @stepComplete.
  ///
  /// In en, this message translates to:
  /// **'4  Complete'**
  String get stepComplete;

  /// No description provided for @profile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// No description provided for @careHospitalDetails.
  ///
  /// In en, this message translates to:
  /// **'Care and hospital details'**
  String get careHospitalDetails;

  /// No description provided for @finishSetup.
  ///
  /// In en, this message translates to:
  /// **'Finish setup'**
  String get finishSetup;

  /// No description provided for @loadingAccount.
  ///
  /// In en, this message translates to:
  /// **'Loading your account'**
  String get loadingAccount;

  /// No description provided for @loadAccountFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to load your account. Try again.'**
  String get loadAccountFailed;

  /// No description provided for @loadingRecoveryPlans.
  ///
  /// In en, this message translates to:
  /// **'Loading recovery plans'**
  String get loadingRecoveryPlans;

  /// No description provided for @loadRecoveryPlansFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to load recovery plans. Try again.'**
  String get loadRecoveryPlansFailed;

  /// No description provided for @loadingProfile.
  ///
  /// In en, this message translates to:
  /// **'Loading your profile'**
  String get loadingProfile;

  /// No description provided for @loadProfileFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to load your profile. Try again.'**
  String get loadProfileFailed;

  /// No description provided for @prescriptions.
  ///
  /// In en, this message translates to:
  /// **'Prescriptions'**
  String get prescriptions;

  /// No description provided for @medicationReminders.
  ///
  /// In en, this message translates to:
  /// **'Medication reminders'**
  String get medicationReminders;

  /// No description provided for @noMedications.
  ///
  /// In en, this message translates to:
  /// **'No medications recorded yet.'**
  String get noMedications;

  /// No description provided for @records.
  ///
  /// In en, this message translates to:
  /// **'Records'**
  String get records;

  /// No description provided for @imaging.
  ///
  /// In en, this message translates to:
  /// **'Imaging'**
  String get imaging;

  /// No description provided for @available.
  ///
  /// In en, this message translates to:
  /// **'Available'**
  String get available;

  /// No description provided for @noneYet.
  ///
  /// In en, this message translates to:
  /// **'None yet'**
  String get noneYet;

  /// No description provided for @loadingActivePlan.
  ///
  /// In en, this message translates to:
  /// **'Loading active plan'**
  String get loadingActivePlan;

  /// No description provided for @loadActivePlanFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to load active recovery plan. Try again.'**
  String get loadActivePlanFailed;

  /// No description provided for @noActivePlan.
  ///
  /// In en, this message translates to:
  /// **'No active recovery plan yet. Your doctor can approve one from Patient Management.'**
  String get noActivePlan;

  /// No description provided for @planHistory.
  ///
  /// In en, this message translates to:
  /// **'Plan History'**
  String get planHistory;

  /// No description provided for @planHistoryEmpty.
  ///
  /// In en, this message translates to:
  /// **'Recovery plan history will appear here.'**
  String get planHistoryEmpty;

  /// No description provided for @completeHealthProfile.
  ///
  /// In en, this message translates to:
  /// **'Complete your health profile'**
  String get completeHealthProfile;

  /// No description provided for @medicalIntake.
  ///
  /// In en, this message translates to:
  /// **'Medical intake'**
  String get medicalIntake;

  /// No description provided for @medicalIntakeDescription.
  ///
  /// In en, this message translates to:
  /// **'Complete this once so your care team can review your profile before the first Clinical Event. Required fields are marked with *. Optional fields can be left blank.'**
  String get medicalIntakeDescription;

  /// No description provided for @aboutYou.
  ///
  /// In en, this message translates to:
  /// **'About you'**
  String get aboutYou;

  /// No description provided for @aboutYouDescription.
  ///
  /// In en, this message translates to:
  /// **'Enter the identity and contact information your care team should use.'**
  String get aboutYouDescription;

  /// No description provided for @fullNameRequired.
  ///
  /// In en, this message translates to:
  /// **'First and last name *'**
  String get fullNameRequired;

  /// No description provided for @homeAddressOptional.
  ///
  /// In en, this message translates to:
  /// **'Home address (optional)'**
  String get homeAddressOptional;

  /// No description provided for @streetBuilding.
  ///
  /// In en, this message translates to:
  /// **'Street and building information'**
  String get streetBuilding;

  /// No description provided for @unspecified.
  ///
  /// In en, this message translates to:
  /// **'Unspecified'**
  String get unspecified;

  /// No description provided for @female.
  ///
  /// In en, this message translates to:
  /// **'Female'**
  String get female;

  /// No description provided for @male.
  ///
  /// In en, this message translates to:
  /// **'Male'**
  String get male;

  /// No description provided for @other.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get other;

  /// No description provided for @emergencyContactOptional.
  ///
  /// In en, this message translates to:
  /// **'Emergency contact (optional)'**
  String get emergencyContactOptional;

  /// No description provided for @fullName.
  ///
  /// In en, this message translates to:
  /// **'Full name'**
  String get fullName;

  /// No description provided for @emergencyPhoneOptional.
  ///
  /// In en, this message translates to:
  /// **'Emergency phone (optional)'**
  String get emergencyPhoneOptional;

  /// No description provided for @includeCountryCode.
  ///
  /// In en, this message translates to:
  /// **'Include country code'**
  String get includeCountryCode;

  /// No description provided for @inApp.
  ///
  /// In en, this message translates to:
  /// **'In-app'**
  String get inApp;

  /// No description provided for @email.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @healthMeasurements.
  ///
  /// In en, this message translates to:
  /// **'Health measurements'**
  String get healthMeasurements;

  /// No description provided for @healthMeasurementsDescription.
  ///
  /// In en, this message translates to:
  /// **'Add your latest known measurements. Leave blood pressure blank if you do not know it.'**
  String get healthMeasurementsDescription;

  /// No description provided for @heightCmRequired.
  ///
  /// In en, this message translates to:
  /// **'Height (cm) *'**
  String get heightCmRequired;

  /// No description provided for @weightKgRequired.
  ///
  /// In en, this message translates to:
  /// **'Weight (kg) *'**
  String get weightKgRequired;

  /// No description provided for @bloodType.
  ///
  /// In en, this message translates to:
  /// **'Blood type'**
  String get bloodType;

  /// No description provided for @bloodPressure.
  ///
  /// In en, this message translates to:
  /// **'Blood pressure'**
  String get bloodPressure;

  /// No description provided for @unknown.
  ///
  /// In en, this message translates to:
  /// **'Unknown'**
  String get unknown;

  /// No description provided for @systolicBp.
  ///
  /// In en, this message translates to:
  /// **'Systolic BP'**
  String get systolicBp;

  /// No description provided for @diastolicBp.
  ///
  /// In en, this message translates to:
  /// **'Diastolic BP'**
  String get diastolicBp;

  /// No description provided for @smokingStatus.
  ///
  /// In en, this message translates to:
  /// **'Smoking status'**
  String get smokingStatus;

  /// No description provided for @never.
  ///
  /// In en, this message translates to:
  /// **'Never'**
  String get never;

  /// No description provided for @former.
  ///
  /// In en, this message translates to:
  /// **'Former'**
  String get former;

  /// No description provided for @current.
  ///
  /// In en, this message translates to:
  /// **'Current'**
  String get current;

  /// No description provided for @alcohol.
  ///
  /// In en, this message translates to:
  /// **'Alcohol'**
  String get alcohol;

  /// No description provided for @noneOrRare.
  ///
  /// In en, this message translates to:
  /// **'None or rare'**
  String get noneOrRare;

  /// No description provided for @occasional.
  ///
  /// In en, this message translates to:
  /// **'Occasional'**
  String get occasional;

  /// No description provided for @weekly.
  ///
  /// In en, this message translates to:
  /// **'Weekly'**
  String get weekly;

  /// No description provided for @daily.
  ///
  /// In en, this message translates to:
  /// **'Daily'**
  String get daily;

  /// No description provided for @allergiesConditions.
  ///
  /// In en, this message translates to:
  /// **'Allergies and health conditions'**
  String get allergiesConditions;

  /// No description provided for @conditionsDescription.
  ///
  /// In en, this message translates to:
  /// **'Choose Yes only when a condition applies. A details box will open for dates, treatment, or current status.'**
  String get conditionsDescription;

  /// No description provided for @hasAllergies.
  ///
  /// In en, this message translates to:
  /// **'Do you have any allergies?'**
  String get hasAllergies;

  /// No description provided for @allergy.
  ///
  /// In en, this message translates to:
  /// **'Allergy'**
  String get allergy;

  /// No description provided for @reactionOptional.
  ///
  /// In en, this message translates to:
  /// **'Reaction (optional)'**
  String get reactionOptional;

  /// No description provided for @hasChronicCondition.
  ///
  /// In en, this message translates to:
  /// **'Do you have hereditary or long-term medical conditions?'**
  String get hasChronicCondition;

  /// No description provided for @condition.
  ///
  /// In en, this message translates to:
  /// **'Condition'**
  String get condition;

  /// No description provided for @notesOptional.
  ///
  /// In en, this message translates to:
  /// **'Notes (optional)'**
  String get notesOptional;

  /// No description provided for @diagnosisTreatmentHint.
  ///
  /// In en, this message translates to:
  /// **'Diagnosis date, treatment, or current status'**
  String get diagnosisTreatmentHint;

  /// No description provided for @heartHistory.
  ///
  /// In en, this message translates to:
  /// **'Heart or blood vessel history'**
  String get heartHistory;

  /// No description provided for @heartHistoryDescription.
  ///
  /// In en, this message translates to:
  /// **'Heart attack, stroke, irregular heartbeat, blood clots, or heart failure.'**
  String get heartHistoryDescription;

  /// No description provided for @endocrineHistory.
  ///
  /// In en, this message translates to:
  /// **'Diabetes, thyroid, or bone health'**
  String get endocrineHistory;

  /// No description provided for @endocrineHistoryDescription.
  ///
  /// In en, this message translates to:
  /// **'Diabetes including gestational diabetes, thyroid disorders, or osteoporosis.'**
  String get endocrineHistoryDescription;

  /// No description provided for @neuroHistory.
  ///
  /// In en, this message translates to:
  /// **'Brain, mood, or nervous system'**
  String get neuroHistory;

  /// No description provided for @neuroHistoryDescription.
  ///
  /// In en, this message translates to:
  /// **'Depression, severe anxiety, seizures, epilepsy, bipolar disorder, or chronic migraines.'**
  String get neuroHistoryDescription;

  /// No description provided for @digestiveHistory.
  ///
  /// In en, this message translates to:
  /// **'Stomach, bowel, or liver history'**
  String get digestiveHistory;

  /// No description provided for @digestiveHistoryDescription.
  ///
  /// In en, this message translates to:
  /// **'Ulcers, Crohn disease, ulcerative colitis, irritable bowel disease, hepatitis, or cirrhosis.'**
  String get digestiveHistoryDescription;

  /// No description provided for @respiratoryHistory.
  ///
  /// In en, this message translates to:
  /// **'Lung or breathing history'**
  String get respiratoryHistory;

  /// No description provided for @respiratoryHistoryDescription.
  ///
  /// In en, this message translates to:
  /// **'Asthma, COPD, emphysema, or severe pneumonia requiring hospitalization.'**
  String get respiratoryHistoryDescription;

  /// No description provided for @kidneyHistory.
  ///
  /// In en, this message translates to:
  /// **'Kidney or urinary history'**
  String get kidneyHistory;

  /// No description provided for @kidneyHistoryDescription.
  ///
  /// In en, this message translates to:
  /// **'Chronic kidney disease, reduced kidney function, or severe kidney stones.'**
  String get kidneyHistoryDescription;

  /// No description provided for @cancerHistory.
  ///
  /// In en, this message translates to:
  /// **'Cancer or active treatment'**
  String get cancerHistory;

  /// No description provided for @cancerHistoryDescription.
  ///
  /// In en, this message translates to:
  /// **'Any cancer including skin cancer, chemotherapy, radiation, or immunotherapy.'**
  String get cancerHistoryDescription;

  /// No description provided for @medicalBackground.
  ///
  /// In en, this message translates to:
  /// **'Medical background and daily life'**
  String get medicalBackground;

  /// No description provided for @medicalBackgroundDescription.
  ///
  /// In en, this message translates to:
  /// **'Use short, plain-language summaries. You can update this information later from My Account.'**
  String get medicalBackgroundDescription;

  /// No description provided for @currentMedicationsOptional.
  ///
  /// In en, this message translates to:
  /// **'Current medications and supplements (optional)'**
  String get currentMedicationsOptional;

  /// No description provided for @medicationHint.
  ///
  /// In en, this message translates to:
  /// **'Name, dose, and how often you take each one'**
  String get medicationHint;

  /// No description provided for @surgeriesOptional.
  ///
  /// In en, this message translates to:
  /// **'Past surgeries or hospitalizations (optional)'**
  String get surgeriesOptional;

  /// No description provided for @surgeriesHint.
  ///
  /// In en, this message translates to:
  /// **'Procedure or reason, year, and hospital if known'**
  String get surgeriesHint;

  /// No description provided for @familyHistoryOptional.
  ///
  /// In en, this message translates to:
  /// **'Family medical history (optional)'**
  String get familyHistoryOptional;

  /// No description provided for @familyHistoryHint.
  ///
  /// In en, this message translates to:
  /// **'Condition and relationship, such as parent or sibling'**
  String get familyHistoryHint;

  /// No description provided for @lifestyleOptional.
  ///
  /// In en, this message translates to:
  /// **'Exercise and sleep notes (optional)'**
  String get lifestyleOptional;

  /// No description provided for @lifestyleHint.
  ///
  /// In en, this message translates to:
  /// **'Typical weekly activity and sleep pattern'**
  String get lifestyleHint;

  /// No description provided for @pregnancyStatus.
  ///
  /// In en, this message translates to:
  /// **'Pregnancy status'**
  String get pregnancyStatus;

  /// No description provided for @preferNotToSay.
  ///
  /// In en, this message translates to:
  /// **'Prefer not to say'**
  String get preferNotToSay;

  /// No description provided for @notApplicable.
  ///
  /// In en, this message translates to:
  /// **'Not applicable'**
  String get notApplicable;

  /// No description provided for @unsure.
  ///
  /// In en, this message translates to:
  /// **'Unsure'**
  String get unsure;

  /// No description provided for @saveProfileFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to save your profile. Check the form and try again.'**
  String get saveProfileFailed;

  /// No description provided for @useNumbersOnly.
  ///
  /// In en, this message translates to:
  /// **'Use numbers only.'**
  String get useNumbersOnly;

  /// No description provided for @useDateFormat.
  ///
  /// In en, this message translates to:
  /// **'Use YYYY-MM-DD.'**
  String get useDateFormat;

  /// No description provided for @provinceState.
  ///
  /// In en, this message translates to:
  /// **'Province / State'**
  String get provinceState;

  /// No description provided for @loadingTodayTasks.
  ///
  /// In en, this message translates to:
  /// **'Loading today recovery tasks'**
  String get loadingTodayTasks;

  /// No description provided for @loadTodayTasksFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to load today recovery tasks. Try again.'**
  String get loadTodayTasksFailed;

  /// No description provided for @preparingNotifications.
  ///
  /// In en, this message translates to:
  /// **'Preparing local medication notification shell...'**
  String get preparingNotifications;

  /// No description provided for @notificationsUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Local medication notification shell is unavailable.'**
  String get notificationsUnavailable;

  /// No description provided for @noTodayTasks.
  ///
  /// In en, this message translates to:
  /// **'No active recovery tasks for today.'**
  String get noTodayTasks;

  /// No description provided for @taskSyncFailed.
  ///
  /// In en, this message translates to:
  /// **'Completion could not sync. Your local tap is still visible; try again when the connection recovers.'**
  String get taskSyncFailed;

  /// No description provided for @loadingMedicationReminders.
  ///
  /// In en, this message translates to:
  /// **'Loading medication reminders...'**
  String get loadingMedicationReminders;

  /// No description provided for @medicationRemindersUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Medication reminders unavailable.'**
  String get medicationRemindersUnavailable;

  /// No description provided for @noMedicationReminders.
  ///
  /// In en, this message translates to:
  /// **'No medication reminders due.'**
  String get noMedicationReminders;

  /// No description provided for @refill.
  ///
  /// In en, this message translates to:
  /// **'Refill'**
  String get refill;

  /// No description provided for @educationalDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'Educational information only - not medical advice.'**
  String get educationalDisclaimer;

  /// No description provided for @prepareQuestion.
  ///
  /// In en, this message translates to:
  /// **'Prepare a question for your clinician'**
  String get prepareQuestion;

  /// No description provided for @sendEducationalQuestion.
  ///
  /// In en, this message translates to:
  /// **'Send educational question'**
  String get sendEducationalQuestion;

  /// No description provided for @streamingResponse.
  ///
  /// In en, this message translates to:
  /// **'Streaming response...'**
  String get streamingResponse;

  /// No description provided for @fallbackReason.
  ///
  /// In en, this message translates to:
  /// **'Fallback: {reason}'**
  String fallbackReason(String reason);

  /// No description provided for @exercise.
  ///
  /// In en, this message translates to:
  /// **'Exercise'**
  String get exercise;

  /// No description provided for @diet.
  ///
  /// In en, this message translates to:
  /// **'Diet'**
  String get diet;

  /// No description provided for @followUp.
  ///
  /// In en, this message translates to:
  /// **'Follow-up'**
  String get followUp;

  /// No description provided for @task.
  ///
  /// In en, this message translates to:
  /// **'Task'**
  String get task;

  /// No description provided for @noClinicalEventUpdate.
  ///
  /// In en, this message translates to:
  /// **'No Clinical Event available for patient update'**
  String get noClinicalEventUpdate;

  /// No description provided for @updateEvent.
  ///
  /// In en, this message translates to:
  /// **'Update: {title}'**
  String updateEvent(String title);

  /// No description provided for @latestPatientUpdate.
  ///
  /// In en, this message translates to:
  /// **'Latest patient update: {summary}'**
  String latestPatientUpdate(String summary);

  /// No description provided for @updateType.
  ///
  /// In en, this message translates to:
  /// **'Update type'**
  String get updateType;

  /// No description provided for @generalUpdate.
  ///
  /// In en, this message translates to:
  /// **'General update'**
  String get generalUpdate;

  /// No description provided for @symptomUpdate.
  ///
  /// In en, this message translates to:
  /// **'Symptom update'**
  String get symptomUpdate;

  /// No description provided for @medicationNote.
  ///
  /// In en, this message translates to:
  /// **'Medication note'**
  String get medicationNote;

  /// No description provided for @recoveryCheckIn.
  ///
  /// In en, this message translates to:
  /// **'Recovery check-in'**
  String get recoveryCheckIn;

  /// No description provided for @selfReportedUpdate.
  ///
  /// In en, this message translates to:
  /// **'Self-reported update'**
  String get selfReportedUpdate;

  /// No description provided for @updateSubmitted.
  ///
  /// In en, this message translates to:
  /// **'Update submitted: {type}'**
  String updateSubmitted(String type);

  /// No description provided for @sendUpdate.
  ///
  /// In en, this message translates to:
  /// **'Send update'**
  String get sendUpdate;

  /// No description provided for @enterUpdate.
  ///
  /// In en, this message translates to:
  /// **'Enter a short update first.'**
  String get enterUpdate;

  /// No description provided for @paymentUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Payment unavailable'**
  String get paymentUnavailable;

  /// No description provided for @payNowUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Pay now unavailable'**
  String get payNowUnavailable;

  /// No description provided for @paymentDescription.
  ///
  /// In en, this message translates to:
  /// **'You can review fee status here. Online payment is not enabled yet.'**
  String get paymentDescription;

  /// No description provided for @chatRateLimited.
  ///
  /// In en, this message translates to:
  /// **'Educational chat is temporarily rate limited.'**
  String get chatRateLimited;

  /// No description provided for @unableToReach.
  ///
  /// In en, this message translates to:
  /// **'Unable to reach Dr. AI.'**
  String get unableToReach;

  /// No description provided for @conditionDetailsHint.
  ///
  /// In en, this message translates to:
  /// **'Add diagnosis, date, treatment, or current status'**
  String get conditionDetailsHint;

  /// No description provided for @china.
  ///
  /// In en, this message translates to:
  /// **'China'**
  String get china;

  /// No description provided for @guangdong.
  ///
  /// In en, this message translates to:
  /// **'Guangdong'**
  String get guangdong;

  /// No description provided for @shenzhen.
  ///
  /// In en, this message translates to:
  /// **'Shenzhen'**
  String get shenzhen;

  /// No description provided for @active.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get active;

  /// No description provided for @paused.
  ///
  /// In en, this message translates to:
  /// **'Paused'**
  String get paused;

  /// No description provided for @stopped.
  ///
  /// In en, this message translates to:
  /// **'Stopped'**
  String get stopped;

  /// No description provided for @monitoring.
  ///
  /// In en, this message translates to:
  /// **'Monitoring'**
  String get monitoring;

  /// No description provided for @resolved.
  ///
  /// In en, this message translates to:
  /// **'Resolved'**
  String get resolved;

  /// No description provided for @draft.
  ///
  /// In en, this message translates to:
  /// **'Draft'**
  String get draft;

  /// No description provided for @pendingReview.
  ///
  /// In en, this message translates to:
  /// **'Pending review'**
  String get pendingReview;

  /// No description provided for @approved.
  ///
  /// In en, this message translates to:
  /// **'Approved'**
  String get approved;

  /// No description provided for @completed.
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get completed;

  /// No description provided for @pending.
  ///
  /// In en, this message translates to:
  /// **'Pending'**
  String get pending;

  /// No description provided for @completeProfileSetup.
  ///
  /// In en, this message translates to:
  /// **'Complete profile setup'**
  String get completeProfileSetup;

  /// No description provided for @sharePatientCode.
  ///
  /// In en, this message translates to:
  /// **'Share your patient code'**
  String get sharePatientCode;

  /// No description provided for @waitDoctorConnect.
  ///
  /// In en, this message translates to:
  /// **'Wait for your doctor to connect'**
  String get waitDoctorConnect;

  /// No description provided for @after.
  ///
  /// In en, this message translates to:
  /// **'After'**
  String get after;

  /// No description provided for @reviewMedicalHistory.
  ///
  /// In en, this message translates to:
  /// **'Review your medical history'**
  String get reviewMedicalHistory;

  /// No description provided for @confirmContactPreferences.
  ///
  /// In en, this message translates to:
  /// **'Confirm contact preferences'**
  String get confirmContactPreferences;

  /// No description provided for @prepareDoctorQuestions.
  ///
  /// In en, this message translates to:
  /// **'Prepare questions for your doctor'**
  String get prepareDoctorQuestions;

  /// No description provided for @followCareTasks.
  ///
  /// In en, this message translates to:
  /// **'Follow doctor-created care tasks'**
  String get followCareTasks;

  /// No description provided for @trackRecovery.
  ///
  /// In en, this message translates to:
  /// **'Track recovery progress'**
  String get trackRecovery;

  /// No description provided for @checkMedicationsImaging.
  ///
  /// In en, this message translates to:
  /// **'Check medications and imaging results'**
  String get checkMedicationsImaging;

  /// No description provided for @doctorNotConnected.
  ///
  /// In en, this message translates to:
  /// **'Doctor not connected'**
  String get doctorNotConnected;

  /// No description provided for @sharePatientCodeAction.
  ///
  /// In en, this message translates to:
  /// **'Share patient code'**
  String get sharePatientCodeAction;

  /// No description provided for @careAfterConnection.
  ///
  /// In en, this message translates to:
  /// **'Care details appear after connection.'**
  String get careAfterConnection;

  /// No description provided for @consultation.
  ///
  /// In en, this message translates to:
  /// **'Consultation'**
  String get consultation;

  /// No description provided for @medicalRecord.
  ///
  /// In en, this message translates to:
  /// **'Medical record'**
  String get medicalRecord;

  /// No description provided for @medication.
  ///
  /// In en, this message translates to:
  /// **'Medication'**
  String get medication;

  /// No description provided for @allergiesSummary.
  ///
  /// In en, this message translates to:
  /// **'Allergies: {value}'**
  String allergiesSummary(String value);

  /// No description provided for @chronicDiseasesSummary.
  ///
  /// In en, this message translates to:
  /// **'Chronic diseases: {value}'**
  String chronicDiseasesSummary(String value);

  /// No description provided for @visitHistorySummary.
  ///
  /// In en, this message translates to:
  /// **'Visit history: {count}'**
  String visitHistorySummary(int count);

  /// No description provided for @diagnosesSummary.
  ///
  /// In en, this message translates to:
  /// **'Diagnoses: {value}'**
  String diagnosesSummary(String value);

  /// No description provided for @loadingDoctorAccount.
  ///
  /// In en, this message translates to:
  /// **'Loading doctor account'**
  String get loadingDoctorAccount;

  /// No description provided for @noAccountChanges.
  ///
  /// In en, this message translates to:
  /// **'No account changes to save.'**
  String get noAccountChanges;

  /// No description provided for @doctorIdentityRequired.
  ///
  /// In en, this message translates to:
  /// **'Display name and title are required before saving.'**
  String get doctorIdentityRequired;

  /// No description provided for @verificationStatus.
  ///
  /// In en, this message translates to:
  /// **'Verification status'**
  String get verificationStatus;

  /// No description provided for @activeDoctorAccount.
  ///
  /// In en, this message translates to:
  /// **'Active doctor account'**
  String get activeDoctorAccount;

  /// No description provided for @inactiveDoctorAccount.
  ///
  /// In en, this message translates to:
  /// **'Not active'**
  String get inactiveDoctorAccount;

  /// No description provided for @doctorLastOnline.
  ///
  /// In en, this message translates to:
  /// **'Not active · Last online {date}'**
  String doctorLastOnline(String date);

  /// No description provided for @accountContact.
  ///
  /// In en, this message translates to:
  /// **'Account contact'**
  String get accountContact;

  /// No description provided for @clinicalIdentity.
  ///
  /// In en, this message translates to:
  /// **'Clinical identity'**
  String get clinicalIdentity;

  /// No description provided for @displayName.
  ///
  /// In en, this message translates to:
  /// **'Display name'**
  String get displayName;

  /// No description provided for @specialty.
  ///
  /// In en, this message translates to:
  /// **'Specialty'**
  String get specialty;

  /// No description provided for @title.
  ///
  /// In en, this message translates to:
  /// **'Title'**
  String get title;

  /// No description provided for @hospitalLocation.
  ///
  /// In en, this message translates to:
  /// **'Hospital & location'**
  String get hospitalLocation;

  /// No description provided for @hospitalManaged.
  ///
  /// In en, this message translates to:
  /// **'Hospital (managed by administrator)'**
  String get hospitalManaged;

  /// No description provided for @department.
  ///
  /// In en, this message translates to:
  /// **'Department'**
  String get department;

  /// No description provided for @contact.
  ///
  /// In en, this message translates to:
  /// **'Contact'**
  String get contact;

  /// No description provided for @hospitalProfilePending.
  ///
  /// In en, this message translates to:
  /// **'Hospital profile pending'**
  String get hospitalProfilePending;

  /// No description provided for @completeHospitalDetails.
  ///
  /// In en, this message translates to:
  /// **'Complete hospital details'**
  String get completeHospitalDetails;

  /// No description provided for @careWorkspaceReady.
  ///
  /// In en, this message translates to:
  /// **'Your care workspace is ready for patient-code connection.'**
  String get careWorkspaceReady;

  /// No description provided for @doctorProfile.
  ///
  /// In en, this message translates to:
  /// **'Doctor profile'**
  String get doctorProfile;

  /// No description provided for @clinician.
  ///
  /// In en, this message translates to:
  /// **'Clinician'**
  String get clinician;

  /// No description provided for @connectPatientsEpisodes.
  ///
  /// In en, this message translates to:
  /// **'Connect patients by code to start care episodes'**
  String get connectPatientsEpisodes;

  /// No description provided for @ctImageReview.
  ///
  /// In en, this message translates to:
  /// **'AI-supported CT image review'**
  String get ctImageReview;

  /// No description provided for @xrayImageReview.
  ///
  /// In en, this message translates to:
  /// **'AI-supported X-ray image review'**
  String get xrayImageReview;

  /// No description provided for @mriImageReview.
  ///
  /// In en, this message translates to:
  /// **'AI-supported MRI image review'**
  String get mriImageReview;

  /// No description provided for @checkMedicalRecords.
  ///
  /// In en, this message translates to:
  /// **'Check Patient Medical Records'**
  String get checkMedicalRecords;

  /// No description provided for @checkRecoveryPlans.
  ///
  /// In en, this message translates to:
  /// **'Check Patient Recovery Plans'**
  String get checkRecoveryPlans;

  /// No description provided for @checkImagingResults.
  ///
  /// In en, this message translates to:
  /// **'Check Imaging Results'**
  String get checkImagingResults;

  /// No description provided for @bookEquipment.
  ///
  /// In en, this message translates to:
  /// **'Book Medical Equipment'**
  String get bookEquipment;

  /// No description provided for @noPatientActivity.
  ///
  /// In en, this message translates to:
  /// **'No patient activity yet'**
  String get noPatientActivity;

  /// No description provided for @xray.
  ///
  /// In en, this message translates to:
  /// **'X-ray'**
  String get xray;

  /// No description provided for @ultrasound.
  ///
  /// In en, this message translates to:
  /// **'Ultrasound'**
  String get ultrasound;

  /// No description provided for @inviteTeamMember.
  ///
  /// In en, this message translates to:
  /// **'Invite team member'**
  String get inviteTeamMember;

  /// No description provided for @connectPatient.
  ///
  /// In en, this message translates to:
  /// **'Connect patient'**
  String get connectPatient;

  /// No description provided for @createEvent.
  ///
  /// In en, this message translates to:
  /// **'Create event'**
  String get createEvent;

  /// No description provided for @quickAccess.
  ///
  /// In en, this message translates to:
  /// **'Quick Access'**
  String get quickAccess;

  /// No description provided for @teamManagement.
  ///
  /// In en, this message translates to:
  /// **'Team Management'**
  String get teamManagement;

  /// No description provided for @recentActivities.
  ///
  /// In en, this message translates to:
  /// **'Recent Activities'**
  String get recentActivities;

  /// No description provided for @resourceOverview.
  ///
  /// In en, this message translates to:
  /// **'Resource Overview'**
  String get resourceOverview;

  /// No description provided for @ok.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get ok;

  /// No description provided for @medicalEquipment.
  ///
  /// In en, this message translates to:
  /// **'Medical Equipment'**
  String get medicalEquipment;

  /// No description provided for @resourceAvailable.
  ///
  /// In en, this message translates to:
  /// **'{available}/{total} Available'**
  String resourceAvailable(int available, int total);

  /// No description provided for @medicationStocks.
  ///
  /// In en, this message translates to:
  /// **'Medication Stocks'**
  String get medicationStocks;

  /// No description provided for @staffingLevels.
  ///
  /// In en, this message translates to:
  /// **'Staffing Levels'**
  String get staffingLevels;

  /// No description provided for @bedAvailability.
  ///
  /// In en, this message translates to:
  /// **'Bed Availability'**
  String get bedAvailability;

  /// No description provided for @operationalSummary.
  ///
  /// In en, this message translates to:
  /// **'Operational summaries update as clinic data becomes available.'**
  String get operationalSummary;

  /// No description provided for @overview.
  ///
  /// In en, this message translates to:
  /// **'Overview'**
  String get overview;

  /// No description provided for @verifiedHistory.
  ///
  /// In en, this message translates to:
  /// **'Verified History'**
  String get verifiedHistory;

  /// No description provided for @activeClinicalEvents.
  ///
  /// In en, this message translates to:
  /// **'Active Clinical Events'**
  String get activeClinicalEvents;

  /// No description provided for @activeRecoveryPlan.
  ///
  /// In en, this message translates to:
  /// **'Active Recovery Plan'**
  String get activeRecoveryPlan;

  /// No description provided for @currentMedications.
  ///
  /// In en, this message translates to:
  /// **'Current Medications'**
  String get currentMedications;

  /// No description provided for @overviewSummary.
  ///
  /// In en, this message translates to:
  /// **'Patient snapshot and active event context'**
  String get overviewSummary;

  /// No description provided for @profileSummary.
  ///
  /// In en, this message translates to:
  /// **'Patient-controlled information for doctor review'**
  String get profileSummary;

  /// No description provided for @medicalHistoryLower.
  ///
  /// In en, this message translates to:
  /// **'Medical history'**
  String get medicalHistoryLower;

  /// No description provided for @medicalHistorySummary.
  ///
  /// In en, this message translates to:
  /// **'Patient-entered history with clinician review context'**
  String get medicalHistorySummary;

  /// No description provided for @clinicalEventsSummary.
  ///
  /// In en, this message translates to:
  /// **'Problems over time with visits, diagnosis, and linked care'**
  String get clinicalEventsSummary;

  /// No description provided for @medicationsPrescriptions.
  ///
  /// In en, this message translates to:
  /// **'Medications & Prescriptions'**
  String get medicationsPrescriptions;

  /// No description provided for @medicationsSummary.
  ///
  /// In en, this message translates to:
  /// **'Event-linked orders, schedules, and generated reminders'**
  String get medicationsSummary;

  /// No description provided for @recoveryPlans.
  ///
  /// In en, this message translates to:
  /// **'Recovery Plans'**
  String get recoveryPlans;

  /// No description provided for @recoveryPlansSummary.
  ///
  /// In en, this message translates to:
  /// **'Event-linked timeline creation, review, and completion'**
  String get recoveryPlansSummary;

  /// No description provided for @imagingSummary.
  ///
  /// In en, this message translates to:
  /// **'Event-linked upload metadata and manual review status'**
  String get imagingSummary;

  /// No description provided for @consultationActivity.
  ///
  /// In en, this message translates to:
  /// **'Consultation & Activity'**
  String get consultationActivity;

  /// No description provided for @consultationActivitySummary.
  ///
  /// In en, this message translates to:
  /// **'Notes, specialist review, and supporting timeline'**
  String get consultationActivitySummary;

  /// No description provided for @searchPatients.
  ///
  /// In en, this message translates to:
  /// **'Search patients'**
  String get searchPatients;

  /// No description provided for @collapsePatientList.
  ///
  /// In en, this message translates to:
  /// **'Collapse patient list'**
  String get collapsePatientList;

  /// No description provided for @expandPatientList.
  ///
  /// In en, this message translates to:
  /// **'Expand patient list'**
  String get expandPatientList;

  /// No description provided for @collapseSectionNavigation.
  ///
  /// In en, this message translates to:
  /// **'Collapse section navigation'**
  String get collapseSectionNavigation;

  /// No description provided for @expandSectionNavigation.
  ///
  /// In en, this message translates to:
  /// **'Expand section navigation'**
  String get expandSectionNavigation;

  /// No description provided for @namePatientId.
  ///
  /// In en, this message translates to:
  /// **'Name or patient ID'**
  String get namePatientId;

  /// No description provided for @loadingPatients.
  ///
  /// In en, this message translates to:
  /// **'Loading patients'**
  String get loadingPatients;

  /// No description provided for @noConnectedPatients.
  ///
  /// In en, this message translates to:
  /// **'No connected patients'**
  String get noConnectedPatients;

  /// No description provided for @connectPatientEmpty.
  ///
  /// In en, this message translates to:
  /// **'Ask the patient for their code, connect them here, then build the care workspace from zero.'**
  String get connectPatientEmpty;

  /// No description provided for @connectPatientByCode.
  ///
  /// In en, this message translates to:
  /// **'Connect patient by code'**
  String get connectPatientByCode;

  /// No description provided for @patientCode.
  ///
  /// In en, this message translates to:
  /// **'Patient code'**
  String get patientCode;

  /// No description provided for @patientCodeHelper.
  ///
  /// In en, this message translates to:
  /// **'Shown on the patient dashboard after sign-up'**
  String get patientCodeHelper;

  /// No description provided for @reviewPatientMatch.
  ///
  /// In en, this message translates to:
  /// **'Review patient match'**
  String get reviewPatientMatch;

  /// No description provided for @connectedPatient.
  ///
  /// In en, this message translates to:
  /// **'Connected {name}.'**
  String connectedPatient(String name);

  /// No description provided for @enterPatientCode.
  ///
  /// In en, this message translates to:
  /// **'Enter the patient code.'**
  String get enterPatientCode;

  /// No description provided for @confirmPatientConnection.
  ///
  /// In en, this message translates to:
  /// **'Confirm patient connection'**
  String get confirmPatientConnection;

  /// No description provided for @confirmPatientDescription.
  ///
  /// In en, this message translates to:
  /// **'Check that this is the patient who gave you the ID before creating access to their care workspace.'**
  String get confirmPatientDescription;

  /// No description provided for @confirmConnect.
  ///
  /// In en, this message translates to:
  /// **'Confirm and connect'**
  String get confirmConnect;

  /// No description provided for @patientNotFound.
  ///
  /// In en, this message translates to:
  /// **'No patient matches this ID. Check it and try again.'**
  String get patientNotFound;

  /// No description provided for @reviewPatientFailed.
  ///
  /// In en, this message translates to:
  /// **'Unable to review this patient ID. Try again.'**
  String get reviewPatientFailed;

  /// No description provided for @patientProfile.
  ///
  /// In en, this message translates to:
  /// **'Patient Profile'**
  String get patientProfile;

  /// No description provided for @choosePatient.
  ///
  /// In en, this message translates to:
  /// **'Choose patient'**
  String get choosePatient;

  /// No description provided for @selectPatient.
  ///
  /// In en, this message translates to:
  /// **'Select a patient'**
  String get selectPatient;

  /// No description provided for @selectPatientDescription.
  ///
  /// In en, this message translates to:
  /// **'Open an assigned patient to review core records.'**
  String get selectPatientDescription;

  /// No description provided for @patientWorkspaceTitle.
  ///
  /// In en, this message translates to:
  /// **'Patient Workspace'**
  String get patientWorkspaceTitle;

  /// No description provided for @loadingPatientProfile.
  ///
  /// In en, this message translates to:
  /// **'Loading patient profile'**
  String get loadingPatientProfile;

  /// No description provided for @changePatient.
  ///
  /// In en, this message translates to:
  /// **'Change patient'**
  String get changePatient;

  /// No description provided for @recoveryPlanLoading.
  ///
  /// In en, this message translates to:
  /// **'Recovery plan loading'**
  String get recoveryPlanLoading;

  /// No description provided for @recoveryPlanUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Recovery plan unavailable'**
  String get recoveryPlanUnavailable;

  /// No description provided for @lastVisit.
  ///
  /// In en, this message translates to:
  /// **'Last visit: {value}'**
  String lastVisit(String value);

  /// No description provided for @activeClinicalEvent.
  ///
  /// In en, this message translates to:
  /// **'Active Clinical Event'**
  String get activeClinicalEvent;

  /// No description provided for @createEventFirst.
  ///
  /// In en, this message translates to:
  /// **'Create a Clinical Event before event-linked care work.'**
  String get createEventFirst;

  /// No description provided for @createEventBeforeCare.
  ///
  /// In en, this message translates to:
  /// **'Create a Clinical Event before authoring event-linked prescriptions, recovery plans, imaging, notes, or consultation.'**
  String get createEventBeforeCare;

  /// No description provided for @selectedCareEpisode.
  ///
  /// In en, this message translates to:
  /// **'Selected care episode'**
  String get selectedCareEpisode;

  /// No description provided for @legacyRecordsNotice.
  ///
  /// In en, this message translates to:
  /// **'Linked sections will show legacy patient-wide records until an event is selected.'**
  String get legacyRecordsNotice;

  /// No description provided for @workspaceSection.
  ///
  /// In en, this message translates to:
  /// **'Workspace section'**
  String get workspaceSection;

  /// No description provided for @clinicalEventReadiness.
  ///
  /// In en, this message translates to:
  /// **'Clinical event readiness'**
  String get clinicalEventReadiness;

  /// No description provided for @activeEventStatus.
  ///
  /// In en, this message translates to:
  /// **'Active event: {status}'**
  String activeEventStatus(String status);

  /// No description provided for @createSelectEventDescription.
  ///
  /// In en, this message translates to:
  /// **'Create or select a Clinical Event to organize prescriptions, medication schedules, recovery plans, imaging, notes, and consultation around one care episode.'**
  String get createSelectEventDescription;

  /// No description provided for @doctorReviewOnly.
  ///
  /// In en, this message translates to:
  /// **'Doctor review only: patient-controlled profile fields are not edited from this workspace.'**
  String get doctorReviewOnly;

  /// No description provided for @profileCorrectionNotice.
  ///
  /// In en, this message translates to:
  /// **'Profile corrections should be requested from the patient; direct doctor editing is intentionally unavailable here.'**
  String get profileCorrectionNotice;

  /// No description provided for @historyAuditNotice.
  ///
  /// In en, this message translates to:
  /// **'Medical history is patient-entered. Doctor verification, correction requests, and amendments are stored as visible audited overlays.'**
  String get historyAuditNotice;

  /// No description provided for @allergies.
  ///
  /// In en, this message translates to:
  /// **'Allergies'**
  String get allergies;

  /// No description provided for @noAllergies.
  ///
  /// In en, this message translates to:
  /// **'No allergies recorded'**
  String get noAllergies;

  /// No description provided for @noReaction.
  ///
  /// In en, this message translates to:
  /// **'No reaction detail recorded.'**
  String get noReaction;

  /// No description provided for @chronicDiseases.
  ///
  /// In en, this message translates to:
  /// **'Chronic diseases'**
  String get chronicDiseases;

  /// No description provided for @noChronicDiseases.
  ///
  /// In en, this message translates to:
  /// **'No chronic diseases recorded'**
  String get noChronicDiseases;

  /// No description provided for @noConditionNote.
  ///
  /// In en, this message translates to:
  /// **'No condition note recorded.'**
  String get noConditionNote;

  /// No description provided for @doctorAmendmentAdded.
  ///
  /// In en, this message translates to:
  /// **'Doctor amendment added after reviewing the patient history.'**
  String get doctorAmendmentAdded;

  /// No description provided for @patientConfirmHistory.
  ///
  /// In en, this message translates to:
  /// **'Please confirm this history item in your profile.'**
  String get patientConfirmHistory;

  /// No description provided for @medicalHistoryReview.
  ///
  /// In en, this message translates to:
  /// **'Medical History Review'**
  String get medicalHistoryReview;

  /// No description provided for @noPatientHistoryItem.
  ///
  /// In en, this message translates to:
  /// **'No patient-entered allergy, chronic disease, or record is available for doctor review yet.'**
  String get noPatientHistoryItem;

  /// No description provided for @patientEnteredItem.
  ///
  /// In en, this message translates to:
  /// **'Patient-entered item'**
  String get patientEnteredItem;

  /// No description provided for @reviewAction.
  ///
  /// In en, this message translates to:
  /// **'Review action'**
  String get reviewAction;

  /// No description provided for @markVerified.
  ///
  /// In en, this message translates to:
  /// **'Mark verified'**
  String get markVerified;

  /// No description provided for @addDoctorAmendment.
  ///
  /// In en, this message translates to:
  /// **'Add doctor amendment'**
  String get addDoctorAmendment;

  /// No description provided for @requestPatientCorrection.
  ///
  /// In en, this message translates to:
  /// **'Request patient correction'**
  String get requestPatientCorrection;

  /// No description provided for @doctorAmendment.
  ///
  /// In en, this message translates to:
  /// **'Doctor amendment'**
  String get doctorAmendment;

  /// No description provided for @patientCorrectionRequest.
  ///
  /// In en, this message translates to:
  /// **'Patient correction request'**
  String get patientCorrectionRequest;

  /// No description provided for @saveAuditedReview.
  ///
  /// In en, this message translates to:
  /// **'Save audited review'**
  String get saveAuditedReview;

  /// No description provided for @historyReviewSaved.
  ///
  /// In en, this message translates to:
  /// **'Medical history review saved: {action}.'**
  String historyReviewSaved(String action);

  /// No description provided for @selectHistoryItem.
  ///
  /// In en, this message translates to:
  /// **'Select a patient-entered item first.'**
  String get selectHistoryItem;

  /// No description provided for @enterDoctorAmendment.
  ///
  /// In en, this message translates to:
  /// **'Enter a doctor amendment.'**
  String get enterDoctorAmendment;

  /// No description provided for @enterPatientCorrection.
  ///
  /// In en, this message translates to:
  /// **'Enter a patient correction request.'**
  String get enterPatientCorrection;

  /// No description provided for @encounterUpdates.
  ///
  /// In en, this message translates to:
  /// **'Encounter updates'**
  String get encounterUpdates;

  /// No description provided for @noEncounterUpdates.
  ///
  /// In en, this message translates to:
  /// **'No encounter updates recorded'**
  String get noEncounterUpdates;

  /// No description provided for @clinicalEventLink.
  ///
  /// In en, this message translates to:
  /// **'Clinical Event link: {title}'**
  String clinicalEventLink(String title);

  /// No description provided for @doctorDiagnosisRecord.
  ///
  /// In en, this message translates to:
  /// **'Doctor diagnosis record'**
  String get doctorDiagnosisRecord;

  /// No description provided for @noDiagnoses.
  ///
  /// In en, this message translates to:
  /// **'No diagnoses recorded'**
  String get noDiagnoses;

  /// No description provided for @noDiagnosisNote.
  ///
  /// In en, this message translates to:
  /// **'No diagnosis note recorded.'**
  String get noDiagnosisNote;

  /// No description provided for @diagnosisReadOnly.
  ///
  /// In en, this message translates to:
  /// **'Patient can read this record but cannot edit doctor diagnosis.'**
  String get diagnosisReadOnly;

  /// No description provided for @doctorNotes.
  ///
  /// In en, this message translates to:
  /// **'Doctor notes'**
  String get doctorNotes;

  /// No description provided for @noDoctorNotes.
  ///
  /// In en, this message translates to:
  /// **'No doctor notes'**
  String get noDoctorNotes;

  /// No description provided for @linkedToEvent.
  ///
  /// In en, this message translates to:
  /// **'Linked to {title}'**
  String linkedToEvent(String title);

  /// No description provided for @prescriptionContextNotice.
  ///
  /// In en, this message translates to:
  /// **'Prescription orders and active medication schedules are shown under {title}. Reminder rows below are generated schedule outputs, not a standalone doctor workspace.'**
  String prescriptionContextNotice(String title);

  /// No description provided for @imagingEvidenceNotice.
  ///
  /// In en, this message translates to:
  /// **'Imaging is reviewed as supporting evidence for {title}. Findings remain doctor-entered; the app does not make automated clinical claims.'**
  String imagingEvidenceNotice(String title);

  /// No description provided for @noEncounterUpdate.
  ///
  /// In en, this message translates to:
  /// **'No encounter update recorded'**
  String get noEncounterUpdate;

  /// No description provided for @diagnosisNotRecorded.
  ///
  /// In en, this message translates to:
  /// **'Diagnosis not recorded'**
  String get diagnosisNotRecorded;

  /// No description provided for @clinicalEventDescription.
  ///
  /// In en, this message translates to:
  /// **'Clinical Event groups one medical problem over time. Doctors create and update it; patients can read it but cannot edit doctor diagnosis.'**
  String get clinicalEventDescription;

  /// No description provided for @latestUpdate.
  ///
  /// In en, this message translates to:
  /// **'Latest update: {value}'**
  String latestUpdate(String value);

  /// No description provided for @eventTimeline.
  ///
  /// In en, this message translates to:
  /// **'Event timeline'**
  String get eventTimeline;

  /// No description provided for @clinicalEventEditor.
  ///
  /// In en, this message translates to:
  /// **'Clinical Event Editor'**
  String get clinicalEventEditor;

  /// No description provided for @createClinicalEvent.
  ///
  /// In en, this message translates to:
  /// **'Create Clinical Event'**
  String get createClinicalEvent;

  /// No description provided for @updateClinicalEvent.
  ///
  /// In en, this message translates to:
  /// **'Update Clinical Event'**
  String get updateClinicalEvent;

  /// No description provided for @newEvent.
  ///
  /// In en, this message translates to:
  /// **'New event'**
  String get newEvent;

  /// No description provided for @noClinicalEvent.
  ///
  /// In en, this message translates to:
  /// **'No Clinical Event exists yet. Create one before authoring linked care outputs.'**
  String get noClinicalEvent;

  /// No description provided for @clinicalEventTitle.
  ///
  /// In en, this message translates to:
  /// **'Clinical Event title'**
  String get clinicalEventTitle;

  /// No description provided for @chiefComplaint.
  ///
  /// In en, this message translates to:
  /// **'Chief complaint'**
  String get chiefComplaint;

  /// No description provided for @onsetDate.
  ///
  /// In en, this message translates to:
  /// **'Onset date'**
  String get onsetDate;

  /// No description provided for @dateOptional.
  ///
  /// In en, this message translates to:
  /// **'YYYY-MM-DD or blank'**
  String get dateOptional;

  /// No description provided for @status.
  ///
  /// In en, this message translates to:
  /// **'Status'**
  String get status;

  /// No description provided for @symptomSummary.
  ///
  /// In en, this message translates to:
  /// **'Symptom/update summary'**
  String get symptomSummary;

  /// No description provided for @doctorDiagnosis.
  ///
  /// In en, this message translates to:
  /// **'Doctor diagnosis or provisional diagnosis'**
  String get doctorDiagnosis;

  /// No description provided for @eventDiagnosisNotice.
  ///
  /// In en, this message translates to:
  /// **'Patients can read Clinical Events, but doctor diagnosis fields are doctor-managed and audited.'**
  String get eventDiagnosisNotice;

  /// No description provided for @newCareEpisode.
  ///
  /// In en, this message translates to:
  /// **'New care episode'**
  String get newCareEpisode;

  /// No description provided for @chiefComplaintMissing.
  ///
  /// In en, this message translates to:
  /// **'Chief complaint not recorded'**
  String get chiefComplaintMissing;

  /// No description provided for @eventValidation.
  ///
  /// In en, this message translates to:
  /// **'Use a title, chief complaint, and optional YYYY-MM-DD onset date.'**
  String get eventValidation;

  /// No description provided for @timelineEntry.
  ///
  /// In en, this message translates to:
  /// **'Clinical Event timeline entry: {type}.'**
  String timelineEntry(String type);

  /// No description provided for @prescriptionStatus.
  ///
  /// In en, this message translates to:
  /// **'Prescription {status}'**
  String prescriptionStatus(String status);

  /// No description provided for @generatedRefillReminder.
  ///
  /// In en, this message translates to:
  /// **'Generated refill reminder'**
  String get generatedRefillReminder;

  /// No description provided for @generatedMedicationReminder.
  ///
  /// In en, this message translates to:
  /// **'Generated medication reminder'**
  String get generatedMedicationReminder;

  /// No description provided for @imagingStatusTitle.
  ///
  /// In en, this message translates to:
  /// **'Imaging {status}'**
  String imagingStatusTitle(String status);

  /// No description provided for @manualReviewStatus.
  ///
  /// In en, this message translates to:
  /// **'Manual review status for {title}.'**
  String manualReviewStatus(String title);

  /// No description provided for @activityTimeline.
  ///
  /// In en, this message translates to:
  /// **'Activity timeline'**
  String get activityTimeline;

  /// No description provided for @noActivity.
  ///
  /// In en, this message translates to:
  /// **'No activity yet'**
  String get noActivity;

  /// No description provided for @noMedicalRecords.
  ///
  /// In en, this message translates to:
  /// **'No Medical Records'**
  String get noMedicalRecords;

  /// No description provided for @doctorReviewAmendments.
  ///
  /// In en, this message translates to:
  /// **'Doctor review and amendments'**
  String get doctorReviewAmendments;

  /// No description provided for @noDoctorReviews.
  ///
  /// In en, this message translates to:
  /// **'No doctor review records'**
  String get noDoctorReviews;

  /// No description provided for @clinicianVerifiedHistory.
  ///
  /// In en, this message translates to:
  /// **'Clinician verified patient-entered history.'**
  String get clinicianVerifiedHistory;

  /// No description provided for @auditOverlayNotice.
  ///
  /// In en, this message translates to:
  /// **'Audit-linked overlay; original patient-entered item is preserved.'**
  String get auditOverlayNotice;

  /// No description provided for @allergyLabel.
  ///
  /// In en, this message translates to:
  /// **'Allergy: {value}'**
  String allergyLabel(String value);

  /// No description provided for @chronicDiseaseLabel.
  ///
  /// In en, this message translates to:
  /// **'Chronic disease: {value}'**
  String chronicDiseaseLabel(String value);

  /// No description provided for @medicalRecordLabel.
  ///
  /// In en, this message translates to:
  /// **'Medical record: {value}'**
  String medicalRecordLabel(String value);

  /// No description provided for @clinicianVerified.
  ///
  /// In en, this message translates to:
  /// **'Clinician verified'**
  String get clinicianVerified;

  /// No description provided for @patientCorrectionRequested.
  ///
  /// In en, this message translates to:
  /// **'Patient correction requested'**
  String get patientCorrectionRequested;

  /// No description provided for @noImagingAssets.
  ///
  /// In en, this message translates to:
  /// **'No imaging assets'**
  String get noImagingAssets;

  /// No description provided for @uploaded.
  ///
  /// In en, this message translates to:
  /// **'Uploaded: {date}'**
  String uploaded(String date);

  /// No description provided for @findingResult.
  ///
  /// In en, this message translates to:
  /// **'Finding/result: {value}'**
  String findingResult(String value);

  /// No description provided for @measurementObservation.
  ///
  /// In en, this message translates to:
  /// **'Measurement/observation: {value}'**
  String measurementObservation(String value);

  /// No description provided for @pendingManualReview.
  ///
  /// In en, this message translates to:
  /// **'Pending manual doctor review'**
  String get pendingManualReview;

  /// No description provided for @medications.
  ///
  /// In en, this message translates to:
  /// **'Medications'**
  String get medications;

  /// No description provided for @noMedicationsRecorded.
  ///
  /// In en, this message translates to:
  /// **'No medications recorded'**
  String get noMedicationsRecorded;

  /// No description provided for @noPrescriptions.
  ///
  /// In en, this message translates to:
  /// **'No prescriptions'**
  String get noPrescriptions;

  /// No description provided for @medicationRemindersTitle.
  ///
  /// In en, this message translates to:
  /// **'Medication Reminders'**
  String get medicationRemindersTitle;

  /// No description provided for @noMedicationReminderRecords.
  ///
  /// In en, this message translates to:
  /// **'No medication reminders'**
  String get noMedicationReminderRecords;

  /// No description provided for @refillReminder.
  ///
  /// In en, this message translates to:
  /// **'Refill reminder'**
  String get refillReminder;

  /// No description provided for @medicationReminder.
  ///
  /// In en, this message translates to:
  /// **'Medication reminder'**
  String get medicationReminder;

  /// No description provided for @medicationScheduleEditor.
  ///
  /// In en, this message translates to:
  /// **'Medication Schedule Editor'**
  String get medicationScheduleEditor;

  /// No description provided for @prescriptionOrderWorkflow.
  ///
  /// In en, this message translates to:
  /// **'Prescription Order Workflow'**
  String get prescriptionOrderWorkflow;

  /// No description provided for @scheduleNotRecorded.
  ///
  /// In en, this message translates to:
  /// **'Schedule not recorded'**
  String get scheduleNotRecorded;

  /// No description provided for @saveMedicationFirst.
  ///
  /// In en, this message translates to:
  /// **'Save a medication before issuing a prescription.'**
  String get saveMedicationFirst;

  /// No description provided for @prescriptionWorkflowDescription.
  ///
  /// In en, this message translates to:
  /// **'Prescription lines use the selected event medication values and feed the patient medication schedule.'**
  String get prescriptionWorkflowDescription;

  /// No description provided for @selectEventMedication.
  ///
  /// In en, this message translates to:
  /// **'Select or create a Clinical Event before saving new event-linked medication work.'**
  String get selectEventMedication;

  /// No description provided for @medicationName.
  ///
  /// In en, this message translates to:
  /// **'Medication name'**
  String get medicationName;

  /// No description provided for @dosage.
  ///
  /// In en, this message translates to:
  /// **'Dosage'**
  String get dosage;

  /// No description provided for @schedule.
  ///
  /// In en, this message translates to:
  /// **'Schedule'**
  String get schedule;

  /// No description provided for @prescriptionNote.
  ///
  /// In en, this message translates to:
  /// **'Prescription note'**
  String get prescriptionNote;

  /// No description provided for @addMedication.
  ///
  /// In en, this message translates to:
  /// **'Add medication'**
  String get addMedication;

  /// No description provided for @updateMedication.
  ///
  /// In en, this message translates to:
  /// **'Update medication'**
  String get updateMedication;

  /// No description provided for @issuePrescription.
  ///
  /// In en, this message translates to:
  /// **'Issue prescription'**
  String get issuePrescription;

  /// No description provided for @medicationValidation.
  ///
  /// In en, this message translates to:
  /// **'Medication name, dosage, and schedule are required.'**
  String get medicationValidation;

  /// No description provided for @asset.
  ///
  /// In en, this message translates to:
  /// **'asset'**
  String get asset;

  /// No description provided for @bytesVia.
  ///
  /// In en, this message translates to:
  /// **'{bytes} bytes via {provider}'**
  String bytesVia(int bytes, String provider);

  /// No description provided for @medicationLines.
  ///
  /// In en, this message translates to:
  /// **'{count} medication line(s)'**
  String medicationLines(int count);

  /// No description provided for @nextDue.
  ///
  /// In en, this message translates to:
  /// **'Next: {date}'**
  String nextDue(String date);

  /// No description provided for @manualFindingDefault.
  ///
  /// In en, this message translates to:
  /// **'Manual finding entered by doctor after imaging review.'**
  String get manualFindingDefault;

  /// No description provided for @manualMeasurementDefault.
  ///
  /// In en, this message translates to:
  /// **'Manual measurement note; no automated interpretation.'**
  String get manualMeasurementDefault;

  /// No description provided for @imagingUpload.
  ///
  /// In en, this message translates to:
  /// **'Imaging Upload'**
  String get imagingUpload;

  /// No description provided for @imageFilename.
  ///
  /// In en, this message translates to:
  /// **'Image filename'**
  String get imageFilename;

  /// No description provided for @imageMetadataHelper.
  ///
  /// In en, this message translates to:
  /// **'PNG, JPEG, or DICOM metadata'**
  String get imageMetadataHelper;

  /// No description provided for @contentType.
  ///
  /// In en, this message translates to:
  /// **'Content type'**
  String get contentType;

  /// No description provided for @sizeBytes.
  ///
  /// In en, this message translates to:
  /// **'Size in bytes'**
  String get sizeBytes;

  /// No description provided for @prepareUpload.
  ///
  /// In en, this message translates to:
  /// **'Prepare upload'**
  String get prepareUpload;

  /// No description provided for @imagingWorkflow.
  ///
  /// In en, this message translates to:
  /// **'Imaging Workflow'**
  String get imagingWorkflow;

  /// No description provided for @manualFinding.
  ///
  /// In en, this message translates to:
  /// **'Manual doctor-entered finding/result'**
  String get manualFinding;

  /// No description provided for @manualMeasurement.
  ///
  /// In en, this message translates to:
  /// **'Manual measurement or observation'**
  String get manualMeasurement;

  /// No description provided for @prepareImaging.
  ///
  /// In en, this message translates to:
  /// **'Prepare imaging'**
  String get prepareImaging;

  /// No description provided for @finalizeUpload.
  ///
  /// In en, this message translates to:
  /// **'Finalize upload'**
  String get finalizeUpload;

  /// No description provided for @markReviewed.
  ///
  /// In en, this message translates to:
  /// **'Mark reviewed'**
  String get markReviewed;

  /// No description provided for @selectEventImaging.
  ///
  /// In en, this message translates to:
  /// **'Select or create a Clinical Event before preparing event-linked imaging metadata.'**
  String get selectEventImaging;

  /// No description provided for @assessmentForm.
  ///
  /// In en, this message translates to:
  /// **'Assessment Form'**
  String get assessmentForm;

  /// No description provided for @assessmentFixture.
  ///
  /// In en, this message translates to:
  /// **'Assessment case'**
  String get assessmentFixture;

  /// No description provided for @runAssessment.
  ///
  /// In en, this message translates to:
  /// **'Run assessment'**
  String get runAssessment;

  /// No description provided for @loadingAssessmentHistory.
  ///
  /// In en, this message translates to:
  /// **'Loading assessment history'**
  String get loadingAssessmentHistory;

  /// No description provided for @noAssessmentResults.
  ///
  /// In en, this message translates to:
  /// **'No assessment results yet'**
  String get noAssessmentResults;

  /// No description provided for @assessmentEmptyDescription.
  ///
  /// In en, this message translates to:
  /// **'Run an assessment case to create a result.'**
  String get assessmentEmptyDescription;

  /// No description provided for @imageUploadValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter an image filename and a positive byte size.'**
  String get imageUploadValidation;

  /// No description provided for @uploadedBytesValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter the uploaded byte size to finalize.'**
  String get uploadedBytesValidation;

  /// No description provided for @manualFindingValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter a manual imaging finding/result before review.'**
  String get manualFindingValidation;

  /// No description provided for @assessmentSelectionValidation.
  ///
  /// In en, this message translates to:
  /// **'Select an assessment case.'**
  String get assessmentSelectionValidation;

  /// No description provided for @recoveryPlanEditor.
  ///
  /// In en, this message translates to:
  /// **'Recovery Plan Editor'**
  String get recoveryPlanEditor;

  /// No description provided for @selectEventRecovery.
  ///
  /// In en, this message translates to:
  /// **'Select or create a Clinical Event before creating an event-linked recovery plan.'**
  String get selectEventRecovery;

  /// No description provided for @noEventRecoveryPlan.
  ///
  /// In en, this message translates to:
  /// **'No recovery plan for this Clinical Event yet. Save a draft first.'**
  String get noEventRecoveryPlan;

  /// No description provided for @planStatusReview.
  ///
  /// In en, this message translates to:
  /// **'Plan {status}; review {review}; {completed}/{total} tasks complete.'**
  String planStatusReview(
    String status,
    String review,
    int completed,
    int total,
  );

  /// No description provided for @noActiveEventPlan.
  ///
  /// In en, this message translates to:
  /// **'No active Recovery Plan for this Clinical Event.'**
  String get noActiveEventPlan;

  /// No description provided for @oneActiveEventPlan.
  ///
  /// In en, this message translates to:
  /// **'One active Recovery Plan is linked to this Clinical Event.'**
  String get oneActiveEventPlan;

  /// No description provided for @multipleActivePlans.
  ///
  /// In en, this message translates to:
  /// **'Multiple active plans are visible for this event; approve a replacement to resolve the workflow.'**
  String get multipleActivePlans;

  /// No description provided for @planTitle.
  ///
  /// In en, this message translates to:
  /// **'Plan title'**
  String get planTitle;

  /// No description provided for @instructions.
  ///
  /// In en, this message translates to:
  /// **'Instructions'**
  String get instructions;

  /// No description provided for @medicationTask.
  ///
  /// In en, this message translates to:
  /// **'Medication task'**
  String get medicationTask;

  /// No description provided for @exerciseTask.
  ///
  /// In en, this message translates to:
  /// **'Exercise task'**
  String get exerciseTask;

  /// No description provided for @dietTask.
  ///
  /// In en, this message translates to:
  /// **'Diet task'**
  String get dietTask;

  /// No description provided for @followUpTask.
  ///
  /// In en, this message translates to:
  /// **'Follow-up task'**
  String get followUpTask;

  /// No description provided for @reviewStatus.
  ///
  /// In en, this message translates to:
  /// **'Review {status}.'**
  String reviewStatus(String status);

  /// No description provided for @saveDraft.
  ///
  /// In en, this message translates to:
  /// **'Save draft'**
  String get saveDraft;

  /// No description provided for @submitReview.
  ///
  /// In en, this message translates to:
  /// **'Submit review'**
  String get submitReview;

  /// No description provided for @requestChanges.
  ///
  /// In en, this message translates to:
  /// **'Request changes'**
  String get requestChanges;

  /// No description provided for @approvePatient.
  ///
  /// In en, this message translates to:
  /// **'Approve for patient'**
  String get approvePatient;

  /// No description provided for @completePlan.
  ///
  /// In en, this message translates to:
  /// **'Complete plan'**
  String get completePlan;

  /// No description provided for @medicationTaskDetail.
  ///
  /// In en, this message translates to:
  /// **'Medication reminder reviewed with the patient.'**
  String get medicationTaskDetail;

  /// No description provided for @exerciseTaskDetail.
  ///
  /// In en, this message translates to:
  /// **'Movement or exercise task reviewed with the patient.'**
  String get exerciseTaskDetail;

  /// No description provided for @dietTaskDetail.
  ///
  /// In en, this message translates to:
  /// **'Nutrition or hydration task reviewed with the patient.'**
  String get dietTaskDetail;

  /// No description provided for @followUpTaskDetail.
  ///
  /// In en, this message translates to:
  /// **'Follow-up preparation reviewed with the patient.'**
  String get followUpTaskDetail;

  /// No description provided for @planFieldsValidation.
  ///
  /// In en, this message translates to:
  /// **'Use at least three characters for every plan field.'**
  String get planFieldsValidation;

  /// No description provided for @savePlanBeforeAction.
  ///
  /// In en, this message translates to:
  /// **'Save the recovery plan before {action}.'**
  String savePlanBeforeAction(String action);

  /// No description provided for @submitPlanFirst.
  ///
  /// In en, this message translates to:
  /// **'Save and submit the recovery plan first.'**
  String get submitPlanFirst;

  /// No description provided for @specialistConsultation.
  ///
  /// In en, this message translates to:
  /// **'Specialist Consultation'**
  String get specialistConsultation;

  /// No description provided for @specialistDescription.
  ///
  /// In en, this message translates to:
  /// **'Asynchronous consultation request. Appointments, billing, video, and voice are not included in this workflow.'**
  String get specialistDescription;

  /// No description provided for @selectEventConsultation.
  ///
  /// In en, this message translates to:
  /// **'Select or create a Clinical Event before requesting event-linked specialist review.'**
  String get selectEventConsultation;

  /// No description provided for @questionSummary.
  ///
  /// In en, this message translates to:
  /// **'Question summary'**
  String get questionSummary;

  /// No description provided for @routine.
  ///
  /// In en, this message translates to:
  /// **'Routine'**
  String get routine;

  /// No description provided for @soon.
  ///
  /// In en, this message translates to:
  /// **'Soon'**
  String get soon;

  /// No description provided for @requestSpecialistReview.
  ///
  /// In en, this message translates to:
  /// **'Request specialist review'**
  String get requestSpecialistReview;

  /// No description provided for @loadingConsultations.
  ///
  /// In en, this message translates to:
  /// **'Loading consultation requests'**
  String get loadingConsultations;

  /// No description provided for @noSpecialistRequest.
  ///
  /// In en, this message translates to:
  /// **'No specialist request yet'**
  String get noSpecialistRequest;

  /// No description provided for @specialistEmptyDescription.
  ///
  /// In en, this message translates to:
  /// **'Submit a request for asynchronous status tracking.'**
  String get specialistEmptyDescription;

  /// No description provided for @priority.
  ///
  /// In en, this message translates to:
  /// **'Priority: {value}'**
  String priority(String value);

  /// No description provided for @consultationValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter a specialty and a concise, relevant summary.'**
  String get consultationValidation;

  /// No description provided for @consultationSubmitted.
  ///
  /// In en, this message translates to:
  /// **'{specialty} consultation {status}.'**
  String consultationSubmitted(String specialty, String status);

  /// No description provided for @bornYear.
  ///
  /// In en, this message translates to:
  /// **'Born {year}'**
  String bornYear(int year);

  /// No description provided for @demographicsMissing.
  ///
  /// In en, this message translates to:
  /// **'Demographics not recorded'**
  String get demographicsMissing;

  /// No description provided for @ageYears.
  ///
  /// In en, this message translates to:
  /// **'Age {age}'**
  String ageYears(int age);

  /// No description provided for @ageSexMissing.
  ///
  /// In en, this message translates to:
  /// **'Age/sex not recorded'**
  String get ageSexMissing;

  /// No description provided for @recoveryPlanNone.
  ///
  /// In en, this message translates to:
  /// **'Recovery plan: none'**
  String get recoveryPlanNone;

  /// No description provided for @recoveryPlanStatus.
  ///
  /// In en, this message translates to:
  /// **'Recovery plan: {status} / {review}'**
  String recoveryPlanStatus(String status, String review);

  /// No description provided for @workflowReviewReady.
  ///
  /// In en, this message translates to:
  /// **'Workflow: review ready'**
  String get workflowReviewReady;

  /// No description provided for @workflowSetupNeeded.
  ///
  /// In en, this message translates to:
  /// **'Workflow: setup needed'**
  String get workflowSetupNeeded;

  /// No description provided for @clinicalEventNamed.
  ///
  /// In en, this message translates to:
  /// **'Clinical Event: {title}'**
  String clinicalEventNamed(String title);

  /// No description provided for @clinicalEventSetup.
  ///
  /// In en, this message translates to:
  /// **'Clinical Event: setup needed'**
  String get clinicalEventSetup;

  /// No description provided for @eventResourceSummary.
  ///
  /// In en, this message translates to:
  /// **'{prescriptions} prescription(s), {medications} medication schedule item(s), {plans} recovery plan(s), {imaging} imaging asset(s), {notes} note(s)'**
  String eventResourceSummary(
    int prescriptions,
    int medications,
    int plans,
    int imaging,
    int notes,
  );

  /// No description provided for @historyOverview.
  ///
  /// In en, this message translates to:
  /// **'Allergies: {allergies} | Chronic diseases: {conditions} | Visits: {visits} | Diagnoses: {diagnoses}'**
  String historyOverview(
    String allergies,
    String conditions,
    String visits,
    String diagnoses,
  );

  /// No description provided for @noPrescriptionNote.
  ///
  /// In en, this message translates to:
  /// **'No prescription note'**
  String get noPrescriptionNote;

  /// No description provided for @notScheduled.
  ///
  /// In en, this message translates to:
  /// **'Not scheduled'**
  String get notScheduled;

  /// No description provided for @emptySectionDescription.
  ///
  /// In en, this message translates to:
  /// **'No information has been recorded for this section yet.'**
  String get emptySectionDescription;

  /// No description provided for @uploadPrepared.
  ///
  /// In en, this message translates to:
  /// **'Upload prepared'**
  String get uploadPrepared;

  /// No description provided for @uploadMetadata.
  ///
  /// In en, this message translates to:
  /// **'{method} metadata'**
  String uploadMetadata(String method);

  /// No description provided for @objectKey.
  ///
  /// In en, this message translates to:
  /// **'Object key: {key}'**
  String objectKey(String key);

  /// No description provided for @expires.
  ///
  /// In en, this message translates to:
  /// **'Expires: {value}'**
  String expires(String value);

  /// No description provided for @imagingUploadPrepared.
  ///
  /// In en, this message translates to:
  /// **'Imaging upload prepared'**
  String get imagingUploadPrepared;

  /// No description provided for @imagingStatus.
  ///
  /// In en, this message translates to:
  /// **'Imaging status'**
  String get imagingStatus;

  /// No description provided for @reviewed.
  ///
  /// In en, this message translates to:
  /// **'Reviewed: {date}'**
  String reviewed(String date);

  /// No description provided for @risk.
  ///
  /// In en, this message translates to:
  /// **'Risk: {value}'**
  String risk(String value);

  /// No description provided for @assessmentScore.
  ///
  /// In en, this message translates to:
  /// **'Assessment score: {score}'**
  String assessmentScore(String score);

  /// No description provided for @modelVersion.
  ///
  /// In en, this message translates to:
  /// **'Model: {version}'**
  String modelVersion(String version);

  /// No description provided for @sessionEnded.
  ///
  /// In en, this message translates to:
  /// **'Your session has ended. Please sign in again.'**
  String get sessionEnded;

  /// No description provided for @patientRecordUnavailable.
  ///
  /// In en, this message translates to:
  /// **'This patient record is not available.'**
  String get patientRecordUnavailable;

  /// No description provided for @checkInformation.
  ///
  /// In en, this message translates to:
  /// **'Check the entered information and try again.'**
  String get checkInformation;

  /// No description provided for @unableToReachRetry.
  ///
  /// In en, this message translates to:
  /// **'Unable to reach Dr. AI. Check your connection and try again.'**
  String get unableToReachRetry;

  /// No description provided for @dateUnknown.
  ///
  /// In en, this message translates to:
  /// **'date unknown'**
  String get dateUnknown;

  /// No description provided for @eventSaved.
  ///
  /// In en, this message translates to:
  /// **'{title} saved as {status}.'**
  String eventSaved(String title, String status);

  /// No description provided for @contentAsset.
  ///
  /// In en, this message translates to:
  /// **'{type} asset'**
  String contentAsset(String type);

  /// No description provided for @assessmentLimitationSynthetic.
  ///
  /// In en, this message translates to:
  /// **'Assessment case result; no clinical inference was performed.'**
  String get assessmentLimitationSynthetic;

  /// No description provided for @assessmentLimitationValidation.
  ///
  /// In en, this message translates to:
  /// **'Not validated for diagnosis, treatment, or prognosis.'**
  String get assessmentLimitationValidation;

  /// No description provided for @assessmentNextStep.
  ///
  /// In en, this message translates to:
  /// **'Review the assessment case with a qualified clinician.'**
  String get assessmentNextStep;

  /// No description provided for @researchNotDiagnosis.
  ///
  /// In en, this message translates to:
  /// **'Research assessment - not for diagnosis.'**
  String get researchNotDiagnosis;

  /// No description provided for @low.
  ///
  /// In en, this message translates to:
  /// **'Low'**
  String get low;

  /// No description provided for @moderate.
  ///
  /// In en, this message translates to:
  /// **'Moderate'**
  String get moderate;

  /// No description provided for @high.
  ///
  /// In en, this message translates to:
  /// **'High'**
  String get high;

  /// No description provided for @partial.
  ///
  /// In en, this message translates to:
  /// **'Partial'**
  String get partial;

  /// No description provided for @insufficient.
  ///
  /// In en, this message translates to:
  /// **'Insufficient'**
  String get insufficient;

  /// No description provided for @sms.
  ///
  /// In en, this message translates to:
  /// **'SMS'**
  String get sms;

  /// No description provided for @specificHomeAddress.
  ///
  /// In en, this message translates to:
  /// **'Specific home address'**
  String get specificHomeAddress;

  /// No description provided for @unableToRequestCode.
  ///
  /// In en, this message translates to:
  /// **'Unable to request a code. Try again.'**
  String get unableToRequestCode;

  /// No description provided for @acceptTermsValidation.
  ///
  /// In en, this message translates to:
  /// **'Accept the terms and policy.'**
  String get acceptTermsValidation;

  /// No description provided for @localDevelopmentCodeFilled.
  ///
  /// In en, this message translates to:
  /// **'{message} The local development code was filled automatically.'**
  String localDevelopmentCodeFilled(String message);

  /// No description provided for @clinicianNamed.
  ///
  /// In en, this message translates to:
  /// **'Clinician: {name}'**
  String clinicianNamed(String name);

  /// No description provided for @medicationLinesLinked.
  ///
  /// In en, this message translates to:
  /// **'{count} medication line(s) linked to {event}.'**
  String medicationLinesLinked(int count, String event);

  /// No description provided for @createdFromMedicationSchedule.
  ///
  /// In en, this message translates to:
  /// **'Created from medication schedule context.'**
  String get createdFromMedicationSchedule;

  /// No description provided for @setupNeeded.
  ///
  /// In en, this message translates to:
  /// **'Setup needed'**
  String get setupNeeded;

  /// No description provided for @secureInformationTitle.
  ///
  /// In en, this message translates to:
  /// **'Your information is secure'**
  String get secureInformationTitle;

  /// No description provided for @secureInformationBody.
  ///
  /// In en, this message translates to:
  /// **'We protect your data and comply with healthcare privacy regulations.'**
  String get secureInformationBody;

  /// No description provided for @unableToChangePassword.
  ///
  /// In en, this message translates to:
  /// **'Unable to change your password. Try again.'**
  String get unableToChangePassword;

  /// No description provided for @signedOut.
  ///
  /// In en, this message translates to:
  /// **'You have signed out.'**
  String get signedOut;

  /// No description provided for @signedOutLocally.
  ///
  /// In en, this message translates to:
  /// **'You have signed out locally. The server could not be reached.'**
  String get signedOutLocally;

  /// No description provided for @incorrectCredentials.
  ///
  /// In en, this message translates to:
  /// **'The email or password is incorrect.'**
  String get incorrectCredentials;

  /// No description provided for @registrationRoleUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Registration is not available for the selected role.'**
  String get registrationRoleUnavailable;

  /// No description provided for @accountAlreadyExists.
  ///
  /// In en, this message translates to:
  /// **'An account already exists for this contact.'**
  String get accountAlreadyExists;

  /// No description provided for @registrationFieldsInvalid.
  ///
  /// In en, this message translates to:
  /// **'Check the phone number, email, password, role, and verification code.'**
  String get registrationFieldsInvalid;

  /// No description provided for @unableToCreateAccount.
  ///
  /// In en, this message translates to:
  /// **'Unable to create the account. Check your connection and try again.'**
  String get unableToCreateAccount;

  /// No description provided for @prescriptionCount.
  ///
  /// In en, this message translates to:
  /// **'{count} prescription(s)'**
  String prescriptionCount(int count);

  /// No description provided for @generatedReminderCount.
  ///
  /// In en, this message translates to:
  /// **'{count} generated reminder(s)'**
  String generatedReminderCount(int count);

  /// No description provided for @imagingAssetCount.
  ///
  /// In en, this message translates to:
  /// **'{count} imaging asset(s)'**
  String imagingAssetCount(int count);

  /// No description provided for @noteCount.
  ///
  /// In en, this message translates to:
  /// **'{count} note(s)'**
  String noteCount(int count);

  /// No description provided for @patientIntakeSummary.
  ///
  /// In en, this message translates to:
  /// **'Patient intake summary'**
  String get patientIntakeSummary;

  /// No description provided for @imagingUploadFinalized.
  ///
  /// In en, this message translates to:
  /// **'Imaging upload finalized.'**
  String get imagingUploadFinalized;

  /// No description provided for @imagingReviewUpdated.
  ///
  /// In en, this message translates to:
  /// **'Imaging review status updated.'**
  String get imagingReviewUpdated;

  /// No description provided for @doctorContactsDescription.
  ///
  /// In en, this message translates to:
  /// **'Private conversations with your connected patients and Dr. AI services.'**
  String get doctorContactsDescription;

  /// No description provided for @systemReadOnlyDescription.
  ///
  /// In en, this message translates to:
  /// **'Reminders and notifications · read-only'**
  String get systemReadOnlyDescription;

  /// No description provided for @aiCareCompanion.
  ///
  /// In en, this message translates to:
  /// **'AI care companion'**
  String get aiCareCompanion;

  /// No description provided for @myPatients.
  ///
  /// In en, this message translates to:
  /// **'My patients'**
  String get myPatients;

  /// No description provided for @connectedPatientPrivateChat.
  ///
  /// In en, this message translates to:
  /// **'Connected patient · private chat'**
  String get connectedPatientPrivateChat;

  /// No description provided for @connectPatientToChat.
  ///
  /// In en, this message translates to:
  /// **'Connect a patient from Patient Management to start a private conversation.'**
  String get connectPatientToChat;

  /// No description provided for @noGroupChats.
  ///
  /// In en, this message translates to:
  /// **'No group chats'**
  String get noGroupChats;

  /// No description provided for @groupChatsUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Group conversations are not available yet.'**
  String get groupChatsUnavailable;

  /// No description provided for @contactsLoadFailed.
  ///
  /// In en, this message translates to:
  /// **'Contacts could not be loaded.'**
  String get contactsLoadFailed;

  /// No description provided for @systemNotifications.
  ///
  /// In en, this message translates to:
  /// **'System notifications'**
  String get systemNotifications;

  /// No description provided for @systemNotificationsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Reminders and important account updates will appear here.'**
  String get systemNotificationsSubtitle;

  /// No description provided for @aiAssistant.
  ///
  /// In en, this message translates to:
  /// **'Dr. AI assistant'**
  String get aiAssistant;

  /// No description provided for @aiAssistantSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Your AI care companion interface is ready for the next phase.'**
  String get aiAssistantSubtitle;

  /// No description provided for @noSystemNotifications.
  ///
  /// In en, this message translates to:
  /// **'No system notifications yet'**
  String get noSystemNotifications;

  /// No description provided for @systemReadOnlyNotice.
  ///
  /// In en, this message translates to:
  /// **'This channel is read-only. You cannot send messages to the system.'**
  String get systemReadOnlyNotice;

  /// No description provided for @aiAvailablePhase3.
  ///
  /// In en, this message translates to:
  /// **'AI conversations will become available in Phase 3'**
  String get aiAvailablePhase3;

  /// No description provided for @aiPlaceholderNotice.
  ///
  /// In en, this message translates to:
  /// **'Generative replies stay unavailable until an evaluated DeepSeek release is activated. Deterministic safety and structured fallback remain active.'**
  String get aiPlaceholderNotice;

  /// No description provided for @aiChatSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Practical health guidance with a clear source or general-AI label.'**
  String get aiChatSubtitle;

  /// No description provided for @aiChatSafetyNotice.
  ///
  /// In en, this message translates to:
  /// **'Dr. AI is an AI assistant and can make mistakes. Verify important details with authoritative sources or a doctor. It cannot confirm a diagnosis, replace emergency care, or change medication.'**
  String get aiChatSafetyNotice;

  /// No description provided for @aiChatWelcome.
  ///
  /// In en, this message translates to:
  /// **'What can I help you work through?'**
  String get aiChatWelcome;

  /// No description provided for @aiChatInputHint.
  ///
  /// In en, this message translates to:
  /// **'Ask about symptoms, tests, medicines, or your care'**
  String get aiChatInputHint;

  /// No description provided for @aiChatSendFailed.
  ///
  /// In en, this message translates to:
  /// **'The secure chat request could not be completed. Try again.'**
  String get aiChatSendFailed;

  /// No description provided for @aiChatHistory.
  ///
  /// In en, this message translates to:
  /// **'Conversation history'**
  String get aiChatHistory;

  /// No description provided for @aiNewChat.
  ///
  /// In en, this message translates to:
  /// **'New chat'**
  String get aiNewChat;

  /// No description provided for @aiPreviousChats.
  ///
  /// In en, this message translates to:
  /// **'Previous chats'**
  String get aiPreviousChats;

  /// No description provided for @aiNoPreviousChats.
  ///
  /// In en, this message translates to:
  /// **'Your health conversations will appear here after you send the first question.'**
  String get aiNoPreviousChats;

  /// No description provided for @aiHistoryRetentionNotice.
  ///
  /// In en, this message translates to:
  /// **'Each conversation is kept for at least 60 days and is visible only in your account.'**
  String get aiHistoryRetentionNotice;

  /// No description provided for @aiArchiveChat.
  ///
  /// In en, this message translates to:
  /// **'Archive conversation'**
  String get aiArchiveChat;

  /// No description provided for @aiReopenChat.
  ///
  /// In en, this message translates to:
  /// **'Reopen conversation'**
  String get aiReopenChat;

  /// No description provided for @aiDeleteChat.
  ///
  /// In en, this message translates to:
  /// **'Delete from my history'**
  String get aiDeleteChat;

  /// No description provided for @aiArchivedChat.
  ///
  /// In en, this message translates to:
  /// **'Archived'**
  String get aiArchivedChat;

  /// No description provided for @aiChatLifecycleFailed.
  ///
  /// In en, this message translates to:
  /// **'The conversation could not be updated. Try again.'**
  String get aiChatLifecycleFailed;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @aiFollowUpQuestion.
  ///
  /// In en, this message translates to:
  /// **'One detail would help'**
  String get aiFollowUpQuestion;

  /// No description provided for @aiReviewMeasurementGuidance.
  ///
  /// In en, this message translates to:
  /// **'Measure correctly'**
  String get aiReviewMeasurementGuidance;

  /// No description provided for @aiTrackMeasurements.
  ///
  /// In en, this message translates to:
  /// **'Track readings'**
  String get aiTrackMeasurements;

  /// No description provided for @aiPrepareDoctorQuestions.
  ///
  /// In en, this message translates to:
  /// **'Prepare doctor questions'**
  String get aiPrepareDoctorQuestions;

  /// No description provided for @aiPrepareSymptomSummary.
  ///
  /// In en, this message translates to:
  /// **'Organize my symptoms'**
  String get aiPrepareSymptomSummary;

  /// No description provided for @aiPrepareSymptomSummaryPrompt.
  ///
  /// In en, this message translates to:
  /// **'Help me organize my symptoms, timeline, and key questions for a clinician.'**
  String get aiPrepareSymptomSummaryPrompt;

  /// No description provided for @aiMeasurementGuidancePrompt.
  ///
  /// In en, this message translates to:
  /// **'How can I measure this correctly?'**
  String get aiMeasurementGuidancePrompt;

  /// No description provided for @aiTrackMeasurementsPrompt.
  ///
  /// In en, this message translates to:
  /// **'Help me make a simple record-tracking plan.'**
  String get aiTrackMeasurementsPrompt;

  /// No description provided for @aiSuggestionEducation.
  ///
  /// In en, this message translates to:
  /// **'What should I understand about recording blood pressure?'**
  String get aiSuggestionEducation;

  /// No description provided for @aiSuggestionSymptoms.
  ///
  /// In en, this message translates to:
  /// **'I feel dizzy. What could explain it, and when should I seek care?'**
  String get aiSuggestionSymptoms;

  /// No description provided for @aiSuggestionMedication.
  ///
  /// In en, this message translates to:
  /// **'What questions should I ask my doctor about a prescribed medicine?'**
  String get aiSuggestionMedication;

  /// No description provided for @aiSuggestionDoctor.
  ///
  /// In en, this message translates to:
  /// **'Help me prepare questions for my next doctor visit.'**
  String get aiSuggestionDoctor;

  /// No description provided for @aiSources.
  ///
  /// In en, this message translates to:
  /// **'Reviewed sources'**
  String get aiSources;

  /// No description provided for @aiApprovedEvidenceBanner.
  ///
  /// In en, this message translates to:
  /// **'Source-grounded answer — supported by reviewed Dr. AI passages.'**
  String get aiApprovedEvidenceBanner;

  /// No description provided for @aiGeneralKnowledgeBanner.
  ///
  /// In en, this message translates to:
  /// **'General AI-generated information — no supporting Dr. AI source was found.'**
  String get aiGeneralKnowledgeBanner;

  /// No description provided for @aiFixedSafetyBanner.
  ///
  /// In en, this message translates to:
  /// **'Server-controlled safety response.'**
  String get aiFixedSafetyBanner;

  /// No description provided for @aiOpenOfficialSource.
  ///
  /// In en, this message translates to:
  /// **'Open official source'**
  String get aiOpenOfficialSource;

  /// No description provided for @aiImportantUncertainty.
  ///
  /// In en, this message translates to:
  /// **'Important uncertainty'**
  String get aiImportantUncertainty;

  /// No description provided for @aiContextUsed.
  ///
  /// In en, this message translates to:
  /// **'Personalized with your records'**
  String get aiContextUsed;

  /// No description provided for @aiContextProfile.
  ///
  /// In en, this message translates to:
  /// **'Profile basics'**
  String get aiContextProfile;

  /// No description provided for @aiContextMeasurements.
  ///
  /// In en, this message translates to:
  /// **'Health measurements'**
  String get aiContextMeasurements;

  /// No description provided for @aiContextConditions.
  ///
  /// In en, this message translates to:
  /// **'Recorded conditions'**
  String get aiContextConditions;

  /// No description provided for @aiContextMedications.
  ///
  /// In en, this message translates to:
  /// **'Medication information'**
  String get aiContextMedications;

  /// No description provided for @aiContextClinicalEvents.
  ///
  /// In en, this message translates to:
  /// **'Current care episode'**
  String get aiContextClinicalEvents;

  /// No description provided for @aiContextRecoveryPlan.
  ///
  /// In en, this message translates to:
  /// **'Recovery plan'**
  String get aiContextRecoveryPlan;

  /// No description provided for @aiContextFromProfile.
  ///
  /// In en, this message translates to:
  /// **'Your profile records'**
  String get aiContextFromProfile;

  /// No description provided for @aiContextPatientReported.
  ///
  /// In en, this message translates to:
  /// **'Your reported history'**
  String get aiContextPatientReported;

  /// No description provided for @aiContextDoctorRecord.
  ///
  /// In en, this message translates to:
  /// **'Doctor\'s record'**
  String get aiContextDoctorRecord;

  /// No description provided for @aiContextCurrentPrescription.
  ///
  /// In en, this message translates to:
  /// **'Current prescription'**
  String get aiContextCurrentPrescription;

  /// No description provided for @aiContextMedicationSchedule.
  ///
  /// In en, this message translates to:
  /// **'Current medication schedule'**
  String get aiContextMedicationSchedule;

  /// No description provided for @aiContextCurrentRecoveryPlan.
  ///
  /// In en, this message translates to:
  /// **'Current recovery plan'**
  String get aiContextCurrentRecoveryPlan;

  /// No description provided for @aiContactDoctor.
  ///
  /// In en, this message translates to:
  /// **'Contact my doctor'**
  String get aiContactDoctor;

  /// No description provided for @privateCareConversation.
  ///
  /// In en, this message translates to:
  /// **'Private care conversation'**
  String get privateCareConversation;

  /// No description provided for @loadingConversation.
  ///
  /// In en, this message translates to:
  /// **'Loading conversation…'**
  String get loadingConversation;

  /// No description provided for @conversationLoadFailed.
  ///
  /// In en, this message translates to:
  /// **'This conversation could not be loaded.'**
  String get conversationLoadFailed;

  /// No description provided for @messageSendFailed.
  ///
  /// In en, this message translates to:
  /// **'Message could not be sent. Please try again.'**
  String get messageSendFailed;

  /// No description provided for @writeMessage.
  ///
  /// In en, this message translates to:
  /// **'Write a message'**
  String get writeMessage;

  /// No description provided for @sendMessage.
  ///
  /// In en, this message translates to:
  /// **'Send message'**
  String get sendMessage;

  /// No description provided for @noPrivateMessages.
  ///
  /// In en, this message translates to:
  /// **'No messages yet. Start a private conversation about ongoing care.'**
  String get noPrivateMessages;

  /// No description provided for @patientFallbackName.
  ///
  /// In en, this message translates to:
  /// **'Patient'**
  String get patientFallbackName;

  /// No description provided for @doctorFallbackName.
  ///
  /// In en, this message translates to:
  /// **'Doctor'**
  String get doctorFallbackName;

  /// No description provided for @resources.
  ///
  /// In en, this message translates to:
  /// **'Resources'**
  String get resources;

  /// No description provided for @medicalResources.
  ///
  /// In en, this message translates to:
  /// **'Medical Resources'**
  String get medicalResources;

  /// No description provided for @medicalResourcesSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Search reviewed clinical sources, verify provenance, and keep guidance for later.'**
  String get medicalResourcesSubtitle;

  /// No description provided for @resourceCatalogPreviewTitle.
  ///
  /// In en, this message translates to:
  /// **'Authoritative source catalog'**
  String get resourceCatalogPreviewTitle;

  /// No description provided for @resourceCatalogPreviewBody.
  ///
  /// In en, this message translates to:
  /// **'These are 200 real WHO fact sheets paired across official Chinese and English pages. Full text is not stored or used for AI retrieval while commercial rights and medical review remain pending.'**
  String get resourceCatalogPreviewBody;

  /// No description provided for @resourceSearchHint.
  ///
  /// In en, this message translates to:
  /// **'Search medical resources in Chinese or English'**
  String get resourceSearchHint;

  /// No description provided for @resourceSearchTab.
  ///
  /// In en, this message translates to:
  /// **'Search'**
  String get resourceSearchTab;

  /// No description provided for @savedResourcesTab.
  ///
  /// In en, this message translates to:
  /// **'Saved'**
  String get savedResourcesTab;

  /// No description provided for @recentUpdatesTab.
  ///
  /// In en, this message translates to:
  /// **'Recent updates'**
  String get recentUpdatesTab;

  /// No description provided for @sourceRegistryTab.
  ///
  /// In en, this message translates to:
  /// **'Source registry'**
  String get sourceRegistryTab;

  /// No description provided for @resourceFilters.
  ///
  /// In en, this message translates to:
  /// **'Filters'**
  String get resourceFilters;

  /// No description provided for @showFilters.
  ///
  /// In en, this message translates to:
  /// **'Show filters'**
  String get showFilters;

  /// No description provided for @hideFilters.
  ///
  /// In en, this message translates to:
  /// **'Hide filters'**
  String get hideFilters;

  /// No description provided for @clearFilters.
  ///
  /// In en, this message translates to:
  /// **'Clear filters'**
  String get clearFilters;

  /// No description provided for @allOptions.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get allOptions;

  /// No description provided for @topicFilter.
  ///
  /// In en, this message translates to:
  /// **'Topic'**
  String get topicFilter;

  /// No description provided for @documentTypeFilter.
  ///
  /// In en, this message translates to:
  /// **'Document type'**
  String get documentTypeFilter;

  /// No description provided for @organizationFilter.
  ///
  /// In en, this message translates to:
  /// **'Organization'**
  String get organizationFilter;

  /// No description provided for @jurisdictionFilter.
  ///
  /// In en, this message translates to:
  /// **'Jurisdiction'**
  String get jurisdictionFilter;

  /// No description provided for @originalLanguageFilter.
  ///
  /// In en, this message translates to:
  /// **'Original language'**
  String get originalLanguageFilter;

  /// No description provided for @intendedAudienceFilter.
  ///
  /// In en, this message translates to:
  /// **'Intended audience'**
  String get intendedAudienceFilter;

  /// No description provided for @publicationReviewDateFilter.
  ///
  /// In en, this message translates to:
  /// **'Publication / catalog date'**
  String get publicationReviewDateFilter;

  /// No description provided for @versionStatusFilter.
  ///
  /// In en, this message translates to:
  /// **'Current / superseded'**
  String get versionStatusFilter;

  /// No description provided for @topicRespiratoryCare.
  ///
  /// In en, this message translates to:
  /// **'Respiratory care'**
  String get topicRespiratoryCare;

  /// No description provided for @topicCardiovascularCare.
  ///
  /// In en, this message translates to:
  /// **'Cardiovascular care'**
  String get topicCardiovascularCare;

  /// No description provided for @topicDiabetesCare.
  ///
  /// In en, this message translates to:
  /// **'Diabetes care'**
  String get topicDiabetesCare;

  /// No description provided for @topicRehabilitation.
  ///
  /// In en, this message translates to:
  /// **'Rehabilitation'**
  String get topicRehabilitation;

  /// No description provided for @documentClinicalGuide.
  ///
  /// In en, this message translates to:
  /// **'Clinical guide'**
  String get documentClinicalGuide;

  /// No description provided for @documentCarePathway.
  ///
  /// In en, this message translates to:
  /// **'Care pathway'**
  String get documentCarePathway;

  /// No description provided for @documentSafetyBulletin.
  ///
  /// In en, this message translates to:
  /// **'Safety bulletin'**
  String get documentSafetyBulletin;

  /// No description provided for @documentPatientEducation.
  ///
  /// In en, this message translates to:
  /// **'Patient education'**
  String get documentPatientEducation;

  /// No description provided for @organizationPrimaryCareCouncil.
  ///
  /// In en, this message translates to:
  /// **'Primary Care Review Council'**
  String get organizationPrimaryCareCouncil;

  /// No description provided for @organizationMedicinesSafetyCenter.
  ///
  /// In en, this message translates to:
  /// **'Medicines Safety Review Center'**
  String get organizationMedicinesSafetyCenter;

  /// No description provided for @organizationRehabilitationCollaborative.
  ///
  /// In en, this message translates to:
  /// **'Continuity and Rehabilitation Collaborative'**
  String get organizationRehabilitationCollaborative;

  /// No description provided for @jurisdictionMainlandChina.
  ///
  /// In en, this message translates to:
  /// **'Mainland China'**
  String get jurisdictionMainlandChina;

  /// No description provided for @jurisdictionInternational.
  ///
  /// In en, this message translates to:
  /// **'International'**
  String get jurisdictionInternational;

  /// No description provided for @jurisdictionChina.
  ///
  /// In en, this message translates to:
  /// **'China'**
  String get jurisdictionChina;

  /// No description provided for @audienceDoctors.
  ///
  /// In en, this message translates to:
  /// **'Doctors'**
  String get audienceDoctors;

  /// No description provided for @audienceDoctorsAndPatients.
  ///
  /// In en, this message translates to:
  /// **'Doctors and patients'**
  String get audienceDoctorsAndPatients;

  /// No description provided for @dateAny.
  ///
  /// In en, this message translates to:
  /// **'Any date'**
  String get dateAny;

  /// No description provided for @datePast12Months.
  ///
  /// In en, this message translates to:
  /// **'Past 12 months'**
  String get datePast12Months;

  /// No description provided for @datePast24Months.
  ///
  /// In en, this message translates to:
  /// **'Past 24 months'**
  String get datePast24Months;

  /// No description provided for @statusCurrent.
  ///
  /// In en, this message translates to:
  /// **'Current'**
  String get statusCurrent;

  /// No description provided for @statusSuperseded.
  ///
  /// In en, this message translates to:
  /// **'Superseded'**
  String get statusSuperseded;

  /// No description provided for @searchSuggestions.
  ///
  /// In en, this message translates to:
  /// **'Suggested searches'**
  String get searchSuggestions;

  /// No description provided for @resourceSuggestionOne.
  ///
  /// In en, this message translates to:
  /// **'Hypertension follow-up'**
  String get resourceSuggestionOne;

  /// No description provided for @resourceSuggestionTwo.
  ///
  /// In en, this message translates to:
  /// **'呼吸道感染用药安全'**
  String get resourceSuggestionTwo;

  /// No description provided for @resourceSuggestionThree.
  ///
  /// In en, this message translates to:
  /// **'Diabetes sick-day education'**
  String get resourceSuggestionThree;

  /// No description provided for @resourceResultCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{No resources} =1{1 resource} other{{count} resources}}'**
  String resourceResultCount(int count);

  /// No description provided for @currentAndReviewed.
  ///
  /// In en, this message translates to:
  /// **'Current and reviewed'**
  String get currentAndReviewed;

  /// No description provided for @supersededDoNotRely.
  ///
  /// In en, this message translates to:
  /// **'Superseded—do not rely on as current guidance'**
  String get supersededDoNotRely;

  /// No description provided for @rightsLimitedLinkOnly.
  ///
  /// In en, this message translates to:
  /// **'Rights-limited—link only / no stored full text'**
  String get rightsLimitedLinkOnly;

  /// No description provided for @doctorOnlyResource.
  ///
  /// In en, this message translates to:
  /// **'Doctor-only'**
  String get doctorOnlyResource;

  /// No description provided for @patientEducationApproved.
  ///
  /// In en, this message translates to:
  /// **'Patient education approved'**
  String get patientEducationApproved;

  /// No description provided for @patientUseNotApproved.
  ///
  /// In en, this message translates to:
  /// **'Not approved for patient use'**
  String get patientUseNotApproved;

  /// No description provided for @publisherLabel.
  ///
  /// In en, this message translates to:
  /// **'Publisher'**
  String get publisherLabel;

  /// No description provided for @sourceTypeLabel.
  ///
  /// In en, this message translates to:
  /// **'Source type'**
  String get sourceTypeLabel;

  /// No description provided for @publishedLabel.
  ///
  /// In en, this message translates to:
  /// **'Published'**
  String get publishedLabel;

  /// No description provided for @lastMedicalReviewLabel.
  ///
  /// In en, this message translates to:
  /// **'Last medical review'**
  String get lastMedicalReviewLabel;

  /// No description provided for @openSourceDetails.
  ///
  /// In en, this message translates to:
  /// **'Open source details'**
  String get openSourceDetails;

  /// No description provided for @saveResource.
  ///
  /// In en, this message translates to:
  /// **'Save resource'**
  String get saveResource;

  /// No description provided for @removeSavedResource.
  ///
  /// In en, this message translates to:
  /// **'Remove from saved'**
  String get removeSavedResource;

  /// No description provided for @resourceSavedConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Resource saved.'**
  String get resourceSavedConfirmation;

  /// No description provided for @resourceRemovedConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Resource removed from saved.'**
  String get resourceRemovedConfirmation;

  /// No description provided for @officialLocator.
  ///
  /// In en, this message translates to:
  /// **'Official locator'**
  String get officialLocator;

  /// No description provided for @provenance.
  ///
  /// In en, this message translates to:
  /// **'Provenance'**
  String get provenance;

  /// No description provided for @provenanceBody.
  ///
  /// In en, this message translates to:
  /// **'Paired from the official WHO Chinese and English fact-sheet indexes on 14 July 2026. Only titles and locators are stored; source bodies remain on WHO\'s website.'**
  String get provenanceBody;

  /// No description provided for @versionHistory.
  ///
  /// In en, this message translates to:
  /// **'Version history'**
  String get versionHistory;

  /// No description provided for @versionCurrentEntry.
  ///
  /// In en, this message translates to:
  /// **'Current reviewed version · active in this catalog'**
  String get versionCurrentEntry;

  /// No description provided for @versionSupersededEntry.
  ///
  /// In en, this message translates to:
  /// **'Previous version · retained only for traceability'**
  String get versionSupersededEntry;

  /// No description provided for @relevantPassages.
  ///
  /// In en, this message translates to:
  /// **'Relevant passages'**
  String get relevantPassages;

  /// No description provided for @relatedSources.
  ///
  /// In en, this message translates to:
  /// **'Related sources'**
  String get relatedSources;

  /// No description provided for @stableInternalReference.
  ///
  /// In en, this message translates to:
  /// **'Stable internal reference'**
  String get stableInternalReference;

  /// No description provided for @copyCitation.
  ///
  /// In en, this message translates to:
  /// **'Copy citation'**
  String get copyCitation;

  /// No description provided for @citationCopied.
  ///
  /// In en, this message translates to:
  /// **'Citation copied.'**
  String get citationCopied;

  /// No description provided for @copyOfficialLocator.
  ///
  /// In en, this message translates to:
  /// **'Copy official locator'**
  String get copyOfficialLocator;

  /// No description provided for @officialLocatorCopied.
  ///
  /// In en, this message translates to:
  /// **'Official locator copied.'**
  String get officialLocatorCopied;

  /// No description provided for @resourceCitation.
  ///
  /// In en, this message translates to:
  /// **'{title}. {publisher}. {year}. {locator}'**
  String resourceCitation(
    String title,
    String publisher,
    String year,
    String locator,
  );

  /// No description provided for @noResourceResultsTitle.
  ///
  /// In en, this message translates to:
  /// **'No matching resources'**
  String get noResourceResultsTitle;

  /// No description provided for @noResourceResultsBody.
  ///
  /// In en, this message translates to:
  /// **'Try another term or clear one or more filters.'**
  String get noResourceResultsBody;

  /// No description provided for @noSavedResourcesTitle.
  ///
  /// In en, this message translates to:
  /// **'No saved resources'**
  String get noSavedResourcesTitle;

  /// No description provided for @noSavedResourcesBody.
  ///
  /// In en, this message translates to:
  /// **'Save a source from Search to keep it available here.'**
  String get noSavedResourcesBody;

  /// No description provided for @noRecentUpdatesTitle.
  ///
  /// In en, this message translates to:
  /// **'No recent updates'**
  String get noRecentUpdatesTitle;

  /// No description provided for @noRecentUpdatesBody.
  ///
  /// In en, this message translates to:
  /// **'Reviewed source updates will appear here when available.'**
  String get noRecentUpdatesBody;

  /// No description provided for @sourceRegistrySubtitle.
  ///
  /// In en, this message translates to:
  /// **'Organizations represented in the current local catalog.'**
  String get sourceRegistrySubtitle;

  /// No description provided for @viewOrganizationSources.
  ///
  /// In en, this message translates to:
  /// **'View sources'**
  String get viewOrganizationSources;

  /// No description provided for @reviewedSourceCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{No catalog sources} =1{1 catalog source} other{{count} catalog sources}}'**
  String reviewedSourceCount(int count);

  /// No description provided for @loadingMedicalResources.
  ///
  /// In en, this message translates to:
  /// **'Loading medical resources'**
  String get loadingMedicalResources;

  /// No description provided for @resourceOfflineTitle.
  ///
  /// In en, this message translates to:
  /// **'Resources are unavailable offline'**
  String get resourceOfflineTitle;

  /// No description provided for @resourceOfflineBody.
  ///
  /// In en, this message translates to:
  /// **'Reconnect to verify current source status. Saved references remain listed without cached full text.'**
  String get resourceOfflineBody;

  /// No description provided for @resourceServiceFailureTitle.
  ///
  /// In en, this message translates to:
  /// **'Medical resources could not be loaded'**
  String get resourceServiceFailureTitle;

  /// No description provided for @resourceServiceFailureBody.
  ///
  /// In en, this message translates to:
  /// **'The source service did not respond. No patient or query content was sent.'**
  String get resourceServiceFailureBody;

  /// No description provided for @resourcePartialIndexTitle.
  ///
  /// In en, this message translates to:
  /// **'Some reviewed sources are temporarily unavailable'**
  String get resourcePartialIndexTitle;

  /// No description provided for @resourcePartialIndexBody.
  ///
  /// In en, this message translates to:
  /// **'Results may be incomplete while the current source index is restored.'**
  String get resourcePartialIndexBody;

  /// No description provided for @resourceRetry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get resourceRetry;

  /// No description provided for @resourceUpdatedLabel.
  ///
  /// In en, this message translates to:
  /// **'Catalog verified {date}'**
  String resourceUpdatedLabel(String date);

  /// No description provided for @resourceTitleRespiratory.
  ///
  /// In en, this message translates to:
  /// **'Safe antibiotic decisions for uncomplicated respiratory symptoms'**
  String get resourceTitleRespiratory;

  /// No description provided for @resourcePassageRespiratory.
  ///
  /// In en, this message translates to:
  /// **'Review symptom duration, severity, red flags, and likely viral features before considering antimicrobial treatment.'**
  String get resourcePassageRespiratory;

  /// No description provided for @resourcePassageRespiratoryDetail.
  ///
  /// In en, this message translates to:
  /// **'Document the clinical rationale and give a clear follow-up threshold when immediate antibiotics are not indicated.'**
  String get resourcePassageRespiratoryDetail;

  /// No description provided for @resourceTitleHypertension.
  ///
  /// In en, this message translates to:
  /// **'Primary-care follow-up pathway for stable hypertension'**
  String get resourceTitleHypertension;

  /// No description provided for @resourcePassageHypertension.
  ///
  /// In en, this message translates to:
  /// **'Use consistent blood-pressure technique, review adherence and adverse effects, and agree on a practical follow-up interval.'**
  String get resourcePassageHypertension;

  /// No description provided for @resourcePassageHypertensionDetail.
  ///
  /// In en, this message translates to:
  /// **'Escalate promptly when severe readings occur with concerning symptoms or evidence of acute organ injury.'**
  String get resourcePassageHypertensionDetail;

  /// No description provided for @resourceTitleDiabetes.
  ///
  /// In en, this message translates to:
  /// **'Sick-day safety education for adults living with type 2 diabetes'**
  String get resourceTitleDiabetes;

  /// No description provided for @resourcePassageDiabetes.
  ///
  /// In en, this message translates to:
  /// **'Explain hydration, monitoring, warning signs, and when to contact a clinician without independently changing prescribed medicines.'**
  String get resourcePassageDiabetes;

  /// No description provided for @resourcePassageDiabetesDetail.
  ///
  /// In en, this message translates to:
  /// **'Patient-facing wording should be checked against the current prescription and the connected clinician\'s instructions.'**
  String get resourcePassageDiabetesDetail;

  /// No description provided for @resourceTitleStroke.
  ///
  /// In en, this message translates to:
  /// **'Transition checklist after stroke rehabilitation discharge'**
  String get resourceTitleStroke;

  /// No description provided for @resourcePassageStroke.
  ///
  /// In en, this message translates to:
  /// **'This earlier checklist covered medication reconciliation, mobility support, caregiver communication, and follow-up ownership.'**
  String get resourcePassageStroke;

  /// No description provided for @resourcePassageStrokeDetail.
  ///
  /// In en, this message translates to:
  /// **'A newer transition standard replaces this version; retain it only to understand prior documentation.'**
  String get resourcePassageStrokeDetail;

  /// No description provided for @resourceOfficialMetadataStatus.
  ///
  /// In en, this message translates to:
  /// **'Official catalog metadata'**
  String get resourceOfficialMetadataStatus;

  /// No description provided for @rightsReviewPending.
  ///
  /// In en, this message translates to:
  /// **'Rights review pending—official link only'**
  String get rightsReviewPending;

  /// No description provided for @resourceCatalogMetadataNote.
  ///
  /// In en, this message translates to:
  /// **'Open either official WHO language page to read the source. Dr. AI stores only paired titles and locators; the content is not yet eligible for excerpts, embeddings, or AI retrieval.'**
  String get resourceCatalogMetadataNote;

  /// No description provided for @catalogVerifiedLabel.
  ///
  /// In en, this message translates to:
  /// **'Catalog verified'**
  String get catalogVerifiedLabel;

  /// No description provided for @documentFactSheet.
  ///
  /// In en, this message translates to:
  /// **'Fact sheet'**
  String get documentFactSheet;

  /// No description provided for @documentClinicalGuideline.
  ///
  /// In en, this message translates to:
  /// **'Clinical guideline'**
  String get documentClinicalGuideline;

  /// No description provided for @documentClinicalProtocol.
  ///
  /// In en, this message translates to:
  /// **'Clinical protocol'**
  String get documentClinicalProtocol;

  /// No description provided for @documentPracticeGuideline.
  ///
  /// In en, this message translates to:
  /// **'Practice guideline'**
  String get documentPracticeGuideline;

  /// No description provided for @documentGuidance.
  ///
  /// In en, this message translates to:
  /// **'Guidance'**
  String get documentGuidance;

  /// No description provided for @organizationWorldHealthOrganization.
  ///
  /// In en, this message translates to:
  /// **'World Health Organization'**
  String get organizationWorldHealthOrganization;

  /// No description provided for @topicInfectiousDisease.
  ///
  /// In en, this message translates to:
  /// **'Infectious diseases'**
  String get topicInfectiousDisease;

  /// No description provided for @topicChronicDisease.
  ///
  /// In en, this message translates to:
  /// **'Chronic diseases'**
  String get topicChronicDisease;

  /// No description provided for @topicMaternalChildHealth.
  ///
  /// In en, this message translates to:
  /// **'Maternal and child health'**
  String get topicMaternalChildHealth;

  /// No description provided for @topicMentalHealth.
  ///
  /// In en, this message translates to:
  /// **'Mental health'**
  String get topicMentalHealth;

  /// No description provided for @topicInjuryEmergency.
  ///
  /// In en, this message translates to:
  /// **'Injury and emergency care'**
  String get topicInjuryEmergency;

  /// No description provided for @topicEnvironmentalHealth.
  ///
  /// In en, this message translates to:
  /// **'Environmental health'**
  String get topicEnvironmentalHealth;

  /// No description provided for @topicNutritionLifestyle.
  ///
  /// In en, this message translates to:
  /// **'Nutrition and lifestyle'**
  String get topicNutritionLifestyle;

  /// No description provided for @topicHealthSystems.
  ///
  /// In en, this message translates to:
  /// **'Health systems and safety'**
  String get topicHealthSystems;

  /// No description provided for @showMoreResources.
  ///
  /// In en, this message translates to:
  /// **'Show 20 more resources'**
  String get showMoreResources;

  /// No description provided for @catalogUseStatus.
  ///
  /// In en, this message translates to:
  /// **'Catalog and retrieval status'**
  String get catalogUseStatus;

  /// No description provided for @bilingualChineseEnglish.
  ///
  /// In en, this message translates to:
  /// **'Bilingual: Chinese and English'**
  String get bilingualChineseEnglish;

  /// No description provided for @languageChinese.
  ///
  /// In en, this message translates to:
  /// **'Chinese'**
  String get languageChinese;

  /// No description provided for @languageEnglish.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get languageEnglish;

  /// No description provided for @organizationNationalHealthCommission.
  ///
  /// In en, this message translates to:
  /// **'National Health Commission of China'**
  String get organizationNationalHealthCommission;

  /// No description provided for @chineseOfficialSource.
  ///
  /// In en, this message translates to:
  /// **'Official Chinese page'**
  String get chineseOfficialSource;

  /// No description provided for @englishOfficialSource.
  ///
  /// In en, this message translates to:
  /// **'Official English page'**
  String get englishOfficialSource;

  /// No description provided for @copyEnglishOfficialLocator.
  ///
  /// In en, this message translates to:
  /// **'Copy English official locator'**
  String get copyEnglishOfficialLocator;

  /// No description provided for @englishOfficialLocatorCopied.
  ///
  /// In en, this message translates to:
  /// **'English official locator copied.'**
  String get englishOfficialLocatorCopied;

  /// No description provided for @close.
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get close;

  /// No description provided for @readOriginalText.
  ///
  /// In en, this message translates to:
  /// **'Read original text'**
  String get readOriginalText;

  /// No description provided for @openOfficialSource.
  ///
  /// In en, this message translates to:
  /// **'Open official source'**
  String get openOfficialSource;

  /// No description provided for @originalEnglish.
  ///
  /// In en, this message translates to:
  /// **'Original English'**
  String get originalEnglish;

  /// No description provided for @backToResources.
  ///
  /// In en, this message translates to:
  /// **'Back to resources'**
  String get backToResources;

  /// No description provided for @resourceReaderTitle.
  ///
  /// In en, this message translates to:
  /// **'Original document'**
  String get resourceReaderTitle;

  /// No description provided for @resourceReaderReviewPending.
  ///
  /// In en, this message translates to:
  /// **'Medical review pending'**
  String get resourceReaderReviewPending;

  /// No description provided for @resourceReaderReviewApproved.
  ///
  /// In en, this message translates to:
  /// **'Medical review approved'**
  String get resourceReaderReviewApproved;

  /// No description provided for @resourceReaderNotice.
  ///
  /// In en, this message translates to:
  /// **'Publisher-authored original text for doctor reference. This foreign-jurisdiction document is not currently used for AI retrieval or patient-facing answers.'**
  String get resourceReaderNotice;

  /// No description provided for @resourceReaderUnavailableTitle.
  ///
  /// In en, this message translates to:
  /// **'Original text is not available'**
  String get resourceReaderUnavailableTitle;

  /// No description provided for @resourceReaderUnavailableBody.
  ///
  /// In en, this message translates to:
  /// **'This source does not currently have stored text approved for display. Use the official publisher source instead.'**
  String get resourceReaderUnavailableBody;

  /// No description provided for @resourceReaderLoadFailedTitle.
  ///
  /// In en, this message translates to:
  /// **'The original document could not be loaded'**
  String get resourceReaderLoadFailedTitle;

  /// No description provided for @resourceReaderLoadFailedBody.
  ///
  /// In en, this message translates to:
  /// **'Check your connection and try again. No patient information was sent.'**
  String get resourceReaderLoadFailedBody;

  /// No description provided for @resourceReaderRetry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get resourceReaderRetry;

  /// No description provided for @publicationDateLabel.
  ///
  /// In en, this message translates to:
  /// **'Published'**
  String get publicationDateLabel;

  /// No description provided for @captureDateLabel.
  ///
  /// In en, this message translates to:
  /// **'Captured'**
  String get captureDateLabel;

  /// No description provided for @rightsAndAttribution.
  ///
  /// In en, this message translates to:
  /// **'Rights and attribution'**
  String get rightsAndAttribution;

  /// No description provided for @copyDocumentCitation.
  ///
  /// In en, this message translates to:
  /// **'Copy document citation'**
  String get copyDocumentCitation;

  /// No description provided for @reviewedChineseTranslation.
  ///
  /// In en, this message translates to:
  /// **'Reviewed Chinese translation'**
  String get reviewedChineseTranslation;

  /// No description provided for @unofficialAiTranslationNotice.
  ///
  /// In en, this message translates to:
  /// **'This is an unofficial AI-generated Chinese translation that has completed medical and native-Chinese review. Use the publisher\'s English original for authoritative verification. The translation remains separate from retrieval approval.'**
  String get unofficialAiTranslationNotice;

  /// No description provided for @financialDetails.
  ///
  /// In en, this message translates to:
  /// **'Financial details'**
  String get financialDetails;

  /// No description provided for @financialDetailsDescription.
  ///
  /// In en, this message translates to:
  /// **'Financial information belongs to the billable service or product that produced it.'**
  String get financialDetailsDescription;

  /// No description provided for @billableClinicalItem.
  ///
  /// In en, this message translates to:
  /// **'This clinical item is billable'**
  String get billableClinicalItem;

  /// No description provided for @billableClinicalItemDescription.
  ///
  /// In en, this message translates to:
  /// **'Leave this off when the record is clinical documentation only.'**
  String get billableClinicalItemDescription;

  /// No description provided for @costStatus.
  ///
  /// In en, this message translates to:
  /// **'Cost status'**
  String get costStatus;

  /// No description provided for @costPending.
  ///
  /// In en, this message translates to:
  /// **'Cost pending'**
  String get costPending;

  /// No description provided for @costEstimate.
  ///
  /// In en, this message translates to:
  /// **'Estimate'**
  String get costEstimate;

  /// No description provided for @costFinal.
  ///
  /// In en, this message translates to:
  /// **'Final'**
  String get costFinal;

  /// No description provided for @currency.
  ///
  /// In en, this message translates to:
  /// **'Currency'**
  String get currency;

  /// No description provided for @pendingCostSubmissionBlocked.
  ///
  /// In en, this message translates to:
  /// **'You can save the clinical record now. It cannot be selected for a payer request until the full allocation is recorded.'**
  String get pendingCostSubmissionBlocked;

  /// No description provided for @totalCostCny.
  ///
  /// In en, this message translates to:
  /// **'Total cost (CNY)'**
  String get totalCostCny;

  /// No description provided for @requestedFromPayerCny.
  ///
  /// In en, this message translates to:
  /// **'Requested from payer (CNY)'**
  String get requestedFromPayerCny;

  /// No description provided for @expectedPatientResponsibilityCny.
  ///
  /// In en, this message translates to:
  /// **'Expected patient responsibility (CNY)'**
  String get expectedPatientResponsibilityCny;

  /// No description provided for @financialAllocationNotice.
  ///
  /// In en, this message translates to:
  /// **'Requested from payer is not a payment guarantee. Expected patient responsibility is not a final adjudicated obligation.'**
  String get financialAllocationNotice;

  /// No description provided for @financialAllocationValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter non-negative amounts. Requested payer amount plus expected patient responsibility must equal the total.'**
  String get financialAllocationValidation;

  /// No description provided for @imagingArtifactNotBillable.
  ///
  /// In en, this message translates to:
  /// **'The uploaded image and report are clinical evidence, not a second charge. A distinct imaging-procedure record is required before procedure costs can be captured.'**
  String get imagingArtifactNotBillable;

  /// No description provided for @editConsultationCost.
  ///
  /// In en, this message translates to:
  /// **'Complete or edit cost'**
  String get editConsultationCost;

  /// No description provided for @saveConsultationCost.
  ///
  /// In en, this message translates to:
  /// **'Save consultation cost'**
  String get saveConsultationCost;

  /// No description provided for @financialStatus.
  ///
  /// In en, this message translates to:
  /// **'Financial status'**
  String get financialStatus;

  /// No description provided for @noCostRecorded.
  ///
  /// In en, this message translates to:
  /// **'No cost recorded'**
  String get noCostRecorded;

  /// No description provided for @estimatedCost.
  ///
  /// In en, this message translates to:
  /// **'Estimated ¥{amount}'**
  String estimatedCost(String amount);

  /// No description provided for @finalCost.
  ///
  /// In en, this message translates to:
  /// **'Final ¥{amount}'**
  String finalCost(String amount);

  /// No description provided for @alreadySubmitted.
  ///
  /// In en, this message translates to:
  /// **'Already submitted'**
  String get alreadySubmitted;

  /// No description provided for @addCost.
  ///
  /// In en, this message translates to:
  /// **'Add cost'**
  String get addCost;

  /// No description provided for @completeCost.
  ///
  /// In en, this message translates to:
  /// **'Complete cost'**
  String get completeCost;

  /// No description provided for @editCost.
  ///
  /// In en, this message translates to:
  /// **'Edit cost'**
  String get editCost;

  /// No description provided for @saveCost.
  ///
  /// In en, this message translates to:
  /// **'Save cost'**
  String get saveCost;

  /// No description provided for @imagingProcedure.
  ///
  /// In en, this message translates to:
  /// **'Imaging procedure'**
  String get imagingProcedure;

  /// No description provided for @imagingProcedures.
  ///
  /// In en, this message translates to:
  /// **'Imaging procedures'**
  String get imagingProcedures;

  /// No description provided for @imagingProcedureDescription.
  ///
  /// In en, this message translates to:
  /// **'Create the ordered, scheduled, or performed service first. Scheduling and evidence remain separate from its financial companion.'**
  String get imagingProcedureDescription;

  /// No description provided for @clinicalDetails.
  ///
  /// In en, this message translates to:
  /// **'Clinical details'**
  String get clinicalDetails;

  /// No description provided for @procedureName.
  ///
  /// In en, this message translates to:
  /// **'Procedure name'**
  String get procedureName;

  /// No description provided for @modality.
  ///
  /// In en, this message translates to:
  /// **'Modality or procedure type'**
  String get modality;

  /// No description provided for @bodyRegion.
  ///
  /// In en, this message translates to:
  /// **'Body region'**
  String get bodyRegion;

  /// No description provided for @clinicalIndication.
  ///
  /// In en, this message translates to:
  /// **'Clinical indication or summary (optional)'**
  String get clinicalIndication;

  /// No description provided for @schedulingServiceDetails.
  ///
  /// In en, this message translates to:
  /// **'Scheduling and service details'**
  String get schedulingServiceDetails;

  /// No description provided for @scheduledDateTime.
  ///
  /// In en, this message translates to:
  /// **'Scheduled date and time'**
  String get scheduledDateTime;

  /// No description provided for @performedDateTime.
  ///
  /// In en, this message translates to:
  /// **'Performed date and time'**
  String get performedDateTime;

  /// No description provided for @createImagingProcedure.
  ///
  /// In en, this message translates to:
  /// **'Create imaging procedure'**
  String get createImagingProcedure;

  /// No description provided for @updateImagingProcedure.
  ///
  /// In en, this message translates to:
  /// **'Update imaging procedure'**
  String get updateImagingProcedure;

  /// No description provided for @editClinicalService.
  ///
  /// In en, this message translates to:
  /// **'Edit details'**
  String get editClinicalService;

  /// No description provided for @imagingProcedureSaved.
  ///
  /// In en, this message translates to:
  /// **'{name} saved.'**
  String imagingProcedureSaved(String name);

  /// No description provided for @noImagingProcedures.
  ///
  /// In en, this message translates to:
  /// **'No imaging procedure has been created for this Clinical Event.'**
  String get noImagingProcedures;

  /// No description provided for @imagingEvidence.
  ///
  /// In en, this message translates to:
  /// **'Imaging evidence and results'**
  String get imagingEvidence;

  /// No description provided for @selectImagingProcedure.
  ///
  /// In en, this message translates to:
  /// **'Imaging procedure'**
  String get selectImagingProcedure;

  /// No description provided for @attachEvidence.
  ///
  /// In en, this message translates to:
  /// **'Attach evidence'**
  String get attachEvidence;

  /// No description provided for @evidenceFileCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{No linked files} =1{1 linked file} other{{count} linked files}}'**
  String evidenceFileCount(int count);

  /// No description provided for @imagingProcedureValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter a procedure name, modality, and body region. Scheduled services need a scheduled time; performed or completed services need a performed time.'**
  String get imagingProcedureValidation;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'zh'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'zh':
      return AppLocalizationsZh();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
