# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLeadTransferWizard(models.TransientModel):
    """Req #4: lets a Sales Agent choose which Closer (Department Head
    or Partner - i.e. any user in the Closer group, per Option A
    agreed earlier) a Hot Lead should be transferred to, then confirms
    the transfer via crm.lead's action_mark_hot_lead().
    """
    _name = 'crm.lead.transfer.wizard'
    _description = 'Hot Lead Transfer Wizard'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead',
        required=True,
        readonly=True,
    )

    # Req: "either me or my business partner" - Option A means this is
    # not hardcoded to 2 users. Domain restricts the selectable list to
    # whoever currently belongs to the Closer group, so the wizard
    # stays correct even if the client adds a third closer later.
    closer_id = fields.Many2one(
        'res.users',
        string='Closer',
        required=True,
        domain=lambda self: [
            ('groups_id', 'in', [
                self.env.ref(
                    'crm_lead_qualification.group_lead_qualification_closer'
                ).id
            ])
        ],
        help="Only users in the Closer group appear here. "
             "Add or remove closers via Settings > Users > "
             "Access Rights, not by editing this wizard.",
    )

    def action_confirm_transfer(self):
        """Calls the actual transfer logic on crm.lead. Kept as a thin
        wrapper - all business logic lives in
        crm.lead.action_mark_hot_lead(), not duplicated here, so there
        is exactly one place that performs a transfer.
        """
        self.ensure_one()

        if not self.lead_id:
            raise UserError(_("No lead found for this transfer."))

        self.lead_id.action_mark_hot_lead(closer_id=self.closer_id.id)

        return {'type': 'ir.actions.act_window_close'}
