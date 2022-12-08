# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

import io
import base64
import xlsxwriter
import time
from datetime import date, datetime
from xlrd import open_workbook
import base64
from io import StringIO
import zipfile

class AccountFiscalReport(models.TransientModel):
    _name = 'l10n_br_ciel_it_account.fiscal.report'
    _description = 'Relatório Documentos Fiscais'

    date_ini = fields.Date( string="Data Saída/Entrada Inicial", required=True )
    date_fim = fields.Date( string="Data Saída/Entrada Final", required=True )
    export_pdf = fields.Boolean( string="Exportar PDF?", default=True )
    export_xml = fields.Boolean( string="Exportar XML?", default=True )
    export_excel = fields.Boolean( string="Exportar Excel?", default=True )
    send_email = fields.Boolean( string="Enviar por Email?", default=False )
    email_to = fields.Char( string="Enviar para" )

    def export_file(self):

        def _get_nextcol(current_col):
            current_col[0] = current_col[0] + 1
            return current_col[0]

        ## Função Auxiliar converter data python para data excel ##
        def _excel_date(date1):
        
            if not date1:
                return False

            temp = date(1899, 12, 30)
            delta = date1 - temp
            return float(delta.days) + (float(delta.seconds) / 86400)

        def _excel_datetime(date1):
            
            if not date1:
                return False

            temp = datetime(1899, 12, 30)
            delta = date1 - temp
            return float(delta.days) + (float(delta.seconds) / 86400)

        ## Aplica Filtro ##
        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)
        types_sel = ["out_invoice","in_refund","out_refund","in_invoice"]
        types_saida = ["out_invoice","in_refund"]
        types_entrada = ["out_refund","in_invoice"]
        move_ids = self.env['account.move'].search([('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('state','!=','draft')])

        ## Variaveis controle arquivo excel ##
        timestemp = int(time.time())
        file_name = str(self._uid)+"_"+str(timestemp)
        file_path = "/tmp/temp_"+file_name+".xlsx"

        ## cria arquivo excel na memoria ##
        workbook = xlsxwriter.Workbook(file_path)
        worksheet_documentos = workbook.add_worksheet("Documentos Fiscais")
        worksheet_resumo_cfop = workbook.add_worksheet("Resumo por CFOP")

        ## define header do arquivo excel ##
        cell_header_format = workbook.add_format({'bold': True})

        # array pra automação geração sequencia coluna
        col = [-1]

        # escreve celula do excel: linha, coluna, conteudo e formato
        
        # Documentos
        worksheet_documentos.write(0, _get_nextcol(col), "Fatura", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Diário", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Nome Empresa", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CNPJ Empresa", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "I.E. Empresa", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Número NF", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Série NF", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Tipo", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Status", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Situação", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Número Pedido", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Data Pedido", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Data Entrega Pedido", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Nome Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Razão Social Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CNPJ Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CPF Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "I.E. Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Cidade Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Estado Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "País Cliente/Fornecedor", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Data Emissão NF", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Data Saída/Entrada NF", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Valor NF", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Transportadora", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Valor Frete", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Total R$ ICMS ST", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Código Item", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Nome Item", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Quantidade", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Valor Unitário", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Valor Total Produto", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "Valor Frete Item", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ ICMS", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CST ICMS", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ ICMS ST", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ ICMS ST Ret.", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ ICMS ST Sub.", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ IPI", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CST IPI", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ IRPJ", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ ISSQN", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ PIS", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CST PIS", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ COFINS", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "CST COFINS", cell_header_format)
        worksheet_documentos.write(0, _get_nextcol(col), "R$ CSLL", cell_header_format)
        worksheet_documentos.freeze_panes(1, 0)

        # array pra automação geração sequencia coluna
        col = [-1]

        # Resumo por CFOP
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ ICMS", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ ICMS ST", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ ICMS ST Ret.", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ ICMS ST Sub.", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ IPI", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ IRPJ", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ ISSQN", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ PIS", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ COFINS", cell_header_format)
        worksheet_resumo_cfop.write(0, _get_nextcol(col), "R$ CSLL", cell_header_format)
        worksheet_resumo_cfop.freeze_panes(1, 1)

        ## define formatos para celulas do excel ##
        cell_text_format = workbook.add_format({})
        cell_date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        cell_integer_format = workbook.add_format({'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)'})
        cell_2decimal_format = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'})
        cell_4decimal_format = workbook.add_format({'num_format': '_(* #,##0.0000_);_(* (#,##0.0000);_(* "-"??_);_(@_)'})
        cell_6decimal_format = workbook.add_format({'num_format': '_(* #,##0.000000_);_(* (#,##0.000000);_(* "-"??_);_(@_)'})

        ## Variável para armazenar os XML/PDF
        attachment_ids = []

        ## looping pelos documentos para gerar arquivo excel ##
        row = 0
        for move_id in move_ids:

            # define sinal da nota fiscal
            if move_id.type in types_saida:
                sign = 1
            else:
                sign = -1

            ## Verificar se deve ser exportado PDF
            if self.export_pdf:
                if move_id.l10n_br_pdf_aut_nfe:
                    attachment_ids.append((0,0,{"name": move_id.l10n_br_pdf_aut_nfe_fname, "type": "binary", "datas": move_id.l10n_br_pdf_aut_nfe, "store_fname": move_id.l10n_br_pdf_aut_nfe_fname}))
                if move_id.l10n_br_pdf_cce_nfe:
                    attachment_ids.append((0,0,{"name": move_id.l10n_br_pdf_cce_nfe_fname, "type": "binary", "datas": move_id.l10n_br_pdf_cce_nfe, "store_fname": move_id.l10n_br_pdf_cce_nfe_fname}))
                if move_id.l10n_br_pdf_can_nfe:
                    attachment_ids.append((0,0,{"name": move_id.l10n_br_pdf_can_nfe_fname, "type": "binary", "datas": move_id.l10n_br_pdf_can_nfe, "store_fname": move_id.l10n_br_pdf_can_nfe_fname}))

            ## Verificar se deve ser exportado XML
            if self.export_xml:
                if move_id.l10n_br_xml_aut_nfe:
                    attachment_ids.append((0,0,{"name": move_id.l10n_br_xml_aut_nfe_fname, "type": "binary", "datas": move_id.l10n_br_xml_aut_nfe, "store_fname": move_id.l10n_br_xml_aut_nfe_fname}))
                if move_id.l10n_br_xml_cce_nfe:
                    attachment_ids.append((0,0,{"name": move_id.l10n_br_xml_cce_nfe_fname, "type": "binary", "datas": move_id.l10n_br_xml_cce_nfe, "store_fname": move_id.l10n_br_xml_cce_nfe_fname}))
                if move_id.l10n_br_xml_can_nfe:
                    attachment_ids.append((0,0,{"name": move_id.l10n_br_xml_can_nfe_fname, "type": "binary", "datas": move_id.l10n_br_xml_can_nfe, "store_fname": move_id.l10n_br_xml_can_nfe_fname}))

            if self.export_excel:
                for line_id in move_id.invoice_line_ids.filtered(lambda l: not l.display_type):

                    row += 1

                    # array pra automação geração sequencia coluna
                    col = [-1]

                    ## dados do header da nota fiscal ##
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.journal_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.company_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.company_id.l10n_br_cnpj or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.company_id.l10n_br_ie or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.l10n_br_numero_nf or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.l10n_br_serie_nf or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), _(dict(move_id._fields['type'].selection).get(move_id.type) or ""), cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), _(dict(move_id._fields['state'].selection).get(move_id.state) or ""), cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.l10n_br_situacao_nf or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), ",".join([so_line.order_id.name for so_line in line_id.sale_line_ids]) or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), ([_excel_datetime(so_line.order_id.create_date) for so_line in line_id.sale_line_ids]+[False])[0] or "", cell_date_format)
                    worksheet_documentos.write(row, _get_nextcol(col), ([_excel_datetime(so_line.order_id.commitment_date if so_line.order_id.commitment_date else so_line.order_id.expected_date) for so_line in line_id.sale_line_ids]+[False])[0] or "", cell_date_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_razao_social or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_cnpj or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_cpf or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_ie or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_municipio_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.state_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.partner_id.country_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), _excel_date(move_id.invoice_date) or "", cell_date_format)
                    worksheet_documentos.write(row, _get_nextcol(col), _excel_date(move_id.date) or "", cell_date_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (move_id.amount_total or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), move_id.l10n_br_carrier_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (move_id.l10n_br_frete or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (move_id.l10n_br_icmsst_valor or 0.00) * sign, cell_2decimal_format)

                    ## dados da linha da nota fiscal ##
                    worksheet_documentos.write(row, _get_nextcol(col), line_id.product_id.product_tmpl_id.default_code or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), line_id.product_id.name or "", cell_text_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.quantity or 0.00) * sign, cell_4decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.price_unit or 0.00) * sign, cell_6decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_prod_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), line_id.l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_frete or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_icms_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), line_id.l10n_br_icms_cst or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_icmsst_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_icmsst_retido_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_icmsst_substituto_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_ipi_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), line_id.l10n_br_ipi_cst or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_irpj_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_iss_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_pis_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), line_id.l10n_br_pis_cst or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_cofins_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_documentos.write(row, _get_nextcol(col), line_id.l10n_br_cofins_cst or "", cell_integer_format)
                    worksheet_documentos.write(row, _get_nextcol(col), (line_id.l10n_br_csll_valor or 0.00) * sign, cell_2decimal_format)

        if self.export_excel:
            ## looping pelos documentos para gerar arquivo excel ##
            row = 0
            
            # apenas nota fiscal não cancelada
            invoice_lines = move_ids.filtered(lambda l: l.state != 'cancel').mapped('invoice_line_ids').filtered(lambda l: not l.display_type)
            
            for sign in [-1,1]:
                for l10n_br_cfop_id in invoice_lines.filtered(lambda l: l.move_id.type in types_saida and sign == 1 or l.move_id.type in types_entrada and sign == -1).mapped('l10n_br_cfop_id').sorted(lambda i: (i.codigo_cfop)):

                    row += 1
                    
                    l10n_br_icms_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_valor'))
                    l10n_br_icmsst_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icmsst_valor'))
                    l10n_br_icmsst_retido_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icmsst_retido_valor'))
                    l10n_br_icmsst_substituto_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icmsst_substituto_valor'))
                    l10n_br_ipi_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_valor'))
                    l10n_br_irpj_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_irpj_valor'))
                    l10n_br_iss_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_iss_valor'))
                    l10n_br_pis_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_valor'))
                    l10n_br_cofins_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_valor'))
                    l10n_br_csll_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_csll_valor'))

                    # array pra automação geração sequencia coluna
                    col = [-1]

                    ## dados da linha da nota fiscal ##
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_icms_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_icmsst_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_icmsst_retido_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_icmsst_substituto_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_ipi_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_irpj_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_iss_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_pis_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_cofins_valor or 0.00) * sign, cell_2decimal_format)
                    worksheet_resumo_cfop.write(row, _get_nextcol(col), (l10n_br_csll_valor or 0.00) * sign, cell_2decimal_format)

            if row > 0:
                row += 1

                # array pra automação geração sequencia coluna
                col = [-1]

                ## dados da linha da nota fiscal ##
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "SUBTOTAL", cell_text_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
                worksheet_resumo_cfop.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)

        ## fecha arquivo excel e salva ##
        workbook.close()

        ## cria arquivo zip com conteudo
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for attach in attachment_ids:
                zip_file.writestr(attach[2]["store_fname"], base64.decodestring(attach[2]["datas"]))

            if self.export_excel:
                with open(file_path,'rb') as f:
                    xls_data = io.BytesIO(f.read())
                    zip_file.writestr("Relatório Documento Fiscal %s %s.xlsx" % (self.date_ini.strftime('%Y%m%d'),self.date_fim.strftime('%Y%m%d')), xls_data.getvalue())

        ## cria registro ir.attachment para download do arquivo ##
        values = dict(
            name="Documentos Fiscais.zip",
            res_model=self._name,
            res_id=self[0].id,
            datas=base64.encodestring(zip_buffer.getvalue()),
            type='binary',
        )
        attachment = self.env['ir.attachment'].create(values)

        ## Verifica se deve ser enviado por email
        if self.send_email:
            template_id = self.env.ref('l10n_br_ciel_it_account.email_template_xmlpdf')
            email_values = {
                'email_to': self.email_to,
                'attachment_ids': [(6,0,[attachment.id])]
            }
            template_id.send_mail(self.id, force_send=True, email_values=email_values)
        
        else:

            ## Retorna download do arquivo
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % (attachment.id),
                'target': 'self',
                'nodestroy': False,
            }

class AccountFiscalIcmsReport(models.TransientModel):
    _name = 'l10n_br_ciel_it_account.fiscal.icms.report'
    _description = 'Relatório Apuração ICMS'

    date_ini = fields.Date( string="Data Saída/Entrada Inicial", required=True )
    date_fim = fields.Date( string="Data Saída/Entrada Final", required=True )

    def export_file(self):

        def _get_nextcol(current_col):
            current_col[0] = current_col[0] + 1
            return current_col[0]

        ## Aplica Filtro ##
        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)

        types_sel = ["out_refund","in_invoice"]
        entrada_move_ids = self.env['account.move'].search([('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('state','!=','draft')])
        types_sel = ["out_invoice","in_refund"]
        saida_move_ids = self.env['account.move'].search([('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('state','!=','draft')])

        ## Variaveis controle arquivo excel ##
        timestemp = int(time.time())
        file_name = str(self._uid)+"_"+str(timestemp)
        file_path = "/tmp/temp_"+file_name+".xlsx"

        ## cria arquivo excel na memoria ##
        workbook = xlsxwriter.Workbook(file_path)
        worksheet_documentos_entrada = workbook.add_worksheet("Entrada")
        worksheet_documentos_saida = workbook.add_worksheet("Saida")

        ## define header do arquivo excel ##
        cell_header_format = workbook.add_format({'bold': True})

        # array pra automação geração sequencia coluna
        col = [-1]

        # escreve celula do excel: linha, coluna, conteudo e formato
        
        # Documentos Entrada
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Natureza Operação", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Valor Contabil", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Base ICMS", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "ICMS Creditado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "ICMS Isento/Não Tributado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "ICMS Outras", cell_header_format)

        worksheet_documentos_entrada.freeze_panes(1, 0)

        col = [-1]

        # Documentos Saida
        worksheet_documentos_saida.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Natureza Operação", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Valor Contabil", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Base ICMS", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "ICMS Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "ICMS Isento/Não Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "ICMS Outras", cell_header_format)

        worksheet_documentos_saida.freeze_panes(1, 0)

        # array pra automação geração sequencia coluna
        col = [-1]

        ## define formatos para celulas do excel ##
        cell_text_format = workbook.add_format({})
        cell_integer_format = workbook.add_format({'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)'})
        cell_2decimal_format = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'})

        ## looping pelos documentos para gerar arquivo excel ##
        row = 0
        
        move_ids = entrada_move_ids
        
        # apenas nota fiscal não cancelada
        invoice_lines = move_ids.mapped('invoice_line_ids').filtered(lambda l: not l.display_type)

        for l10n_br_cfop_id in invoice_lines.mapped('l10n_br_cfop_id').sorted(lambda i: (i.codigo_cfop)):

            row += 1

            l10n_br_total_nfe = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_total_nfe'))
            l10n_br_icms_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_base'))
            l10n_br_icms_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_valor'))
            l10n_br_icms_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_valor_isento'))
            l10n_br_icms_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_valor_outros'))

            # array pra automação geração sequencia coluna
            col = [-1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_entrada.write(row, _get_nextcol(col), l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), l10n_br_cfop_id.name or "", cell_text_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_total_nfe or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_icms_base or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_icms_valor or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_icms_valor_isento or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_icms_valor_outros or 0.00), cell_2decimal_format)

        if row > 0:
            row += 1

            # array pra automação geração sequencia coluna
            col = [1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)

        ## looping pelos documentos para gerar arquivo excel ##
        row = 0
        
        move_ids = saida_move_ids
        
        # apenas nota fiscal não cancelada
        invoice_lines = move_ids.mapped('invoice_line_ids').filtered(lambda l: not l.display_type)

        for l10n_br_cfop_id in invoice_lines.mapped('l10n_br_cfop_id').sorted(lambda i: (i.codigo_cfop)):

            row += 1

            l10n_br_total_nfe = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_total_nfe'))
            l10n_br_icms_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_base'))
            l10n_br_icms_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_valor'))
            l10n_br_icms_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_valor_isento'))
            l10n_br_icms_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_icms_valor_outros'))

            # array pra automação geração sequencia coluna
            col = [-1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_saida.write(row, _get_nextcol(col), l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), l10n_br_cfop_id.name or "", cell_text_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_total_nfe or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_icms_base or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_icms_valor or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_icms_valor_isento or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_icms_valor_outros or 0.00), cell_2decimal_format)

        if row > 0:
            row += 1

            # array pra automação geração sequencia coluna
            col = [1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)

        ## fecha arquivo excel e salva ##
        workbook.close()

        ## cria arquivo zip com conteudo
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            with open(file_path,'rb') as f:
                xls_data = io.BytesIO(f.read())
                zip_file.writestr("Relatório Apuração ICMS %s %s.xlsx" % (self.date_ini.strftime('%Y%m%d'),self.date_fim.strftime('%Y%m%d')), xls_data.getvalue())

        ## cria registro ir.attachment para download do arquivo ##
        values = dict(
            name="Relatório Apuração ICMS.zip",
            res_model=self._name,
            res_id=self[0].id,
            datas=base64.encodestring(zip_buffer.getvalue()),
            type='binary',
        )
        attachment = self.env['ir.attachment'].create(values)

        ## Retorna download do arquivo
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'self',
            'nodestroy': False,
        }

class AccountFiscalIpiReport(models.TransientModel):
    _name = 'l10n_br_ciel_it_account.fiscal.ipi.report'
    _description = 'Relatório Apuração IPI'

    date_ini = fields.Date( string="Data Saída/Entrada Inicial", required=True )
    date_fim = fields.Date( string="Data Saída/Entrada Final", required=True )

    def export_file(self):

        def _get_nextcol(current_col):
            current_col[0] = current_col[0] + 1
            return current_col[0]

        ## Aplica Filtro ##
        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)

        types_sel = ["out_refund","in_invoice"]
        entrada_move_ids = self.env['account.move'].search([('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('state','!=','draft')])
        types_sel = ["out_invoice","in_refund"]
        saida_move_ids = self.env['account.move'].search([('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('state','!=','draft')])

        ## Variaveis controle arquivo excel ##
        timestemp = int(time.time())
        file_name = str(self._uid)+"_"+str(timestemp)
        file_path = "/tmp/temp_"+file_name+".xlsx"

        ## cria arquivo excel na memoria ##
        workbook = xlsxwriter.Workbook(file_path)
        worksheet_documentos_entrada = workbook.add_worksheet("Entrada")
        worksheet_documentos_saida = workbook.add_worksheet("Saida")

        ## define header do arquivo excel ##
        cell_header_format = workbook.add_format({'bold': True})

        # array pra automação geração sequencia coluna
        col = [-1]

        # escreve celula do excel: linha, coluna, conteudo e formato
        
        # Documentos
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Natureza Operação", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Valor Contabil", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Base IPI", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "IPI Creditado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "IPI Isento/Não Tributado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "IPI Outras", cell_header_format)

        worksheet_documentos_entrada.freeze_panes(1, 0)

        col = [-1]

        # Documentos
        worksheet_documentos_saida.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Natureza Operação", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Valor Contabil", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Base IPI", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "IPI Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "IPI Isento/Não Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "IPI Outras", cell_header_format)

        worksheet_documentos_saida.freeze_panes(1, 0)

        # array pra automação geração sequencia coluna
        col = [-1]

        ## define formatos para celulas do excel ##
        cell_text_format = workbook.add_format({})
        cell_integer_format = workbook.add_format({'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)'})
        cell_2decimal_format = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'})

        ## looping pelos documentos para gerar arquivo excel ##
        row = 0
        
        move_ids = entrada_move_ids
        
        # apenas nota fiscal não cancelada
        invoice_lines = move_ids.mapped('invoice_line_ids').filtered(lambda l: not l.display_type)

        for l10n_br_cfop_id in invoice_lines.mapped('l10n_br_cfop_id').sorted(lambda i: (i.codigo_cfop)):

            row += 1

            l10n_br_total_nfe = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_total_nfe'))
            l10n_br_ipi_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_base'))
            l10n_br_ipi_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_valor'))
            l10n_br_ipi_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_valor_isento'))
            l10n_br_ipi_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_valor_outros'))

            # array pra automação geração sequencia coluna
            col = [-1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_entrada.write(row, _get_nextcol(col), l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), l10n_br_cfop_id.name or "", cell_text_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_total_nfe or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_ipi_base or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_ipi_valor or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_ipi_valor_isento or 0.00), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_ipi_valor_outros or 0.00), cell_2decimal_format)

        if row > 0:
            row += 1

            # array pra automação geração sequencia coluna
            col = [1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)

        ## looping pelos documentos para gerar arquivo excel ##
        row = 0
        
        move_ids = saida_move_ids
        
        # apenas nota fiscal não cancelada
        invoice_lines = move_ids.mapped('invoice_line_ids').filtered(lambda l: not l.display_type)

        for l10n_br_cfop_id in invoice_lines.mapped('l10n_br_cfop_id').sorted(lambda i: (i.codigo_cfop)):

            row += 1

            l10n_br_total_nfe = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_total_nfe'))
            l10n_br_ipi_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_base'))
            l10n_br_ipi_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_valor'))
            l10n_br_ipi_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_valor_isento'))
            l10n_br_ipi_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_ipi_valor_outros'))

            # array pra automação geração sequencia coluna
            col = [-1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_saida.write(row, _get_nextcol(col), l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), l10n_br_cfop_id.name or "", cell_text_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_total_nfe or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_ipi_base or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_ipi_valor or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_ipi_valor_isento or 0.00), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_ipi_valor_outros or 0.00), cell_2decimal_format)

        if row > 0:
            row += 1

            # array pra automação geração sequencia coluna
            col = [1]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)

        ## fecha arquivo excel e salva ##
        workbook.close()

        ## cria arquivo zip com conteudo
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            with open(file_path,'rb') as f:
                xls_data = io.BytesIO(f.read())
                zip_file.writestr("Relatório Apuração IPI %s %s.xlsx" % (self.date_ini.strftime('%Y%m%d'),self.date_fim.strftime('%Y%m%d')), xls_data.getvalue())

        ## cria registro ir.attachment para download do arquivo ##
        values = dict(
            name="Relatório Apuração IPI.zip",
            res_model=self._name,
            res_id=self[0].id,
            datas=base64.encodestring(zip_buffer.getvalue()),
            type='binary',
        )
        attachment = self.env['ir.attachment'].create(values)

        ## Retorna download do arquivo
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'self',
            'nodestroy': False,
        }

class AccountFiscalPisCofinsReport(models.TransientModel):
    _name = 'l10n_br_ciel_it_account.fiscal.piscofins.report'
    _description = 'Relatório Apuração PIS/COFINS'

    date_ini = fields.Date( string="Data Saída/Entrada Inicial", required=True )
    date_fim = fields.Date( string="Data Saída/Entrada Final", required=True )

    def export_file(self):

        def _get_nextcol(current_col):
            current_col[0] = current_col[0] + 1
            return current_col[0]

        ## Função Auxiliar converter data python para data excel ##
        def _excel_date(date1):
        
            if not date1:
                return False

            temp = date(1899, 12, 30)
            delta = date1 - temp
            return float(delta.days) + (float(delta.seconds) / 86400)

        ## Aplica Filtro ##
        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)

        types_sel = ["out_refund","in_invoice"]
        entrada_move_ids = self.env['account.move'].search([('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('state','!=','draft')])
        types_sel = ["out_invoice","in_refund"]
        saida_move_ids = self.env['account.move'].search([('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('state','!=','draft')])

        ## Variaveis controle arquivo excel ##
        timestemp = int(time.time())
        file_name = str(self._uid)+"_"+str(timestemp)
        file_path = "/tmp/temp_"+file_name+".xlsx"

        ## cria arquivo excel na memoria ##
        workbook = xlsxwriter.Workbook(file_path)
        worksheet_documentos_entrada = workbook.add_worksheet("Entrada")
        worksheet_documentos_saida = workbook.add_worksheet("Saida")

        ## define header do arquivo excel ##
        cell_header_format = workbook.add_format({'bold': True})

        # array pra automação geração sequencia coluna
        col = [-1]

        # escreve celula do excel: linha, coluna, conteudo e formato
        
        # Documentos
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Tipo Documento", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Número NF", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Série NF", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Data Emissão NF", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Data Saída/Entrada NF", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Razão Social Cliente/Fornecedor", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "CNPJ Cliente/Fornecedor", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "CPF Cliente/Fornecedor", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Natureza Operação", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Valor Contabil", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Base PIS", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "PIS Creditado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "PIS Isento/Não Tributado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "PIS Outras", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "Base COFINS", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "COFINS Creditado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "COFINS Isento/Não Tributado", cell_header_format)
        worksheet_documentos_entrada.write(0, _get_nextcol(col), "COFINS Outras", cell_header_format)

        worksheet_documentos_entrada.freeze_panes(1, 0)

        # array pra automação geração sequencia coluna
        col = [-1]

        # escreve celula do excel: linha, coluna, conteudo e formato
        
        # Documentos
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Tipo Documento", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Número NF", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Série NF", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Data Emissão NF", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Data Saída/Entrada NF", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Razão Social Cliente/Fornecedor", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "CNPJ Cliente/Fornecedor", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "CPF Cliente/Fornecedor", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "CFOP", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Natureza Operação", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Valor Contabil", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Base PIS", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "PIS Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "PIS Isento/Não Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "PIS Outras", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "Base COFINS", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "COFINS Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "COFINS Isento/Não Tributado", cell_header_format)
        worksheet_documentos_saida.write(0, _get_nextcol(col), "COFINS Outras", cell_header_format)

        worksheet_documentos_saida.freeze_panes(1, 0)

        # array pra automação geração sequencia coluna
        col = [-1]

        ## define formatos para celulas do excel ##
        cell_text_format = workbook.add_format({})
        cell_date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        cell_integer_format = workbook.add_format({'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)'})
        cell_2decimal_format = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'})

        ## looping pelos documentos para gerar arquivo excel ##
        row = 0
        
        move_ids = entrada_move_ids
        
        for move_id in move_ids.sorted(lambda i: (i.type,i.date)):

            # apenas nota fiscal não cancelada
            invoice_lines = move_id.filtered(lambda l: l.state != 'cancel').mapped('invoice_line_ids').filtered(lambda l: not l.display_type)

            for l10n_br_cfop_id in invoice_lines.mapped('l10n_br_cfop_id').sorted(lambda i: (i.codigo_cfop)):

                row += 1

                l10n_br_total_nfe = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_total_nfe'))
                l10n_br_pis_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_base'))
                l10n_br_pis_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_valor'))
                l10n_br_pis_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_valor_isento'))
                l10n_br_pis_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_valor_outros'))
                l10n_br_cofins_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_base'))
                l10n_br_cofins_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_valor'))
                l10n_br_cofins_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_valor_isento'))
                l10n_br_cofins_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_valor_outros'))

                # array pra automação geração sequencia coluna
                col = [-1]

                ## dados da linha da nota fiscal ##
                worksheet_documentos_entrada.write(row, _get_nextcol(col), move_id.l10n_br_tipo_documento or "", cell_text_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), move_id.l10n_br_numero_nf or "", cell_text_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), move_id.l10n_br_serie_nf or "", cell_text_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), _excel_date(move_id.invoice_date) or "", cell_date_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), _excel_date(move_id.date) or "", cell_date_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_razao_social or "", cell_text_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_cnpj or "", cell_text_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_cpf or "", cell_text_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), l10n_br_cfop_id.name or "", cell_text_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_total_nfe or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_pis_base or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_pis_valor or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_pis_valor_isento or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_pis_valor_outros or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_cofins_base or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_cofins_valor or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_cofins_valor_isento or 0.00), cell_2decimal_format)
                worksheet_documentos_entrada.write(row, _get_nextcol(col), (l10n_br_cofins_valor_outros or 0.00), cell_2decimal_format)

        if row > 0:
            row += 1

            # array pra automação geração sequencia coluna
            col = [9]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_entrada.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)

        ## looping pelos documentos para gerar arquivo excel ##
        row = 0
        
        move_ids = saida_move_ids
        
        for move_id in move_ids.sorted(lambda i: (i.type,i.date)):

            # apenas nota fiscal não cancelada
            invoice_lines = move_id.filtered(lambda l: l.state != 'cancel').mapped('invoice_line_ids').filtered(lambda l: not l.display_type)

            for l10n_br_cfop_id in invoice_lines.mapped('l10n_br_cfop_id').sorted(lambda i: (i.codigo_cfop)):

                row += 1

                l10n_br_total_nfe = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_total_nfe'))
                l10n_br_pis_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_base'))
                l10n_br_pis_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_valor'))
                l10n_br_pis_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_valor_isento'))
                l10n_br_pis_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_pis_valor_outros'))
                l10n_br_cofins_base = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_base'))
                l10n_br_cofins_valor = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_valor'))
                l10n_br_cofins_valor_isento = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_valor_isento'))
                l10n_br_cofins_valor_outros = sum(invoice_lines.filtered(lambda l: l.l10n_br_cfop_id.id == l10n_br_cfop_id.id ).mapped('l10n_br_cofins_valor_outros'))

                # array pra automação geração sequencia coluna
                col = [-1]

                ## dados da linha da nota fiscal ##
                worksheet_documentos_saida.write(row, _get_nextcol(col), move_id.l10n_br_tipo_documento or "", cell_text_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), move_id.l10n_br_numero_nf or "", cell_text_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), move_id.l10n_br_serie_nf or "", cell_text_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), _excel_date(move_id.invoice_date) or "", cell_date_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), _excel_date(move_id.date) or "", cell_date_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_razao_social or "", cell_text_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_cnpj or "", cell_text_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), move_id.partner_id.l10n_br_cpf or "", cell_text_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), l10n_br_cfop_id.codigo_cfop or "", cell_integer_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), l10n_br_cfop_id.name or "", cell_text_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_total_nfe or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_pis_base or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_pis_valor or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_pis_valor_isento or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_pis_valor_outros or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_cofins_base or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_cofins_valor or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_cofins_valor_isento or 0.00), cell_2decimal_format)
                worksheet_documentos_saida.write(row, _get_nextcol(col), (l10n_br_cofins_valor_outros or 0.00), cell_2decimal_format)

        if row > 0:
            row += 1

            # array pra automação geração sequencia coluna
            col = [9]

            ## dados da linha da nota fiscal ##
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)
            worksheet_documentos_saida.write(row, _get_nextcol(col), "=SUM(INDIRECT(ADDRESS(2,%d)):INDIRECT(ADDRESS(%d,%d)))" % (col[0]+1,row,col[0]+1), cell_2decimal_format)

        ## fecha arquivo excel e salva ##
        workbook.close()

        ## cria arquivo zip com conteudo
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            with open(file_path,'rb') as f:
                xls_data = io.BytesIO(f.read())
                zip_file.writestr("Relatório Apuração PIS COFINS %s %s.xlsx" % (self.date_ini.strftime('%Y%m%d'),self.date_fim.strftime('%Y%m%d')), xls_data.getvalue())

        ## cria registro ir.attachment para download do arquivo ##
        values = dict(
            name="Relatório Apuração PIS COFINS.zip",
            res_model=self._name,
            res_id=self[0].id,
            datas=base64.encodestring(zip_buffer.getvalue()),
            type='binary',
        )
        attachment = self.env['ir.attachment'].create(values)

        ## Retorna download do arquivo
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'self',
            'nodestroy': False,
        }

