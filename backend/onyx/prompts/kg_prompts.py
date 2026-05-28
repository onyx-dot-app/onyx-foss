# Standards
SEPARATOR_LINE = "-------"
SEPARATOR_LINE_LONG = "---------------"
NO_EXTRACTION = "No extraction of knowledge graph objects was feasible."
YES = "yes"
NO = "no"

# Framing/Support/Template Prompts
ENTITY_TYPE_SETTING_PROMPT = f"""
{SEPARATOR_LINE}
{{entity_types}}
{SEPARATOR_LINE}
""".strip()

RELATIONSHIP_TYPE_SETTING_PROMPT = f"""
Here are the types of relationships:
{SEPARATOR_LINE}
{{relationship_types}}
{SEPARATOR_LINE}
""".strip()

EXTRACTION_FORMATTING_PROMPT = r"""
{{"entities": [<a list of entities of the prescribed entity types that you can reliably identify in the text, \
formatted as '<ENTITY_TYPE_NAME>::<entity_name>' (please use that capitalization). If allowed options \
are provided above, you can only extract those types of entities! If none of the entity types fits, \
skip the entity — do not invent new types. \
\
OPTIONAL ATTRIBUTE BLOCK: an entity may carry structured attributes by appending the suffix \
'--[attr_key: "value", attr_key: "value"]' to its id. Use the suffix ONLY if the content-specific \
instructions below (in the text you are extracting from) explicitly tell you which attributes to \
emit for that entity type — otherwise omit it and use the bare 'TYPE::name' form. When present, the \
suffix is part of the same string: 'CERTIFICATION::PMP--[name: \"PMP\", issuing_authority: \"PMI\", \
valid_until: 2027, language: \"EN\"]'. Quote string values; integers and null are allowed unquoted. \
This suffix goes ONLY on entities — NEVER on relationship endpoints.>],
"relationships": [<a list of IMPORTANT relationships between the identified entities, formatted as \
'<SOURCE_ENTITY_TYPE_NAME>::<source_entity_name>__<relationship_verb>\
__<TARGET_ENTITY_TYPE_NAME>::<target_entity_name>'>. \
If the content-specific instructions below provide a CANONICAL list of relationship verbs, you MUST \
use ONLY those verbs — do not invent synonyms. If no canonical list is provided, use a word or two \
that captures the nature of the relationship (e.g. 'likes', 'dislikes', 'uses'). \
Use spaces for word separation. DO NOT INCLUDE RELATIONSHIPS THAT ARE SIMPLY MENTIONED, BUT ONLY \
THOSE THAT ARE CENTRAL TO THE CONTENT! Note: relationship endpoints use bare 'TYPE::name' — do NOT \
include the '--[...]' attribute suffix on either side of the '__verb__'.>],
"terms": [<a comma-separated list of high-level terms (each one one or two words) that you can reliably \
identify in the text, each formatted simply as '<term>'>]
}}
""".strip()

QUERY_ENTITY_EXTRACTION_FORMATTING_PROMPT = r"""
{{"entities": [<a list of entities of the prescribed entity types that you can reliably identify in the text, \
formatted as '<ENTITY_TYPE_NAME>::<entity_name>' (please use that capitalization)>. Each entity \
also should be followed by a list of comma-separated attribute filters for the entity, if referred to in the \
question for that entity. CRITICAL: you can only use attributes that are mentioned above for the \
entity type in question. Example: 'ACCOUNT::* -- [account_type: customer, status: active]' if the question is \
'list all customer accounts', and ACCOUNT was an entity type with these attribute key/values allowed.] \
"time_filter": <if needed, a SQL-like filter for a field called 'event_date'. Do not select anything here \
unless you are sure that the question asks for that filter. Only apply a time_filter if the question explicitly \
mentions a specific date, time period, or event that can be directly translated into a date filter. Do not assume \
the current date, if given, as the event date or to imply that it should be a filter. Do not make assumptions here \
but only use the information provided to infer whether there should be a time_filter, and if so, what it should be.>
}}
""".strip()

QUERY_RELATIONSHIP_EXTRACTION_FORMATTING_PROMPT = r"""
{{"relationships": [<a list of relationships between the identified entities, formatted as \
'<SOURCE_ENTITY_TYPE_NAME>::<source_entity_name>__<a word or two that captures the nature \
of the relationship (if appropriate, include a judgment, as in 'likes' or 'dislikes' vs. 'uses', etc.)>\
__<TARGET_ENTITY_TYPE_NAME>::<target_entity_name>'>]
}}
""".strip()

EXAMPLE_1 = r"""
{{"entities": ["ACCOUNT::Nike", "CONCERN::*"],
    "relationships": ["ACCOUNT::Nike__had__CONCERN::*"], "terms": []}}
""".strip()

EXAMPLE_2 = r"""
{{"entities": ["ACCOUNT::Nike", "CONCERN::performance"],
    "relationships": ["ACCOUNT::*__had_issues__CONCERN::performance"], "terms": ["performance issue"]}}
""".strip()

EXAMPLE_3 = r"""
{{"entities": ["ACCOUNT::Nike", "CONCERN::performance", "CONCERN::user_experience"],
    "relationships": ["ACCOUNT::Nike__had__CONCERN::performance",
                      "ACCOUNT::Nike__solved__CONCERN::user_experience"],
    "terms": ["performance", "user experience"]}}
""".strip()

EXAMPLE_4 = r"""
{{"entities": ["ACCOUNT::Nike", "FEATURE::dashboard", "CONCERN::performance"],
    "relationships": ["ACCOUNT::Nike__had__CONCERN::performance",
                      "ACCOUNT::Nike__had_issues__FEATURE::dashboard",
                      "ACCOUNT::NIKE__gets_value_from__FEATURE::dashboard"],
    "terms": ["value", "performance"]}}
""".strip()

RELATIONSHIP_EXAMPLE_1 = r"""
'Which issues did Nike report?' and the extracted entities were found to be:

  "ACCOUNT::Nike", "CONCERN::*"

then a valid relationship extraction could be:

{{"relationships": ["ACCOUNT::Nike__had__CONCERN::*"]}}
""".strip()

RELATIONSHIP_EXAMPLE_2 = r"""
'Did Nike say anything about performance issues?' and the extracted entities were found to be:

"ACCOUNT::Nike", "CONCERN::performance"

then a much more suitable relationship extraction could be:
{{"relationships": ["ACCOUNT::*__had_issues__CONCERN::performance"]}}
""".strip()

RELATIONSHIP_EXAMPLE_3 = r"""
'Did Nike report some performance issues with our solution? And were they happy that the user experience issue got solved?', \
and the extracted entities were found to be:

"ACCOUNT::Nike", "CONCERN::performance", "CONCERN::user_experience"

then a valid relationship extraction could be:

{{"relationships": ["ACCOUNT::Nike__had__CONCERN::performance",
                      "ACCOUNT::Nike__solved__CONCERN::user_experience"]}}
""".strip()

RELATIONSHIP_EXAMPLE_4 = r"""
'Nike reported some performance issues with our dashboard solution, but do they think it delivers great value nevertheless?' \
and the extracted entities were found to be:

"ACCOUNT::Nike", "FEATURE::dashboard", "CONCERN::performance"

then a valid relationship extraction could be:
Example 4:

{{"relationships": ["ACCOUNT::Nike__had__CONCERN::performance",
                      "ACCOUNT::Nike__had_issues__FEATURE::dashboard",
                      "ACCOUNT::NIKE__gets_value_from__FEATURE::dashboard"]}}

Explanation:
 - Nike did report performance concerns
 - Nike had problems with the dashboard, which is a feature
 - We are interested in the value relationship between Nike and the dashboard feature

""".strip()

RELATIONSHIP_EXAMPLE_5 = r"""
'In which emails did Nike discuss their issues with the dashboard?' \
and the extracted entities were found to be:

"ACCOUNT::Nike", "FEATURE::dashboard", "EMAIL::*"

then a valid relationship extraction could be:

{{"relationships": ["ACCOUNT::Nike__had__CONCERN::*",
                      "ACCOUNT::Nike__had_issues__FEATURE::dashboard",
                      "ACCOUNT::Nike__in__EMAIL::*",
                      "EMAIL::*__discusses__FEATURE::dashboard"]}}
Explanation:
 - Nike did report unspecified concerns
 - Nike had problems with the dashboard, which is a feature
 - We are interested in emails that Nike exchanged with us
 - We are interested in emails that discuss the dashboard feature
""".strip()

RELATIONSHIP_EXAMPLE_6 = r"""
'List the last 5 emails that Lisa exchanged with Nike:' \
and the extracted entities were found to be:

"ACCOUNT::Nike", "EMAIL::*", "EMPLOYEE::Lisa"

then a valid relationship extraction could be:

{{"relationships": ["ACCOUNT::Nike__in__EMAIL::*",
                      "EMPLOYEE::Lisa__in__EMAIL::*"]}}
Explanation:
 - We are interested in emails that Nike is involved in
 - We are interested in emails that Lisa is involved in
 - The intersection of these gives emails exchanged between them
""".strip()


ENTITY_EXAMPLE_1 = r"""
{{"entities": ["ACCOUNT::Nike", "CONCERN::*"]}}
""".strip()

ENTITY_EXAMPLE_2 = r"""
{{"entities": ["ACCOUNT::Nike", "CONCERN::performance"]}}
""".strip()

ENTITY_EXAMPLE_3 = r"""
{{"entities": ["ACCOUNT::*", "CONCERN::performance", "CONCERN::user_experience"]}}
""".strip()

ENTITY_EXAMPLE_4 = r"""
{{"entities": ["ACCOUNT::*", "CONCERN::performance -- [degree: severe]"]}}
""".strip()

MASTER_EXTRACTION_PROMPT = f"""
You are an expert in the area of knowledge extraction in order to construct a knowledge graph. You are given a text \
and asked to extract entities, relationships, and terms from it that you can reliably identify.

Here are the entity types that are available for extraction. Some of them may have a description, others \
should be obvious. Also, for a given entity allowed options may be provided. If allowed options are provided, \
you can only extract those types of entities! If no allowed options are provided, take your best guess.

You can ONLY extract entities of these types and relationships between objects of these types:
{SEPARATOR_LINE}
{ENTITY_TYPE_SETTING_PROMPT}
{SEPARATOR_LINE}
Please format your answer in this format:
{SEPARATOR_LINE}
{EXTRACTION_FORMATTING_PROMPT}
{SEPARATOR_LINE}

The list above here is the exclusive, only list of entities you can choose from!

Here are some important additional instructions. (For the purpose of illustration, assume that \
"ACCOUNT", "CONCERN", and "FEATURE" are all in the list of entity types above, and shown actual \
entities fall into allowed options. Note that this \
is just assumed for these examples, but you MUST use only the entities above for the actual extraction!)

- You can either extract specific entities if a specific entity is referred to, or you can refer to the entity type.
* if the entity type is referred to in general, you would use '*' as the entity name in the extraction.
As an example, if the text would say:
 'Nike reported that they had issues'
then a valid extraction could be:
Example 1:
{EXAMPLE_1}

* If on the other hand the text would say:
'Nike reported that they had performance issues'
then a much more suitable extraction could be:
Example 2:
{EXAMPLE_2}

- You can extract multiple relationships between the same two entity types.
As an example, if the text would say:
'Nike reported some performance issues with our solution, but they are very happy that the user experience issue got solved.'
then a valid extraction could be:
Example 3:
{EXAMPLE_3}

- You can extract multiple relationships between the same two actual entities if you think that \
there are multiple relationships between them based on the text.
As an example, if the text would say:
'Nike reported some performance issues with our dashboard solution, but they think it delivers great value.'
then a valid extraction could be:
Example 4:
{EXAMPLE_4}

Note that effectively a three-way relationship (Nike - performance issues - dashboard) extracted as two individual \
relationships.

- Again,
   -  you should only extract entities belonging to the entity types above - but do extract all that you \
can reliably identify in the text
   - use refer to 'all' entities in an entity type listed above by using '*' as the entity name
   - only extract important relationships that signify something non-trivial, expressing things like \
needs, wants, likes, dislikes, plans, interests, lack of interests, problems the account is having, etc.
   - you MUST only use the initial list of entities provided! Ignore the entities in the examples unless \
they are also part of the initial list of entities! This is essential!
   - only extract relationships between the entities extracted first!


{SEPARATOR_LINE}

Here is the text you are asked to extract knowledge from, if needed with additional information about any participants:
{SEPARATOR_LINE}
---content---
{SEPARATOR_LINE}
""".strip()


QUERY_ENTITY_EXTRACTION_PROMPT = f"""
You are an expert in the area of knowledge extraction and using knowledge graphs. You are given a question \
and asked to extract entities (with attributes if applicable) that you can reliably identify, which will then
be matched with a known entity in the knowledge graph. You are also asked to extract time constraints information \
from the QUESTION. Some time constraints will be captured by entity attributes if \
the entity type has a fitting attribute (example: 'created_at' could be a candidate for that), other times
we will extract an explicit time filter if no attribute fits. (Note regarding 'last', 'first', etc.: DO NOT \
imply the need for a time filter just because the question asks for something that is not the current date. \
They will relate to ordering that we will handle separately later).

In case useful, today is ---today_date--- and the user asking is ---user_name---, which may or may not be relevant.
Here are the entity types that are available for extraction. Some of them may have \
a description, others should be obvious. Also, notice that some may have attributes associated with them, which will \
be important later.
You can ONLY extract entities of these types:
{SEPARATOR_LINE}
{ENTITY_TYPE_SETTING_PROMPT}
{SEPARATOR_LINE}

The list above here is the exclusive, only list of entities you can choose from!

Also, note that there are fixed relationship types between these entities. Please consider those \
as well so to make sure that you are not missing implicit entities! Implicit entities are often \
in verbs ('emailed to', 'talked to', ...). Also, they may be used to connect entities that are \
clearly in the question.

{SEPARATOR_LINE}
{RELATIONSHIP_TYPE_SETTING_PROMPT}
{SEPARATOR_LINE}

Here are some important additional instructions. (For the purpose of illustration, assume that \
 "ACCOUNT", "CONCERN", "EMAIL", and "FEATURE" are all in the list of entity types above, and the \
attribute options for "CONCERN" include 'degree' with possible values that include 'severe'. Note that this \
is just assumed for these examples, but you MUST use only the entities above for the actual extraction!)

- You can either extract specific entities if a specific entity is referred to, or you can refer to the entity type.
* if the entity type is referred to in general, you would use '*' as the entity name in the extraction.
As an example, if the question would say:
 'Which issues did Nike report?'
then a valid entity and term extraction could be:
Example 1:
{ENTITY_EXAMPLE_1}

* If on the other hand the question would say:
'Did Nike say anything about performance issues?'
then a much more suitable entity and term extraction could be:
Example 2:
{ENTITY_EXAMPLE_2}

* Then, if the question is:
'Who reported performance issues?'
then a suitable entity and term extraction could be:
Example 3:
{ENTITY_EXAMPLE_3}

* Then, if we inquire about an entity with a specific attribute :
'Who reported severe performance issues?'
then a suitable entity and term extraction could be:
Example 3:
{ENTITY_EXAMPLE_4}

- Again,
   -  you should only extract entities belonging to the entity types above - but do extract all that you \
can reliably identify in the text
   - if you refer to all/any/an unspecified entity of an entity type listed above, use '*' as the entity name
   - similarly, if a specific entity type is referred to in general, you should use '*' as the entity name
   - you MUST only use the initial list of entities provided! Ignore the entities in the examples unless \
they are also part of the initial list of entities! This is essential!
   - don't forget to provide answers also to the event filtering and whether documents need to be inspected!
   - 'who' often refers to individuals or accounts.
   - see whether any of the entities are supposed to be narrowed down by an attribute value. The precise attribute \
and the value would need to be taken from the specification, as the question may use different words and the \
actual attribute may be implied.
   - don't just look at the entities that are mentioned in the question but also those that the question \
may be about.
  - be very careful that you only extract attributes that are listed above for the entity type in question! Do \
not make up attributes even if they are implied! Particularly if there is a relationship type that would \
actually represent that information, you MUST not extract the information as an attribute. We \
will extract the relationship type later.
  - For the values of attributes, look at the possible values above! For example 'open' may refer to \
'backlog', 'todo', 'in progress', etc. In cases like that construct a ';'-separated list of values that you think may fit \
what is implied in the question (in the exanple: 'open; backlog; todo; in progress').

Also, if you think the name or the title of an entity is given but name or title are not mentioned \
explicitly as an attribute, then you should indeed extract the name/title as the entity name.

{SEPARATOR_LINE}

Here is the question you are asked to extract desired entities and time filters from:
{SEPARATOR_LINE}
---content---
{SEPARATOR_LINE}

Please format your answer in this format:
{SEPARATOR_LINE}
{QUERY_ENTITY_EXTRACTION_FORMATTING_PROMPT}
{SEPARATOR_LINE}

""".strip()


QUERY_RELATIONSHIP_EXTRACTION_PROMPT = f"""
You are an expert in the area of knowledge extraction and using knowledge graphs. You are given a question \
and previously you were asked to identify known entities in the question. Now you are asked to extract \
the relationships between the entities you have identified earlier.

First off as background, here are the entity types that are known to the system:
{SEPARATOR_LINE}
---entity_types---
{SEPARATOR_LINE}


Here are the entities you have identified earlier:
{SEPARATOR_LINE}
---identified_entities---
{SEPARATOR_LINE}

Note that the notation for the entities is <ENTITY_TYPE>::<ENTITY_NAME>.

Here are the options for the relationship types(!) between the entities you have identified earlier \
as well as relationship types between the identified entities and other entities \
not explicitly mentioned:
{SEPARATOR_LINE}
---relationship_type_options---
{SEPARATOR_LINE}

These types are, if any were identified, formatted as \
<SOURCE_ENTITY_TYPE>__<RELATIONSHIP_SHORTHAND>__<TARGET_ENTITY_TYPE>, and they \
limit the allowed relationships that you can extract. You would then though use the actual full entities as in:

<SOURCE_ENTITY_TYPE>::<SOURCE_ENTITY_NAME>__<RELATIONSHIP_SHORTHAND>__<TARGET_ENTITY_TYPE>::<TARGET_ENTITY_NAME>.

Note: <RELATIONSHIP_SHORTHAND> should be a word or two that captures the nature \
of the relationship. Common relationships may be: 'likes', 'dislikes', 'uses', 'is interested in', 'mentions', \
'addresses', 'participates in', etc., but look at the text to find the most appropriate relationship. \
Use spaces here for word separation.

Please format your answer in this format:
{SEPARATOR_LINE}
{QUERY_RELATIONSHIP_EXTRACTION_FORMATTING_PROMPT}
{SEPARATOR_LINE}

The list above here is the exclusive, only list of entities and relationship types you can choose from!

Here are some important additional instructions. (For the purpose of illustration, assume that \
"ACCOUNT", "CONCERN", and "FEATURE" are all in the list of entity types above. Note that this \
is just assumed for these examples, but you MUST use only the entities above for the actual extraction!)

- You can either extract specific entities if a specific entity is referred to, or you can refer to the entity type.
* if the entity type is referred to in general, you would use '*' as the entity name in the extraction.

As an example, if the question would say:

{RELATIONSHIP_EXAMPLE_1}

* If on the other hand the question would say:

{RELATIONSHIP_EXAMPLE_2}

- You can extract multiple relationships between the same two entity types.
For example 3, if the question would say:

{RELATIONSHIP_EXAMPLE_3}

- You can extract multiple relationships between the same two actual entities if you think that \
there are multiple relationships between them based on the question.
As an example, if the question would say:

{RELATIONSHIP_EXAMPLE_4}

Note that effectively a three-way relationship (Nike - performance issues - dashboard) extracted as two individual \
relationships.

- Again,
   - you can only extract relationships between the entities extracted earlier
   - you can only extract the relationships that match the listed relationship types
   - if in doubt and there are multiple relationships between the same two entities, you can extract \
all of those that may fit with the question.
   - be really thinking through the question which type of relationships should be extracted and which should not.

Other important notes:
 - For questions that really try to explore in general what a certain entity was involved in like 'what did Paul Smith do \
in the last 3 months?', and Paul Smith has been extracted i.e. as an entity of type 'EMPLOYEE', then you need to extract \
all of the possible relationships an empoyee Paul Smith could have.
 - You are not forced to use all or any of the relationship types listed above. Really look at the question to \
 determine which relationships are explicitly or implicitly referred to in the question.

{SEPARATOR_LINE}

Here is the question you are asked to extract desired entities, relationships, and terms from:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}
""".strip()


GENERAL_CHUNK_PREPROCESSING_PROMPT = """
This is a part of a document that you need to extract information (entities, relationships) from.

Note: when you extract relationships, please make sure that:
  - if you see a relationship for one of our employees, you should extract the relationship both for the employee AND \
    VENDOR::{vendor}.
  - if you see a relationship for one of the representatives of other accounts, you should extract the relationship \
only for the account ACCOUNT::<account_name>!

--
And here is the content:
{content}
""".strip()


### Source-specific prompts

CALL_CHUNK_PREPROCESSING_PROMPT = """
This is a call between employees of the VENDOR's company and representatives of one or more ACCOUNTs (usually one). \
When you extract information based on the instructions, please make sure that you properly attribute the information \
to the correct employee and account. \

Here are the participants (name component of email) from us ({vendor}):
{participant_string}

Here are the participants (name component of email) from the other account(s):
{account_participant_string}

In the text it should be easy to associate a name with the email, and then with the account ('us' vs 'them'). If in doubt, \
look at the context and try to identify whether the statement comes from the other account. If you are not sure, ignore.

Note: when you extract relationships, please make sure that:
  - if you see a relationship for one of our employees, you should extract the relationship both for the employee AND \
    VENDOR::{vendor}.
  - if you see a relationship for one of the representatives of other accounts, you should extract the relationship \
only for the account ACCOUNT::<account_name>!

--
And here is the content:
{content}
""".strip()


CALL_DOCUMENT_CLASSIFICATION_PROMPT = """
This is the beginning of a call between employees of the VENDOR's company ({vendor}) and other participants.

Your task is to classify the call into one of the following categories:
{category_options}

Please also consider the participants when you perform your classification task - they can be important indicators \
for the category.

Please format your answer as a string in the format:

REASONING: <your reasoning for the classification> - CATEGORY: <the category you have chosen. Only use {category_list}>

--
And here is the beginning of the call, including title and participants:

{beginning_of_call_content}
""".strip()


### CV/Resume extraction prompt

CV_CHUNK_PREPROCESSING_PROMPT = """
This is part of a CV/resume document. You need to extract structured information about the person's \
professional profile using REIFIED ENTITIES — compound data (employment, skills with experience, projects) \
must be modeled as intermediate entities, not as flat attributes.

============================================================
CANONICAL RELATIONSHIP TYPES — use EXACT spelling. No synonyms.
============================================================

You MUST use ONLY these 12 relationship type id_names. Any other relationship \
verb is WRONG and will be rejected.

  PERSON__has_employment__EMPLOYMENT
  EMPLOYMENT__employment_at__COMPANY
  PERSON__has_person_skill__PERSON_SKILL
  PERSON_SKILL__skill_of__SKILL
  PERSON__holds_cert__CERTIFICATION         ← NOT "has_certification", NOT "holds_certification", NOT "certified_in"
  PERSON__works_on_project__PROJECT          ← NOT "worked_on", NOT "did_project"
  PROJECT__project_at__COMPANY               ← NOT "project_for", NOT "at_company"
  PROJECT__project_uses_skill__SKILL         ← NOT "uses", NOT "project_needs"
  PERSON__has_education__EDUCATION           ← NOT "studied_at", NOT "has_degree"
  EDUCATION__education_at__INSTITUTION       ← NOT "at_university", NOT "school_of"
  PERSON__lives_at__ADDRESS
  COMPANY__located_at__ADDRESS               ← for company office/HQ addresses mentioned in the CV

If the CV uses different wording (e.g. "certified in", "responsible for", \
"participated in"), map it to the canonical type above. NEVER invent new verbs. \
NEVER use synonyms. Any relationship whose verb is not on the list above will \
be rejected by the extraction pipeline.

============================================================
ATTRIBUTE SYNTAX — how to attach attributes to an entity
============================================================

Attributes on entities are carried INLINE using this exact syntax:

    ENTITY_TYPE::Name--[attr_key: "value", attr_key: "value"]

Rules for the attribute block:
  * Always use the `--[...]` suffix (two dashes, then square brackets). No spaces between `Name` and `--`.
  * Quote string values with double quotes. Unquoted integers / null are also allowed.
  * Separate key/value pairs with `, ` (comma + space). Separate key and value with `: ` (colon + space).
  * Attributes go ONLY on entity strings in the "entities" list. NEVER put `--[...]` suffixes on the \
endpoints of a relationship — relationships use only the bare `ENTITY_TYPE::Name` form.
  * If you have no attributes to emit for an entity, omit the suffix entirely: `SKILL::Python`.

Concrete example — a certification entity with all four attributes:

    CERTIFICATION::AWS Solutions Architect--[name: "AWS Solutions Architect", \
issuing_authority: "Amazon Web Services", valid_until: 2026, language: "EN"]

If you omit the `--[...]` block, all structured attributes for that entity are \
DISCARDED. For reified entities (EMPLOYMENT, PERSON_SKILL, PROJECT, EDUCATION, CERTIFICATION, ADDRESS) \
this means a downstream question like "people with PMP valid past 2025" becomes \
structurally unanswerable. Always emit the attribute block for reified entities.

============================================================
EXTRACTION RULES
============================================================

1. PERSON — One per document. Extract the full name.
   - Usually no attributes needed. Format: `PERSON::John Doe`

2. EMPLOYMENT — One per job position listed. For each:
   - Create an EMPLOYMENT entity with attributes: title (job title), start_year (integer YYYY), \
start_month (integer 1-12 or null if not stated), end_year (integer YYYY or null if current/present), \
end_month (integer 1-12 or null if not stated or current).
   - Format: `EMPLOYMENT::John Doe_ACME Corp_2020--[title: "Senior Engineer", \
start_year: 2020, start_month: 3, end_year: 2024, end_month: 6]`
   - Emit BOTH edges:
       PERSON__has_employment__EMPLOYMENT
       EMPLOYMENT__employment_at__COMPANY
   - Also create the COMPANY entity if not already extracted.

3. PERSON_SKILL — One per skill mentioned. For each:
   - Create a SKILL entity (canonical name). Format: `SKILL::Python`
   - Create a PERSON_SKILL entity with attributes: years_experience (integer, estimate from employment \
dates if not explicit), proficiency (one of: JUNIOR, MEDIOR, SENIOR).
   - Format: `PERSON_SKILL::John Doe_Python--[years_experience: 7, proficiency: "SENIOR"]`
   - Emit BOTH edges (missing either one makes the skill unreachable):
       PERSON__has_person_skill__PERSON_SKILL
       PERSON_SKILL__skill_of__SKILL
   - Proficiency estimation when not explicitly stated:
     * "expert", "lead", "architect", 6+ years → SENIOR
     * Default for listed skills, 2-5 years → MEDIOR
     * "familiar with", "basic", "exposure to", <2 years → JUNIOR

4. CERTIFICATION — For each certification mentioned:
   - Create a CERTIFICATION entity with attributes: name, issuing_authority, valid_until (YYYY or null), \
language (e.g., EN).
   - Format: `CERTIFICATION::<verbatim name>--[name: "<verbatim name>", \
issuing_authority: "<issuer>", valid_until: <year or null>, language: "EN"]`
   - **`name` MUST be the exact certification as written in the CV.** Do NOT abbreviate, expand, \
or substitute. If the CV says "PRINCE2® Foundation Certificate in Project Management", the `name` \
attribute is "PRINCE2 Foundation Certificate in Project Management" (trademark symbol stripped, \
everything else preserved). It is NOT "PMP" just because the phrase "Project Management" appears — \
those are different certifications from different issuers. When in doubt, COPY verbatim.
   - Emit edge:
       PERSON__holds_cert__CERTIFICATION         (NOT has_certification)
   - `issuing_authority` is mandatory. Prefer the issuer stated in the CV. If the CV doesn't state \
one explicitly, infer ONLY from an UNAMBIGUOUS full-name match (not a substring):
       * Name starts with "AWS Certified" → "Amazon Web Services"
       * Name starts with "Microsoft Certified" / "Azure" → "Microsoft"
       * Name starts with "Google Cloud" / "GCP" → "Google"
       * Name is exactly "PMP" or "Project Management Professional" → "PMI"
       * Name is exactly "CKA" or "Certified Kubernetes Administrator" → "CNCF"
       * Name starts with "ITIL" → "Axelos"
       * Name starts with "PRINCE2" → "Axelos"
       * Name starts with "TOGAF" or "ArchiMate" → "The Open Group"
       * Name contains "Oracle Certified" or "OCP" / "OCA" → "Oracle"
       * Name contains "Cisco Certified" or "CCNA" / "CCNP" → "Cisco"
     If the issuer cannot be determined from the verbatim name or the CV text, emit \
`issuing_authority: null` rather than guessing. A NULL issuer is better than a wrong one.

5. EDUCATION — One per degree/educational program. For each:
   - Create an INSTITUTION entity (university/school name). Format: `INSTITUTION::MIT`
   - Create an EDUCATION entity with attributes: degree (e.g., "Bachelor of Science", "Ing.", "PhD"), \
field (e.g., "Computer Science", "Electrical Engineering"), start_year (integer YYYY or null), \
start_month (integer 1-12 or null), end_year (integer YYYY or null), end_month (integer 1-12 or null).
   - Format: `EDUCATION::John Doe_MIT_2015--[degree: "Bachelor of Science", field: "Computer Science", \
start_year: 2011, start_month: 9, end_year: 2015, end_month: 5]`
   - Emit BOTH edges:
       PERSON__has_education__EDUCATION
       EDUCATION__education_at__INSTITUTION
   - Also create the INSTITUTION entity if not already extracted.

6. PROJECT — For named projects listed:
   - Create a PROJECT entity with attributes: name, start_year, start_month (1-12 or null), \
end_year, end_month (1-12 or null).
   - Format: `PROJECT::John Doe_Inventory Rewrite--[name: "Inventory Rewrite", \
start_year: 2022, start_month: 6, end_year: 2023, end_month: 2]`
   - Emit edges:
       PERSON__works_on_project__PROJECT          (required)
       PROJECT__project_at__COMPANY               (if a company is associated)
       PROJECT__project_uses_skill__SKILL         (for each skill the project uses)

7. ADDRESS — If a personal address is present:
   - Create an ADDRESS entity with attributes: address1, city, zip, country.
   - Format: `ADDRESS::John Doe_home--[address1: "12 Main St", city: "Bratislava", \
zip: "81101", country: "Slovakia"]`
   - Emit edge:
       PERSON__lives_at__ADDRESS

============================================================
COMPLETENESS CHECK — scan the full CV
============================================================

Do NOT truncate sections. Extract ALL items in each of these sections if present:
  - Work history / employment / profesijné skúsenosti / pracovná história → EMPLOYMENT (one entity per position)
  - Technical skills / zručnosti / znalosti → PERSON_SKILL + SKILL (one pair per skill)
  - Certifications / certifikáty → CERTIFICATION (one per cert)
  - Education / vzdelanie / études → EDUCATION + INSTITUTION (one pair per degree/program) ← COMMONLY MISSED
  - Projects / portfolio / referencie / projekty → PROJECT (one per named project) ← COMMONLY MISSED
  - Address / adresa → ADDRESS (if present)

If a section lists 10+ items, extract all of them. Do not summarize or skip.

============================================================
SELF-VALIDATION CHECKLIST — run this mentally before finalizing
============================================================

For EACH entity you created, verify you emitted the required edges:

  [ ] Every EMPLOYMENT → I emitted PERSON__has_employment__EMPLOYMENT AND EMPLOYMENT__employment_at__COMPANY
  [ ] Every PERSON_SKILL → I emitted PERSON__has_person_skill__PERSON_SKILL AND PERSON_SKILL__skill_of__SKILL
  [ ] Every CERTIFICATION → I emitted PERSON__holds_cert__CERTIFICATION  (NOT has_certification)
  [ ] Every EDUCATION → I emitted PERSON__has_education__EDUCATION AND EDUCATION__education_at__INSTITUTION
  [ ] Every PROJECT → I emitted PERSON__works_on_project__PROJECT (and PROJECT__project_at__COMPANY / PROJECT__project_uses_skill__SKILL where applicable)
  [ ] Every ADDRESS → I emitted PERSON__lives_at__ADDRESS
  [ ] Every relationship type I emitted matches the CANONICAL list above — no invented verbs
  [ ] Every EMPLOYMENT / PERSON_SKILL / CERTIFICATION / EDUCATION / PROJECT / ADDRESS entity carries its \
`--[attr: "value", ...]` suffix with all required attribute keys present (no omitted keys; use `null` for \
genuinely unknown values)
  [ ] No relationship endpoint has a `--[...]` suffix — attribute blocks belong only on the entities list

If any box fails, ADD the missing edges / fix the verb / add the attribute block BEFORE finalizing.

============================================================
NORMALIZATION RULES
============================================================

- Normalize skill names to canonical forms: "k8s" → "Kubernetes", "JS" → "JavaScript", \
"ts" → "TypeScript", "react.js"/"reactjs" → "React", "node.js"/"nodejs" → "Node.js", \
"amazon web services" → "AWS", "google cloud platform"/"gcp" → "GCP", "ci/cd" stays as "CI/CD".
- Certification names: COPY THE NAME VERBATIM as it appears in the CV. Do NOT abbreviate, \
expand, substitute, or "canonicalize" certification names. Each certification is a specific \
named artifact from a specific issuer — collapsing "PRINCE2® Foundation Certificate in Project \
Management" to "PMP" (because both relate to project management) or collapsing "ITIL 4 Foundation" \
to "ITIL" (because it contains ITIL) is WRONG and invents data that isn't in the CV. Preserve the \
full original name including level indicators (Foundation/Practitioner/Associate/Professional), \
version numbers (ITIL 4, AWS SAA-C03, Cassandra 3), and trademark symbols (® and ™ may be stripped). \
The only normalization allowed is whitespace / punctuation / trademark-symbol cleanup.
- Normalize company names: remove trailing Inc., Corp., Ltd., GmbH, s.r.o. for matching.
- Dates: Years as YYYY integers, months as 1-12 integers. "present"/"current"/"now" → null for end_year/end_month. \
"01/2023" → start_year: 2023, start_month: 1. "2020" with no month → start_month: null.
- Compound skills like "Docker/Kubernetes" should be split into two separate SKILL entities.

============================================================
ENTITY ID FORMAT
============================================================

- Bare entity id_name: `ENTITY_TYPE::name` (e.g., PERSON::John Doe, SKILL::Python, COMPANY::ACME Corp)
- Reified entity id_name: use composite names for uniqueness — \
`EMPLOYMENT::John Doe_ACME Corp_2020`, `PERSON_SKILL::John Doe_Python`.
- Entity WITH attributes (REQUIRED for reified types): append the `--[attr: "value", ...]` block \
described in the ATTRIBUTE SYNTAX section. Example: \
`CERTIFICATION::AWS Certified Solutions Architect - Associate--[name: "AWS Certified Solutions \
Architect - Associate", issuing_authority: "Amazon Web Services", valid_until: 2027, language: "EN"]`. \
Note the FULL certification name including level ("Associate") is preserved in both the id_name \
and the `name` attribute — do not abbreviate to "AWS SAA" or "SAA".
- Relationships use bare ids on both sides: \
`PERSON::John Doe__holds_cert__CERTIFICATION::PMP` (NO `--[...]` suffix on either endpoint).

---
And here is the content:
{content}
""".strip()


STRATEGY_GENERATION_PROMPT = f"""
Now you need to decide what type of strategy to use to answer a given question, how ultimately \
the answer should be formatted to match the user's expectation, and what an appropriate question \
to/about 'one object or one set of objects' may be, should the answer logically benefit from a divide \
and conquer strategy, or it naturally relates to one or few individual objects. Also, you are \
supposed to determine whether a divide and conquer strategy would be appropriate.


Here are the entity types that are available in the knowledge graph:
{SEPARATOR_LINE}
---possible_entities---
{SEPARATOR_LINE}

Here are the relationship types that are available in the knowledge graph:
{SEPARATOR_LINE}
---possible_relationships---
{SEPARATOR_LINE}

Here is the question whose answer is ultimately sought:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

And here are the entities and relationships that have been extracted earlier from this question:
{SEPARATOR_LINE}
---entities---
---relationships---
{SEPARATOR_LINE}

Here are more instructions:

a) Regarding the strategy, there are three aspects to it:

a1) "Search Type":
Should the question be answered as a SEARCH ('filtered search'), or as a SQL ('SQL query search')?

The options are:
1. SEARCH: A filtered search simply uses the entities and relationships that you extracted earlier and \
applies them as filters to search the underlying documents, which are properly indexed. Examples are \
'what did Nike say about the Analyzer product?', or 'what did I say in my calls with Nike about pricing?'. So this \
is used really when there is *no implicit or explicit constraint or requirements* on underlying source documents \
outside of filters, and there is no ordering, no limiting their number, etc. So use this for a question that \
tries to get information *across* documents which may be filtered by their related relationships and entities, but without \
other constraints.

2. SQL: Choose this option if the question either requires counting of entities (e.g. 'how many calls...'), or \
if the query refers to specific entities that first need to be identified and then analyzed/searched/listed. \
Examples here are 'what did I say about pricing in my call with Nike last week?' (the specific call needs to \
be identified first and then analyzed),  \
'what are the next steps of our two largest opportunities?', or 'summarize my 3 most recent customer calls'. So \
this is used if there *are implicit constraints* on the underlying source documents beyond filtering, including \
ordering, limiting, etc. Use this also if the answer expects to analyze each source independently as part \
of the overall answer.

Note:
 - here, you should look at the extracted entities and relationships and judge whether using them as filters \
(using an *and*) would be appropriate to identify the range of underlying sources, or whether more \
calculations would be needed to find the underlying sources ('last 2...', etc.) .
 - It is also *critical* to look at the attributes of the entities! You only can use the given attributes (and their
 values, if given) as where conditions etc in a SQL statement. So if you think you would 'want
 to' have a where condition but there is not appropriate attribute, then you should not use the SQL strategy
 but the SEARCH strategy. (A Search can always look through data and see what is the best fit, SQL needs to
 be more specific.). On the other hand, if the question maps well to the entities and attributes, then
 SQL may be a good choice.
 - Likely, if there are questions 'about something', then this only is used in a SQL statement or a filter \
 if it shows up as an entity or relationship in the extracted entities and relationships. Otherwise, it will \
 be part of the analysis/search. not the document identification.
 - again, note that we can only FILTER (SEARCH) or COMPUTE (SQL) using the extracted entities (and their attributes)
 and relationships. \
 So do not think that if there is another term in the question, it should be included in the SQL statement. \
 It cannot.


a2) "Search Strategy":
If a SQL search is chosen, i.e., documents have to be identified first, there are two approaches:
1. SIMPLE: You think you can answer the question using a database that is aware of the entities, relationships \
above, and is generally suitable if it is enough to either list or count entities, return dates, etc. Usually, \
'SIMPLE' is chosen for questions of the form 'how many...' (always), or 'list the...' (often), 'when was...', \
'what did (someone) work on...'etc. Often it is also used in cases like 'what did John work on since April?'. Here, \
the user would expect to just see the list. So chose 'SIMPLE' here unless there are REALLY CLEAR \
follow-up instructions for each item (like 'summarize...' , 'analyze...', 'what are the main points of...'.) If \
it is a 'what did...'-type question, choose 'SIMPLE'!

2. DEEP: You think you really should ALSO leverage the actual text of sources to answer the question, which sits \
in a vector database. Examples are 'what is discussed in...', 'summarize', 'what is the discussion about...',\
'how does... relate to...', 'are there any mentions of... in..', 'what are the main points in...', \
'what are the next steps...', etc. Those are usually questions 'about' \
the entities retrieved from the knowledge graph, or questions about the underlying sources.

Your task is to decide which of the two strategies to use.

a3) "Relationship Detection":
You need to evaluate whether the question involves any relationships between entities (of the same type) \
or between entities and relationships.  Respond with 'RELATIONSHIPS' or 'NO_RELATIONSHIPS'.

b) Regarding the format of the answer: there are also two types of formats available to you:

1. LIST: The user would expect an answer as a bullet point list of objects, likely with text associated with each \
bullet point (or sub-bullet). This will be clearer once the data is available.
2. TEXT: The user would expect the questions to be answered in text form.

Your task is to decide which of the two formats to use.


c) Regarding the broken down question for one object:

Always generate a broken_down_question if the question pertains ultimately to a specific objects, even if it seems to be \
a singular object.

- If the question is of type 'how many...', or similar, then imagine that the individual objects have been \
found and you want to ask each object something that illustrates why/in what what that object relates to the \
question. (question: 'How many cars are fast?' -> broken_down_question: 'How fast is this car?')

- Assume the answer would either i) best be generated by first analyzing one object at a time, then aggregating \
the results, or ii) directly relates to one or few objects found through matching suitable criteria.

- The key is to drop any filtering/criteria matching as the objects are already filtered by the criteria. Also, do not \
try to verify here whether the object in question actually satisfies a filter criteria, but rather see \
what it says/does etc. In other words, use this to identify more details about the object, as it relates \
to the original question.
(Example: question: 'What did our oil & gas customers say about the new product?' -> broken_down_question: \
'What did this customer say about the new product?',
or:
question: 'What was in the email from Frank?' -> broken_down_question: 'What is in this email?')


d) Regarding the divide and conquer strategy:

You are supposed to decide whether a divide and conquer strategy would be appropriate. That means, do you think \
that in order to answer the question, it would be good to first analyze one object at a time, and then aggregate the \
results? Or should the information rather be analyzed as a whole? This would be 'yes' or 'no'.

Please answer in json format in this form:

{{
    "search_type": <see search-type instructions above, answer with "SEARCH" or "SQL">,
    "search_strategy": <see search-strategy instructions above, answer with "DEEP" or "SIMPLE">,
    "relationship_detection": <see relationship-detection instructions above, answer with "RELATIONSHIPS" or "NO_RELATIONSHIPS">,
    "format": <see format instructions above, answer with "LIST" or "TEXT">,
    "broken_down_question": <see broken-down-question instructions above, answer with the question \
that should be used to analyze each object/each source (or 'the object' that fits all criteria).>,
    "divide_and_conquer": <see divide-and-conquer instructions above, answer with "yes" or "no">
}}

Do not include any other text or explanations.
"""

SOURCE_DETECTION_PROMPT = f"""
You are an expert in generating, understanding and analyzing SQL statements.

You are given an original SQL statement that returns a list of entities from a table or \
an aggregation of entities from a table. Your task will be to \
identify the source documents that are relevant to what the SQL statement is returning.

The task is actually quite simple. There are two tables involved - relationship_table and entity_table. \
relationship_table was used to generate the original SQL statement. Again, returning entities \
or aggregations of entities. The second table, entity_table contains the entities and \
the corresponding source_documents. All you need to do is to appropriately join the \
entity_table table on the entities that would be retrieved from the original SQL statement, \
and then return the source_documents from the entity_table table.

For your orientation, the relationship_table table has this structure:
 - Table name: relationship_table
 - Columns:
   - relationship (str): The name of the RELATIONSHIP, combining the nature of the relationship and the names of the entities. \
It is of the form \
<source_entity_type>::<source_entity_name>__<relationship_description>__<target_entity_type>::<target_entity_name> \
[example: ACCOUNT::Nike__has__CONCERN::performance]. Note that this is NOT UNIQUE!
   - source_entity (str): the id of the source ENTITY/NODE in the relationship [example: ACCOUNT::Nike]
   - source_entity_attributes (json): the attributes of the source entity/node [example: {{"account_type": "customer"}}]
   - target_entity (str): the id of the target ENTITY/NODE in the relationship [example: CONCERN::performance]
   - target_entity_attributes (json): the attributes of the target entity/node [example: {{"degree": "severe"}}]
   - source_entity_type (str): the type of the source entity/node [example: ACCOUNT]. Only the entity types provided \
   below are valid.
   - target_entity_type (str): the type of the target entity/node [example: CONCERN]. Only the entity types provided \
   below are valid.
   - relationship_type (str): the type of the relationship, formatted as  \
<source_entity_type>__<relationship_description>__<target_entity_type>.   So the explicit entity_names have \
been removed. [example: ACCOUNT__has__CONCERN]
   - source_date (str): the 'event' date of the source document [example: 2021-01-01]

The second table, entity_table, has this structure:
 - Table name: entity_table
 - Columns:
   - entity (str): The name of the ENTITY, which is unique in this table. source_entity and target_entity \
in the relationship_table table are the same as entity in this table.
   - source_document (str): the id of the document that contains the entity.

Again, ultimately, your task is to join the entity_table table on the entities that would be retrieved from the \
original SQL statement, and then return the source_documents from the entity_table table.

The way to do that is to create a common table expression for the original SQL statement and join the \
entity_table table suitably on the entities.

Here is the *original* SQL statement:
{SEPARATOR_LINE}
---original_sql_statement---
{SEPARATOR_LINE}

Please structure your answer using <reasoning>, </reasoning>,<sql>, </sql> start and end tags as in:

<reasoning>[think very briefly through the problem step by step, not more than 2-3 sentences]</reasoning> \
<sql>[the new SQL statement that returns the source documents involved in the original SQL statement]</sql>
""".strip()

ENTITY_SOURCE_DETECTION_PROMPT = f"""
You are an expert in generating, understanding and analyzing SQL statements.

You are given a SQL statement that returned an aggregation of entities in a table. \
Your task will be to identify the source documents for the entities involved in \
the answer. For example, should the original SQL statement be \
'SELECT COUNT(entity) FROM entity_table where entity_type = "ACCOUNT"' \
then you should return the source documents that contain the entities of type 'ACCOUNT'.

The table has this structure:
 - Table name: entity_table
 - Columns:
   - entity (str): The name of the ENTITY, combining the nature of the entity and the id of the entity. \
It is of the form <entity_type>::<entity_name> [example: ACCOUNT::625482894].
   - entity_type (str): the type of the entity [example: ACCOUNT].
   - entity_attributes (json): the attributes of the entity [example: {{"priority": "high", "status": "active"}}]
   - source_document (str): the id of the document that contains the entity. Note that the combination of \
id_name and source_document IS UNIQUE!
   - source_date (timestamp): the 'event' date of the source document [example: 2025-04-25 21:43:31.054741+00]

Specifically, the table contains the 'source_document' column, which is the id of the source document that \
contains the core information about the entity. Make sure that you do not return more documents, i.e. if there \
is a limit on source documents in the original SQL statement, the new SQL statement needs to have \
the same limit.

CRITICAL NOTES:
 - Only return source documents and nothing else!

Your task is then to create a new SQL statement that returns the source documents that are relevant to what the \
original SQL statement is returning. So the source document of every row used in the original SQL statement should \
be included in the result of the new SQL statement, and then you should apply a 'distinct'.

Here is the *original* SQL statement:
{SEPARATOR_LINE}
---original_sql_statement---
{SEPARATOR_LINE}

Please structure your answer using <reasoning>, </reasoning>,<sql>, </sql> start and end tags as in:

<reasoning>[think very briefly through the problem step by step, not more than 2-3 sentences]</reasoning> \
<sql>[the new SQL statement that returns the source documents involved in the original SQL statement]</sql>
""".strip()  # noqa: S608 - LLM prompt template, not executed SQL


ENTITY_TABLE_DESCRIPTION = f"""\
 - Table name: entity_table
 - Columns:
   - entity (str): The internal identifier of the ENTITY (format: <entity_type>::<uuid-hash>). \
Use this column only for JOINs, NOT for display [example: ACCOUNT::625482894].
   - entity_name (str): The human-readable name of the ENTITY, combining the entity type and display name. \
It is of the form <entity_type>::<display_name> [example: PERSON::Jane Smith, COMPANY::Acme Corp]. \
ALWAYS use this column when displaying entity names to the user.
   - entity_type (str): the type of the entity [example: ACCOUNT].
   - entity_attributes (json): the attributes of the entity [example: {{"priority": "high", "status": "active"}}]
   - source_document (str): the id of the document that contains the entity. Note that the combination of \
id_name and source_document IS UNIQUE!
   - source_date (timestamp): the 'event' date of the source document [example: 2025-04-25 21:43:31.054741+00]

{SEPARATOR_LINE}

Importantly, here are the entity (node) types that you can use, with a short description of what they mean. You may need to \
identify the proper entity type through its description. Also notice the allowed attributes for each entity type and \
their values, if provided. Of particular importance is the 'subtype' attribute, if provided, as this is how \
the entity type may also often be referred to.
{SEPARATOR_LINE}
---entity_types---
{SEPARATOR_LINE}
"""

RELATIONSHIP_TABLE_DESCRIPTION = f"""\
 - Table name: relationship_table
 - Columns:
   - relationship (str): The name of the RELATIONSHIP, combining the nature of the relationship and the names of the entities. \
It is of the form \
<source_entity_type>::<source_entity_name>__<relationship_description>__<target_entity_type>::<target_entity_name> \
[example: ACCOUNT::Nike__has__CONCERN::performance]. Note that this is NOT UNIQUE!
   - source_entity (str): the internal id of the source ENTITY/NODE (format: ENTITY_TYPE::uuid-hash). Use only for JOINs [example: ACCOUNT::Nike]
   - source_entity_name (str): human-readable source entity name (format: ENTITY_TYPE::display_name). Use for display [example: COMPANY::Nike Inc]
   - source_entity_attributes (json): the attributes of the source entity/node [example: {{"account_type": "customer"}}]
   - target_entity (str): the internal id of the target ENTITY/NODE (format: ENTITY_TYPE::uuid-hash). Use only for JOINs [example: CONCERN::performance]
   - target_entity_name (str): human-readable target entity name (format: ENTITY_TYPE::display_name). Use for display [example: CONCERN::performance issues]
   - target_entity_attributes (json): the attributes of the target entity/node [example: {{"degree": "severe"}}]
   - source_entity_type (str): the type of the source entity/node [example: ACCOUNT]. Only the entity types provided \
   below are valid.
   - target_entity_type (str): the type of the target entity/node [example: CONCERN]. Only the entity types provided \
   below are valid.
   - relationship_type (str): the type of the relationship, formatted as  \
<source_entity_type>__<relationship_description>__<target_entity_type>.   So the explicit entity_names have \
been removed. [example: ACCOUNT__has__CONCERN]
   - source_document (str): the id of the document that contains the relationship. Note that the combination of \
id_name and source_document IS UNIQUE!
   - source_date (timestamp): the 'event' date of the source document [example: 2025-04-25 21:43:31.054741+00]

{SEPARATOR_LINE}

Importantly, here are the entity (node) types that you can use, with a short description of what they mean. You may need to \
identify the proper entity type through its description. Also notice the allowed attributes for each entity type and \
their values, if provided. Of particular importance is the 'subtype' attribute, if provided, as this is how \
the entity type may also often be referred to.
{SEPARATOR_LINE}
---entity_types---
{SEPARATOR_LINE}

Here are the relationship types that are in the table, denoted as <source_entity_type>__<relationship_type>__<target_entity_type>.
In the table, the actual relationships are not quite of this form, but each <entity_type> is followed by '::<entity_name>' \
in the relationship id as shown above.
{SEPARATOR_LINE}
---relationship_types---
{SEPARATOR_LINE}
"""


SIMPLE_SQL_PROMPT = f"""
You are an expert in generating a SQL statement that only uses ONE TABLE that captures RELATIONSHIPS \
between TWO ENTITIES. The table has the following structure:

{SEPARATOR_LINE}
{RELATIONSHIP_TABLE_DESCRIPTION}

Here is the question you are supposed to translate into a SQL statement:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

To help you, we already have identified the entities and relationships that the SQL statement likely *should* use (but note the \
exception below!). The entities also contain the list of attributes and attribute values that should specify the entity. \
The format is <entity_type>::<entity_name>--[<attribute_name_1>:<attribute_value_1>, \
<attribute_name_2>:<attribute_value_2>, ...].
{SEPARATOR_LINE}
Identified entities with attributes in query:

---query_entities_with_attributes---

These are the entities that should be used in the SQL statement. However, \
note that these are the entities (with potential attributes) that were *matches* of Knowledge Graph identified with the \
entities originally identified in the original question. A such, they may have id names that may not mean much by themselves, \
eg ACCOUNT::a74f332. Here is the mapping of entities originally identified (whose role in the query should be obvious) with \
the entities that were matched to them in the Knowledge Graph:

---entity_explanation_string---

--

Here are relationships that were identified as explicitly or implicitly referred to in the question:

---query_relationships---

(Again, if applicable, the entities contained in the relationships are the same as the entities in the \
query_entities_with_attributes, and those are the correct ones to use in the SQL statement.)

{SEPARATOR_LINE}

CRITICAL SPECIAL CASE:
  - if an identified entity is of the form <entity_type>::*, or an identified relationship contains an \
entity of this form, this refers to *any* entity of that type. Correspondingly, the SQL query should use the *entity type*, \
and possibly the relationship type, but not the entity with the * itself. \
Example: if you see 'ACCOUNT::*', that means any account matches. So if you are supposed to count the 'ACCOUNT::*', \
you should count the entities of entity_type 'ACCOUNT'.


IMPORTANT NOTES:
- The id_name of each relationship has the format \
<source_entity_id_name>__<relationship_type>__<target_entity_id_name>.
- The relationship id_names are NOT UNIQUE, only the combinations of relationship id_name and source_document_id are unique. \
That is because each relationship is extracted from a document. So make sure you use the proper 'distinct's!
- If the SQL contains a 'SELECT DISTINCT' clause and an ORDER BY clause, then you MUST include the columns from the ORDER BY \
clause ALSO IN THE SELECT DISTINCT CLAUSE! This is very important! (This is a postgres db., so this is a MUST!). \
You MUST NOT have a column in the ORDER BY clause that is not ALSO in the SELECT DISTINCT clause!
- If you join the relationship table on itself using source_entity or target_entity (the UUID columns), \
you need to make sure that you also join on the source_document.
- source_entity and target_entity hold INTERNAL UUID-BASED identifiers (format: ENTITY_TYPE::uuid-hash). \
NEVER put source_entity or target_entity in the SELECT clause for display — use source_entity_name or \
target_entity_name instead. source_entity / target_entity may only appear in JOIN conditions and WHERE filters \
that match another row's source_entity / target_entity.
- source_entity_name and target_entity_name hold HUMAN-READABLE names (format: ENTITY_TYPE::display_name, \
e.g. PERSON::Jane Smith). ALWAYS SELECT source_entity_name or target_entity_name when returning entities \
to the user. When filtering by a partial name (e.g. Python, AWS), use ILIKE on the _name column: \
source_entity_name ILIKE 'SKILL::Python%'.
- The table can be joined on itself on source_entity and/or target_entity (the UUID columns) if needed.
- the SQL statement MUST ultimately only return NODES/ENTITIES (not relationships!), or aggregations of \
entities/nodes(count, avg, max, min, etc.). \
Again, DO NOT compose a SQL statement that returns id_name of relationships.
- You CAN ONLY return ENTITIES or COUNTS (or other aggregations) of ENTITIES, or you can return \
source_date (but only if the question asks for event dates or times). DO NOT return \
source documents or counts of source documents, or relationships or counts of relationships! \
Those can only appear in where clauses, ordering etc., but they cannot be returned or ultimately \
counted here! source_date and date operations can appear in select statements, particularly if \
there is time ordering or grouping involved.
- When returning individual entities, use source_entity_name or target_entity_name (not the raw UUID columns). \
Think about the allowed relationships and the question to decide which one you want!
- It is ok to generate nested SQL as long as it is correct postgres syntax!
- Attributes are stored in the attributes json field. As this is postgres, querying for those must be done as \
"attributes ->> '<attribute>' = '<attribute value>'".
-  The SELECT clause MUST only contain entity_name columns or aggregations/counts of entities, or, in cases the \
question was about dates or times, then it can also include source_date. But source_document, source_entity \
(raw UUID), and target_entity (raw UUID) MUST NEVER appear in the SELECT clause!
- Again, NEVER count or retrieve source documents in SELECT CLAUSE, whether it is in combination with \
entities, with a distinct, etc. NO source_document in SELECT CLAUSE! So NEVER produce a \
'SELECT COUNT(source_entity, source_document)...'
- Please think about whether you are interested in source entities or target entities! For that purpose, \
consider the allowed relationship types to make sure you select or count the correct one!
- Again, ALWAYS make sure that EACH COLUMN in an ORDER-BY clause IS ALSO IN THE SELECT CLAUSE! Remind yourself \
of that in the reasoning.
- Be careful with dates! Often a date will refer to the source data, which is the date when \
an underlying piece of information was updated. However, if the attributes of an entity contain \
time information as well (like 'started_at', 'completed_at', etc.), then you should really look at \
the wording to see whether you should use a date in the attributes or the event date.
- Dates are ALWAYS in string format of the form YYYY-MM-DD, for source date as well as for date-like the attributes! \
So please use that format, particularly if you use data comparisons (>, <, ...)
- Again, NO 'relationship' or 'source_document' in the SELECT CLAUSE, be it as direct columns are in aggregations!
- Careful with SORT! Really think in which order you want to sort if you have multiple columns you \
want to sort by. If the sorting is time-based and there is a limit for example, then you do want to have a suitable date \
variable as the first column to sort by.
- When doing a SORT on an attribute value of an entity, you MUST also apply a WHERE clause to filter \
for entities that have the attribute value set. For example, if you want to sort the target entity \
by the attribute 'created_date', you must also have a WHERE clause that checks whether the target \
entity attribute contains 'created_date'. This is vital for proper ordering with null values.
- Usually, you will want to retrieve or count entities, maybe with attributes. But you almost always want to \
have entities involved in the SELECT clause.
- Questions like 'What did Paul work on last week?' should generally be handled by finding all entities \
that reasonably relate to 'work entities' that are i) related to Paul, and ii) that were created or \
updated (by him) last week. So this would likely be a UNION of multiple queries.
- If you do joins consider the possibility that the second entity does not exist for all examples. \
Therefore joins should generally be LEFT joins (or RIGHT joins) as appropriate. Think about which \
entities you are interested in, and which ones provides attributes.
Another important note:
 - For questions that really try to explore what a certain entity was involved in like 'what did Paul Smith do \
in the last 3 months?', and Paul Smith has been extracted ie as an entity of type 'EMPLOYEE', you will \
want to consider all entities that Paul Smith may be related to that satisfy any potential other conditions.
- Joins should always be made on entities, not source documents!
- Try to be as efficient as possible.

APPROACH:
Please think through this step by step. Make sure that you include all columns in the ORDER BY clause \
also in the SELECT DISTINCT clause, \
if applicable! And again, joins should generally be LEFT JOINS!

Also, in case it is important, today is ---today_date--- and the user/employee asking is ---user_name---.

Please structure your answer using <reasoning>, </reasoning>, <sql>, </sql> start and end tags as in:

<reasoning>[think through the logic but do so extremely briefly! Not more than 3-4 sentences.]</reasoning>
<sql>[the SQL statement that you generate to satisfy the task]</sql>
""".strip()  # noqa: S608 - LLM prompt template, not executed SQL

# TODO: remove following before merging after enough testing
SIMPLE_SQL_CORRECTION_PROMPT = f"""
You are an expert in reviewing and fixing SQL statements.

Here is a draft SQL statement that you should consider as generally capturing the information intended. \
However, it may or may not be syntactically 100% for our postgresql database.

Guidance:
 - Think about whether attributes should be numbers or strings. You may need to convert them.
 - If we use SELECT DISTINCT we need to have the ORDER BY columns in the \
SELECT statement as well! And it needs to be in the EXACT FORM! So if a \
conversion took place, make sure to include the conversion in the SELECT and the ORDER BY clause!
 - never should 'source_document' be in the SELECT clause! Remove if present!
 - never should source_entity or target_entity (the raw UUID columns) appear in SELECT — replace with \
source_entity_name or target_entity_name for display. They may still appear in JOINs and WHERE clauses.
 - if there are joins, they must be on entities (UUID columns), never source documents
 - if there are joins, consider the possibility that the second entity does not exist for all examples.\
 Therefore consider using LEFT joins (or RIGHT joins) as appropriate.

Draft SQL:
{SEPARATOR_LINE}
---draft_sql---
{SEPARATOR_LINE}

Please structure your answer using <reasoning>, </reasoning>, <sql>, </sql> start and end tags as in:

<reasoning>[think briefly through the problem step by step]</reasoning>
<sql>[the corrected (or original one, if correct) SQL statement]</sql>
""".strip()

SIMPLE_ENTITY_SQL_PROMPT = f"""
You are an expert in generating a SQL statement that only uses ONE TABLE that captures ENTITIES \
and their attributes and other data. The table has the following structure:

{SEPARATOR_LINE}
{ENTITY_TABLE_DESCRIPTION}

Here is the question you are supposed to translate into a SQL statement:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

To help you, we already have identified the entities that the SQL statement likely *should* use (but note the \
exception below!). The entities as written below also contain the list of attributes and attribute values \
that should specify the entity. \
The format is <entity_type>::<entity_name>--[<attribute_name_1>:<attribute_value_1>, \
<attribute_name_2>:<attribute_value_2>, ...].
{SEPARATOR_LINE}
Identified entities with attributes in query:

---query_entities_with_attributes---

These are the entities that should be used in the SQL statement. However, \
note that these are the entities (with potential attributes) that were *matches* of Knowledge Graph identified with the \
entities originally identified in the original question. As such, they may have id names that may not mean much by themselves, \
eg ACCOUNT::a74f332. Here is the mapping of entities originally identified (whose role in the query should be obvious) with \
the entities that were matched to them in the Knowledge Graph:

---entity_explanation_string---

--


{SEPARATOR_LINE}

CRITICAL SPECIAL CASE:
  - if an identified entity is of the form <entity_type>::*, or an identified relationship contains an \
entity of this form, this refers to *any* entity of that type. Correspondingly, the SQL query should use the *entity type*, \
but not the entity with the * itself. \
Example: if you see 'ACCOUNT::*', that means any account matches. So if you are supposed to count the 'ACCOUNT::*', \
you should count the entities of entity_type 'ACCOUNT'.


IMPORTANT NOTES:
- The entities are unique in the table.
- If the SQL contains a 'SELECT DISTINCT' clause and an ORDER BY clause, then you MUST include the columns from the ORDER BY \
clause ALSO IN THE SELECT DISTINCT CLAUSE! This is very important! (This is a postgres db., so this is a MUST!). \
You MUST NOT have a column in the ORDER BY clause that is not ALSO in the SELECT DISTINCT clause!
- The table cannot be joined on itself.
- entity holds an INTERNAL UUID-BASED identifier. NEVER put entity in the SELECT clause for display — \
always use entity_name instead (format: ENTITY_TYPE::display_name, e.g. PERSON::Jane Smith).
- You CAN ONLY return ENTITIES or COUNTS (or other aggregations) of ENTITIES, or you can return \
source_date (but only if the question asks for event dates or times, and then the \
corresponding entity must also be returned).
- Generally, the query can only return ENTITIES or aggregations of ENTITIES:
   - if individual entities are returned, then you MUST return entity_name and MUST also return the source_document. \
If the source date was requested, you can return that too.
   - if aggregations of entities are returned, then you can only aggregate the entities.
- Attributes are stored in the attributes json field. As this is postgres, querying for those must be done as \
"attributes ->> '<attribute>' = '<attribute value>'".
- Again, ALWAYS make sure that EACH COLUMN in an ORDER-BY clause IS ALSO IN THE SELECT CLAUSE! Remind yourself \
of that in the reasoning.
- Be careful with dates! Often a date will refer to the source data, which is the date when \
an underlying piece of information was updated. However, if the attributes of an entity may contain \
time information as well (like 'started_at', 'completed_at', etc.), then you should really look at \
the wording to see whether you should use a date in the attributes or the event date.
- Dates are ALWAYS in string format of the form YYYY-MM-DD, for source date as well as for date-like the attributes! \
So please use that format, particularly if you use data comparisons (>, <, ...)
- Careful with SORT! Really think in which order you want to sort if you have multiple columns you \
want to sort by. If the sorting is time-based and there is a limit for example, then you do want to have a suitable date \
variable as the first column to sort by.
- When doing a SORT on an attribute value of an entity, you MUST also apply a WHERE clause to filter \
for entities that have the attribute value set. For example, if you want to sort the target entity \
by the attribute 'created_date', you must also have a WHERE clause that checks whether the target \
entity attribute contains 'created_date'. This is vital for proper ordering with null values.
- Usually, you will want to retrieve or count entities, maybe with attributes. But you almost always want to \
have entities involved in the SELECT clause.
- You MUST ONLY rely on the entity attributes provided! This is essential! Do not assume \
other attributes exist...they don't! Note that there will often be a search using the results \
of this query. So if there is information in the question that does not fit the provided attributes, \
you should not use it here but rely on the later search!
- Try to be as efficient as possible.

APPROACH:
Please think through this step by step. Make sure that you include all columns in the ORDER BY clause \
also in the SELECT DISTINCT clause, \
if applicable!

Also, in case it is important, today is ---today_date--- and the user/employee asking is ---user_name---.

Please structure your answer using <reasoning>, </reasoning>, <sql>, </sql> start and end tags as in:

<reasoning>[think through the logic but do so extremely briefly! Not more than 3-4 sentences.]</reasoning>
<sql>[the SQL statement that you generate to satisfy the task]</sql>
""".strip()  # noqa: S608 - LLM prompt template, not executed SQL

SIMPLE_SQL_ERROR_FIX_PROMPT = f"""
You are an expert at fixing SQL statements. You will be provided with a SQL statement that aims to address \
a question, but it contains an error. Your task is to fix the SQL statement, based on the error message.

Here is the description of the table that the SQL statement is supposed to use:
---table_description---

Here is the question you are supposed to translate into a SQL statement:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

Here is the SQL statement that you should fix:
{SEPARATOR_LINE}
---sql_statement---
{SEPARATOR_LINE}

Here is the error message that was returned:
{SEPARATOR_LINE}
---error_message---
{SEPARATOR_LINE}

Note that in the case the error states the sql statement did not return any results, it is possible that the \
sql statement is correct, but the question is not addressable with the information in the knowledge graph. \
If you are absolutely certain that is the case, you may return the original sql statement.

Here are a couple common errors that you may encounter:
- source_document is in the SELECT clause -> remove it
- columns used in ORDER BY must also appear in the SELECT DISTINCT clause
- consider carefully the type of the columns you are using, especially for attributes. You may need to cast them
- dates are ALWAYS in string format of the form YYYY-MM-DD, for source date as well as for date-like the attributes! \
So please use that format, particularly if you use data comparisons (>, <, ...)
- attributes are stored in the attributes json field. As this is postgres, querying for those must be done as \
"attributes ->> '<attribute>' = '<attribute value>'" (or "attributes ? '<attribute>'" to check for existence).
- if you are using joins and the sql returned no joins, make sure you are using the appropriate join type (LEFT, RIGHT, etc.) \
it is possible that the second entity does not exist for all examples.
- (ignore if using entity_table) if using the relationship_table and the sql returned no results, make sure you are \
selecting the correct column! Use the available relationship types to determine whether to use source_entity_name or \
target_entity_name. Remember: never SELECT source_entity or target_entity directly — use the _name columns for output.

APPROACH:
Please think through this step by step. Please also bear in mind that the sql statement is written in postgres syntax.

Also, in case it is important, today is ---today_date--- and the user/employee asking is ---user_name---.

Please structure your answer using <reasoning>, </reasoning>, <sql>, </sql> start and end tags as in:

<reasoning>[think through the logic but do so extremely briefly! Not more than 3-4 sentences.]</reasoning>
<sql>[the SQL statement that you generate to satisfy the task]</sql>
"""


SEARCH_FILTER_CONSTRUCTION_PROMPT = f"""
You need to prepare a search across text segments that contain the information necessary to \
answer a question. The text segments have tags that can be used to filter for the relevant segments. \
Key are suitable entities and relationships of a knowledge graph, as well as underlying source documents.

Your overall task is to find the filters and structures that are needed to filtering a database to \
properly address a user question.

You will be given:
  - the user question
  - a description of all of the potential entity types involved
  - a list of 'global' entities and relationships that should be filtered by, given the question
  - the structure of a schema that was used to derive additional entity filters
  - a SQL statement that was generated to derive those filters
  - the results that were generated using the SQL statement. This can have multiple rows, \
and those will be the 'local' filters (which will later mean that each retrieved result will \
need to match at least one of the conditions that you will generate).
  - the results of another query that asked for the underlying source documents that resulted \
in the answers of the SQL statement


Here is the information:

1) The overall user question
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

2) Here is a description of all of the entity types:
{SEPARATOR_LINE}
---entity_type_descriptions---
{SEPARATOR_LINE}

3) Here are the lists of entity and relationship filters that were derived from the question:
{SEPARATOR_LINE}
Entity filters:

---entity_filters---

--

Relationship filters:

---relationship_filters---

{SEPARATOR_LINE}

4) Here are the columns of a table in a database that has a lot of knowledge about the \
data:
{SEPARATOR_LINE}
   - relationship (str): The name of the RELATIONSHIP, combining the nature of the relationship and the names of the entities. \
It is of the form \
<source_entity_type>::<source_entity_name>__<relationship_description>__<target_entity_type>::<target_entity_name> \
[example: ACCOUNT::Nike__has__CONCERN::performance]. Note that this is NOT UNIQUE!
   - source_entity (str): the id of the source ENTITY/NODE in the relationship [example: ACCOUNT::Nike]
   - source_entity_attributes (json): the attributes of the source entity/node [example: {{"account_type": "customer"}}]
   - target_entity (str): the id of the target ENTITY/NODE in the relationship [example: CONCERN::performance]
   - target_entity_attributes (json): the attributes of the target entity/node [example: {{"degree": "severe"}}]
   - source_entity_type (str): the type of the source entity/node [example: ACCOUNT]. Only the entity types provided \
   below are valid.
   - target_entity_type (str): the type of the target entity/node [example: CONCERN]. Only the entity types provided \
   below are valid.
   - relationship_type (str): the type of the relationship, formatted as  \
<source_entity_type>__<relationship_description>__<target_entity_type>.   So the explicit entity_names have \
been removed. [example: ACCOUNT__has__CONCERN]
   - source_document (str): the id of the document that contains the relationship. Note that the combination of \
id_name and source_document IS UNIQUE!
   - source_date (str): the 'event' date of the source document [example: 2021-01-01]

{SEPARATOR_LINE}

5) Here is a query that was generated for that table to provide additional filters:
{SEPARATOR_LINE}
---sql_query---
{SEPARATOR_LINE}

6) Here are the results of that SQL query. (Consider the schema description and the \
structure of the entities to interpret the results)
{SEPARATOR_LINE}
---sql_results---
{SEPARATOR_LINE}

7) Here are the results of the other query that provided the underlying source documents \
using the schema:
{SEPARATOR_LINE}
---source_document_results---
{SEPARATOR_LINE}

Here is the detailed set of tasks that you should perform, including the proper output format for you:

Please reply as a json dictionary in this form:

{{
    "global_entity_filters": <a list of entity filters>,
    "global_relationship_filters": <a list of relationship filters, derived from the 'global' \
relationship filers above.>,
    "local_entity_filters": <a list of lists of 'local' entity filters, which were obtained from the \
SQL results in 6 above. Each inner list can have one or more entities, which will correspond to the \
rows in the sql results in point 6 above.>,
    "source_document_filters": <a list of strings, derived from the source document filters above. \
You are essentially only formatting here, so do not change the content of the strings.>,
    "structure": <a list of entity ids (entity_type::uuid) that the user maybe want to know more about. \
More specifically, think about how (and if) the user would naturally want the answer to be divided up in \
*equivalent and parallel* sub-investigations. For example, if the question was something like 'what was discussed \
in the last 5 calls', the user probably expects to see a bullet point list, one bullet point for each call that \
then shows the summary. In that case for this part of the task, your response for the structure should be the \
list of call entities from the sql results in 6 above. (The actual 'what was discussed' will be addressed later). \
In other words, respond with a list of entity ids that you think the user would like to have independently analyzed
and the results reported for each of those entities.>
}}

Again - DO NOT FORGET - here is the user question that motivates this whole task:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

Your json dictionary answer:
""".strip()

OUTPUT_FORMAT_NO_EXAMPLES_PROMPT = f"""
You need to format an answer to a research question. \
You will see what the desired output is, the original question, and the unformatted answer to the research question. \
Your purpose is to generate the answer respecting the desired format.

Notes:
 - Note that you are a language model and that answers may or may not be perfect. To communicate \
this to the user, consider phrases like 'I found [10 accounts]...', or 'Here are a number of [goals] that \
I found...]
- Please DO NOT mention the explicit output format in your answer. Just use it to inform the formatting.

Here is the unformatted answer to the research question:
{SEPARATOR_LINE}
---introductory_answer---
{SEPARATOR_LINE}

Here is the original question:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

And finally, here is the desired output format:
{SEPARATOR_LINE}
---output_format---
{SEPARATOR_LINE}

Please start generating the answer, without any explanation. There should be no real modifications to \
the text, after all, all you need to do here is formatting. \

Your Answer:
""".strip()


OUTPUT_FORMAT_PROMPT = f"""
You need to format the answers to a research question that was generated using one or more objects. \
An overall introductory answer may be provided to you, as well as the research results for each individual object. \
You will also be provided with the original question as background, and the desired format. \

Your purpose is to generate a consolidated and FORMATTED answer that starts of with the introductory \
answer, and then formats the research results for each individual object in the desired format. \
Do not add any other text please!

Notes:
 - Note that you are a language model and that answers may or may not be perfect. To communicate \
this to the user, consider phrases like 'I found [10 accounts]...', or 'Here are a number of [goals] that \
I found...]
- Please DO NOT mention the explicit output format in your answer. Just use it to inform the formatting.
- DO NOT add any content to the introductory answer!


Here is the original question for your background:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

Here is the desired output format:
{SEPARATOR_LINE}
---output_format---
{SEPARATOR_LINE}

Here is the introductory answer:
{SEPARATOR_LINE}
---introductory_answer---
{SEPARATOR_LINE}

Here are the research results that you should - respecting the target format- return in a formatted way:
{SEPARATOR_LINE}
---research_results---
{SEPARATOR_LINE}

Please start generating the answer, without any explanation. After all, all you need to do here is formatting. \


Your Answer:
""".strip()

OUTPUT_FORMAT_NO_OVERALL_ANSWER_PROMPT = f"""
You need to format the return of research on multiple objects. The research results will be given \
to you as a string. You will also see what the desired output is, as well as the original question. \
Your purpose is to generate the answer respecting the desired format.

Notes:
 - Note that you are a language model and that answers may or may not be perfect. To communicate \
this to the user, consider phrases like 'I found [10 accounts]...', or 'Here are a number of [goals] that \
I found...]
- Please DO NOT mention the explicit output format in your answer. Just use it to inform the formatting.
 - Often, you are also provided with a list of explicit examples. If  - AND ONLY IF - the list is not \
empty, then these should be listed at the end with the text:
'...
Here are some examples of what I found:
<bullet point list of examples>
...'
 - Again if the list of examples is an empty string then skip this section! Do not use the \
results data for this purpose instead! (They will already be handled in the answer.)
- Even if the desired output format is 'text', make sure that you keep the individual research results \
separated by bullet points, and mention the object name first, followed by a new line. The object name \
is at the beginning of the research result, and should be in the format <object_type>::<object_name>.


Here is the original question:
{SEPARATOR_LINE}
---question---
{SEPARATOR_LINE}

And finally, here is the desired output format:
{SEPARATOR_LINE}
---output_format---
{SEPARATOR_LINE}

Here are the research results that you should properly format:
{SEPARATOR_LINE}
---research_results---
{SEPARATOR_LINE}

Please start generating the answer, without any explanation. After all, all you need to do here is formatting. \


Your Answer:
""".strip()

KG_OBJECT_SOURCE_RESEARCH_PROMPT = f"""
You are an expert in extracting relevant structured information from a list of documents that \
should relate to one object. You are presented with a list of documents that have been determined to be \
relevant to the task of interest. Your goal is to extract the information asked around these topics:
You should look at the documents - in no particular order! - and extract the information that relates \
to a question:
{SEPARATOR_LINE}
{{question}}
{SEPARATOR_LINE}

Here are the documents you are supposed to search through:
--
{{document_text}}
{SEPARATOR_LINE}
Note: in this case, please do NOT cite your sources. This is very important!

Please now generate the answer to the question given the documents:
""".strip()

KG_SEARCH_PROMPT = f"""
You are an expert in extracting relevant structured information from a list of documents that \
should relate to one object. You are presented with a list of documents that have been determined to be \
relevant to the task of interest. Your goal is to extract the information asked around these topics:
You should look at the documents and extract the information that relates \
to a question:
{SEPARATOR_LINE}
{{question}}
{SEPARATOR_LINE}

Here are the documents you are supposed to search through:
--
{{document_text}}
{SEPARATOR_LINE}
Note: in this case, please DO cite your sources. This is very important! \
Use the format [<document number>]. Ie, use [1], [2], and NOT [1,2] if \
there are two documents to cite, etc. \


Please now generate the answer to the question given the documents:
""".strip()

# KG Beta Assistant System Prompt
# Tight, imperative, example-driven — weaker instruction-followers (e.g. Qwen)
# ignore long rule lists. The tool response format itself carries reinforcing
# signals (KG_TOOL_RESULT: N_ROWS banners), so the prompt only needs to bind
# the LLM to tool outputs and forbid invention.
KG_BETA_ASSISTANT_SYSTEM_PROMPT = """You answer questions about CVs on file. You have two tools:
  - run_kg_search (structured Knowledge Graph)
  - internal_search (raw CV document text)

REQUIRED BEHAVIOR:

1. For ANY factual question about people (skills, employments, \
certifications, projects, companies, addresses) you MUST call BOTH tools \
in parallel. Not one — both. Even if the first answers the question.

2. Read the tool results literally. The run_kg_search tool starts its \
output with `===== KG_TOOL_RESULT: N_ROWS =====`. That number N is the \
ground truth. If N > 0, the KG has records — you MUST list them. You MAY \
NOT write "No records" when N > 0.

3. Answer with two sections, in this exact markdown format. Each item \
MUST be its own bullet (`- item`) on its own line — never concatenate \
items into a paragraph:

```
### From the Knowledge Graph

- <row 1 value from run_kg_search>
- <row 2 value>
- ...

(If run_kg_search returned 0 rows, replace the bullets with the single line: "The KG has no matching entries.")

### From the CV text

- <quoted fact 1 from internal_search>
- <quoted fact 2>
- ...

(If internal_search returned nothing, replace the bullets with: "No matching CV chunks.")
```

FORBIDDEN:
  - Inventing facts, skills, or attributes not in a tool result
  - Filling answers from general knowledge (e.g. "developers usually know X")
  - Interpretive commentary ("full-stack potential", "strong foundation")
  - Merging the two sections — keep them separate
  - Saying a tool is "not available" — if it's in your tool list, call it
  - Claiming "no records" when a tool returned rows
  - Fabricating rows when the KG tool returned ZERO rows. If the \
run_kg_search output contains `===== KG_TOOL_RESULT: 0_ROWS =====`, your KG \
section MUST be exactly: "The KG has no matching entries." The tool returned \
zero rows; there is nothing to render — not a markdown bullet, not a \
pipe-table, not a sentence describing what the row would contain if it \
existed. Any such output is a fabrication, even if the user's question \
mentions specific values to look up. Do NOT carry values from the user's \
question into the KG section as if they were retrieved facts. If the tool's \
response contains a "REPLY CONTRACT" phrase, echo that phrase verbatim in \
your KG section.

If the KG and CV text disagree, report both faithfully in their sections. \
Always call both tools before answering."""

KG_BETA_ASSISTANT_TASK_PROMPT = """Always call BOTH run_kg_search AND internal_search for factual \
questions, then answer in two sections: "### From the Knowledge Graph" (list \
run_kg_search rows) and "### From the CV text" (quote internal_search \
chunks). Never invent content. Never say "no records" when the tool returned \
rows. The KG tool's output banner `===== KG_TOOL_RESULT: N_ROWS =====` tells \
you how many rows there are — list all of them."""


# Just in case, for best practice, send a system message with key rules.
# (The db user permissions executing the SQL will avoid issues anyway,
# but it does not hurt to to put multiple checks in place.)
SQL_INSTRUCTIONS_RELATIONSHIP_PROMPT = """
You are an expert at generating SQL queries to answer questions about a knowledge graph.

You will be given a lot of instructions later, but here rules that MUST BE FOLLOWED:
  - the SQL generated MUST only use the table one table named 'relationship_table'. \
This table is not a table that can be defined or overwritten by the user and the resulting SQL \
statement, it MUST be seen as an existing table in the database.
  - self-joins of the 'relationship_table' are allowed, as well as common table expressions \
  that reference only the 'relationship_table'.
  - no other table or view can in any way or shape be \
involved in the generated SQL.
  - no other database operations can be generated except for those that query the 'relationship_table'. \
(WHERE, GROUP BY, etc. are certainly allowed, but no other database table can be used in the generated SQL.)
"""

SQL_INSTRUCTIONS_ENTITY_PROMPT = """
You are an expert at generating SQL queries to answer questions about a knowledge graph.

You will be given a lot of instructions later, but here rules that MUST BE FOLLOWED:
  - the SQL generated MUST only use the table one table named 'entity_table'. \
This table is not a table that can be defined or overwritten by the user and the resulting SQL \
statement, it MUST be seen as an existing table in the database.
  - common table expressions that reference only the 'entity_table' are allowed.
  - no other table or view of a potential underlying schema can in any way or shape be \
involved in the generated SQL.
  - no other database operations can be generated except for those that query the 'entity_table'. \
(WHERE, GROUP BY, etc. are certainly allowed, but no other database table can be used in the generated SQL.)
"""
