"""Pure allowlisted projection of native app-server policy metadata.

No I/O, authentication, configuration writes or model requests. Full config
responses may contain secrets; callers must never log them. This module reads
only enumerated policy fields and MCP names/enabled flags, never credential
values, commands, headers, environment contents or instruction text.
"""
from __future__ import annotations


class MetadataRefusal(ValueError):
    pass


CAPABILITIES = (
    'apps', 'plugins', 'plugin_hooks', 'hooks', 'computer_use', 'multi_agent',
    'multi_agent_v2', 'multi_agent_v2_dynamic_tools', 'code_mode', 'code_mode_only',
    'enable_mcp_apps', 'recommended_plugins', 'executor_capability_discovery_v2',
    'memories', 'external_agent_memory_import',
    'shell_snapshot', 'undo',
)


def native_setup_settings(context: dict, mcp_names: list[str], workspaces: list[str]) -> dict:
    """Per-process supported overrides, without touching global configuration."""
    if not context.get('model') or not context.get('effort'):
        raise MetadataRefusal('current parent model and effort are required')
    settings = {
        'model_provider': 'openai', 'model': context['model'],
        'model_reasoning_effort': context['effort'], 'approval_policy': 'never',
        'web_search': 'disabled', 'project_doc_max_bytes': 0,
        'plugins._default.enabled': False, 'apps._default.enabled': False,
        'agents.enabled': False, 'cloud.skills.enabled': False,
        'skills.bundled.enabled': False, 'skills.include_instructions': False,
        'allow_login_shell': False, 'memories.generate_memories': False,
        'memories.use_memories': False, 'memories.dedicated_tools': False,
        'analytics.enabled': False, 'feedback.enabled': False,
        'mcp_servers': {name: {'enabled': False} for name in mcp_names},
        'projects': {path: {'trust_level': 'untrusted'} for path in workspaces},
    }
    settings.update({'features.' + name: False for name in CAPABILITIES})
    return settings


def _object(value) -> dict:
    if not isinstance(value, dict):
        raise MetadataRefusal('native policy metadata has an invalid shape')
    return value


def _false(mapping: dict, name: str):
    mapping = _object(mapping)
    if mapping.get(name) is not False:
        raise MetadataRefusal('required disabled capability is absent or enabled')


def project_policy(config_response: dict, providers: dict, context: dict, *,
                   require_mcp_disabled: bool = True) -> dict:
    """Return only nonsecret proof fields, or a constant-text refusal."""
    cfg = config_response.get('config')
    if not isinstance(cfg, dict):
        raise MetadataRefusal('native policy response is absent')
    if cfg.get('model_provider') != 'openai':
        raise MetadataRefusal('effective provider differs from native OpenAI')
    if cfg.get('model') != context.get('model') or not context.get('model'):
        raise MetadataRefusal('effective model differs from current parent')
    if cfg.get('model_reasoning_effort') != context.get('effort') or not context.get('effort'):
        raise MetadataRefusal('effective effort differs from current parent')
    # Compare only to the exact production endpoint forms recognized by the
    # pinned native source. Never return or log endpoint values.
    endpoint = cfg.get('chatgpt_base_url')
    production = ('https://chatgpt.com', 'https://chatgpt.com/backend-api',
                  'https://chatgpt.com/codex', 'https://chatgpt.com/backend-api/codex')
    if endpoint is not None and (not isinstance(endpoint, str)
                                 or endpoint.rstrip('/') not in production):
        raise MetadataRefusal('custom native ChatGPT endpoint requires review')
    endpoint = cfg.get('openai_base_url')
    if endpoint is not None:
        raise MetadataRefusal('native OpenAI endpoint override requires review')
    # Presence checks do not read instruction contents.
    for name in ('model_instructions_file', 'instructions'):
        if cfg.get(name) is not None:
            raise MetadataRefusal('endpoint or base-instruction override requires review: ' + name)
    if cfg.get('service_tier') not in (None, 'default'):
        raise MetadataRefusal('nondefault service tier is outside the authorized route')
    if providers.get('defaultProviderId') != 'openai':
        raise MetadataRefusal('native provider default drifted')
    entries = providers.get('data', [])
    if not isinstance(entries, list) or not all(isinstance(p, dict) for p in entries):
        raise MetadataRefusal('native provider metadata has an invalid shape')
    selected = [p for p in entries if p.get('id') == 'openai']
    if (len(selected) != 1 or selected[0].get('settings') != {'type': 'openai'}
            or selected[0].get('baseUrl') is not None):
        raise MetadataRefusal('native builtin provider summary is incompatible')
    if cfg.get('approval_policy') != 'never' or cfg.get('web_search') != 'disabled':
        raise MetadataRefusal('native approval or web policy differs')
    if cfg.get('project_doc_max_bytes') != 0:
        raise MetadataRefusal('project instruction budget is not isolated')
    features = cfg.get('features', {})
    for name in CAPABILITIES:
        _false(features, name)
    memories = _object(cfg.get('memories', {}))
    _false(memories, 'generate_memories')
    _false(memories, 'use_memories')
    _false(memories, 'dedicated_tools')
    skills = _object(cfg.get('skills', {}))
    _false(skills, 'include_instructions')
    _false(skills.get('bundled', {}), 'enabled')
    _false(_object(cfg.get('cloud', {})).get('skills', {}), 'enabled')
    servers = cfg.get('mcp_servers', {})
    if not isinstance(servers, dict) or not all(isinstance(name, str) for name in servers):
        raise MetadataRefusal('native MCP metadata is invalid')
    names = sorted(servers)
    if require_mcp_disabled:
        for name in names:
            if not isinstance(servers[name], dict) or servers[name].get('enabled') is not False:
                raise MetadataRefusal('a native MCP server is enabled or unresolved')
    return {
        'model': context['model'], 'effort': context['effort'], 'provider': 'openai',
        'builtin_provider_verified': True, 'required_capabilities_disabled': True,
        'memory_disabled': True, 'project_instruction_budget': 0,
        'mcp_names': names, 'mcp_disabled': require_mcp_disabled,
    }


def verify_thread_settings(settings: dict, context: dict, environment_id: str) -> dict:
    if (settings.get('model') != context.get('model')
            or settings.get('effort') != context.get('effort')
            or settings.get('modelProvider') != 'openai'):
        raise MetadataRefusal('native thread model/provider/effort drifted')
    envs = settings.get('environments')
    if (not isinstance(envs, list) or len(envs) != 1 or not isinstance(envs[0], dict)
            or envs[0].get('environmentId') != environment_id):
        raise MetadataRefusal('native thread is not exclusively on its owned remote executor')
    if settings.get('sandboxPolicy') != {'type': 'externalSandbox', 'networkAccess': 'restricted'}:
        raise MetadataRefusal('explicit external sandbox was not accepted')
    if settings.get('approvalPolicy') != 'never':
        raise MetadataRefusal('native thread approval policy differs')
    return {'model': context['model'], 'effort': context['effort'],
            'provider': 'openai', 'environment_id': environment_id,
            'external_isolation_owner': 'verified task-owned container',
            'approval_policy': 'never'}
