import re

from onyx.db.kg_config import KGConfigSettings
from onyx.kg.models import KGPerson


def format_entity_id(entity_id_name: str) -> str:
    return make_entity_id(*split_entity_id(entity_id_name))


def make_entity_id(entity_type: str, entity_name: str) -> str:
    # Normalize underscores to spaces so "Ivan_Kopáčik" and "Ivan Kopáčik"
    # always produce the same id_name regardless of LLM formatting choices.
    return f"{entity_type.upper()}::{entity_name.replace('_', ' ').lower()}"


def split_entity_id(entity_id_name: str) -> list[str]:
    return entity_id_name.split("::")


def get_entity_type(entity_id_name: str) -> str:
    return entity_id_name.split("::", 1)[0].upper()


def format_entity_id_for_models(entity_id_name: str) -> str:
    entity_split = entity_id_name.split("::")
    if len(entity_split) == 2:
        entity_type, entity_name = entity_split
        separator = "::"
    elif len(entity_split) > 2:
        raise ValueError(f"Entity {entity_id_name} is not in the correct format")
    else:
        entity_name = entity_id_name
        separator = entity_type = ""

    formatted_entity_type = entity_type.strip().upper()
    formatted_entity_name = entity_name.strip().replace('"', "").replace("'", "")

    return f"{formatted_entity_type}{separator}{formatted_entity_name}"


def get_attributes(entity_w_attributes: str) -> dict[str, str]:
    """
    Extract attributes from an entity string.
    E.g., "TYPE::Entity--[attr1: value1, attr2: value2]" -> {"attr1": "value1", "attr2": "value2"}
    """
    attr_split = entity_w_attributes.split("--")
    if len(attr_split) != 2:
        raise ValueError(f"Invalid entity with attributes: {entity_w_attributes}")

    match = re.search(r"\[(.*)\]", attr_split[1])
    if not match:
        return {}

    attr_list_str = match.group(1)
    return {
        attr_split[0].strip(): attr_split[1].strip()
        for attr in attr_list_str.split(",")
        if len(attr_split := attr.split(":", 1)) == 2
    }


def split_entity_and_attributes(entity_w_attributes: str) -> tuple[str, dict[str, str]]:
    """
    Safely split an entity string into (bare_entity_id, attributes).

    Accepts both forms:
      - Without attributes:    "TYPE::Name"           -> ("TYPE::Name", {})
      - With attributes:       "TYPE::Name--[k: v]"   -> ("TYPE::Name", {"k": "v"})

    Values surrounded by matching single or double quotes are unquoted so
    that `--[name: "AWS Solutions Architect"]` parses to
    `{"name": "AWS Solutions Architect"}`. Values without quotes are kept
    as-is (trimmed of whitespace).

    Unlike `get_attributes`, this helper never raises on missing `--`, so
    it's safe to call on every entity the LLM emits without pre-inspection.
    """
    if "--" not in entity_w_attributes:
        return entity_w_attributes, {}

    bare, _, attr_tail = entity_w_attributes.partition("--")
    bare = bare.strip()

    match = re.search(r"\[(.*)\]", attr_tail)
    if not match:
        return bare, {}

    attr_list_str = match.group(1).strip()
    if not attr_list_str:
        return bare, {}

    attrs: dict[str, str | None] = {}
    for attr in attr_list_str.split(","):
        key, sep, value = attr.partition(":")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            # Drop unquoted `null` values entirely rather than storing
            # the string "null". A missing key is equivalent to JSON null
            # for JSONB queries (->>'key' returns SQL NULL either way),
            # and avoids `COALESCE((attrs->>'end_year')::int, 2026)`
            # crashing with "invalid input syntax for integer: 'null'".
            if value.lower() == "null":
                continue
            attrs[key] = value
    return bare, attrs


def make_entity_w_attributes(entity: str, attributes: dict[str, str]) -> str:
    return f"{entity}--[{', '.join(f'{k}: {v}' for k, v in attributes.items())}]"


def format_relationship_id(relationship_id_name: str) -> str:
    return make_relationship_id(*split_relationship_id(relationship_id_name))


def make_relationship_id(
    source_node: str, relationship_type: str, target_node: str
) -> str:
    return f"{format_entity_id(source_node)}__{relationship_type.lower()}__{format_entity_id(target_node)}"


# Matches the first `__lowercase_verb__` in a relationship id_name.
# Entity types use UPPER_CASE (with single `_`), so `__` followed by a
# lowercase word followed by `__` is unambiguous as the verb separator.
_VERB_RE = re.compile(r"__([a-z][a-z_]+?)__")


def split_relationship_id(relationship_id_name: str) -> list[str]:
    """Split a relationship id_name into [source, verb, target].

    The naive ``split("__")`` breaks when the LLM emits bare source types
    (e.g. ``PROJECT__project_at__COMPANY::Name``) because entity type names
    like ``PERSON_SKILL`` contain single ``_`` that survive the split while
    the missing ``::`` causes extra parts. The regex approach finds the
    verb (always lowercase) and splits around it, producing exactly 3
    parts regardless of how the LLM formatted the endpoints.
    """
    m = _VERB_RE.search(relationship_id_name)
    if m:
        return [
            relationship_id_name[: m.start()],
            m.group(1),
            relationship_id_name[m.end() :],
        ]
    return relationship_id_name.split("__")


def format_relationship_type_id(relationship_type_id_name: str) -> str:
    return make_relationship_type_id(
        *split_relationship_type_id(relationship_type_id_name)
    )


def make_relationship_type_id(
    source_node_type: str, relationship_type: str, target_node_type: str
) -> str:
    return f"{source_node_type.upper()}__{relationship_type.lower()}__{target_node_type.upper()}"


def split_relationship_type_id(relationship_type_id_name: str) -> list[str]:
    return relationship_type_id_name.split("__")


def extract_relationship_type_id(relationship_id_name: str) -> str:
    source_node, relationship_type, target_node = split_relationship_id(
        relationship_id_name
    )
    return make_relationship_type_id(
        get_entity_type(source_node), relationship_type, get_entity_type(target_node)
    )


def extract_email(email: str) -> str | None:
    """
    Extract an email from an arbitrary string (if any).
    Only the first email is returned.
    """
    match = re.search(r"([A-Za-z0-9._+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)", email)
    return match.group(0) if match else None


def kg_email_processing(email: str, kg_config_settings: KGConfigSettings) -> KGPerson:
    """
    Process the email.
    """
    name, company_domain = email.split("@")
    assert isinstance(company_domain, str)
    assert isinstance(kg_config_settings.KG_VENDOR_DOMAINS, list)
    assert isinstance(kg_config_settings.KG_VENDOR, str)

    employee = any(
        domain in company_domain for domain in kg_config_settings.KG_VENDOR_DOMAINS
    )
    if employee:
        company = kg_config_settings.KG_VENDOR
    else:
        # TODO: maybe store a list of domains for each account and use that to match
        # right now, gmail and other random domains are being converted into accounts
        company = company_domain.title()

    return KGPerson(name=name, company=company, employee=employee)
