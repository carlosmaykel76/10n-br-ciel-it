# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)

TIPO_CALCULO_COMISSAO = [
    ('fatura', 'Fatura'),
    ('pagamento', 'Pagamento'),
]

COMISSAO_STATUS = [
    ('rascunho','Rascunho'),
    ('calculado','Calculado'),
    ('aprovado','Aprovado'),
    ('pago','Pago'),
]

class L10nBrComissaoRegras(models.Model):
    _name = "l10n_br_ciel_it_account.comissao.regras"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    salesrep_ids = fields.Many2many('res.users', 'comissao_salesrep_rel', string='Vendedores')
    team_ids = fields.Many2many('crm.team', string='Times de Vendas')
    manager_ids = fields.Many2many('res.users', 'comissao_manager_rel', string='Gerentes')
    partner_ids = fields.Many2many('res.partner', string='Parceiros')

    salesrep_is_set = fields.Boolean(string='Vendedor Set', store=True, compute_sudo=False, compute='_l10n_br_m2m_set' )
    team_is_set = fields.Boolean(string='Times de Vendas Set', store=True, compute_sudo=False, compute='_l10n_br_m2m_set' )
    manager_is_set = fields.Boolean(string='Gerente Set', store=True, compute_sudo=False, compute='_l10n_br_m2m_set' )
    partner_is_set = fields.Boolean(string='Parceiro Set', store=True, compute_sudo=False, compute='_l10n_br_m2m_set' )

    date_start = fields.Date( 'Data de Início', required=True )
    date_end = fields.Date( 'Data Final', required=True )

    comissao_manager = fields.Float( string='% Comissão Gerente', digits = (12,6) )
    comissao_salesrep = fields.Float( string='% Comissão Vendedor', digits = (12,6) )

    @api.depends('salesrep_ids','team_ids','manager_ids','partner_ids')
    def _l10n_br_m2m_set(self):
        for line in self:
            line.update({
                'salesrep_is_set': True if line.salesrep_ids else False,
                'team_is_set': True if line.team_ids else False,
                'manager_is_set': True if line.manager_ids else False,
                'partner_is_set': True if line.partner_ids else False,
            })

class L10nBrComissao(models.Model):
    _name = "l10n_br_ciel_it_account.comissao"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Cálculo',required=True, readonly=True, copy=False, default='/')

    state = fields.Selection( COMISSAO_STATUS, string='Situação', default='rascunho', copy=False )
    lines_ids = fields.One2many( comodel_name='l10n_br_ciel_it_account.comissao.line', string='Itens', inverse_name='comissao_id', copy=False, readonly=True, states={'rascunho': [('readonly', False)], 'calculado': [('readonly', False)]} )

    user_pago_id = fields.Many2one('res.users', string='Pago por', readonly=True)
    date_pago = fields.Datetime('Pago em', readonly=True)
    user_aprovado_id = fields.Many2one('res.users', string='Aprovado por', readonly=True)
    date_aprovado = fields.Datetime('Aprovado em', readonly=True)
    user_calculo_id = fields.Many2one('res.users', string='Calculado por', readonly=True)
    date_calculo = fields.Datetime('Calculado em', readonly=True)

    calcular_salesrep = fields.Boolean( string='Calcular Comissão Vendedor?', default=True, readonly=True, states={'rascunho': [('readonly', False)]} )
    calcular_manager = fields.Boolean( string='Calcular Comissão Gerente?', readonly=True, states={'rascunho': [('readonly', False)]} )
    date_start = fields.Date( 'Data de Início', readonly=True, states={'rascunho': [('readonly', False)]} )
    date_end = fields.Date( 'Data Final', readonly=True, states={'rascunho': [('readonly', False)]} )

    def pagar_comissao(self):

        self.ensure_one()

        if self.state != 'aprovado':
            raise UserError('Cálculo de comissão somente pode ser pago quando situação Aprovado.')

        to_write = {}
        to_write['state'] = 'pago'
        to_write['user_pago_id'] = self.env.user.id
        to_write['date_pago'] = fields.Datetime.now()
        self.write(to_write)

    def aprovar_comissao(self):

        self.ensure_one()

        if self.state != 'calculado':
            raise UserError('Cálculo de comissão somente pode ser aprovado quando situação Cálculado.')

        to_write = {}
        to_write['state'] = 'aprovado'
        to_write['user_aprovado_id'] = self.env.user.id
        to_write['date_aprovado'] = fields.Datetime.now()
        self.write(to_write)

    def _get_rule_order_extended(self):
        return 'salesrep_is_set desc, team_is_set desc, manager_is_set desc, partner_is_set desc'

    def _get_regra_domain_extended(self, regra_domain, move_id):
        return regra_domain

    def _get_comissao_create_extended(self, regra_domain, to_create, move_id):
        return to_create

    def calcular_comissao(self):
    
        self.ensure_one()

        if not self.state in ['rascunho','calculado']:
            raise UserError('Cálculo de comissão somente pode ser alterado quando situação Rascunho ou Calculado.')

        data_ini = self.date_start.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_end.strftime(DEFAULT_SERVER_DATE_FORMAT)
        payment_domain = [('payment_date','>=',data_ini),('payment_date','<=',data_fim),('state','!=','draft'),('state','!=','cancelled'),('partner_type','=','customer')]
        payment_ids = self.env['account.payment'].search(payment_domain)
        move_ids = payment_ids.mapped('invoice_ids')
        
        self.lines_ids.unlink()
        
        lines_ids = []
        for move_id in move_ids:
            for item in move_id._get_reconciled_info_JSON_values():
                if item['account_payment_id'] in payment_ids.ids:
                    to_create = {}
                    to_create['comissao_id'] = self.id
                    to_create['move_id'] = move_id.id
                    to_create['payment_id'] = item['account_payment_id']
                    to_create['data_base'] = item['date']
                    to_create['valor_base'] = item['amount']
                    
                    manager_comissao = 0.00
                    salesrep_comissao = 0.00

                    data_base = item['date'].strftime(DEFAULT_SERVER_DATE_FORMAT)
                    regra_domain = [('date_start','<=',data_base),('date_end','>=',data_base)]

                    domain_aux = expression.OR([
                        [('salesrep_ids','in',move_id.user_id.id)],
                        [('salesrep_ids','=',False)],
                    ])
                    regra_domain = expression.AND([regra_domain,domain_aux])

                    domain_aux = expression.OR([
                        [('team_ids','in',move_id.team_id.id)],
                        [('team_ids','=',False)],
                    ])
                    regra_domain = expression.AND([regra_domain,domain_aux])

                    domain_aux = expression.OR([
                        [('manager_ids','in',move_id.team_id.user_id.id)],
                        [('manager_ids','=',False)],
                    ])
                    regra_domain = expression.AND([regra_domain,domain_aux])

                    domain_aux = expression.OR([
                        [('partner_ids','in',move_id.partner_id.id)],
                        [('partner_ids','=',False)],
                    ])
                    regra_domain = expression.AND([regra_domain,domain_aux])
                    
                    regra_domain = self._get_regra_domain_extended(regra_domain, move_id)
                    
                    salesrep_domain = expression.AND([regra_domain,[('comissao_salesrep','>',0.00)]])
                    manager_domain = expression.AND([regra_domain,[('comissao_manager','>',0.00)]])

                    regra_salesrep_id = self.env['l10n_br_ciel_it_account.comissao.regras'].search(salesrep_domain, order=self._get_rule_order_extended(), limit=1)
                    if regra_salesrep_id:
                        salesrep_comissao = regra_salesrep_id.comissao_salesrep or 0.00
                    regra_manager_id = self.env['l10n_br_ciel_it_account.comissao.regras'].search(manager_domain, order=self._get_rule_order_extended(), limit=1)
                    if regra_manager_id:
                        manager_comissao = regra_manager_id.comissao_manager or 0.00

                    if self.calcular_manager:
                        to_create['manager_id'] = move_id.team_id.user_id.id
                        to_create['comissao_manager'] = manager_comissao
                        to_create['valor_comissao_manager'] = to_create['valor_base'] * manager_comissao / 100.00
                    if self.calcular_salesrep:
                        to_create['salesrep_id'] = move_id.user_id.id
                        to_create['comissao_salesrep'] = salesrep_comissao
                        to_create['valor_comissao_salesrep'] = to_create['valor_base'] * salesrep_comissao / 100.00
                    
                    to_create = self._get_comissao_create_extended(regra_domain, to_create, move_id)
                    
                    lines_ids.append((0,0,to_create))

        to_write = {}
        if self.name == '/':
            to_write['name'] = self.env.ref("l10n_br_ciel_it_account.sequence_comissao").next_by_id(sequence_date=fields.Date.context_today(self))
        to_write['user_calculo_id'] = self.env.user.id
        to_write['date_calculo'] = fields.Datetime.now()
        to_write['state'] = 'calculado'
        to_write['lines_ids'] = lines_ids
        self.write(to_write)

class L10nBrComissaoLines(models.Model):
    _name = "l10n_br_ciel_it_account.comissao.line"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    comissao_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.comissao', string='Comissão', ondelete="cascade" )

    manager_id = fields.Many2one('res.users', string='Gerente')
    salesrep_id = fields.Many2one('res.users', string='Vendedor')

    move_id = fields.Many2one('account.move', string='Fatura')
    partner_id = fields.Many2one(related='move_id.partner_id', string='Cliente', store=True)
    payment_id = fields.Many2one('account.payment', string="Pagamento")

    valor_base = fields.Float(string='Valor Base')
    data_base = fields.Date(string='Data Base')
    comissao_manager = fields.Float( string='% Comissão Gerente', digits = (12,6) )
    valor_comissao_manager = fields.Float(string='Comissão Gerente')
    comissao_salesrep = fields.Float( string='% Comissão Vendedor', digits = (12,6) )
    valor_comissao_salesrep = fields.Float(string='Comissão Vendedor')
