"""Build the checked-in WHO + NHC metadata catalog and Flutter source.

Inputs are explicitly downloaded official WHO Chinese and English fact-sheet
indexes plus a reviewed manifest of official NHC guidelines. Only titles and
official locators are retained. Article bodies are never copied.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

ANCHOR_PATTERN = re.compile(
    r'href="(?P<href>/zh/news-room/fact-sheets/detail/[^"]+)"[^>]*>(?P<title>[^<]+)'
)
ENGLISH_ANCHOR_PATTERN = re.compile(
    r'href="(?P<href>/news-room/fact-sheets/detail/[^"]+)"[^>]*>(?P<title>[^<]+)'
)
WHO_INDEX = "https://www.who.int/zh/news-room/fact-sheets"
WHO_ENGLISH_INDEX = "https://www.who.int/news-room/fact-sheets"
WHO_RIGHTS = "https://www.who.int/about/policies/publishing/copyright"
NHC_HOME = "https://www.nhc.gov.cn/"
ALLOWED_SOURCE_TYPES = {
    "clinical_guideline",
    "clinical_protocol",
    "practice_guideline",
    "guidance",
}

TOPIC_KEYWORDS = {
    "maternal_child_health": ("儿童", "新生儿", "孕", "妇女", "乳", "避孕", "流产"),
    "mental_health": ("精神", "焦虑", "抑郁", "自杀", "暴力", "虐待", "赌博"),
    "nutrition_lifestyle": ("饮食", "营养", "肥胖", "烟草", "酒精", "钠", "身体活动"),
    "environmental_health": ("污染", "环境", "气候", "辐射", "石棉", "铅", "汞", "砷"),
    "injury_emergency": ("伤", "中毒", "溺水", "烧伤", "咬伤", "急", "败血症"),
    "chronic_disease": (
        "癌",
        "糖尿病",
        "高血压",
        "心血管",
        "卒中",
        "哮喘",
        "慢性",
        "痴呆",
        "关节炎",
    ),
    "health_systems": ("卫生服务", "患者安全", "初级卫生", "健康素养", "基本药物"),
}

PRIMARY_CARE_PRIORITY = (
    "高血压",
    "糖尿病",
    "哮喘",
    "慢性阻塞性肺病",
    "心血管疾病",
    "卒中",
    "癌症",
    "乳腺癌",
    "宫颈癌",
    "肺癌",
    "结直肠癌",
    "季节性流感",
    "儿童肺炎",
    "结核病",
    "冠状病毒病（COVID-19）",
    "腹泻病",
    "败血症",
    "抗微生物药物耐药性",
    "艾滋病毒和艾滋病",
    "甲型肝炎",
    "乙型肝炎",
    "丙型肝炎",
    "麻疹",
    "狂犬病",
    "破伤风",
    "登革热和重症登革热",
    "疟疾",
    "身体活动",
    "健康饮食",
    "肥胖和超重",
    "减少钠摄入",
    "烟草",
    "酒精",
    "精神卫生",
    "焦虑症",
    "抑郁障碍（抑郁症）",
    "老年人的精神卫生",
    "痴呆症",
    "老龄化与健康",
    "妇女健康",
    "儿童：提高存活率和增进福祉",
    "新生儿：提高存活率和增进福祉",
    "计划生育/避孕",
    "贫血症",
    "营养不良",
    "患者安全",
    "初级卫生保健",
    "基本药物",
    "健康素养",
    "康复",
    "跌伤",
    "烧伤",
    "溺水",
    "动物咬伤",
    "食品安全",
    "环境（室外）空气污染和健康",
    "家庭空气污染",
    "饮用水",
    "高温与健康",
)

TOPIC_SEARCH_METADATA = {
    "infectious_disease": (
        "传染病与感染性疾病",
        ["感染", "传染病", "infectious disease", "infection"],
    ),
    "chronic_disease": ("慢性病", ["慢性病", "长期健康问题", "chronic disease"]),
    "maternal_child_health": (
        "妇幼健康",
        ["妇女", "孕产妇", "儿童", "maternal health", "child health"],
    ),
    "mental_health": ("心理与精神健康", ["心理健康", "精神健康", "mental health"]),
    "injury_emergency": ("伤害与急救", ["急救", "伤害", "emergency", "injury"]),
    "environmental_health": ("环境健康", ["环境卫生", "environmental health"]),
    "nutrition_lifestyle": ("营养与生活方式", ["营养", "生活方式", "nutrition", "lifestyle"]),
    "health_systems": (
        "卫生系统与健康服务",
        ["医疗服务", "公共卫生", "health services", "health system"],
    ),
}

TITLE_SEARCH_ALIASES = {
    "高血压": ["血压高", "血压", "high blood pressure"],
    "糖尿病": ["血糖高", "血糖", "diabetes mellitus"],
    "哮喘": ["喘息", "气喘", "asthma attack"],
    "慢性阻塞性肺病": ["慢阻肺", "呼吸困难", "COPD"],
    "心血管疾病": ["心脏病", "心血管", "CVD"],
    "卒中": ["中风", "脑卒中", "stroke"],
    "流感（季节性）": ["流行性感冒", "发热", "influenza", "flu"],
    "肺炎": ["咳嗽", "发热", "呼吸困难", "pneumonia"],
    "结核病": ["肺结核", "咳嗽", "tuberculosis", "TB"],
    "抑郁症": ["抑郁", "情绪低落", "depression"],
    "焦虑症": ["焦虑", "紧张", "anxiety"],
    "痴呆": ["认知下降", "记忆力下降", "dementia"],
    "肥胖和超重": ["体重超标", "BMI", "obesity", "overweight"],
    "健康饮食": ["膳食", "饮食", "healthy diet"],
    "身体活动": ["运动", "锻炼", "physical activity", "exercise"],
    "抗微生物药物耐药性": ["抗生素耐药", "耐药", "AMR", "antimicrobial resistance"],
    "艾滋病毒和艾滋病": ["HIV", "AIDS", "艾滋病"],
    "狂犬病": ["狗咬", "动物咬伤", "rabies"],
    "烧伤": ["烫伤", "灼伤", "burns"],
    "溺水": ["淹溺", "drowning"],
}


def search_metadata(
    *,
    title: str,
    title_en: str | None,
    topic: str,
    source_type: str,
    publisher_name: str,
    original_language: str,
) -> tuple[str, list[str]]:
    """Build searchable catalog metadata without claiming to summarize unstored bodies."""

    topic_label, topic_terms = TOPIC_SEARCH_METADATA[topic]
    aliases = TITLE_SEARCH_ALIASES.get(title, [])
    keywords = list(
        dict.fromkeys([title, *(title_en and [title_en] or []), *aliases, *topic_terms])
    )
    type_label = {
        "fact_sheet": "事实清单",
        "clinical_guideline": "临床指南",
        "clinical_protocol": "诊疗方案",
        "practice_guideline": "实践指南",
        "guidance": "指导文件",
    }[source_type]
    if original_language == "en":
        summary = (
            f"Official {source_type.replace('_', ' ')} from {publisher_name} about {title}. "
            "This catalog summary describes verified metadata only; article text is not stored."
        )
    else:
        summary = (
            f"{publisher_name}发布的《{title}》官方{type_label}，归入{topic_label}。"
            "此目录摘要仅描述已核验的元数据，尚未存储或概括文章正文。"
        )
    return summary, keywords


def topic_for(title: str) -> str:
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in title for keyword in keywords):
            return topic
    return "infectious_disease"


def dart_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def load_nhc_manifest(path: Path) -> tuple[dict[str, object], bytes]:
    raw = path.read_bytes()
    manifest = json.loads(raw)
    if manifest.get("schema_version") != "1.0":
        raise ValueError("Unsupported NHC manifest schema version.")
    checksum = str(manifest.get("rights_evidence_checksum", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("NHC rights evidence checksum must be SHA-256.")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("NHC manifest must contain at least one source.")
    locators: set[str] = set()
    for item in sources:
        if not isinstance(item, dict):
            raise ValueError("Every NHC source must be an object.")
        if set(item) != {"title", "canonical_locator", "source_type", "topic"}:
            raise ValueError("NHC sources must use the reviewed metadata-only schema.")
        locator = str(item["canonical_locator"])
        if urlparse(locator).scheme != "https" or urlparse(locator).hostname != "www.nhc.gov.cn":
            raise ValueError(f"NHC source is outside the verified official domain: {locator}")
        if locator in locators:
            raise ValueError(f"Duplicate NHC canonical locator: {locator}")
        if item["source_type"] not in ALLOWED_SOURCE_TYPES:
            raise ValueError(f"Unsupported NHC source type: {item['source_type']}")
        if item["topic"] not in {*TOPIC_KEYWORDS, "infectious_disease"}:
            raise ValueError(f"Unsupported NHC topic: {item['topic']}")
        locators.add(locator)
    return manifest, raw


def build_catalog(
    index_path: Path,
    english_index_path: Path,
    rights_path: Path,
    limit: int | None,
    generated_at: datetime,
    nhc_manifest_path: Path | None = None,
) -> dict[str, object]:
    raw = index_path.read_bytes()
    text = raw.decode("utf-8")
    seen: set[str] = set()
    chinese_entries: list[tuple[str, str, str]] = []
    for match in ANCHOR_PATTERN.finditer(text):
        locator = urljoin(WHO_INDEX, html.unescape(match.group("href")))
        title = html.unescape(match.group("title")).strip().replace("\u200e", "")
        if locator in seen:
            continue
        seen.add(locator)
        slug = locator.rsplit("/", 1)[-1]
        chinese_entries.append((title, locator, slug))

    english_raw = english_index_path.read_bytes()
    english_text = english_raw.decode("utf-8")
    english_by_slug: dict[str, tuple[str, str]] = {}
    for match in ENGLISH_ANCHOR_PATTERN.finditer(english_text):
        locator = urljoin(WHO_ENGLISH_INDEX, html.unescape(match.group("href")))
        title = html.unescape(match.group("title")).strip()
        slug = locator.rsplit("/", 1)[-1]
        english_by_slug.setdefault(slug, (title, locator))

    bilingual_entries = [
        (title_zh, locator_zh, slug, *english_by_slug[slug])
        for title_zh, locator_zh, slug in chinese_entries
        if slug in english_by_slug
    ]
    by_title = {entry[0]: entry for entry in bilingual_entries}
    prioritized = [by_title[title] for title in PRIMARY_CARE_PRIORITY if title in by_title]
    priority_titles = {entry[0] for entry in prioritized}
    bilingual_entries = prioritized + [
        entry for entry in bilingual_entries if entry[0] not in priority_titles
    ]
    paired_slugs = {entry[2] for entry in bilingual_entries}
    who_entries: list[tuple[str, str, str, str | None, str | None]] = [
        (title_zh, locator_zh, "zh-Hans", title_en, locator_en)
        for title_zh, locator_zh, _slug, title_en, locator_en in bilingual_entries
    ]
    who_entries.extend(
        (title_zh, locator_zh, "zh-Hans", None, None)
        for title_zh, locator_zh, slug in chinese_entries
        if slug not in paired_slugs
    )
    who_entries.extend(
        (title_en, locator_en, "en", None, None)
        for slug, (title_en, locator_en) in english_by_slug.items()
        if slug not in paired_slugs
    )
    if limit is not None:
        who_entries = who_entries[:limit]

    source_checksum = hashlib.sha256(raw).hexdigest()
    english_source_checksum = hashlib.sha256(english_raw).hexdigest()
    rights_checksum = hashlib.sha256(rights_path.read_bytes()).hexdigest()
    timestamp = generated_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    sources: list[dict[str, object]] = []
    for title, locator, original_language, title_en, locator_en in who_entries:
        translations = (
            [{"language": "en", "title": title_en, "official_locator": locator_en}]
            if title_en and locator_en
            else []
        )
        locator_digest = hashlib.sha256(locator.encode()).hexdigest()[:16].upper()
        language_code = "ZH" if original_language == "zh-Hans" else "EN"
        summary, search_keywords = search_metadata(
            title=title,
            title_en=title_en,
            topic=topic_for(title),
            source_type="fact_sheet",
            publisher_name="世界卫生组织",
            original_language=original_language,
        )
        metadata_checksum = hashlib.sha256(
            json.dumps(
                {
                    "title": title,
                    "locator": locator,
                    "official_translations": translations,
                    "catalog_summary": summary,
                    "search_keywords": search_keywords,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        sources.append(
            {
                "stable_id": f"KBS-WHO-{language_code}-{locator_digest}",
                "publisher_stable_id": "KBP-WHO",
                "rights_record_stable_id": "KBR-WHO-LINK-ONLY-PENDING",
                "title": title,
                "canonical_locator": locator,
                "source_type": "fact_sheet",
                "jurisdiction": "GLOBAL",
                "intended_audiences": ["doctor"],
                "topic": topic_for(title),
                "original_language": original_language,
                "official_translations": translations,
                "catalog_summary": summary,
                "search_keywords": search_keywords,
                "authority_tier": "B",
                "lifecycle_state": "rights_pending",
                "catalog_visible": True,
                "catalog_verified_at": timestamp,
                "metadata_checksum": metadata_checksum,
            }
        )
    supplemental_discovery_sources: list[dict[str, str]] = []
    nhc_manifest: dict[str, object] | None = None
    if nhc_manifest_path is not None:
        nhc_manifest, nhc_raw = load_nhc_manifest(nhc_manifest_path)
        supplemental_discovery_sources.append(
            {
                "locator": str(nhc_manifest["discovery_source_locator"]),
                "checksum": hashlib.sha256(nhc_raw).hexdigest(),
            }
        )
        for item in nhc_manifest["sources"]:
            locator = str(item["canonical_locator"])
            locator_digest = hashlib.sha256(locator.encode()).hexdigest()[:16].upper()
            summary, search_keywords = search_metadata(
                title=str(item["title"]),
                title_en=None,
                topic=str(item["topic"]),
                source_type=str(item["source_type"]),
                publisher_name="国家卫生健康委员会",
                original_language="zh-Hans",
            )
            metadata = {
                "title": item["title"],
                "locator": locator,
                "official_translations": [],
                "catalog_summary": summary,
                "search_keywords": search_keywords,
            }
            sources.append(
                {
                    "stable_id": f"KBS-NHC-ZH-{locator_digest}",
                    "publisher_stable_id": "KBP-NHC",
                    "rights_record_stable_id": "KBR-NHC-LINK-ONLY-PENDING",
                    "title": item["title"],
                    "canonical_locator": locator,
                    "source_type": item["source_type"],
                    "jurisdiction": "CN",
                    "intended_audiences": ["doctor"],
                    "topic": item["topic"],
                    "original_language": "zh-Hans",
                    "official_translations": [],
                    "catalog_summary": summary,
                    "search_keywords": search_keywords,
                    "authority_tier": "A",
                    "lifecycle_state": "rights_pending",
                    "catalog_visible": True,
                    "catalog_verified_at": timestamp,
                    "metadata_checksum": hashlib.sha256(
                        json.dumps(
                            metadata,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                    ).hexdigest(),
                }
            )
    return {
        "schema_version": "1.0",
        "generated_at": timestamp,
        "discovery_source_locator": WHO_INDEX,
        "discovery_source_checksum": source_checksum,
        "translation_discovery_source_locator": WHO_ENGLISH_INDEX,
        "translation_discovery_source_checksum": english_source_checksum,
        "supplemental_discovery_sources": supplemental_discovery_sources,
        "publishers": [
            {
                "stable_id": "KBP-WHO",
                "official_name_zh": "世界卫生组织",
                "official_name_en": "World Health Organization",
                "organization_type": "intergovernmental_health_organization",
                "authority_basis": (
                    "Official WHO Chinese- and English-language fact-sheet publishing channels."
                ),
                "authority_evidence_locator": WHO_INDEX,
                "verified_domains": ["who.int", "www.who.int"],
                "jurisdiction": "GLOBAL",
                "allowed_content_classes": ["fact_sheet_metadata"],
            },
            *(
                [
                    {
                        "stable_id": "KBP-NHC",
                        "official_name_zh": "中华人民共和国国家卫生健康委员会",
                        "official_name_en": (
                            "National Health Commission of the People's Republic of China"
                        ),
                        "organization_type": "national_health_authority",
                        "authority_basis": (
                            "Official policy, guideline, and attachment publishing "
                            "channels of China's national health authority."
                        ),
                        "authority_evidence_locator": NHC_HOME,
                        "verified_domains": ["nhc.gov.cn", "www.nhc.gov.cn"],
                        "jurisdiction": "CN",
                        "allowed_content_classes": [
                            "guideline_metadata",
                            "clinical_protocol_metadata",
                        ],
                    }
                ]
                if nhc_manifest is not None
                else []
            ),
        ],
        "rights_records": [
            {
                "stable_id": "KBR-WHO-LINK-ONLY-PENDING",
                "publisher_stable_id": "KBP-WHO",
                "scope": "publisher",
                "evidence_locator": WHO_RIGHTS,
                "evidence_checksum": rights_checksum,
                "decision_status": "pending",
                "commercial_use_allowed": False,
                "storage_allowed": False,
                "transformation_allowed": False,
                "translation_allowed": False,
                "embedding_allowed": False,
                "excerpt_display_allowed": False,
                "model_provider_transmission_allowed": False,
                "redistribution_allowed": False,
                "prior_version_retention_allowed": False,
                "attribution_requirements": (
                    "Display WHO as publisher and link to the official page."
                ),
            },
            *(
                [
                    {
                        "stable_id": "KBR-NHC-LINK-ONLY-PENDING",
                        "publisher_stable_id": "KBP-NHC",
                        "scope": "publisher",
                        "evidence_locator": NHC_HOME,
                        "evidence_checksum": str(nhc_manifest["rights_evidence_checksum"]),
                        "decision_status": "pending",
                        "commercial_use_allowed": False,
                        "storage_allowed": False,
                        "transformation_allowed": False,
                        "translation_allowed": False,
                        "embedding_allowed": False,
                        "excerpt_display_allowed": False,
                        "model_provider_transmission_allowed": False,
                        "redistribution_allowed": False,
                        "prior_version_retention_allowed": False,
                        "attribution_requirements": (
                            "Display 国家卫生健康委员会 as publisher and link to the official page."
                        ),
                    }
                ]
                if nhc_manifest is not None
                else []
            ),
        ],
        "sources": sources,
    }


def render_dart(catalog: dict[str, object]) -> str:
    lines = [
        "// Generated by services/api/scripts/build_authoritative_catalog.py.",
        "// Contains official metadata and locators only; no article text is stored.",
        "",
        "enum MedicalResourceTopic {",
        "  infectiousDisease,",
        "  chronicDisease,",
        "  maternalChildHealth,",
        "  mentalHealth,",
        "  injuryEmergency,",
        "  environmentalHealth,",
        "  nutritionLifestyle,",
        "  healthSystems,",
        "}",
        "",
        "enum MedicalDocumentType {",
        "  factSheet,",
        "  clinicalGuideline,",
        "  clinicalProtocol,",
        "  practiceGuideline,",
        "  guidance,",
        "}",
        "enum MedicalOrganization { worldHealthOrganization, nationalHealthCommission }",
        "enum MedicalJurisdiction { international, china }",
        "enum MedicalResourceLanguage { bilingualChineseEnglish, chinese, english }",
        "enum MedicalAudience { doctors }",
        "enum MedicalVersionStatus { current, superseded }",
        "enum MedicalRightsStatus { linkOnlyPending }",
        "",
        "class MedicalResourceFixture {",
        "  const MedicalResourceFixture({",
        "    required this.id,",
        "    required this.stableReference,",
        "    required this.title,",
        "    this.titleEn,",
        "    required this.catalogSummary,",
        "    required this.searchKeywords,",
        "    required this.officialLocator,",
        "    this.englishOfficialLocator,",
        "    required this.documentType,",
        "    required this.organization,",
        "    required this.jurisdiction,",
        "    required this.language,",
        "    required this.topic,",
        "    required this.catalogVerifiedAt,",
        "  });",
        "",
        "  final String id;",
        "  final String stableReference;",
        "  final String title;",
        "  final String? titleEn;",
        "  final String catalogSummary;",
        "  final List<String> searchKeywords;",
        "  final String officialLocator;",
        "  final String? englishOfficialLocator;",
        "  final MedicalDocumentType documentType;",
        "  final MedicalOrganization organization;",
        "  final MedicalJurisdiction jurisdiction;",
        "  final MedicalResourceLanguage language;",
        "  final MedicalResourceTopic topic;",
        "  final DateTime catalogVerifiedAt;",
        "  MedicalAudience get audience => MedicalAudience.doctors;",
        "  MedicalVersionStatus get versionStatus => MedicalVersionStatus.current;",
        "  MedicalRightsStatus get rightsStatus => MedicalRightsStatus.linkOnlyPending;",
        "  bool get patientUseEligible => false;",
        "}",
        "",
        "final List<MedicalResourceFixture> authoritativeMedicalResourceCatalog =",
        "    <MedicalResourceFixture>[",
    ]
    generated_at = datetime.fromisoformat(str(catalog["generated_at"]).replace("Z", "+00:00"))
    for source in catalog["sources"]:
        translation = next(
            (item for item in source["official_translations"] if item["language"] == "en"),
            None,
        )
        topic = "".join(
            part.capitalize() if index else part
            for index, part in enumerate(str(source["topic"]).split("_"))
        )
        document_type = {
            "fact_sheet": "factSheet",
            "clinical_guideline": "clinicalGuideline",
            "clinical_protocol": "clinicalProtocol",
            "practice_guideline": "practiceGuideline",
            "guidance": "guidance",
        }[str(source["source_type"])]
        is_who = source["publisher_stable_id"] == "KBP-WHO"
        language = (
            "bilingualChineseEnglish"
            if translation is not None
            else "chinese"
            if source["original_language"] == "zh-Hans"
            else "english"
        )
        lines.extend(
            [
                "  MedicalResourceFixture(",
                f"    id: {dart_string(str(source['stable_id']))},",
                f"    stableReference: {dart_string(str(source['stable_id']))},",
                f"    title: {dart_string(str(source['title']))},",
                *(
                    [f"    titleEn: {dart_string(str(translation['title']))},"]
                    if translation is not None
                    else []
                ),
                f"    catalogSummary: {dart_string(str(source['catalog_summary']))},",
                "    searchKeywords: <String>["
                + ", ".join(dart_string(str(term)) for term in source["search_keywords"])
                + "],",
                f"    officialLocator: {dart_string(str(source['canonical_locator']))},",
                *(
                    [
                        "    englishOfficialLocator: "
                        f"{dart_string(str(translation['official_locator']))},"
                    ]
                    if translation is not None
                    else []
                ),
                f"    documentType: MedicalDocumentType.{document_type},",
                "    organization: MedicalOrganization."
                + ("worldHealthOrganization," if is_who else "nationalHealthCommission,"),
                "    jurisdiction: MedicalJurisdiction."
                + ("international," if is_who else "china,"),
                f"    language: MedicalResourceLanguage.{language},",
                f"    topic: MedicalResourceTopic.{topic},",
                "    catalogVerifiedAt: DateTime.utc(",
                f"      {generated_at.year}, {generated_at.month}, {generated_at.day},",
                "    ),",
                "  ),",
            ]
        )
    lines.extend(["];"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-html", type=Path, required=True)
    parser.add_argument("--english-index-html", type=Path, required=True)
    parser.add_argument("--rights-html", type=Path, required=True)
    parser.add_argument("--catalog-output", type=Path, required=True)
    parser.add_argument("--dart-output", type=Path, required=True)
    parser.add_argument("--nhc-manifest", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--generated-at", required=True)
    args = parser.parse_args()
    generated_at = datetime.fromisoformat(args.generated_at.replace("Z", "+00:00"))
    catalog = build_catalog(
        args.index_html,
        args.english_index_html,
        args.rights_html,
        args.limit,
        generated_at,
        args.nhc_manifest,
    )
    args.catalog_output.parent.mkdir(parents=True, exist_ok=True)
    args.catalog_output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.dart_output.write_text(render_dart(catalog), encoding="utf-8")


if __name__ == "__main__":
    main()
