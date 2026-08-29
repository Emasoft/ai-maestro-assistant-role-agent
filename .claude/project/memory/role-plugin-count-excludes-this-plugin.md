---
name: role-plugin-count-excludes-this-plugin
description: "why is ai-maestro-assistant-role-agent missing from PREDEFINED_ROLE_PLUGIN_NAMES / should I add this plugin to the role-plugin list / the role plugin count is 8 not 9 / consumers assume exactly eight role plugins / is the missing role plugin entry a bug / can I bump PREDEFINED_ROLE_PLUGIN_NAMES to nine / persona alignment pass wants to add the plugin name / do not tidy the role-plugin registry / ai-maestro issue 86 F2 open question / role plugin registry omission is deliberate / why does the fleet list only eight roles / assistant-role-agent not registered as a role plugin / adding a ninth role plugin breaks consumers / known open question not a defect / leave the role plugin count alone"
ocd: 2026-08-29
lmd: 2026-08-29
publish-globally: false
metadata:
  node_type: memory
  type: project
  tier: component
---

# role-plugin-count-excludes-this-plugin


^ATOM-B4SG-VAMM [desc: "ai-maestro deliberately keeps ai-maestro-assistant-role-agent OUT of PREDEFINED_ROLE_PLUGIN_NAMES because consumers assume exactly 8 role plugins", keywords: PREDEFINED_ROLE_PLUGIN_NAMES role_plugin_count eight_role_plugins nine_role_plugins assistant-role-agent_not_listed missing_from_role_plugin_registry ai-maestro_issue_86_F2 persona_alignment_pass do_not_bump_the_count deliberate_omission_not_a_bug, type: project, trdd: TRDD-8GZ3TZD0, ocd: 2026-08-29, lmd: 2026-08-29]
The ai-maestro repo deliberately excludes `ai-maestro-assistant-role-agent` from
`PREDEFINED_ROLE_PLUGIN_NAMES`, because downstream consumers assume that list has
exactly 8 entries. This is a known OPEN QUESTION tracked as ai-maestro#86 F2 — not a
registry oversight.

DO NOT "fix" it by adding this plugin to the list or bumping the count to 9: that
changes an assumption consumers encode, and the open question is about whether the
8-entry contract should change at all, which is not this plugin's call to make.

Reported by the ai-maestro session on 2026-08-29 while answering a pre-publish
dependency check for 0.5.1; measured there by grep, not assumed.

## Notes and lessons learned
