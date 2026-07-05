# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    """Extends crm.lead to support the two-stage
    Lead Qualification -> Closing workflow.
    """
    _inherit = 'crm.lead'

    # ------------------------------------------------------------
    # FIELDS
    # ------------------------------------------------------------

    # Req #2: manual assignment. Set once when a manager assigns the
    # cold lead to an agent. Deliberately NEVER overwritten by the
    # transfer action below, so it remains the permanent record of
    # "who generated this lead" for reporting (req #7, #9c).
    qualification_agent_id = fields.Many2one(
        'res.users',
        string='Qualification Agent',
        tracking=True,
        help="The Sales Agent responsible for qualifying this lead. "
             "This value is set on assignment and is not changed when "
             "the lead is later transferred to the Closing Team.",
    )

    # Req #4: set only when the wizard confirms a transfer.
    closer_id = fields.Many2one(
        'res.users',
        string='Closer',
        tracking=True,
        help="The Closing Team member (Department Head or Partner) "
             "this Hot Lead has been transferred to.",
    )

    # Req #4/#5: drives the record rules that hide the lead from the
    # agent's editable pipeline and expose it read-only instead.
    is_transferred = fields.Boolean(
        string='Transferred to Closing Team',
        default=False,
        tracking=True,
        copy=False,
    )

    # Req #5: shown on the agent's read-only "My Qualified Leads" dashboard.
    date_transferred = fields.Datetime(
        string='Date Transferred',
        copy=False,
    )

    # Req #5/#6: the Closer's own working status, separate from stage_id
    # so the sales pipeline stages (req #8) are not reused for this.
    closing_status = fields.Selection(
        selection=[
            ('waiting_contact', 'Waiting for Contact'),
            ('meeting_scheduled', 'Meeting Scheduled'),
            ('negotiating', 'Negotiating'),
            ('customer_setup', 'Customer Setup in Progress'),
            ('won', 'Won (Customer Approved)'),
            ('lost', 'Lost'),
            ('not_interested', 'Not Interested'),
            ('follow_up_later', 'Follow Up Later'),
        ],
        string='Closing Status',
        tracking=True,
        copy=False,
    )

    # Req #6: closer's notes on progress.
    closing_notes = fields.Text(
        string='Closing Notes',
        copy=False,
    )

    # Req #5: final outcome, shown on agent's read-only dashboard.
    outcome = fields.Selection(
        selection=[
            ('won', 'Won'),
            ('lost', 'Lost'),
            ('not_interested', 'Not Interested'),
            ('follow_up_later', 'Follow Up Later'),
        ],
        string='Outcome',
        tracking=True,
        copy=False,
    )

    def _validate_team_agent_combination(self, vals, existing=None):
        """If team is Lead Qualification Team, qualification_agent_id
        must be a Sales Agent group member.
        If team is Closing Team, qualification_agent_id must be a
        Closer group member.
        """
        team_id = vals.get('team_id') or (existing and existing.team_id.id)
        agent_id = vals.get('qualification_agent_id') or (
            existing and existing.qualification_agent_id.id)

        if not team_id or not agent_id:
            return

        qual_team = self.env.ref(
            'crm_lead_qualification.team_lead_qualification',
            raise_if_not_found=False)
        closing_team = self.env.ref(
            'crm_lead_qualification.team_closing',
            raise_if_not_found=False)
        agent_group = self.env.ref(
            'crm_lead_qualification.group_lead_qualification_agent',
            raise_if_not_found=False)
        closer_group = self.env.ref(
            'crm_lead_qualification.group_lead_qualification_closer',
            raise_if_not_found=False)

        agent = self.env['res.users'].browse(agent_id)

        if qual_team and team_id == qual_team.id:
            if agent_group and agent_group not in agent.groups_id:
                raise UserError(_(
                    '"%s" is not a Sales Agent. '
                    'When Sales Team is "Lead Qualification Team", '
                    'Sales Agent must be a member of the Sales Agent group.'
                ) % agent.name)

        if closing_team and team_id == closing_team.id:
            if closer_group and closer_group not in agent.groups_id:
                raise UserError(_(
                    '"%s" is not a Closer. '
                    'When Sales Team is "Closing Team", '
                    'Sales Agent must be a member of the Closer group.'
                ) % agent.name)

    # ------------------------------------------------------------
    # ORM OVERRIDES
    # ------------------------------------------------------------

    def create(self, vals_list):
        """Auto-move to Assigned stage when a lead is created with
        qualification_agent_id already set (manager creates and
        assigns in one step).
        """
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        for vals in vals_list:
            self._validate_team_agent_combination(vals)
        assigned_stage = self.env.ref(
            'crm_lead_qualification.stage_assigned',
            raise_if_not_found=False
        )
        new_lead_stage = self.env.ref(
            'crm_lead_qualification.stage_new_lead',
            raise_if_not_found=False
        )
        closing_team = self.env.ref(
            'crm_lead_qualification.team_closing',
            raise_if_not_found=False
        )
        for vals in vals_list:
            if vals.get('qualification_agent_id'):
                if not vals.get('user_id'):
                    vals['user_id'] = vals['qualification_agent_id']
                if assigned_stage:
                    current_stage_id = vals.get('stage_id')
                    if not current_stage_id or (
                        new_lead_stage and current_stage_id == new_lead_stage.id
                    ):
                        vals['stage_id'] = assigned_stage.id
            # Auto-set is_transferred if team is Closing Team
            if closing_team and vals.get('team_id') == closing_team.id:
                vals['is_transferred'] = True
                if not vals.get('date_transferred'):
                    vals['date_transferred'] = fields.Datetime.now()
                if not vals.get('closing_status'):
                    vals['closing_status'] = 'waiting_contact'
                transferred_stage = self.env.ref(
                    'crm_lead_qualification.stage_transferred',
                    raise_if_not_found=False
                )
                if transferred_stage and not vals.get('stage_id'):
                    vals['stage_id'] = transferred_stage.id
        return super().create(vals_list)

    def write(self, vals):
        # Skip validation during transfer operation
        if not vals.get('is_transferred'):
            if 'team_id' in vals or 'qualification_agent_id' in vals:
                for rec in self:
                    self._validate_team_agent_combination(vals, existing=rec)

        # Auto-set is_transferred=True when team is changed to Closing Team
        if 'team_id' in vals:
            closing_team = self.env.ref(
                'crm_lead_qualification.team_closing',
                raise_if_not_found=False
            )
            if closing_team and vals['team_id'] == closing_team.id:
                vals['is_transferred'] = True
                if not vals.get('date_transferred'):
                    vals['date_transferred'] = fields.Datetime.now()
                if not vals.get('closing_status'):
                    vals['closing_status'] = 'waiting_contact'
                # Move to Transferred stage
                transferred_stage = self.env.ref(
                    'crm_lead_qualification.stage_transferred',
                    raise_if_not_found=False
                )
                if transferred_stage and not vals.get('stage_id'):
                    vals['stage_id'] = transferred_stage.id
        if vals.get('qualification_agent_id') and not vals.get('user_id'):
            vals['user_id'] = vals['qualification_agent_id']
            # Auto-move to Assigned stage when manager assigns an agent
            # only if lead is still on New Lead stage (don't override
            # if manager is reassigning mid-pipeline)
            assigned_stage = self.env.ref(
                'crm_lead_qualification.stage_assigned', raise_if_not_found=False
            )
            if assigned_stage:
                for rec in self:
                    new_lead_stage = self.env.ref(
                        'crm_lead_qualification.stage_new_lead',
                        raise_if_not_found=False
                    )
                    if rec.stage_id == new_lead_stage:
                        vals['stage_id'] = assigned_stage.id
        if vals.get('closer_id') and not vals.get('user_id'):
            vals['user_id'] = vals['closer_id']
        return super().write(vals)

    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------

    def action_assign_to_agent(self, agent_id):
        """Req #2: manager manually assigns a cold lead to a Sales Agent.
        Sets qualification_agent_id (permanent record for reporting)
        AND syncs user_id (stock Salesperson field), for the same
        reason as in action_mark_hot_lead: keeps Odoo's native
        My Pipeline / activity defaults working correctly for the
        agent, and keeps user_id aligned with what our record rules
        actually check.
        """
        self.ensure_one()

        agent = self.env['res.users'].browse(agent_id)
        if not agent.exists():
            raise UserError(_("Please select a valid Sales Agent."))

        # user_id sync now happens automatically in write() override
        self.write({
            'qualification_agent_id': agent.id,
        })

        return True

    def action_open_transfer_wizard(self):
        """Req #4: entry point button on the agent's lead form/kanban.
        Opens the transfer wizard so the agent can pick a closer
        (Department Head or Partner) from the Closer group.
        """
        self.ensure_one()

        if self.is_transferred:
            raise UserError(_(
                "This lead has already been transferred to the Closing Team."
            ))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfer Hot Lead'),
            'res_model': 'crm.lead.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            },
        }

    def action_mark_hot_lead(self, closer_id):
        """Req #4 and #9b: performs the actual Hot Lead transfer.
        Called by the transfer wizard on confirm, not by an
        automated action, so the logic stays visible and testable.

        - Sets closer_id, is_transferred, date_transferred.
        - Leaves qualification_agent_id untouched (req #2/#5).
        - Removing the lead from the agent's active pipeline is not a
          separate step: it is a direct consequence of is_transferred
          switching the record rule that applies to this record
          (see security.xml Rule A vs Rule B).
        """
        self.ensure_one()

        if self.is_transferred:
            raise UserError(_(
                "This lead has already been transferred to the Closing Team."
            ))

        closer = self.env['res.users'].browse(closer_id)
        if not closer.exists():
            raise UserError(_("Please select a valid Closer."))

        # user_id sync now happens automatically in write() override
        self.sudo().write({
            'closer_id': closer.id,
            'is_transferred': True,
            'date_transferred': fields.Datetime.now(),
            'closing_status': 'waiting_contact',
            'team_id': self.env.ref('crm_lead_qualification.team_closing').id,
            'stage_id': self.env.ref('crm_lead_qualification.stage_transferred').id,
        })

        self.message_post(
            body=_('This lead was qualified and transferred to %s by %s.') % (
                closer.name,
                self.qualification_agent_id.name or self.env.user.name,
            ),
            subtype_xmlid='mail.mt_note',
        )

        return True

    def action_close_as_won(self):
        """Req #6: closer converts the opportunity into an active
        customer. Sets stage_id and outcome together in one write, so
        the two can never end up out of sync (e.g. stage says Active
        Customer but outcome is still blank).
        """
        self.ensure_one()

        if not self.is_transferred:
            raise UserError(_(
                "Only transferred Hot Leads can be closed by the Closing Team."
            ))

        self.sudo().write({
            'stage_id': self.env.ref('crm_lead_qualification.stage_active_customer').id,
            'outcome': 'won',
            'closing_status': 'won',
        })
        return True

    def action_close_as_lost(self):
        """Req #6: closer marks the deal as lost. Same atomic-write
        reasoning as action_close_as_won().
        """
        self.ensure_one()

        if not self.is_transferred:
            raise UserError(_(
                "Only transferred Hot Leads can be closed by the Closing Team."
            ))

        self.sudo().write({
            'stage_id': self.env.ref('crm_lead_qualification.stage_lost').id,
            'outcome': 'lost',
            'closing_status': 'lost',
        })
        return True