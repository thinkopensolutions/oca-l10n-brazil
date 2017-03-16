# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import time
import datetime


class TestFinancialMove(TransactionCase):

    def setUp(self):
        super(TestFinancialMove, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_euro = self.env.ref('base.EUR')

        self.financial_move = self.env['financial.move']
        self.financial_move_create = self.env['financial.move.create']
        self.financial_move_line_create = \
            self.env['financial.move.line.create']
        self.financial_pay_receive = self.env['financial.pay_receive']
        self.financial_edit = self.env['financial.edit']
        self.partner_agrolait = self.env.ref("base.res_partner_2")
        self.partner_axelor = self.env.ref("base.res_partner_2")

        self.cr_1 = self.financial_move.create(dict(
            due_date='2017-02-27',
            company_id=self.main_company.id,
            currency_id=self.currency_euro.id,
            amount_document=100.00,
            partner_id=self.partner_agrolait.id,
            document_date=time.strftime('%Y') + '-01-01',
            document_number='1111',
            move_type='r',
        ))

    # """US1 # Como um operador de cobrança, eu gostaria de cadastrar uma conta
    #  a receber/pagar para manter controle sobre o fluxo de caixa.
    # """
    def test_us_1_ac_1(self):
        """ DADO a data de vencimento de 27/02/2017
        QUANDO criado um lançamento de contas a receber
        ENTÃO a data de vencimento útil deve ser de 01/03/2017"""

        self.assertEqual(self.cr_1.business_due_date, '2017-03-01')

    def test_us_1_ac_2(self):
        """DADO uma conta a pagar ou receber
        QUANDO o valor for igual a zero
        ENTÃO apresentar uma mensagem solicitando preenchimento de valor
            maior que zero
        E impedir lançamento"""
        with self.assertRaises(ValidationError):
            self.financial_move.create(dict(
                due_date='2017-02-27',
                company_id=self.main_company.id,
                currency_id=self.currency_euro.id,
                amount_document=0.00,
                partner_id=self.partner_agrolait.id,
                document_date=time.strftime('%Y') + '-01-02',
                document_number='2222',
                move_type='r',
            ))
            self.financial_move.create(dict(
                due_date='2017-02-27',
                company_id=self.main_company.id,
                currency_id=self.currency_euro.id,
                amount_document=-10.00,
                partner_id=self.partner_agrolait.id,
                document_date=time.strftime('%Y') + '-01-03',
                document_number='3333',
                move_type='r',
            ))

    def test_us1_ac_3(self):
        """ DADO a criação de uma nova parcela
        QUANDO confirmada
        ENTÃO esta parcela deve ter um número sequencial único chamado
         de código da parcela"""

        cr_1 = self.cr_1
        ctx = cr_1._context.copy()
        ctx['active_id'] = cr_1.id
        ctx['active_ids'] = [cr_1.id]
        ctx['active_model'] = cr_1._module

        cr_1.action_confirm()

        cr_2 = self.financial_move.create(dict(
            due_date='2017-02-27',
            company_id=self.main_company.id,
            currency_id=self.currency_euro.id,
            amount_document=100.00,
            partner_id=self.partner_agrolait.id,
            document_date=time.strftime('%Y') + '-01-01',
            document_number='2222',
            move_type='r',
        ))

        cty = cr_2._context.copy()
        cty['active_id'] = cr_2.id
        cty['active_ids'] = [cr_2.id]
        cty['active_model'] = cr_2._module

        cr_2.action_confirm()

        self.assertNotEqual(cr_1.display_name, cr_2.display_name)

    # def test_us1_ac_4(self):
    #     """ DADO a criação de uma nova parcela
    #     QUANDO confirmada
    #     ENTÃO os seus campos não poderão mais ser alterados pela
    #     interface de cadastro
    #     :return:
    #     """
    #     TODO: implementar teste quando for possivel pelo framework

    # """ Como um operador de cobrança, eu gostaria de alterar o vencimento ou
    # valor de uma conta a receber/pagar para auditar as alterações do fluxo
    # de caixa."""

    def test_us2_ac_1(self):
        """ DADO a alteração de uma parcela via assistente
        QUANDO solicitada a alteração do vencimento
        OU valor
        ENTÃO deve ser registrado o histórico no
            histórico da alteração o motivo
        E a alteração dos campos

        :return:
        """
        cr_1 = self.cr_1
        ctx = cr_1._context.copy()
        ctx['active_id'] = cr_1.id
        ctx['active_ids'] = [cr_1.id]
        ctx['active_model'] = 'financial.move'
        cr_1.action_confirm()

        fr = self.financial_edit.with_context(ctx)
        vals = self.financial_edit.with_context(ctx).\
            default_get([u'due_date',
                         u'amount_document',
                         u'currency_id',
                         u'change_reason'])
        vals['change_reason'] = 'qualquer coisa'
        message_number_before = len(self.env['financial.move'].browse(cr_1.id).
                                    message_ids.ids)

        edit = fr.create(vals)
        edit.write(dict(
            due_date=time.strftime('%Y') + '-01-10',
            currency_id=self.currency_euro.id,
            amount_document=50.00,
            change_reason='qualquer coisa',
        ))
        edit.doit()
        message_number_after = len(self.env['financial.move'].browse(cr_1.id)
                                   .message_ids.ids)
        self.assertEqual(50.00, cr_1.amount_document)
        self.assertEqual(message_number_before + 1, message_number_after)

    # """Como um operador de cobrança, eu preciso registrar um pagamento para
    # atualizar o fluxo de caixa e os saldos dos clientes, fornecedores, contas
    # bancárias. """

    def test_us_3_cr_3(self):
        """DADO que existe uma parcela de 100 reais em aberto
        QUANDO for recebido/pago 50 reais
        ENTÃO o valor do balanço da parcela deve ser 50 reais
        E o status da parcela deve permanecer em aberto."""
        cr_1 = self.cr_1
        ctx = cr_1._context.copy()
        ctx['active_id'] = cr_1.id
        ctx['active_ids'] = [cr_1.id]
        ctx['active_model'] = cr_1._module

        cr_1.action_confirm()
        fr = self.financial_pay_receive.with_context(ctx)
        pay = fr.create(
            dict(
                ammount_paid=50.00,
                payment_date=time.strftime('%Y') + '-01-10',
                move_type='rr',
                currency_id=self.currency_euro.id,
            )
        )
        pay.doit()

        self.assertEqual(50.00, cr_1.balance)
        self.assertEqual('open', cr_1.state)

    def test_us_3_cr_4(self):
        """DADO que existe uma parcela de 100 reais em aberto
        QUANDO for recebido/pago 100 reais
        ENTÃO o valor do balanço da parcela deve ser 0
        E o status da parcela deve mudar para pago."""
        cr_1 = self.cr_1
        ctx = cr_1._context.copy()
        ctx['active_id'] = cr_1.id
        ctx['active_ids'] = [cr_1.id]
        ctx['active_model'] = cr_1._module

        cr_1.action_confirm()
        fr = self.financial_pay_receive.with_context(ctx)
        pay = fr.create(
            dict(
                ammount_paid=100.00,
                payment_date=time.strftime('%Y') + '-01-10',
                move_type='rr',
                currency_id=self.currency_euro.id,
            )
        )
        pay.doit()

        self.assertEqual(0.00, cr_1.balance)
        self.assertEqual('paid', cr_1.state)

    def test_us_3_cr_5(self):
        """DADO que existe uma parcela de 100 reais em aberto
        QUANDO for recebido/pago 150 reais
        ENTÃO o valor do balanço da parcela deve ser 0
        E o status da parcela deve mudar para pago
        E o parceiro deve ficar com um crédito de 50 reais"""
        cr_1 = self.cr_1
        ctx = cr_1._context.copy()

        ctx['active_id'] = self.cr_1.id
        ctx['active_ids'] = [self.cr_1.id]
        ctx['active_model'] = self.cr_1._module
        cr_1.action_confirm()
        fr = self.financial_pay_receive.with_context(ctx)
        pay = fr.create(
            dict(
                ammount_paid=150.00,
                payment_date=time.strftime('%Y') + '-01-10',
                move_type='rr',
                currency_id=self.currency_euro.id,
            )
        )
        pay.doit()

        self.assertEqual(-50.00, cr_1.balance)
        self.assertEqual('paid', cr_1.state)

    # """
    # Como um operador de cobrança, eu gostaria de criar multiplas contas a
    # receber/pagar de forma automatica dependendo do termo de pagamento.
    # """

    def test_usX_ac_Y(self):
        """
        DADO o lancamento de uma parcela via assistente
        QUANDO especificado algum termo de pagamento
        ENTÃO devem ser registradas uma ou mais parcelas em funcao do termo de
            pagamento

        :return:
        """
        date_today_iso = datetime.date.today().isoformat()
        amount = 1000.00
        doc_number = '2222'

        fm = self.financial_move_create
        cr_1 = fm.create(
            dict(
                company_id=self.main_company.id,
                currency_id=self.currency_euro.id,
                move_type='r',
                partner_id=self.partner_agrolait.id,
                document_number=doc_number,
                document_date=date_today_iso,
                payment_mode=self.payment_mode_1.id,
                payment_term=self.payment_term_30_70.id,
                amount_document=amount,
            )
        )
        ctx = cr_1._context.copy()
        ctx['active_id'] = cr_1.id
        ctx['active_ids'] = [cr_1.id]
        ctx['active_model'] = cr_1._module

        items_before = self.financial_move.search([])
        count_before = len(items_before)

        cr_1.onchange_fields()
        cr_1.compute()

        items_after = self.financial_move.search([])
        count_after = len(items_after)

        sorted_items = list(items_after)
        sorted_items.sort(key=lambda x: x.id)
        fm_1 = sorted_items[-2]
        fm_2 = sorted_items[-1]
        computations = \
            self.payment_term_30_70.compute(amount, date_today_iso)
        expected_1 = computations[0][0]
        expected_2 = computations[0][1]

        # Count verification
        self.assertTrue(count_before < count_after)

        # Ids verification
        self.assertEqual(fm_1.document_item, doc_number + '/1')
        self.assertEqual(fm_2.document_item, doc_number + '/2')

        # Dates verification
        self.assertEqual(fm_1.due_date, date_today_iso)
        self.assertEqual(fm_2.due_date, expected_2[0])

        # Amounts verification
        self.assertEqual(fm_1.amount_document, expected_1[1])
        self.assertEqual(fm_2.amount_document, expected_2[1])