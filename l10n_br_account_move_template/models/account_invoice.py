# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _map_move_template_domain(self, move_line, type):
        """
        Método para mapear qual é o roteiro correto para cada tipo de lançamento
        ou manter as contas originais caso não exista roteiro que se encaixe
        na operação
        :param move_line:
        :param type:
        :return:
        """
        values_dict = {'type': type}
        domain = ['&']
        if move_line[2].get('invl_id', False):
            line = self.env['account.invoice.line'].browse(
                move_line[2].get('invl_id', False))
            invoice =line.invoice_id

        values_dict.update(dict(
            company_id=invoice.company_id.id or False,
            fiscal_document_id=invoice.fiscal_document_id.id or False,
            fiscal_category=invoice.fiscal_category_id.id or False,
            # operation_type= False,
            operation_destination=line.product_id.cfop.id_dest or False,
            product_fiscal_type=line.product.template.type or False,
            product_origin=line.product_id.origin or False,
        ))

        for key, value in values_dict.iteritems():
            domain.append('|')
            domain.append((key, '=', value))
            domain.append((key, '=', False))

        return domain

    def define_account(self, move_line, type):
        """
        Definir contas das novas partidas de acordo com o roteiro contabil
        :param move_line:  - dict - partida duplicada para contra-partida
                                    na conta contabil
        :param type: sting - Tipo de partida ['CLIENTE', 'RECEITA', 'IMPOSTO']
        :return:
        """
        account_id = False
        amt = self.env['account.move.template']
        if type in ['client','receipt']:
            # definir parâmetros search
            domain = self._map_move_template_domain(move_line, type)
            amt = amt.search(domain)

            if move_line[2].debit:
                account_id = amt.debit_account_id
            else:
                account_id = amt.credit_account_id

        # elif type == 'tax':
        #     amt = amt.search([]) #definir parâmetros search
        #     account_id = amt.debit_account_id

        # Se definir uma conta no mapeamento, seta a conta,
        # senão fica com a conta padrão
        if account_id:
            move_line['account_id'] = account_id

    def finalize_invoice_move_lines(self, move_lines):
        """
        Sobrescrever hook do core para criar as contrapartidas de acordo com
        o tipo da partida e mapear as contas seguindo o roteiro contábil.
        :param move_lines: lista com [0,0, dict] - Move lines geradas pelo core
        :return: - lista com [0,0, dict] onde o dict são as partidas a serem 
                                         criadas para o lançamento contabil
                                         da invoice.
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        lines = list(move_lines)
        for move in lines:
            if move[2].get('product_id', False):
                type =  'receipt'
                move_lines.remove(move)

            elif move[2].get('tax_amount', False):
                type =  'tax'

            else:
                type = 'client'

            # Criar contra-partidas
            if type in ['tax', 'client']:
                partida = dict(move[2])
                partida['name'] = 'Contrapartida - ' + move[2]['name']
                move[2]['account_id'] = 30
                partida['debit'] = move[2]['credit']
                partida['credit'] = move[2]['debit']
                move_lines.append([0, 0, partida])
                self.define_account(move, type)

        return move_lines
