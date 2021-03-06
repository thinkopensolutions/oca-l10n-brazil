# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import (
    SpedCalculoImpostoItem
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class StockMove(SpedCalculoImpostoItem, models.Model):
    _inherit = 'stock.move'
    _abstract = False

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='picking_id.is_brazilian',
    )
    #
    # O campo documento_id serve para que a classe SpedCalculoImpostoItem
    # saiba qual o cabeçalho do documento (venda, compra, NF etc.)
    # tem as definições da empresa, participante, data de emissão etc.
    # necessárias aos cálculos dos impostos;
    # Uma vez definido o documento, a operação pode variar entre produto e
    # serviço, por isso o compute no campo; a data de emissão também vem
    # trazida do campo correspondente no model que estamos tratando no momento
    #
    documento_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Transferência de Estoque',
        related='picking_id',
        readonly=True,
    )
    data_emissao = fields.Datetime(
        string='Data de emissão',
        related='documento_id.date',
        readonly=True,
    )
    documento_item_ids = fields.One2many(
        comodel_name='sped.documento.item',
        inverse_name='stock_move_id',
        string='Itens dos Documentos Fiscais',
        copy=False,
    )

    data = fields.Date(
        string='Data',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )

    sped_documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
        ondelete='restrict',
    )
    sped_documento_item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string='Item do Documento Fiscal',
        ondelete='restrict',
    )

    especie = fields.Char(
        string='Espécie/embalagem',
        size=60,
        related='produto_id.especie',
    )
    fator_quantidade_especie = fields.Float(
        string='Quantidade por espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
        related='produto_id.fator_quantidade_especie',
    )
    quantidade_especie = fields.Float(
        string='Quantidade em espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
        compute='_compute_quantidade_especie',
        store=False,
    )
    descricao_especie = fields.Char(
        string='Apresentação/embalagem',
        size=60,
        compute='_compute_descricao_especie',
        store=False,
    )

    @api.depends('date')
    def _compute_data_hora_separadas(self):
        for move in self:
            data, hora = self._separa_data_hora(move.date)
            move.data = data
            #move.hora = hora

    def _onchange_produto_id_emissao_propria(self):
        self.ensure_one()

        if not (self.picking_id and self.picking_id.operacao_id):
            return

        return super(StockMove, self)._onchange_produto_id_emissao_propria()

    def prepara_dados_documento_item(self):
        self.ensure_one()

        return {
            'stock_move_id': self.id,
            'vr_unitario': self.price_unit,
        }

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)

        if 'produto_id' in dados:
            produto = self.env['sped.produto'].browse(dados['produto_id'])
            dados['product_id'] = produto.product_id.id

        if 'product_id' in dados and not 'produto_id' in dados:
            product = self.env['product.product'].browse(dados['product_id'])
            if product.sped_produto_id:
                dados['produto_id'] = product.sped_produto_id.id

        return super(StockMove, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)

        if 'produto_id' in dados:
            produto = self.env['sped.produto'].browse(dados['produto_id'])
            dados['product_id'] = produto.product_id.id

        if 'product_id' in dados and not 'produto_id' in dados:
            product = self.env['product.product'].browse(dados['product_id'])
            if product.sped_produto_id:
                dados['produto_id'] = product.sped_produto_id.id

        return super(StockMove, self).write(dados)

    def product_price_update_after_done(self):
        pass

    def product_price_update_before_done(self):
        pass

    def _prepare_account_move_line(self, qty, cost, credit_account_id,
                                   debit_account_id):
        return []

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        self.ensure_one()
        res = super(StockMove, self)._onchange_produto_id()

        if hasattr(self, 'product_id'):
            self.product_id = self.produto_id.product_id.id
        if hasattr(self, 'product_uom'):
            self.product_uom = self.produto_id.unidade_id.uom_id
        if hasattr(self, 'uom_id'):
            self.uom_id = self.produto_id.unidade_id.uom_id

        self.fator_quantidade_especie = \
            self.produto_id.fator_quantidade_especie

        return res

    @api.depends('produto_id', 'quantidade', 'fator_quantidade_especie',
                 'especie')
    def _compute_quantidade_especie(self):
        for item in self:
            if item.fator_quantidade_especie > 0 and item.especie:
                quantidade_especie = D(item.quantidade) / \
                    D(item.fator_quantidade_especie)
                quantidade_especie = quantidade_especie.quantize(D('0.0001'))

            else:
                quantidade_especie = 0

            item.quantidade_especie = quantidade_especie
