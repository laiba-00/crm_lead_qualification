# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ManagerDashboard(http.Controller):

    @http.route('/crm_lead_qualification/dashboard_data',
                type='json', auth='user')
    def get_dashboard_data(self):
        """Returns all data needed for the Manager OWL dashboard:
        - KPI cards
        - Agent performance table
        - Pipeline stage chart data
        - Closing team performance
        """
        Lead = request.env['crm.lead']

        # --------------------------------------------------------
        # KPI CARDS
        # --------------------------------------------------------
        total_leads = Lead.search_count([
            ('is_transferred', '=', False)
        ])
        total_hot_leads = Lead.search_count([
            ('is_transferred', '=', True)
        ])
        total_won = Lead.search_count([
            ('outcome', '=', 'won')
        ])
        total_lost = Lead.search_count([
            ('outcome', '=', 'lost')
        ])
        conversion_rate = 0
        if total_hot_leads > 0:
            conversion_rate = round((total_won / total_hot_leads) * 100, 1)

        # --------------------------------------------------------
        # AGENT PERFORMANCE
        # --------------------------------------------------------
        agents = Lead.read_group(
            domain=[('qualification_agent_id', '!=', False)],
            fields=['qualification_agent_id', 'is_transferred', 'outcome'],
            groupby=['qualification_agent_id'],
        )

        agent_performance = []
        for agent in agents:
            agent_id = agent['qualification_agent_id'][0]
            agent_name = agent['qualification_agent_id'][1]

            assigned = Lead.search_count([
                ('qualification_agent_id', '=', agent_id),
                ('is_transferred', '=', False),
            ])
            hot_leads = Lead.search_count([
                ('qualification_agent_id', '=', agent_id),
                ('is_transferred', '=', True),
            ])
            won = Lead.search_count([
                ('qualification_agent_id', '=', agent_id),
                ('outcome', '=', 'won'),
            ])
            lost = Lead.search_count([
                ('qualification_agent_id', '=', agent_id),
                ('outcome', '=', 'lost'),
            ])
            agent_conv_rate = 0
            if hot_leads > 0:
                agent_conv_rate = round((won / hot_leads) * 100, 1)

            agent_performance.append({
                'name': agent_name,
                'assigned': assigned,
                'hot_leads': hot_leads,
                'won': won,
                'lost': lost,
                'conversion_rate': agent_conv_rate,
            })

        # --------------------------------------------------------
        # PIPELINE STAGE CHART
        # Only Qualification Team stages
        # --------------------------------------------------------
        qual_team = request.env.ref(
            'crm_lead_qualification.team_lead_qualification',
            raise_if_not_found=False
        )
        stages = request.env['crm.stage'].search([
            ('team_id', '=', qual_team.id if qual_team else False)
        ], order='sequence asc')

        pipeline_data = []
        for stage in stages:
            count = Lead.search_count([
                ('stage_id', '=', stage.id),
                ('is_transferred', '=', False),
            ])
            pipeline_data.append({
                'stage': stage.name,
                'count': count,
            })

        # --------------------------------------------------------
        # CLOSING TEAM PERFORMANCE
        # --------------------------------------------------------
        closers = Lead.read_group(
            domain=[('closer_id', '!=', False)],
            fields=['closer_id', 'outcome'],
            groupby=['closer_id'],
        )

        closer_performance = []
        for closer in closers:
            closer_id = closer['closer_id'][0]
            closer_name = closer['closer_id'][1]

            received = Lead.search_count([
                ('closer_id', '=', closer_id),
            ])
            won_c = Lead.search_count([
                ('closer_id', '=', closer_id),
                ('outcome', '=', 'won'),
            ])
            lost_c = Lead.search_count([
                ('closer_id', '=', closer_id),
                ('outcome', '=', 'lost'),
            ])
            pending = Lead.search_count([
                ('closer_id', '=', closer_id),
                ('outcome', '=', False),
            ])
            win_rate = 0
            if received > 0:
                win_rate = round((won_c / received) * 100, 1)

            closer_performance.append({
                'name': closer_name,
                'received': received,
                'won': won_c,
                'lost': lost_c,
                'pending': pending,
                'win_rate': win_rate,
            })

        return {
            'kpis': {
                'total_leads': total_leads,
                'total_hot_leads': total_hot_leads,
                'total_won': total_won,
                'total_lost': total_lost,
                'conversion_rate': conversion_rate,
            },
            'agent_performance': agent_performance,
            'pipeline_data': pipeline_data,
            'closer_performance': closer_performance,
        }