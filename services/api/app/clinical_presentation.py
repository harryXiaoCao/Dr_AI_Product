from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from app.chatbot_contracts import SafetyCode


class UrgencyRoute(StrEnum):
    emergency_120 = "emergency_120"
    urgent_same_day = "urgent_same_day"
    clinician_contact = "clinician_contact"
    routine_education = "routine_education"


class PresentationViewKind(StrEnum):
    literal = "literal"
    clinical_presentation = "clinical_presentation"
    population_exposure = "population_exposure"
    requested_action = "requested_action"


class ContinuityReason(StrEnum):
    standalone = "standalone"
    explicit_reference = "explicit_reference"
    temporal_symptom_follow_up = "temporal_symptom_follow_up"
    pregnancy_dependency = "pregnancy_dependency"


@dataclass(frozen=True)
class BoundedContinuityResolution:
    """One-turn, user-only context admitted before safety and retrieval.

    ``analysis_message`` may contain the immediately preceding user turn so
    deterministic rules can understand an elliptical follow-up. ``literal_query``
    is always the current turn and remains the only literal retrieval view.
    """

    analysis_message: str
    literal_query: str
    reason: ContinuityReason
    carried_previous_user_turn: bool


@dataclass(frozen=True)
class PresentationRetrievalView:
    kind: PresentationViewKind
    text: str


@dataclass(frozen=True)
class ClinicalPresentation:
    """Deterministic, content-only representation of the user's presentation.

    The representation is intentionally descriptive. It is not a diagnosis,
    probability estimate, or model-generated clinical classification.
    """

    literal_query: str
    symptoms: tuple[str, ...] = ()
    anatomy: tuple[str, ...] = ()
    onset: tuple[str, ...] = ()
    duration: tuple[str, ...] = ()
    trajectory: tuple[str, ...] = ()
    severity: tuple[str, ...] = ()
    associated_signs: tuple[str, ...] = ()
    measurements: tuple[str, ...] = ()
    population: tuple[str, ...] = ()
    pregnancy: tuple[str, ...] = ()
    exposures: tuple[str, ...] = ()
    trauma: tuple[str, ...] = ()
    requested_actions: tuple[str, ...] = ()
    danger_signals: tuple[str, ...] = ()
    negated_concepts: tuple[str, ...] = ()
    hypothetical_concepts: tuple[str, ...] = ()

    def canonical_view(self, language: str = "zh-Hans") -> str:
        values = _labels_for(
            language,
            (
                (self.symptoms, SYMPTOM_LABELS),
                (self.anatomy, ANATOMY_LABELS),
                (self.onset, ONSET_LABELS),
                (self.trajectory, TRAJECTORY_LABELS),
                (self.severity, SEVERITY_LABELS),
                (self.associated_signs, SYMPTOM_LABELS),
                (self.population, POPULATION_LABELS),
                (self.pregnancy, PREGNANCY_LABELS),
                (self.exposures, EXPOSURE_LABELS),
                (self.trauma, TRAUMA_LABELS),
            ),
        )
        return " ".join(dict.fromkeys([*values, *self.duration, *self.measurements]))

    def population_exposure_view(self, language: str = "zh-Hans") -> str:
        return " ".join(
            _labels_for(
                language,
                (
                    (self.symptoms, SYMPTOM_LABELS),
                    (self.population, POPULATION_LABELS),
                    (self.pregnancy, PREGNANCY_LABELS),
                    (self.exposures, EXPOSURE_LABELS),
                    (self.trauma, TRAUMA_LABELS),
                ),
            )
        )

    def requested_action_view(self, language: str = "zh-Hans") -> str:
        return " ".join(
            _labels_for(
                language,
                (
                    (self.symptoms, SYMPTOM_LABELS),
                    (self.exposures, EXPOSURE_LABELS),
                    (self.trauma, TRAUMA_LABELS),
                    (self.requested_actions, ACTION_LABELS),
                ),
            )
        )

    def retrieval_views(self, language: str = "zh-Hans") -> tuple[PresentationRetrievalView, ...]:
        candidates = (
            PresentationRetrievalView(PresentationViewKind.literal, self.literal_query),
            PresentationRetrievalView(
                PresentationViewKind.clinical_presentation,
                self.canonical_view(language),
            ),
            PresentationRetrievalView(
                PresentationViewKind.population_exposure,
                self.population_exposure_view(language),
            ),
            PresentationRetrievalView(
                PresentationViewKind.requested_action,
                self.requested_action_view(language),
            ),
        )
        views: list[PresentationRetrievalView] = []
        normalized_seen: set[str] = set()
        for view in candidates:
            normalized = _normalized(view.text)
            if not normalized or normalized in normalized_seen:
                continue
            normalized_seen.add(normalized)
            views.append(view)
        return tuple(views)

    def central_concept_groups(self) -> tuple[tuple[str, ...], ...]:
        """Alias groups that evidence metadata must centrally represent.

        Negated concepts are intentionally absent. These groups describe only
        what the user actually reported and never add a disease diagnosis.
        """

        groups: list[tuple[str, ...]] = []
        for codes, aliases in (
            (self.symptoms, CONCEPT_ALIASES),
            (self.pregnancy, PREGNANCY_ALIASES),
            (self.exposures, EXPOSURE_ALIASES),
            (self.trauma, TRAUMA_ALIASES),
        ):
            groups.extend(aliases[code] for code in codes if code in aliases)
        return tuple(groups)

    def central_context_groups(self) -> tuple[tuple[str, ...], ...]:
        groups: list[tuple[str, ...]] = []
        for codes, aliases in (
            (self.pregnancy, PREGNANCY_ALIASES),
            (self.exposures, EXPOSURE_ALIASES),
            (self.trauma, TRAUMA_ALIASES),
        ):
            groups.extend(aliases[code] for code in codes if code in aliases)
        return tuple(groups)

    def central_symptom_groups(self) -> tuple[tuple[str, ...], ...]:
        return tuple(CONCEPT_ALIASES[code] for code in self.symptoms if code in CONCEPT_ALIASES)


@dataclass(frozen=True)
class SafetyAssessment:
    safety_code: SafetyCode
    urgency_route: UrgencyRoute
    rule_id: str | None = None
    guidance_code: str | None = None
    presentation: ClinicalPresentation | None = None


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _labels_for(
    language: str,
    fields: tuple[tuple[tuple[str, ...], dict[str, tuple[str, str]]], ...],
) -> list[str]:
    index = 0 if language == "zh-Hans" else 1
    return [labels[code][index] for codes, labels in fields for code in codes if code in labels]


CONCEPT_ALIASES: dict[str, tuple[str, ...]] = {
    "fever": ("发烧", "发热", "高烧", "低烧", "fever"),
    "cough": ("咳嗽", "咳", "cough"),
    "sputum": ("咳痰", "痰", "sputum", "phlegm"),
    "breathing_difficulty": (
        "呼吸困难",
        "呼吸不畅",
        "呼吸费劲",
        "呼吸很费劲",
        "呼吸吃力",
        "呼吸很吃力",
        "喘不上气",
        "不能呼吸",
        "无法呼吸",
        "气短",
        "喘气",
        "喘",
        "上不来气",
        "喘不过气",
        "没正常呼吸",
        "shortness of breath",
        "short of breath",
        "difficulty breathing",
        "trouble breathing",
        "having trouble breathing",
        "hard to breathe",
        "breathless",
        "cannot breathe",
        "can't breathe",
    ),
    "chest_pressure": (
        "胸口像被石头压",
        "胸口像石头压",
        "压榨样",
        "胸部压迫感",
        "胸口有压迫感",
        "胸口发紧",
        "胸口压",
        "胸痛",
        "胸闷",
        "闷得慌",
        "chest pressure",
        "chest pain",
    ),
    "palpitations": (
        "心慌",
        "心悸",
        "心跳很快",
        "心跳突然很快",
        "心跳很乱",
        "跳得又快又乱",
        "蹦得又快又乱",
        "漏跳",
        "跳空",
        "palpitation",
        "irregular heartbeat",
    ),
    "abdominal_pain": (
        "腹痛",
        "肚子疼",
        "肚脐周围疼",
        "下腹痛",
        "上腹部",
        "上腹",
        "小肚子疼",
        "右下腹",
        "右上腹",
        "abdominal pain",
    ),
    "vomiting": (
        "呕吐",
        "一直吐",
        "吐了",
        "还吐",
        "又吐",
        "开始吐",
        "吐血",
        "vomit",
        "vomiting",
    ),
    "nausea": ("恶心", "反胃", "想吐", "nausea", "nauseous"),
    "diarrhea": (
        "腹泻",
        "拉肚子",
        "稀水样大便",
        "拉稀水",
        "又吐又拉",
        "吐拉",
        "diarrhea",
    ),
    "bleeding": (
        "出血",
        "流血",
        "血丝",
        "鲜血",
        "黑色",
        "柏油样",
        "好多血",
        "湿透",
        "止不住",
        "bleeding",
    ),
    "headache": ("头痛", "头疼", "headache"),
    "dizziness": (
        "头晕",
        "发晕",
        "老晕",
        "眼前发黑",
        "天旋地转",
        "dizzy",
        "dizziness",
    ),
    "weakness": (
        "没有力气",
        "没劲",
        "乏力",
        "无力",
        "发软",
        "浑身软",
        "weakness",
        "weak",
    ),
    "focal_neurologic_deficit": (
        "一侧手脚无力",
        "一边手脚没有力气",
        "一边手脚无力",
        "一边手脚没力",
        "一边没力",
        "半边没力",
        "嘴歪",
        "说话含糊",
        "说话不清",
        "话说不清",
        "突然说不出话",
        "one-sided weakness",
        "slurred speech",
        "face droop",
    ),
    "confusion": (
        "意识混乱",
        "说话混乱",
        "精神变差",
        "反应差",
        "叫错家人名字",
        "叫错人",
        "犯糊涂",
        "变糊涂",
        "说话乱",
        "confused",
        "confusion",
    ),
    "unresponsive": (
        "叫不醒",
        "没有清醒",
        "没反应",
        "没醒",
        "昏迷",
        "unresponsive",
        "unconscious",
    ),
    "seizure": ("抽搐", "抽了", "seizure", "convulsion"),
    "cyanosis": (
        "脸色发紫",
        "嘴唇发紫",
        "嘴唇紫",
        "发紫",
        "blue lips",
        "cyanosis",
    ),
    "choking": ("气道堵塞", "食物卡住", "卡住了", "choking"),
    "shock_signs": (
        "脸色苍白",
        "脸色发白",
        "脸白",
        "浑身冒冷汗",
        "冒冷汗",
        "冷汗",
        "头晕心慌",
        "pale",
        "cold sweat",
    ),
    "rash": ("红疹", "红点", "疙瘩", "满身疙瘩", "rash", "hives"),
    "swelling": ("肿了", "肿胀", "肿起来", "肿", "swelling"),
    "poor_feeding": ("不吃奶", "不进食", "poor feeding"),
    "decreased_fetal_movement": (
        "明显不怎么动",
        "明显不咋动",
        "几乎不动",
        "胎动减少",
        "不动了",
        "reduced fetal movement",
    ),
    "visual_change": (
        "视物模糊",
        "看东西模糊",
        "看东西发糊",
        "眼前闪光",
        "blurred vision",
    ),
    "wheeze": ("呼呼", "哮鸣", "喘鸣", "wheeze", "wheezing"),
    "night_sweats": ("盗汗", "夜里出汗", "夜间出汗", "night sweats"),
    "weight_loss": ("瘦了不少", "瘦了", "明显变瘦", "体重下降", "weight loss"),
    "abdominal_distension": ("肚子胀", "腹胀", "腹部胀", "abdominal distension"),
    "constipation": ("没有排便", "没排便", "没拉", "便秘", "constipation"),
    "tarry_stool": ("柏油", "黑便", "大便是黑色", "tarry stool", "black stool"),
    "rectal_bleeding": ("大便里有鲜血", "便血", "血便", "blood in stool"),
    "heartburn": ("烧灼", "烧心", "反酸", "heartburn", "acid reflux"),
    "photophobia": ("怕光", "见不得光", "photophobia"),
    "pallor": ("脸色发白", "脸色苍白", "脸也白", "脸白", "pale", "pallor"),
    "redness": (
        "发红",
        "变红",
        "越来越红",
        "红肿",
        "又红又痛",
        "又红又肿",
        "redness",
    ),
    "warmth": (
        "发热发烫",
        "发烫",
        "红、肿、热",
        "红肿热痛",
        "warm to touch",
        "warmth",
    ),
    "wound_discharge": ("化脓", "流脓", "有脓", "pus", "purulent"),
    "foul_odor": ("臭味", "发臭", "很臭", "foul smell", "foul odor"),
    "itching": ("很痒", "特别痒", "发痒", "itching", "itchy"),
    "nonhealing_wound": (
        "伤口一个月都不愈合",
        "伤口一直不愈合",
        "伤口不愈合",
        "伤口不愈",
        "不愈",
        "non-healing wound",
        "wound not healing",
    ),
    "tremor": ("手抖", "发抖", "颤抖", "tremor", "shaking"),
    "sweating": ("冒冷汗", "出冷汗", "浑身是汗", "sweating", "cold sweat"),
    "numbness": (
        "没有感觉",
        "没感觉",
        "发木",
        "麻木",
        "腿也麻",
        "腿还麻",
        "腿麻",
        "numb",
        "numbness",
    ),
    "burn_injury": ("烫伤", "烧伤", "burn injury", "burned"),
    "jaundice": (
        "眼睛和皮肤变黄",
        "眼白和皮肤黄",
        "皮肤越来越黄",
        "手心脚心都黄",
        "黄疸",
        "jaundice",
    ),
    "dark_urine": ("尿液像浓茶", "尿像浓茶", "茶色尿", "dark urine"),
    "sleepiness": ("犯困", "嗜睡", "总想睡", "sleepiness", "drowsy"),
    "falls": ("容易跌倒", "总跌倒", "反复跌倒", "falls", "falling"),
    "poor_appetite": ("吃不下饭", "食欲差", "不想吃饭", "poor appetite"),
    "breast_inflammation": (
        "乳房又红又痛",
        "乳房红痛",
        "乳房红肿痛",
        "red painful breast",
    ),
    "poor_growth": (
        "比同龄人矮很多",
        "体重也不增加",
        "不长个",
        "不长体重",
        "poor growth",
        "not gaining weight",
    ),
    "back_pain": ("腰突然剧痛", "腰痛", "腰疼", "back pain", "low back pain"),
    "pale_hard_extremity": (
        "手脚发白、发硬",
        "手脚发白发硬",
        "手脚白硬",
        "肢体发白发硬",
        "pale hard extremity",
    ),
    "foreign_body_ingestion": (
        "误吞了一枚硬币",
        "吞了硬币",
        "吞下硬币",
        "swallowed a coin",
        "foreign body ingestion",
    ),
    "nonblanching_rash": (
        "按压后不褪色",
        "按了也不变白",
        "non-blanching rash",
        "nonblanching rash",
    ),
    "medication_overdose": (
        "服药过量",
        "药吃多了",
        "吃了过量药",
        "一次吃了太多药",
        "medication overdose",
        "drug overdose",
        "took too many pills",
        "overdosed on medication",
    ),
    "self_harm_intent": (
        "有自杀想法",
        "自杀想法",
        "想自杀",
        "准备自杀",
        "有自残的想法",
        "有自残想法",
        "有人自残",
        "正在自残",
        "想伤害自己",
        "不想活了",
        "suicidal thoughts",
        "thinking about suicide",
        "want to kill myself",
        "thoughts of self-harm",
        "thinking of hurting myself",
    ),
}

ANATOMY_ALIASES = {
    "chest": ("胸口", "胸部", "chest"),
    "head": ("头部", "头", "脑", "head"),
    "abdomen": ("腹部", "肚子", "abdomen"),
    "eye": ("眼睛", "眼", "eye"),
    "airway": ("气道", "喉咙", "airway", "throat"),
    "limb": ("手脚", "手", "脚", "腿", "arm", "leg"),
    "skin_wound": ("皮肤", "伤口", "咬伤", "扎了", "skin", "wound"),
    "right_lower_abdomen": ("右下腹", "右下边", "right lower abdomen"),
    "right_upper_abdomen": ("右上腹", "右上肚子", "right upper abdomen"),
    "breast": ("乳房", "breast"),
    "lower_back": ("腰", "下背", "lower back"),
}

POPULATION_ALIASES = {
    "newborn": ("新生儿", "出生后", "刚出生", "刚生的娃", "newborn"),
    "infant": ("婴儿", "baby", "infant"),
    "child": ("孩子", "儿童", "小孩", "娃", "child"),
    "older_adult": ("老人", "老年人", "older adult", "elderly"),
    "diabetes": ("糖尿病", "diabetic"),
    "copd": ("慢性阻塞性肺病", "慢阻肺", "copd"),
    "hepatitis_b": ("乙肝", "hepatitis b"),
    "postmenopausal": ("绝经以后", "绝经后", "postmenopausal"),
    "polypharmacy": ("长期吃多种药", "吃很多种药", "多种药", "polypharmacy"),
}

PREGNANCY_ALIASES = {
    "pregnant": ("孕妇", "怀孕", "pregnant"),
    "postpartum": ("产后", "产妇", "生完", "postpartum"),
    "lactating": ("哺乳", "喂奶", "母乳", "哺乳妈妈", "哺乳期", "breastfeeding"),
    "ruptured_membranes": ("羊水好像破了", "破水", "waters broke"),
    "vaginal_bleeding": ("阴道出血", "少量出血", "vaginal bleeding"),
}

EXPOSURE_ALIASES = {
    "pesticide": ("农药", "喷洒", "pesticide"),
    "herbicide_ingestion": ("喝了除草剂", "误服除草剂", "herbicide"),
    "carbon_monoxide": ("烧煤取暖", "烧煤", "一氧化碳", "carbon monoxide"),
    "confined_space": ("密闭地窖", "地窖", "confined space"),
    "heat": (
        "天气很热",
        "大热天",
        "天太热",
        "高温",
        "太阳下",
        "烈日下",
        "晒后",
        "中暑",
        "热射病",
        "heat",
    ),
    "cold": ("受冻", "冻伤", "冻后", "cold exposure", "frostbite"),
    "methanol": ("来源不明的自酿酒", "不明自酿酒", "甲醇", "methanol"),
    "wild_mushroom": ("野生蘑菇", "野蘑菇", "自己采的蘑菇", "wild mushroom"),
    "snake_bite": ("被蛇咬", "蛇咬", "snake bite"),
    "food_poisoning": (
        "腌制的食物",
        "腌菜",
        "可疑食物",
        "吃完后多人呕吐",
        "food poisoning",
    ),
    "insulin_use": ("胰岛素", "注射胰岛素", "打完胰岛素", "insulin"),
    "allergen": ("全身起疙瘩", "嘴唇也肿", "allergic", "allergy"),
    "drowning": ("溺水", "drowning"),
    "insect_bite": ("被虫子咬", "虫咬", "insect bite"),
    "puncture_wound": ("铁钉扎", "钉子扎", "扎了脚", "puncture wound"),
    "dog_bite": ("被家里的狗咬", "被狗咬", "狗咬", "dog bite"),
    "vaccination": ("打疫苗后", "接种后", "after vaccination", "after a vaccine"),
    "chemical_eye": ("农药溅进眼睛", "农药进眼", "chemical in the eye"),
    "fatty_meal": ("吃油腻食物后", "吃油的", "油腻食物", "fatty meal"),
    "alcohol": ("喝酒后", "饮酒后", "after drinking alcohol"),
    "glucose_monitoring_unavailable": (
        "血糖试纸用完",
        "不能测血糖",
        "无法测血糖",
        "no glucose test strips",
        "cannot check blood glucose",
    ),
}

TRAUMA_ALIASES = {
    "head_trauma": ("头部摔伤", "摔到头", "head injury"),
    "abdominal_trauma": ("腹部受撞击", "肚子被撞", "撞到肚子", "abdominal trauma"),
    "high_voltage": ("高压电击", "高压电", "high-voltage"),
    "lightning": ("雷击", "雷打在附近", "lightning"),
    "machinery_injury": ("农机割伤", "农机把人割", "机器割伤", "machinery injury"),
    "heavy_lifting": (
        "搬重物后",
        "抬重物后",
        "扛重东西后",
        "after heavy lifting",
    ),
}

ACTION_ALIASES = {
    "care_seeking": (
        "需要去医院",
        "要去医院",
        "需要马上送医院",
        "需要急诊",
        "需要马上转院",
        "需要立即转院",
        "要就医",
        "call an ambulance",
        "go to hospital",
        "seek care",
    ),
    "explanation": (
        "什么原因",
        "怎么回事",
        "可能是什么",
        "症状可能类别",
        "会不会是",
        "是不是",
        "为什么",
        "possible symptom categories",
        "what could cause",
        "what is happening",
        "why",
    ),
    "testing": ("需要检查", "应该做什么检查", "做心电图", "要检查", "what test"),
    "self_care": (
        "怎么处理",
        "怎样处理",
        "应该怎么办",
        "该怎么办",
        "怎么办",
        "怎样观察",
        "what should i do",
        "self care",
    ),
    "prevention": ("怎样避免", "怎么避免", "如何预防", "prevent", "avoid"),
    "storage": ("怎样保存", "怎么保存", "如何保存", "store", "storage"),
    "medication_change": (
        "能不能停",
        "可以不吃",
        "还能继续吃",
        "能不能一起吃",
        "自己减量",
        "自己加",
        "停几天",
        "加量",
        "减量",
        "换药",
        "改药",
    ),
    "medication_use": (
        "用药",
        "吃药",
        "停药",
        "剂量",
        "medicine",
        "medication",
        "dose",
    ),
}

# Labels are descriptive retrieval vocabulary, never inferred diagnoses. The
# first item is Simplified Chinese and the second is English.
SYMPTOM_LABELS = {
    "fever": ("发热", "fever"),
    "cough": ("咳嗽", "cough"),
    "sputum": ("咳痰", "sputum"),
    "breathing_difficulty": ("呼吸困难或气短", "difficulty breathing or breathlessness"),
    "chest_pressure": ("胸部压迫或疼痛", "chest pressure or pain"),
    "palpitations": ("心悸或心跳不规则", "palpitations or irregular heartbeat"),
    "abdominal_pain": ("腹痛", "abdominal pain"),
    "vomiting": ("呕吐", "vomiting"),
    "nausea": ("恶心或想吐", "nausea"),
    "diarrhea": ("腹泻", "diarrhea"),
    "bleeding": ("出血表现", "bleeding"),
    "headache": ("头痛", "headache"),
    "dizziness": ("头晕", "dizziness"),
    "weakness": ("乏力或无力", "weakness"),
    "focal_neurologic_deficit": ("单侧无力或言语异常", "one-sided weakness or speech change"),
    "confusion": ("意识或精神状态改变", "confusion or altered mental state"),
    "unresponsive": ("反应差或叫不醒", "unresponsive or difficult to wake"),
    "seizure": ("抽搐", "seizure"),
    "cyanosis": ("皮肤或嘴唇发紫", "blue skin or lips"),
    "choking": ("疑似气道异物", "possible airway obstruction"),
    "shock_signs": ("面色苍白或冷汗", "pallor or cold sweat"),
    "rash": ("皮疹", "rash"),
    "swelling": ("肿胀", "swelling"),
    "poor_feeding": ("不吃奶或进食差", "poor feeding"),
    "decreased_fetal_movement": ("胎动减少", "reduced fetal movement"),
    "visual_change": ("视物模糊或视觉改变", "blurred vision or visual change"),
    "wheeze": ("喘鸣或呼吸有哨音", "wheeze or noisy breathing"),
    "night_sweats": ("夜间出汗", "night sweats"),
    "weight_loss": ("非预期体重下降", "unintentional weight loss"),
    "abdominal_distension": ("腹胀", "abdominal distension"),
    "constipation": ("排便停止或便秘", "stopped bowel movements or constipation"),
    "tarry_stool": ("黑色柏油样大便", "black tarry stool"),
    "rectal_bleeding": ("大便带鲜血", "fresh blood in stool"),
    "heartburn": ("上腹烧灼或反酸", "upper abdominal burning or reflux"),
    "photophobia": ("畏光", "light sensitivity"),
    "pallor": ("面色苍白", "pallor"),
    "redness": ("局部发红", "local redness"),
    "warmth": ("局部发热", "local warmth"),
    "wound_discharge": ("伤口流脓", "wound discharge or pus"),
    "foul_odor": ("伤口异味", "foul wound odor"),
    "itching": ("瘙痒", "itching"),
    "nonhealing_wound": ("伤口长期不愈合", "non-healing wound"),
    "tremor": ("手抖或颤抖", "tremor or shaking"),
    "sweating": ("出冷汗", "cold sweating"),
    "numbness": ("感觉减退或麻木", "reduced sensation or numbness"),
    "burn_injury": ("烫伤或烧伤", "burn injury"),
    "jaundice": ("皮肤或眼白变黄", "yellow skin or eyes"),
    "dark_urine": ("浓茶色尿", "dark tea-colored urine"),
    "sleepiness": ("异常犯困或嗜睡", "unusual sleepiness"),
    "falls": ("跌倒", "falls"),
    "poor_appetite": ("食欲下降", "poor appetite"),
    "breast_inflammation": ("乳房红痛", "red painful breast"),
    "poor_growth": ("身高或体重增长不足", "poor height or weight gain"),
    "back_pain": ("腰背痛", "low back pain"),
    "pale_hard_extremity": ("肢端发白发硬", "pale hard extremity"),
    "foreign_body_ingestion": ("吞入异物", "swallowed foreign body"),
    "nonblanching_rash": ("按压不褪色皮疹", "non-blanching rash"),
    "medication_overdose": ("可能服药过量", "possible medication overdose"),
    "self_harm_intent": ("自伤或自杀想法", "self-harm or suicidal thoughts"),
}

ANATOMY_LABELS = {
    "chest": ("胸部", "chest"),
    "head": ("头部", "head"),
    "abdomen": ("腹部", "abdomen"),
    "eye": ("眼部", "eye"),
    "airway": ("气道", "airway"),
    "limb": ("肢体", "limb"),
    "skin_wound": ("皮肤或伤口", "skin or wound"),
    "right_lower_abdomen": ("右下腹", "right lower abdomen"),
    "right_upper_abdomen": ("右上腹", "right upper abdomen"),
    "breast": ("乳房", "breast"),
    "lower_back": ("腰背部", "lower back"),
}

POPULATION_LABELS = {
    "newborn": ("新生儿", "newborn"),
    "infant": ("婴儿", "infant"),
    "child": ("儿童", "child"),
    "older_adult": ("老年人", "older adult"),
    "diabetes": ("糖尿病人群", "person with diabetes"),
    "copd": ("慢性阻塞性肺病人群", "person with COPD"),
    "hepatitis_b": ("乙肝人群", "person with hepatitis B"),
    "postmenopausal": ("绝经后人群", "postmenopausal person"),
    "polypharmacy": ("同时使用多种药物", "person taking multiple medicines"),
}

PREGNANCY_LABELS = {
    "pregnant": ("孕期", "pregnancy"),
    "postpartum": ("产后", "postpartum"),
    "lactating": ("哺乳期或母乳喂养", "lactation or breastfeeding"),
    "ruptured_membranes": ("疑似破水", "possible ruptured membranes"),
    "vaginal_bleeding": ("阴道出血", "vaginal bleeding"),
}

EXPOSURE_LABELS = {
    "pesticide": ("农药暴露", "pesticide exposure"),
    "herbicide_ingestion": ("除草剂摄入暴露", "herbicide ingestion exposure"),
    "carbon_monoxide": ("燃煤取暖暴露", "coal-heater exposure"),
    "confined_space": ("密闭空间暴露", "confined-space exposure"),
    "heat": ("高温或日晒暴露 热相关不适 热伤害", "heat exposure or heat-related illness"),
    "cold": ("寒冷暴露", "cold exposure"),
    "methanol": ("来源不明自酿酒暴露", "unknown home-brewed alcohol exposure"),
    "wild_mushroom": ("野生蘑菇摄入", "wild mushroom ingestion"),
    "snake_bite": ("蛇咬伤暴露", "snake-bite exposure"),
    "food_poisoning": ("可疑食物暴露", "suspected food exposure"),
    "insulin_use": ("胰岛素使用后", "after insulin use"),
    "allergen": ("可能的过敏原暴露", "possible allergen exposure"),
    "drowning": ("溺水暴露", "drowning exposure"),
    "insect_bite": ("虫咬伤", "insect bite"),
    "puncture_wound": ("足部穿刺伤", "puncture wound"),
    "dog_bite": ("犬咬伤", "dog bite"),
    "vaccination": ("疫苗接种后", "after vaccination"),
    "chemical_eye": ("农药眼部暴露", "pesticide eye exposure"),
    "fatty_meal": ("油腻饮食后", "after a fatty meal"),
    "alcohol": ("饮酒后", "after alcohol use"),
    "glucose_monitoring_unavailable": (
        "暂时无法监测血糖",
        "blood-glucose monitoring temporarily unavailable",
    ),
}

TRAUMA_LABELS = {
    "head_trauma": ("头部外伤", "head trauma"),
    "abdominal_trauma": ("腹部外伤", "abdominal trauma"),
    "high_voltage": ("高压电暴露", "high-voltage exposure"),
    "lightning": ("雷电暴露", "lightning exposure"),
    "machinery_injury": ("农机损伤", "machinery injury"),
    "heavy_lifting": ("搬重物后", "after heavy lifting"),
}

ONSET_LABELS = {
    "sudden": ("突然起病", "sudden onset"),
    "night": ("夜间发生或加重", "night-time onset or worsening"),
}

TRAJECTORY_LABELS = {
    "worsening": ("逐渐加重", "worsening"),
    "improved_or_transient": ("已缓解或短暂发作", "improved or transient"),
    "persistent": ("持续存在", "persistent"),
    "migrating": ("症状位置发生转移", "migrating location"),
    "positional": ("体位改变时诱发或加重", "triggered or worsened by position"),
    "supine_worse": ("平躺时加重", "worse when lying flat"),
    "exertional": ("活动时出现或加重", "triggered or worsened by exertion"),
    "after_meal": ("进食后出现或加重", "triggered or worsened after eating"),
}

SEVERITY_LABELS = {
    "severe": ("严重表现", "severe presentation"),
    "functional_compromise": ("影响说话呼吸或活动", "functional compromise"),
    "exertional_limitation": ("轻微活动即受限", "limited by minimal exertion"),
    "high_frequency": ("短时间内反复多次", "frequent repeated episodes"),
    "high_fever": ("高热", "high fever"),
}

ACTION_LABELS = {
    "care_seeking": ("就医时机", "when to seek care"),
    "explanation": ("症状可能类别", "possible symptom categories"),
    "testing": ("检查与评估", "testing and evaluation"),
    "self_care": ("现场处理和下一步", "immediate care and next steps"),
    "prevention": ("预防与风险降低", "prevention and risk reduction"),
    "storage": ("安全储存", "safe storage"),
    "medication_change": ("药物变更请求", "requested medication change"),
    "medication_use": ("用药安全", "medication safety"),
}

NEGATION_PATTERN = re.compile(
    r"(?:没有|并无|无|未见|不是|不再|否认|not|no|without|denies?"
    r"|(?:do|does|did)\s+not\s+(?:have|feel|experience)"
    r"|(?:don't|doesn't|didn't)\s+(?:have|feel|experience))\s*$",
    re.IGNORECASE,
)


def _is_negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 16) : start]
    return bool(NEGATION_PATTERN.search(prefix))


HYPOTHETICAL_PATTERN = re.compile(
    r"(?:想|要|希望)?(?:先)?了解(?:一下)?(?:如果|当|在)?"
    r"(?:孩子|儿童|老人|孕妇|有人|一个人)?\s*$"
    r"|(?:want to know|learn about|what if)\s*$",
    re.IGNORECASE,
)


def _is_hypothetical(text: str, start: int) -> bool:
    prefix = text[max(0, start - 28) : start]
    return bool(HYPOTHETICAL_PATTERN.search(prefix))


def _alias_pattern(alias: str) -> str:
    normalized = _normalized(alias)
    escaped = re.escape(normalized)
    if normalized and normalized[0].isascii() and normalized[0].isalnum():
        escaped = rf"(?<!\w){escaped}"
    if normalized and normalized[-1].isascii() and normalized[-1].isalnum():
        escaped = rf"{escaped}(?!\w)"
    return escaped


def _extract_aliases(
    text: str, aliases_by_code: dict[str, tuple[str, ...]]
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    affirmed: list[str] = []
    negated: list[str] = []
    hypothetical: list[str] = []
    for code, aliases in aliases_by_code.items():
        code_affirmed = False
        code_negated = False
        code_hypothetical = False
        for alias in aliases:
            for match in re.finditer(_alias_pattern(alias), text, flags=re.IGNORECASE):
                if _is_negated(text, match.start()):
                    code_negated = True
                elif _is_hypothetical(text, match.start()):
                    code_hypothetical = True
                else:
                    code_affirmed = True
        if code_affirmed:
            affirmed.append(code)
        elif code_negated:
            negated.append(code)
        if code_hypothetical:
            hypothetical.append(code)
    return tuple(affirmed), tuple(negated), tuple(hypothetical)


def _markers(text: str, mapping: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    return tuple(
        code
        for code, aliases in mapping.items()
        if any(re.search(_alias_pattern(alias), text, flags=re.IGNORECASE) for alias in aliases)
    )


def extract_clinical_presentation(message: str) -> ClinicalPresentation:
    text = _normalized(message)
    symptoms, negated, hypothetical = _extract_aliases(text, CONCEPT_ALIASES)
    anatomy = _markers(text, ANATOMY_ALIASES)
    population = _markers(text, POPULATION_ALIASES)
    pregnancy = _markers(text, PREGNANCY_ALIASES)
    exposures = _markers(text, EXPOSURE_ALIASES)
    trauma = _markers(text, TRAUMA_ALIASES)
    requested_actions = _markers(text, ACTION_ALIASES)

    onset: list[str] = []
    if re.search(r"(突然|突发|一下子|刚才|sudden|suddenly)", text):
        onset.append("sudden")
    if re.search(r"(半夜|夜间|晚上|night)", text):
        onset.append("night")

    duration = tuple(
        match.group(0)
        for match in re.finditer(
            r"(?:\d+(?:\.\d+)?|[一二两三四五六七八九十]+)\s*"
            r"(?:个)?(?:分钟|小时|天|周|星期|个月|年|minutes?|hours?|days?|weeks?|months?|years?)",
            text,
            flags=re.IGNORECASE,
        )
    )

    trajectory: list[str] = []
    if re.search(
        r"(越来越|加重|更严重|更重|比平时厉害|比平时重|越来越想睡|worsen|worse|progressive)",
        text,
    ):
        trajectory.append("worsening")
    if re.search(r"(恢复了|现在好了|好转|缓解|recovered|improved|relieved)", text):
        trajectory.append("improved_or_transient")
    if re.search(r"(一直|持续|不停|止不住|persistent|continuously)", text):
        trajectory.append("persistent")
    if re.search(r"(转到|转移到|跑到|migrat)", text):
        trajectory.append("migrating")
    if re.search(r"(翻身|起床时|站起来|猛一站|体位|position|turning over)", text):
        trajectory.append("positional")
    if re.search(
        r"(躺下更|一躺就|一躺下|只能坐着睡|平躺.*加重|worse.*lying|orthopnea)",
        text,
    ):
        trajectory.append("supine_worse")
    if re.search(r"(干活时|活动时|走几步|劳累时|exertion|during activity)", text):
        trajectory.append("exertional")
    if re.search(r"(吃饭后|进食后|吃完|吃油.*后|after (?:eating|a meal))", text):
        trajectory.append("after_meal")

    severity: list[str] = []
    if re.search(
        r"(剧烈|最严重|最厉害|受不了|大量|好多血|止不住|"
        r"每小时.*湿透|超过五分钟|五分多钟|>\s*5\s*min|severe)",
        text,
    ):
        severity.append("severe")
    if re.search(
        r"(无法完整说一句话|一句话说不全|不能说话|不能咳嗽|不能站|cannot speak)",
        text,
    ):
        severity.append("functional_compromise")
    if re.search(r"(走几步就|轻微活动就|minimal exertion)", text):
        severity.append("exertional_limitation")
    if re.search(
        r"(七八(?:次|回)|7\s*[-到至]\s*8\s*(?:次|回)|"
        r"[7-9]\s*(?:次|回)|一天.*(?:次|回)|many times)",
        text,
    ):
        severity.append("high_frequency")
    if re.search(r"(高烧|高热|烧得很高|high fever)", text):
        severity.append("high_fever")

    measurements: list[str] = []
    measurement_patterns = (
        r"\d{2,3}(?:\.\d+)?\s*(?:℃|°\s*c|度)",
        r"\d{2,3}\s*/\s*\d{2,3}\s*(?:毫米汞柱|mmhg)?",
        r"\d+(?:\.\d+)?\s*mmol\s*/?\s*l",
    )
    for pattern in measurement_patterns:
        measurements.extend(match.group(0) for match in re.finditer(pattern, text))

    associated: list[str] = []
    for code in ("cyanosis", "shock_signs", "confusion", "unresponsive", "visual_change"):
        if code in symptoms:
            associated.append(code)

    presentation = ClinicalPresentation(
        literal_query=message,
        symptoms=symptoms,
        anatomy=anatomy,
        onset=tuple(onset),
        duration=duration,
        trajectory=tuple(trajectory),
        severity=tuple(severity),
        associated_signs=tuple(associated),
        measurements=tuple(measurements),
        population=population,
        pregnancy=pregnancy,
        exposures=exposures,
        trauma=trauma,
        requested_actions=requested_actions,
        negated_concepts=negated,
        hypothetical_concepts=hypothetical,
    )
    return ClinicalPresentation(
        **{
            **presentation.__dict__,
            "danger_signals": _danger_signals(text, presentation),
        }
    )


def _has(presentation: ClinicalPresentation, *codes: str) -> bool:
    observed = {
        *presentation.symptoms,
        *presentation.population,
        *presentation.pregnancy,
        *presentation.exposures,
        *presentation.trauma,
        *presentation.onset,
        *presentation.trajectory,
        *presentation.severity,
    }
    return all(code in observed for code in codes)


def _danger_signals(text: str, presentation: ClinicalPresentation) -> tuple[str, ...]:
    signals: list[str] = []

    # Absence of normal breathing is a positive danger sign, not a negated
    # mention of breathing difficulty.
    if re.search(
        r"(没有正常呼吸|没正常呼吸|无正常呼吸|not breathing normally|no normal breathing)",
        text,
    ):
        signals.append("absent_normal_breathing")
    if _has(presentation, "unresponsive") and (
        "absent_normal_breathing" in signals or _has(presentation, "breathing_difficulty")
    ):
        signals.append("cardiac_arrest_pattern")
    if _has(presentation, "medication_overdose"):
        signals.append("suspected_medication_overdose")
    if _has(presentation, "self_harm_intent"):
        signals.append("self_harm_crisis")
    if (
        _has(presentation, "breathing_difficulty", "cyanosis")
        or (_has(presentation, "breathing_difficulty", "functional_compromise"))
        or re.search(r"(不能呼吸|无法呼吸|cannot breathe|can't breathe)", text)
    ):
        signals.append("severe_respiratory_distress")
    # Either concept alone may have non-emergency explanations, but their
    # affirmed combination requires deterministic emergency escalation.
    if _has(presentation, "chest_pressure", "breathing_difficulty"):
        signals.append("chest_pressure_with_breathing_difficulty")
    if (
        _has(presentation, "choking", "cyanosis")
        or re.search(r"(不能说话.{0,12}不能咳嗽|cannot speak.{0,24}cannot cough)", text)
        or re.search(r"(吃饭|进食|吃东西).{0,16}(说不出话|呼吸困难|喘不上气)", text)
    ):
        signals.append("complete_airway_obstruction")
    if _has(presentation, "chest_pressure", "shock_signs") and (
        "persistent" in presentation.trajectory
        or re.search(r"(超过十分钟|十多分钟|over ten minutes|more than 10 minutes)", text)
    ):
        signals.append("acute_coronary_pattern")
    if _has(presentation, "focal_neurologic_deficit") and (
        "sudden" in presentation.onset or "improved_or_transient" in presentation.trajectory
    ):
        signals.append("stroke_or_tia_pattern")
    if _has(presentation, "seizure") and re.search(
        r"(超过五分钟|五分多钟|连续抽搐|一直没有清醒|一直没醒|"
        r"more than five minutes|without waking)",
        text,
    ):
        signals.append("prolonged_or_recurrent_seizure")
    if re.search(
        r"(呕吐大量鲜血|大量吐血|吐了好多鲜血|vomit(?:ing)? a large amount of blood)",
        text,
    ) and _has(presentation, "shock_signs"):
        signals.append("major_gastrointestinal_bleeding")
    if _has(presentation, "abdominal_trauma", "abdominal_pain", "shock_signs"):
        signals.append("internal_bleeding_pattern")
    elif _has(presentation, "abdominal_trauma", "shock_signs") and re.search(
        r"(越来越疼|腹部.*疼|肚子.*疼)", text
    ):
        signals.append("internal_bleeding_pattern")
    if _has(presentation, "head_trauma", "vomiting") and re.search(
        r"(嗜睡|越来越想睡|叫不醒|drowsy|sleepy|unresponsive)", text
    ):
        signals.append("delayed_head_injury_deterioration")
    if _has(presentation, "rash", "swelling") and re.search(
        r"(嘴唇|嘴|舌头|喉咙|lip|tongue|throat)", text
    ):
        signals.append("anaphylaxis_pattern")
    if _has(presentation, "headache", "sudden", "severe") and _has(presentation, "vomiting"):
        signals.append("thunderclap_headache_pattern")
    if _has(presentation, "abdominal_pain", "vomiting", "sudden", "severe"):
        signals.append("acute_severe_abdominal_pattern")
    if re.search(r"(三天|多日).{0,12}(没有排便|没拉)", text) and re.search(
        r"(肚子胀|腹胀).{0,16}(呕吐|吐)", text
    ):
        signals.append("bowel_obstruction_pattern")
    if _has(presentation, "postpartum", "bleeding", "shock_signs") and re.search(
        r"(大量|大出血|好多血|heavy|soak)", text
    ):
        signals.append("postpartum_hemorrhage_pattern")
    if _has(presentation, "pregnant", "headache", "visual_change") and re.search(
        r"(血压高|高血压|high blood pressure)", text
    ):
        signals.append("severe_pregnancy_hypertension_pattern")
    ectopic_pattern = re.search(
        r"(月经推迟|月经晚).{0,24}(一侧|一边).{0,12}(下腹|小肚子).{0,16}出血",
        text,
    )
    if (
        _has(presentation, "pregnant", "abdominal_pain", "vaginal_bleeding")
        and re.search(r"(月经推迟|一侧|missed period|one-sided)", text)
    ) or ectopic_pattern:
        signals.append("ectopic_pregnancy_pattern")
    if _has(presentation, "newborn", "poor_feeding") and (
        _has(presentation, "confusion") or _has(presentation, "unresponsive")
    ):
        signals.append("unwell_newborn_pattern")
    if _has(presentation, "infant") and re.search(
        r"(呼吸很快|喘得快|胸口.*凹|胸壁.*凹|chest indrawing|retractions?)", text
    ):
        signals.append("infant_respiratory_distress")
    if re.search(r"(按压后不褪色|按了也不变白|non[- ]blanching)", text) and _has(
        presentation, "fever"
    ):
        signals.append("fever_nonblanching_rash")
    if _has(presentation, "snake_bite", "swelling"):
        signals.append("snake_envenomation_pattern")
    if _has(presentation, "herbicide_ingestion"):
        signals.append("toxic_ingestion")
    if _has(presentation, "pesticide") and re.search(r"(流口水|头晕|恶心|drooling)", text):
        signals.append("pesticide_poisoning_pattern")
    if _has(presentation, "carbon_monoxide") and re.search(
        r"(全家|多人|几个人|everyone|family)", text
    ):
        signals.append("carbon_monoxide_cluster")
    if _has(presentation, "confined_space") and _has(presentation, "headache"):
        signals.append("confined_space_exposure")
    if _has(presentation, "heat", "confusion") and re.search(
        r"(40\s*(?:℃|度)|超过40|四十多|over 40)", text
    ):
        signals.append("heatstroke_pattern")
    if _has(presentation, "methanol", "visual_change"):
        signals.append("methanol_poisoning_pattern")
    if _has(presentation, "wild_mushroom", "vomiting", "abdominal_pain"):
        signals.append("wild_mushroom_poisoning")
    if _has(presentation, "drowning"):
        signals.append("post_drowning_risk")
    if _has(presentation, "high_voltage") or _has(presentation, "lightning"):
        signals.append("electrical_injury")
    if _has(presentation, "ruptured_membranes"):
        signals.append("ruptured_membranes_remote_from_care")
    if re.search(r"(月经量|来月经|阴道).{0,18}(每小时|一小时).{0,18}湿透", text):
        signals.append("major_vaginal_bleeding")
    if _has(presentation, "machinery_injury", "bleeding") and (
        "persistent" in presentation.trajectory or "severe" in presentation.severity
    ):
        signals.append("uncontrolled_traumatic_bleeding")
    if re.search(r"(血糖很高|血糖高|高血糖)", text) and _has(presentation, "confusion"):
        signals.append("hyperglycemic_decompensation_pattern")
    if _has(presentation, "confusion", "sudden"):
        signals.append("acute_confusion_pattern")
    return tuple(dict.fromkeys(signals))


GUIDANCE_BY_SIGNAL = {
    "cardiac_arrest_pattern": "cpr_aed",
    "suspected_medication_overdose": "poisoning",
    "self_harm_crisis": "general_emergency",
    "complete_airway_obstruction": "choking",
    "stroke_or_tia_pattern": "stroke",
    "prolonged_or_recurrent_seizure": "seizure",
    "major_gastrointestinal_bleeding": "bleeding",
    "internal_bleeding_pattern": "bleeding",
    "postpartum_hemorrhage_pattern": "bleeding",
    "pesticide_poisoning_pattern": "poisoning",
    "toxic_ingestion": "poisoning",
    "methanol_poisoning_pattern": "poisoning",
    "wild_mushroom_poisoning": "poisoning",
    "carbon_monoxide_cluster": "fresh_air",
    "confined_space_exposure": "fresh_air",
    "electrical_injury": "electrical",
    "snake_envenomation_pattern": "snake_bite",
    "post_drowning_risk": "drowning",
    "major_vaginal_bleeding": "bleeding",
    "uncontrolled_traumatic_bleeding": "bleeding",
}

DANGER_PRIORITY = (
    "cardiac_arrest_pattern",
    "suspected_medication_overdose",
    "self_harm_crisis",
    "complete_airway_obstruction",
    "severe_respiratory_distress",
    "chest_pressure_with_breathing_difficulty",
    "acute_coronary_pattern",
    "stroke_or_tia_pattern",
    "prolonged_or_recurrent_seizure",
    "major_gastrointestinal_bleeding",
    "postpartum_hemorrhage_pattern",
    "major_vaginal_bleeding",
    "uncontrolled_traumatic_bleeding",
    "internal_bleeding_pattern",
    "delayed_head_injury_deterioration",
    "anaphylaxis_pattern",
    "thunderclap_headache_pattern",
    "acute_severe_abdominal_pattern",
    "bowel_obstruction_pattern",
    "severe_pregnancy_hypertension_pattern",
    "ectopic_pregnancy_pattern",
    "ruptured_membranes_remote_from_care",
    "unwell_newborn_pattern",
    "infant_respiratory_distress",
    "fever_nonblanching_rash",
    "snake_envenomation_pattern",
    "toxic_ingestion",
    "pesticide_poisoning_pattern",
    "carbon_monoxide_cluster",
    "confined_space_exposure",
    "heatstroke_pattern",
    "methanol_poisoning_pattern",
    "wild_mushroom_poisoning",
    "post_drowning_risk",
    "electrical_injury",
    "hyperglycemic_decompensation_pattern",
    "acute_confusion_pattern",
    "absent_normal_breathing",
)


@dataclass(frozen=True)
class CareUrgencyRule:
    """Candidate, reviewable non-emergency care-timing rule.

    Rules consume only controlled presentation features. They do not name or
    infer a diagnosis, and they never downgrade an emergency signal.
    """

    rule_id: str
    urgency_route: UrgencyRoute
    all_of: frozenset[str] = frozenset()
    any_groups: tuple[frozenset[str], ...] = ()
    none_of: frozenset[str] = frozenset()
    minimum_duration_days: float | None = None
    minimum_temperature_c: float | None = None
    minimum_systolic_mmhg: float | None = None
    minimum_diastolic_mmhg: float | None = None
    minimum_glucose_mmol_l: float | None = None


def _presentation_codes(presentation: ClinicalPresentation) -> frozenset[str]:
    return frozenset(
        (
            *presentation.symptoms,
            *presentation.anatomy,
            *presentation.onset,
            *presentation.trajectory,
            *presentation.severity,
            *presentation.population,
            *presentation.pregnancy,
            *presentation.exposures,
            *presentation.trauma,
        )
    )


_CHINESE_NUMBERS = {
    "一": 1.0,
    "两": 2.0,
    "二": 2.0,
    "三": 3.0,
    "四": 4.0,
    "五": 5.0,
    "六": 6.0,
    "七": 7.0,
    "八": 8.0,
    "九": 9.0,
    "十": 10.0,
}


def _numeric_value(raw: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", raw)
    if match:
        return float(match.group(0))
    compact = raw.replace("个", "").strip()
    for token, value in _CHINESE_NUMBERS.items():
        if compact.startswith(token):
            return value
    return None


def _duration_days(presentation: ClinicalPresentation) -> float | None:
    values: list[float] = []
    for raw in presentation.duration:
        value = _numeric_value(raw)
        if value is None:
            continue
        normalized = _normalized(raw)
        if re.search(r"(分钟|minutes?)", normalized):
            values.append(value / 1440)
        elif re.search(r"(小时|hours?)", normalized):
            values.append(value / 24)
        elif re.search(r"(天|days?)", normalized):
            values.append(value)
        elif re.search(r"(周|星期|weeks?)", normalized):
            values.append(value * 7)
        elif re.search(r"(个月|months?)", normalized):
            values.append(value * 30)
        elif re.search(r"(年|years?)", normalized):
            values.append(value * 365)
    return max(values) if values else None


def _measurement_values(presentation: ClinicalPresentation) -> dict[str, tuple[float, ...]]:
    temperature: list[float] = []
    systolic: list[float] = []
    diastolic: list[float] = []
    glucose: list[float] = []
    for raw in presentation.measurements:
        normalized = _normalized(raw)
        if re.search(r"(?:℃|°\s*c|度)", normalized):
            value = _numeric_value(normalized)
            if value is not None:
                temperature.append(value)
        elif "mmol" in normalized:
            value = _numeric_value(normalized)
            if value is not None:
                glucose.append(value)
        elif "/" in normalized:
            match = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", normalized)
            if match:
                systolic.append(float(match.group(1)))
                diastolic.append(float(match.group(2)))
    return {
        "temperature": tuple(temperature),
        "systolic": tuple(systolic),
        "diastolic": tuple(diastolic),
        "glucose": tuple(glucose),
    }


def _minimum_met(values: tuple[float, ...], minimum: float | None) -> bool:
    return minimum is None or bool(values and max(values) >= minimum)


def _urgency_rule_matches(
    rule: CareUrgencyRule,
    presentation: ClinicalPresentation,
) -> bool:
    codes = _presentation_codes(presentation)
    if not rule.all_of.issubset(codes):
        return False
    if rule.none_of & codes:
        return False
    if any(not group & codes for group in rule.any_groups):
        return False
    duration_days = _duration_days(presentation)
    if rule.minimum_duration_days is not None and (
        duration_days is None or duration_days < rule.minimum_duration_days
    ):
        return False
    measurements = _measurement_values(presentation)
    return all(
        (
            _minimum_met(measurements["temperature"], rule.minimum_temperature_c),
            _minimum_met(measurements["systolic"], rule.minimum_systolic_mmhg),
            _minimum_met(measurements["diastolic"], rule.minimum_diastolic_mmhg),
            _minimum_met(measurements["glucose"], rule.minimum_glucose_mmol_l),
        )
    )


# This is a candidate policy pending the named clinical and native-Chinese
# review recorded in the canonical contract. Ordering is conservative: an
# emergency signal has already won before these rules run, then same-day rules
# take precedence over clinician-contact rules. A missing feature cannot be
# invented to make a rule match.
NON_EMERGENCY_URGENCY_RULES = (
    CareUrgencyRule(
        "child_high_fever_measurement",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"child", "fever"}),
        minimum_temperature_c=39.0,
    ),
    CareUrgencyRule(
        "child_high_fever_description",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"child", "fever", "high_fever"}),
    ),
    CareUrgencyRule(
        "older_adult_exertional_breathlessness",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"older_adult", "breathing_difficulty"}),
        any_groups=(frozenset({"exertional", "exertional_limitation"}),),
    ),
    CareUrgencyRule(
        "blood_with_cough_or_sputum",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"bleeding"}),
        any_groups=(frozenset({"cough", "sputum"}),),
    ),
    CareUrgencyRule(
        "child_cough_with_noisy_breathing",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"child", "cough"}),
        any_groups=(frozenset({"wheeze", "breathing_difficulty"}),),
    ),
    CareUrgencyRule(
        "migrating_right_lower_abdominal_pain",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"abdominal_pain", "right_lower_abdomen", "migrating"}),
    ),
    CareUrgencyRule(
        "persistent_gastrointestinal_symptoms_after_suspect_food",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"food_poisoning", "vomiting", "diarrhea", "persistent"}),
    ),
    CareUrgencyRule(
        "child_frequent_watery_diarrhea",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"child", "diarrhea", "high_frequency"}),
    ),
    CareUrgencyRule(
        "black_tarry_stool",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"tarry_stool"}),
    ),
    CareUrgencyRule(
        "right_upper_abdominal_pain_after_fatty_food",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"abdominal_pain", "right_upper_abdomen", "fatty_meal"}),
    ),
    CareUrgencyRule(
        "headache_with_visual_or_light_sensitivity",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"headache"}),
        any_groups=(frozenset({"visual_change", "photophobia"}),),
    ),
    CareUrgencyRule(
        "symptomatic_heat_exposure",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"heat"}),
        any_groups=(frozenset({"headache", "nausea", "weakness", "dizziness"}),),
    ),
    CareUrgencyRule(
        "worsening_inflammatory_limb_after_bite",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"insect_bite", "worsening", "swelling"}),
        any_groups=(frozenset({"redness", "warmth"}),),
    ),
    CareUrgencyRule(
        "puncture_wound",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"puncture_wound"}),
    ),
    CareUrgencyRule(
        "purulent_or_foul_wound",
        UrgencyRoute.urgent_same_day,
        any_groups=(frozenset({"wound_discharge", "foul_odor"}),),
    ),
    CareUrgencyRule(
        "diabetes_nonhealing_wound",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"diabetes", "nonhealing_wound"}),
    ),
    CareUrgencyRule(
        "dog_bite_with_broken_skin",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"dog_bite", "bleeding"}),
    ),
    CareUrgencyRule(
        "marked_systolic_measurement",
        UrgencyRoute.urgent_same_day,
        minimum_systolic_mmhg=180.0,
    ),
    CareUrgencyRule(
        "marked_diastolic_measurement",
        UrgencyRoute.urgent_same_day,
        minimum_diastolic_mmhg=110.0,
    ),
    CareUrgencyRule(
        "exertional_chest_pressure",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"chest_pressure", "exertional"}),
    ),
    CareUrgencyRule(
        "palpitations_with_chest_pressure",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"palpitations", "chest_pressure"}),
    ),
    CareUrgencyRule(
        "older_adult_breathlessness_worse_supine_with_swelling",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"older_adult", "breathing_difficulty", "supine_worse", "swelling"}),
    ),
    CareUrgencyRule(
        "symptoms_after_insulin",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"insulin_use"}),
        any_groups=(frozenset({"tremor", "sweating", "palpitations"}),),
    ),
    CareUrgencyRule(
        "diabetes_burn_with_reduced_sensation",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"burn_injury", "numbness"}),
    ),
    CareUrgencyRule(
        "worsening_copd_respiratory_presentation",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"breathing_difficulty", "worsening"}),
        any_groups=(frozenset({"sputum", "cough"}),),
    ),
    CareUrgencyRule(
        "yellow_skin_or_eyes_with_dark_urine",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"jaundice", "dark_urine"}),
    ),
    CareUrgencyRule(
        "pregnancy_with_vaginal_bleeding",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"pregnant", "vaginal_bleeding"}),
    ),
    CareUrgencyRule(
        "decreased_fetal_movement",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"decreased_fetal_movement"}),
    ),
    CareUrgencyRule(
        "postpartum_fever_with_breast_inflammation",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"postpartum", "fever", "breast_inflammation"}),
    ),
    CareUrgencyRule(
        "newborn_progressive_jaundice",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"newborn", "jaundice", "worsening"}),
    ),
    CareUrgencyRule(
        "child_swallowed_foreign_body",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"child", "foreign_body_ingestion"}),
    ),
    CareUrgencyRule(
        "pesticide_eye_exposure",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"pesticide", "chemical_eye"}),
    ),
    CareUrgencyRule(
        "back_pain_with_leg_numbness_after_lifting",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"back_pain", "numbness", "heavy_lifting"}),
    ),
    CareUrgencyRule(
        "cold_exposure_with_pale_hard_extremity",
        UrgencyRoute.urgent_same_day,
        all_of=frozenset({"cold", "pale_hard_extremity"}),
    ),
    CareUrgencyRule(
        "prolonged_productive_cough",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"cough", "sputum"}),
        minimum_duration_days=21.0,
    ),
    CareUrgencyRule(
        "cough_worse_at_night_or_lying_flat",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"cough", "night"}),
        any_groups=(frozenset({"supine_worse", "worsening"}),),
    ),
    CareUrgencyRule(
        "fever_night_sweats_weight_loss",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"fever", "night_sweats", "weight_loss"}),
    ),
    CareUrgencyRule(
        "position_related_dizziness",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"dizziness", "positional"}),
    ),
    CareUrgencyRule(
        "dizziness_palpitations_pallor",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"dizziness", "palpitations", "pallor"}),
    ),
    CareUrgencyRule(
        "older_adult_weakness_with_poor_appetite_or_sleepiness",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"older_adult", "weakness"}),
        any_groups=(frozenset({"poor_appetite", "sleepiness"}),),
    ),
    CareUrgencyRule(
        "itchy_rash_after_pesticide_exposure",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"pesticide", "rash", "itching"}),
    ),
    CareUrgencyRule(
        "fresh_blood_in_stool",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"rectal_bleeding"}),
    ),
    CareUrgencyRule(
        "upper_abdominal_burning_or_reflux",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"heartburn"}),
    ),
    CareUrgencyRule(
        "elevated_fasting_glucose_measurement",
        UrgencyRoute.clinician_contact,
        minimum_glucose_mmol_l=7.0,
    ),
    CareUrgencyRule(
        "hepatitis_b_monitoring_question",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"hepatitis_b"}),
    ),
    CareUrgencyRule(
        "polypharmacy_with_sleepiness_or_falls",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"older_adult", "polypharmacy"}),
        any_groups=(frozenset({"sleepiness", "falls"}),),
    ),
    CareUrgencyRule(
        "postmenopausal_bleeding",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"postmenopausal", "vaginal_bleeding"}),
    ),
    CareUrgencyRule(
        "child_poor_growth",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"child", "poor_growth"}),
    ),
    CareUrgencyRule(
        "glucose_monitoring_temporarily_unavailable",
        UrgencyRoute.clinician_contact,
        all_of=frozenset({"glucose_monitoring_unavailable"}),
    ),
)


def _non_emergency_urgency(
    presentation: ClinicalPresentation,
) -> tuple[UrgencyRoute, str | None]:
    for rule in NON_EMERGENCY_URGENCY_RULES:
        if _urgency_rule_matches(rule, presentation):
            return rule.urgency_route, rule.rule_id
    return UrgencyRoute.routine_education, None


def assess_safety(message: str) -> SafetyAssessment:
    presentation = extract_clinical_presentation(message)
    if presentation.danger_signals:
        rule_id = next(
            (signal for signal in DANGER_PRIORITY if signal in presentation.danger_signals),
            presentation.danger_signals[0],
        )
        return SafetyAssessment(
            safety_code=SafetyCode.emergency,
            urgency_route=UrgencyRoute.emergency_120,
            rule_id=rule_id,
            guidance_code=GUIDANCE_BY_SIGNAL.get(rule_id, "general_emergency"),
            presentation=presentation,
        )
    urgency_route, rule_id = _non_emergency_urgency(presentation)
    return SafetyAssessment(
        safety_code=SafetyCode.permitted_symptom_guidance,
        urgency_route=urgency_route,
        rule_id=rule_id,
        presentation=presentation,
    )


def resolve_bounded_user_continuity(
    message: str,
    previous_user_messages: list[str] | tuple[str, ...],
) -> BoundedContinuityResolution:
    """Resolve a short follow-up without model inference or assistant content.

    At most the most recent non-empty user turn is admitted. Generic temporal
    markers only carry context when the current turn contains a controlled
    presentation feature, preventing a new unrelated conversational topic from
    inheriting old medical details merely because it begins with "now".
    """

    previous_user = next(
        (item.strip() for item in reversed(previous_user_messages) if item.strip()),
        None,
    )
    if previous_user is None:
        return BoundedContinuityResolution(
            analysis_message=message,
            literal_query=message,
            reason=ContinuityReason.standalone,
            carried_previous_user_turn=False,
        )

    explicit_reference = bool(
        re.search(
            r"(^.{0,10}(that|this|it|those|still|how long|what about)\b)"
            r"|(^\s*(?:那|这个|这种|它|还有|而且|可是|但是))"
            r"|(多久|呢|还是|还要|还用)"
            r"|((?:怎么|怎样).{0,8}(?:才算|算).{0,4}(?:对|正确))"
            r"|((?:现在|已经).{0,12}(?:好些|好了|缓解|恢复|怎么办))",
            message,
            flags=re.IGNORECASE,
        )
    )
    if explicit_reference:
        reason = ContinuityReason.explicit_reference
    else:
        current = extract_clinical_presentation(message)
        previous = extract_clinical_presentation(previous_user)
        has_current_presentation = bool(
            current.symptoms
            or current.associated_signs
            or current.measurements
            or current.trajectory
            or current.severity
        )
        temporal_ellipsis = bool(
            re.search(
                r"^\s*(?:now|then|later|currently|since then|"
                r"现在|后来|刚才|这会儿|目前|然后|接着|又|也)",
                message,
                flags=re.IGNORECASE,
            )
        )
        if temporal_ellipsis and has_current_presentation:
            reason = ContinuityReason.temporal_symptom_follow_up
        elif "decreased_fetal_movement" in current.symptoms and "pregnant" in previous.pregnancy:
            reason = ContinuityReason.pregnancy_dependency
        else:
            return BoundedContinuityResolution(
                analysis_message=message,
                literal_query=message,
                reason=ContinuityReason.standalone,
                carried_previous_user_turn=False,
            )

    return BoundedContinuityResolution(
        analysis_message=f"{previous_user}\nFollow-up: {message}",
        literal_query=message,
        reason=reason,
        carried_previous_user_turn=True,
    )


def emergency_guidance(language: str, guidance_code: str | None) -> str:
    zh = {
        "general_emergency": "请立即拨打120。不要自行开车；请让身边的人陪同并保持电话畅通。",
        "cpr_aed": (
            "请立即拨打120并打开免提。按调度员指示开始心肺复苏；如有AED，立即取来并按语音提示使用。"
        ),
        "choking": (
            "请立即拨打120。若患者不能说话、咳嗽或呼吸，请立刻按调度员指导"
            "实施窒息急救；不要盲目用手掏取异物。"
        ),
        "stroke": (
            "请立即拨打120，记下最后一次正常的时间。不要给患者吃喝或自行加药；"
            "若呕吐，让其侧卧并保持呼吸道通畅。"
        ),
        "seizure": (
            "请立即拨打120。移开周围硬物、保护头部并计时；不要按住患者，也不要往嘴里塞任何东西。"
        ),
        "bleeding": (
            "请立即拨打120。若有外部出血，用干净布持续直接按压；让患者平躺保暖，不要给吃喝。"
        ),
        "poisoning": (
            "请立即拨打120并保留包装或容器。不要催吐、不要自行喂食或喂药；避免自己接触残留毒物。"
        ),
        "fresh_air": (
            "请立即拨打120并转移到新鲜空气处，但不要在没有防护时重新进入密闭或疑似有毒环境。"
        ),
        "electrical": (
            "请立即拨打120。先确认电源已切断再接触患者；持续观察呼吸和意识，"
            "不要只根据皮肤伤口判断轻重。"
        ),
        "snake_bite": "请立即拨打120。让伤肢少动并取下戒指等紧物；不要切开、吸吮、冰敷或绑止血带。",
        "drowning": (
            "请立即拨打120。持续观察呼吸；若再次无正常呼吸，按调度员指导开始"
            "心肺复苏。注意施救者自身安全。"
        ),
    }
    en = {
        "general_emergency": (
            "Call 120 now. Do not drive yourself; have someone stay with the patient "
            "and keep the phone available."
        ),
        "cpr_aed": (
            "Call 120 on speaker now. Start CPR as directed by the dispatcher and use "
            "an AED immediately if one is available."
        ),
        "choking": (
            "Call 120 now. If the person cannot speak, cough, or breathe, follow "
            "dispatcher-guided choking first aid. Do not blindly sweep the mouth."
        ),
        "stroke": (
            "Call 120 now and note the last-known-well time. Give no food, drink, or "
            "extra medicine; place the person on their side if vomiting."
        ),
        "seizure": (
            "Call 120 now. Clear hard objects, protect the head, and time the seizure. "
            "Do not restrain the person or put anything in the mouth."
        ),
        "bleeding": (
            "Call 120 now. Apply continuous direct pressure to external bleeding with a "
            "clean cloth; keep the person lying down and warm, with no food or drink."
        ),
        "poisoning": (
            "Call 120 now and keep the product container. Do not induce vomiting or give "
            "food, drink, or medicine; avoid exposing yourself to residue."
        ),
        "fresh_air": (
            "Call 120 now and move to fresh air, but do not re-enter a confined or "
            "possibly toxic space without proper protection."
        ),
        "electrical": (
            "Call 120 now. Do not touch the person until power is disconnected; keep "
            "watching breathing and consciousness even if the skin wound is small."
        ),
        "snake_bite": (
            "Call 120 now. Keep the limb still and remove tight items; do not cut, suck, "
            "ice, or apply a tourniquet."
        ),
        "drowning": (
            "Call 120 now. Keep watching breathing and start dispatcher-guided CPR if "
            "normal breathing stops again. Keep rescuers safe."
        ),
    }
    selected = zh if language == "zh-Hans" else en
    return selected.get(guidance_code or "general_emergency", selected["general_emergency"])
