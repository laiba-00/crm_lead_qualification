# -*- coding: utf-8 -*-
{
    'name': 'CRM Lead Qualification',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Two-stage Lead Qualification -> Closing Team CRM workflow',
    'description': """
CRM Lead Qualification
=======================
Implements a two-department sales workflow on top of crm.lead:

- Lead Qualification Team: Sales Agents qualify cold leads into Hot
  Leads.
- Closing Team: Department Head / Partner close transferred Hot
  Leads into active customers.

Includes role-based security (Administrator, Manager, Sales Agent,
Closer), a Hot Lead transfer wizard, an 11-stage pipeline split
across two crm.team records, and manager reporting (pivot/graph) on
agent productivity and conversion rates.
    """,
    'author': 'Laiba Waseem',
    'license': 'LGPL-3',

    # crm.lead, crm.team, and crm.stage all come from the stock 'crm'
    # module - that is the only hard dependency. 'crm' itself already
    # depends on 'mail' (chatter/activities/tracking used throughout
    # this module), so it does not need to be listed separately here.
    'depends': ['crm',
                'crm_iap_mine',
                ],

    'assets': {
        'web.assets_backend': [
            'crm_lead_qualification/static/src/components/manager_dashboard.js',
            'crm_lead_qualification/static/src/components/manager_dashboard.xml',
            'crm_lead_qualification/static/src/css/dashboard.css',
        ],
    },

    # ------------------------------------------------------------
    # LOAD ORDER - this is not arbitrary. Each dependency below was
    # flagged as it came up while building the individual files:
    #
    # 1. security.xml first - defines the 4 groups. Referenced by
    #    ir.model.access.csv (group_id column), by the wizard's
    #    closer_id domain (env.ref to group_lead_qualification_closer),
    #    and by every menuitem's groups attribute.
    #
    # 2. ir.model.access.csv - grants baseline model access per group.
    #    Must exist before any user can interact with crm.lead through
    #    these groups at all.
    #
    # 3. crm_team_data.xml before crm_stage_data.xml - stage records
    #    reference team_lead_qualification / team_closing via ref=,
    #    which requires the team records to already be loaded.
    #
    # 4. wizard view - depends on security.xml only (for the group
    #    ref in the domain), safe to load any time after step 1.
    #
    # 5. crm_lead_agent_views.xml / crm_lead_closer_views.xml - depend
    #    on crm_stage_data.xml (stage_id domains reference team_id)
    #    and on the action_open_transfer_wizard/action_close_as_won
    #    /action_close_as_lost methods in models/crm_lead.py, not on
    #    each other.
    #
    # 6. crm_lead_manager_views.xml BEFORE
    #    report/crm_lead_report_views.xml - the report action reuses
    #    view_crm_lead_manager_search and view_crm_lead_manager_tree
    #    by ref=. Reversing this order breaks install.
    #
    # 7. crm_menus.xml last - every menuitem's action= references an
    #    ir.actions.act_window defined in one of the view/report files
    #    above. Must load after all of them.
    # ------------------------------------------------------------
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'data/crm_team_data.xml',
        'data/crm_stage_data.xml',

        'wizard/lead_transfer_wizard_views.xml',

        'views/crm_lead_agent_views.xml',
        'views/crm_lead_closer_views.xml',
        'views/crm_lead_manager_views.xml',
        'views/crm_lead_inherit_views.xml',
        'views/dashboard_views.xml',

        'report/crm_lead_report_views.xml',

        'views/crm_menus.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}