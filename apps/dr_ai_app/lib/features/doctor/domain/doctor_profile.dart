class DoctorProfile {
  const DoctorProfile({
    required this.id,
    required this.displayName,
    required this.title,
    required this.hospitalName,
    this.birthDate,
    this.gender,
    this.contactPhone,
    this.avatarUrl,
    this.country,
    this.province,
    this.city,
    this.specialty,
    this.department,
    this.preferredLanguage,
  });

  factory DoctorProfile.fromJson(Map<String, dynamic> json) {
    return DoctorProfile(
      id: json['id'] as String,
      displayName: json['display_name'] as String,
      title: json['title'] as String,
      birthDate: json['birth_date'] as String?,
      gender: json['gender'] as String?,
      contactPhone: json['contact_phone'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      country: json['country'] as String?,
      province: json['province'] as String?,
      city: json['city'] as String?,
      hospitalName: json['hospital_name'] as String,
      specialty: json['specialty'] as String?,
      department: json['department'] as String?,
      preferredLanguage: json['preferred_language'] as String?,
    );
  }

  final String id;
  final String displayName;
  final String title;
  final String? birthDate;
  final String? gender;
  final String? contactPhone;
  final String? avatarUrl;
  final String? country;
  final String? province;
  final String? city;
  final String hospitalName;
  final String? specialty;
  final String? department;
  final String? preferredLanguage;
}
