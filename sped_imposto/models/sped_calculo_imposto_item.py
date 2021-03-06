# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kme.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedCalculoImpostoItem(SpedBase):
    _abstract = False

    @api.one
    def _amount_price_brazil(self):
        # if not self.data_emissao:
        #     self.data_emissao = self.order_id._get_date()
        self.calcula_impostos()

    # documento_id = fields.Many2one(
    #     comodel_name='sped.calculo.imposto',
    #     string='Documento',
    # )
    documento_id = fields.Reference(
        string='Documento',
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        related='documento_id.operacao_id',
        readonly=True,
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        related='operacao_id.regime_tributario',
        readonly=True,
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL,
        string='Modelo',
        related='operacao_id.modelo',
        readonly=True,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='documento_id.empresa_id',
        readonly=True,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente',
        related='documento_id.participante_id',
        readonly=True,
    )
    contribuinte = fields.Selection(
        selection=IE_DESTINATARIO,
        string='Contribuinte',
        related='participante_id.contribuinte',
        readonly=True,
    )
    emissao = fields.Selection(
        selection=TIPO_EMISSAO,
        string='Tipo de emissão',
        related='operacao_id.emissao',
        readonly=True,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        related='documento_id.data_emissao',
        readonly=True,
        default=fields.Date.today,
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string='Entrada/saída',
        related='operacao_id.entrada_saida',
        readonly=True,
    )
    consumidor_final = fields.Selection(
        selection=TIPO_CONSUMIDOR_FINAL,
        string='Tipo do consumidor',
        related='operacao_id.consumidor_final',
        readonly=True,
    )
    cfop_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP',
        ondelete='restrict',
        index=True,
    )
    cfop_posicao = fields.Selection(
        selection=POSICAO_CFOP,
        string='Posição da CFOP',
        related='cfop_id.posicao',
        readonly=True,
    )
    cfop_eh_venda = fields.Boolean(
        string='CFOP é venda?',
        related='cfop_id.eh_venda',
        readonly=True,
    )
    cfop_eh_devolucao_compra = fields.Boolean(
        string='CFOP é devolução de compra?',
        related='cfop_id.eh_devolucao_compra',
        readonly=True,
    )
    cfop_eh_retorno_saida = fields.Boolean(
        string='CFOP é retorno saída?',
        related='cfop_id.eh_retorno_saida',
        readonly=True,
    )
    compoe_total = fields.Boolean(
        string='Compõe o valor total da NF-e?',
        index=True,
        default=True,
    )
    movimentacao_fisica = fields.Boolean(
        string='Há movimentação física do produto?',
        default=True,
    )

    # Dados do produto/serviço
    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto/Serviço',
        ondelete='restrict',
        index=True,
    )
    ncm_id = fields.Many2one(
        comodel_name='sped.ncm',
        string='NCM',
        related='produto_id.ncm_id',
        readonly=True,
    )
    cest_id = fields.Many2one(
        comodel_name='sped.cest',
        string='CEST',
        related='produto_id.cest_id',
        readonly=True,
    )
    protocolo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string='Protocolo ICMS',
        ondelete='restrict',
    )
    operacao_item_id = fields.Many2one(
        comodel_name='sped.operacao.item',
        string='Item da operação fiscal',
        ondelete='restrict',
    )
    # quantidade = fields.Float(
    # string='Quantidade',
    # default=1,
    #digits=dp.get_precision('SPED - Quantidade'),
    #)
    unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade',
        ondelete='restrict',
    )
    currency_unidade_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unidade',
        related='unidade_id.currency_id',
        readonly=True,
    )
    quantidade = fields.Monetary(
        string='Quantidade',
        default=1,
        currency_field='currency_unidade_id',
    )
    vr_unitario = fields.Monetary(
        string='Valor unitário',
        currency_field='currency_unitario_id',
    )
    # Quantidade de tributação
    fator_conversao_unidade_tributacao = fields.Float(
        string='Fator de conversão entre as unidades',
        default=1,
        digits=dp.get_precision('SPED - Quantidade'),
    )
    quantidade_tributacao = fields.Float(
        string='Quantidade para tributação',
        digits=(18, 4),
    )
    unidade_tributacao_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade para tributação',
        ondelete='restrict',
    )
    currency_unidade_tributacao_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unidade para tributação',
        related='unidade_tributacao_id.currency_id',
        readonly=True,
    )
    vr_unitario_tributacao = fields.Float(
        string='Valor unitário para tributação',
        digits=(18, 10),
    )
    exibe_tributacao = fields.Boolean(
        string='Exibe tributação à parte?',
    )

    # Valor total dos produtos
    vr_produtos = fields.Monetary(
        string='Valor do produto/serviço',
    )
    vr_produtos_tributacao = fields.Monetary(
        string='Valor do produto/serviço para tributação',
    )

    # Outros valores acessórios
    vr_frete = fields.Monetary(
        string='Valor do frete',
    )
    vr_seguro = fields.Monetary(
        string='Valor do seguro',
    )
    #al_desconto = fields.Monetary(
        #string='Percentual de desconto',
        #currency_field='currency_aliquota_rateio_id',
        #compute='_compute_al_desconto',
        #inverse='_inverse_al_desconto',
        #store=True,
    #)
    vr_desconto = fields.Monetary(
        string='Valor do desconto',
    )
    vr_outras = fields.Monetary(
        string='Outras despesas acessórias',
    )
    vr_operacao = fields.Monetary(
        string='Valor da operação',
    )
    vr_operacao_tributacao = fields.Monetary(
        string='Valor da operação para tributação',
    )

    #
    # ICMS próprio
    #
    org_icms = fields.Selection(
        selection=ORIGEM_MERCADORIA,
        string='Origem da mercadoria',
        index=True,
        default=ORIGEM_MERCADORIA_NACIONAL,
    )
    cst_icms = fields.Selection(
        selection=ST_ICMS,
        string='CST ICMS',
        index=True,
    )
    partilha = fields.Boolean(
        string='Partilha de ICMS entre estados (CST 10 ou 90)?',
    )
    al_bc_icms_proprio_partilha = fields.Monetary(
        string='% da base de cálculo da operação própria',
        currency_field='currency_aliquota_id',
    )
    estado_partilha_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado para o qual é devido o ICMS ST',
        index=True,
    )
    repasse = fields.Boolean(
        string='Repasse de ICMS retido anteriormente entre estados (CST 41)?',
        index=True,
    )
    md_icms_proprio = fields.Selection(
        selection=MODALIDADE_BASE_ICMS_PROPRIO,
        string='Modalidade da base de cálculo do ICMS próprio',
        default=MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO,
    )
    pr_icms_proprio = fields.Float(
        string='Parâmetro do ICMS próprio',
        digits=(18, 4),
    )
    rd_icms_proprio = fields.Monetary(
        string='% de redução da base de cálculo do ICMS próprio',
        currency_field='currency_aliquota_id',
    )
    bc_icms_proprio_com_ipi = fields.Boolean(
        string='IPI integra a base do ICMS próprio?',
    )
    bc_icms_proprio = fields.Monetary(
        string='Base do ICMS próprio',
    )
    al_icms_proprio = fields.Monetary(
        string='alíquota do ICMS próprio',
        currency_field='currency_aliquota_id',
    )
    al_efetiva_icms_proprio = fields.Monetary(
        string='Alíquota efetiva do ICMS próprio',
        currency_field='currency_aliquota_id',
        readonly=True,
        help='Percentual do ICMS próprio c/ a redução aplicada, \n'
             'de forma a representar o valor do icms sobre a base de cálculo\n'
             '- Campo útilizado para emissão do CF-E'
    )
    vr_icms_proprio = fields.Monetary(
        string='valor do ICMS próprio',
    )
    motivo_icms_desonerado = fields.Selection(
        selection=MOTIVO_DESONERACAO_ICMS,
        string='Motivo da desoneração do ICMS',
    )
    vr_icms_desonerado = fields.Monetary(
        string='valor do ICMS desonerado',
    )

    #
    # Parâmetros relativos ao ICMS Simples Nacional
    #
    cst_icms_sn = fields.Selection(
        selection=ST_ICMS_SN,
        string='CST ICMS - SIMPLES',
        index=True,
    )
    al_icms_sn = fields.Monetary(
        string='Alíquota do crédito de ICMS',
        currency_field='currency_aliquota_id',
    )
    rd_icms_sn = fields.Monetary(
        string='% estadual de redução da alíquota de ICMS',
        currency_field='currency_aliquota_id',
    )
    vr_icms_sn = fields.Monetary(
        string='valor do crédito de ICMS - SIMPLES',
    )
    al_simples = fields.Monetary(
        string='Alíquota do SIMPLES',
        currency_field='currency_aliquota_id',
    )
    vr_simples = fields.Monetary(
        string='Valor do SIMPLES',
    )

    #
    # ICMS ST
    #
    md_icms_st = fields.Selection(
        selection=MODALIDADE_BASE_ICMS_ST,
        string='Modalidade da base de cálculo do ICMS ST',
        default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO,
    )
    pr_icms_st = fields.Float(
        string='Parâmetro do ICMS ST',
        digits=(18, 4),
    )
    rd_icms_st = fields.Monetary(
        string='% de redução da base de cálculo do ICMS ST',
        currency_field='currency_aliquota_id',
    )
    bc_icms_st_com_ipi = fields.Boolean(
        string='IPI integra a base do ICMS ST?',
    )
    bc_icms_st = fields.Monetary(
        string='Base do ICMS ST',
    )
    al_icms_st = fields.Monetary(
        string='Alíquota do ICMS ST',
        currency_field='currency_aliquota_id',
    )
    vr_icms_st = fields.Monetary(
        string='Valor do ICMS ST',
    )

    #
    # Parâmetros relativos ao ICMS retido anteriormente por substituição
    # tributária na origem
    #
    md_icms_st_retido = fields.Selection(
        selection=MODALIDADE_BASE_ICMS_ST,
        string='Modalidade da base de cálculo',
        default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO,
    )
    pr_icms_st_retido = fields.Float(
        string='Parâmetro da base de cáculo',
        digits=(18, 4),
    )
    rd_icms_st_retido = fields.Monetary(
        string='% de redução da base de cálculo do ICMS retido',
        currency_field='currency_aliquota_id',
    )
    bc_icms_st_retido = fields.Monetary(
        string='Base do ICMS ST retido na origem',
    )
    al_icms_st_retido = fields.Monetary(
        string='Alíquota do ICMS ST retido na origem',
        currency_field='currency_aliquota_id',
    )
    vr_icms_st_retido = fields.Monetary(
        string='Valor do ICMS ST retido na origem',
    )

    #
    # IPI padrão
    #
    apuracao_ipi = fields.Selection(
        selection=APURACAO_IPI,
        string='Período de apuração do IPI',
        index=True,
        default=APURACAO_IPI_MENSAL,
    )
    cst_ipi = fields.Selection(
        selection=ST_IPI,
        string='CST IPI',
        index=True,
    )
    cst_ipi_entrada = fields.Selection(
        selection=ST_IPI_ENTRADA,
        string='CST IPI',
    )
    cst_ipi_saida = fields.Selection(
        selection=ST_IPI_SAIDA,
        string='CST IPI',
    )
    md_ipi = fields.Selection(
        selection=MODALIDADE_BASE_IPI,
        string='Modalidade BC do IPI',
        default=MODALIDADE_BASE_IPI_ALIQUOTA,
    )
    bc_ipi = fields.Monetary(
        string='Base do IPI',
    )
    al_ipi = fields.Monetary(
        string='Alíquota do IPI',
        digits=(18, 2),
        currency_field='currency_aliquota_id',
    )
    vr_ipi = fields.Monetary(
        string='Valor do IPI',
    )
    enquadramento_ipi = fields.Char(
        string='Enquadramento legal do IPI',
        size=3
    )

    #
    # Imposto de importação
    #
    bc_ii = fields.Monetary(
        string='Base do imposto de importação',
    )
    vr_despesas_aduaneiras = fields.Monetary(
        string='Despesas aduaneiras',
    )
    vr_ii = fields.Monetary(
        string='Valor do imposto de importação',
    )
    vr_iof = fields.Monetary(
        string='Valor do IOF',
    )
    numero_fci = fields.Char(
        string='Nº controle FCI',
        size=36,
    )

    #
    # PIS próprio
    #
    al_pis_cofins_id = fields.Many2one(
        comodel_name='sped.aliquota.pis.cofins',
        string='Alíquota e CST do PIS-COFINS',
        index=True,
    )
    codigo_natureza_receita_pis_cofins = fields.Char(
        string='Natureza da receita',
        size=3,
        index=True,
    )
    cst_pis = fields.Selection(
        selection=ST_PIS,
        string='CST PIS',
        index=True,
    )
    cst_pis_entrada = fields.Selection(
        selection=ST_PIS_ENTRADA,
        string='CST PIS',
    )
    cst_pis_saida = fields.Selection(
        selection=ST_PIS_SAIDA,
        string='CST PIS',
    )
    md_pis_proprio = fields.Selection(
        selection=MODALIDADE_BASE_PIS,
        string='Modalidade BC do PIS próprio',
        default=MODALIDADE_BASE_PIS_ALIQUOTA,
    )
    bc_pis_proprio = fields.Monetary(
        string='Base do PIS próprio',
    )
    al_pis_proprio = fields.Monetary(
        string='Alíquota do PIS próprio',
        digits=(18, 2),
        currency_field='currency_aliquota_id',
    )
    vr_pis_proprio = fields.Monetary(
        string='Valor do PIS próprio',
    )

    #
    # COFINS própria
    #
    cst_cofins = fields.Selection(
        selection=ST_COFINS,
        string='CST COFINS',
        index=True,
    )
    cst_cofins_entrada = fields.Selection(
        selection=ST_COFINS_ENTRADA,
        string='CST COFINS',
    )
    cst_cofins_saida = fields.Selection(
        selection=ST_COFINS_SAIDA,
        string='CST COFINS',
    )
    md_cofins_proprio = fields.Selection(
        selection=MODALIDADE_BASE_COFINS,
        string='Modalidade BC da COFINS própria',
        default=MODALIDADE_BASE_COFINS_ALIQUOTA,
    )
    bc_cofins_proprio = fields.Monetary(
        string='Base do COFINS próprio',
    )
    al_cofins_proprio = fields.Monetary(
        string='Alíquota da COFINS própria',
        digits=(18, 2),
        currency_field='currency_aliquota_id',
    )
    vr_cofins_proprio = fields.Monetary(
        string='Valor do COFINS próprio',
    )

    #
    # Grupo ISS
    #

    # ISS
    # cst_iss = fields.Selection(ST_ISS, 'CST ISS', index=True)
    bc_iss = fields.Monetary(
        string='Base do ISS',
    )
    al_iss = fields.Monetary(
        string='Alíquota do ISS',
        currency_field='currency_aliquota_id',
    )
    vr_iss = fields.Monetary(
        string='Valor do ISS',
    )

    #
    # Total da NF e da fatura (podem ser diferentes no caso de operação
    # triangular)
    #
    vr_nf = fields.Monetary(
        string='Valor da NF',
    )
    vr_fatura = fields.Monetary(
        string='Valor da fatura',
    )

    al_ibpt = fields.Monetary(
        string='Alíquota IBPT',
        currency_field='currency_aliquota_id'
    )
    vr_ibpt = fields.Monetary(
        string='Valor IBPT',
    )

    # Previdência social
    inss_retido = fields.Boolean(
        string='INSS retido?',
        index=True,
    )
    bc_inss_retido = fields.Monetary(
        string='Base do INSS',
    )
    al_inss_retido = fields.Monetary(
        string='Alíquota do INSS',
        currency_field='currency_aliquota_id',
    )
    vr_inss_retido = fields.Monetary(
        string='Valor do INSS',
    )

    mensagens_complementares = fields.Text(
        string='Mensagens complementares',
    )

    # Informações adicionais
    infcomplementar = fields.Text(
        string='Informações complementares',
    )

    #
    # Dados especiais para troca de informações entre empresas
    #
    numero_pedido = fields.Char(
        string='Número do pedido',
        size=15,
    )
    numero_item_pedido = fields.Integer(
        string='Número do item pedido',
    )

    #
    # Campos para a validação das entradas
    #
    produto_codigo = fields.Char(
        string='Código do produto original',
        size=60,
        index=True,
    )
    produto_nome = fields.Char(
        string='Nome do produto original',
        size=120,
        oldname='produto_descricao'
    )
    produto_ncm = fields.Char(
        string='NCM do produto original',
        size=8,
    )
    produto_ncm_ex = fields.Char(
        string='NCM EX do produto original',
        size=2,
    )
    produto_cest = fields.Char(
        string='CEST do produto original',
        size=7,
    )
    produto_codigo_barras = fields.Char(
        string='Código de barras do produto original',
        size=14,
        index=True,
    )
    produto_codigo_barras_tributacao = fields.Char(
        string='Código de barras de tributação do produto original',
        size=14,
    )
    produto_unidade = fields.Char(
        string='Unidade do produto original',
        size=6,
    )
    produto_unidade_tributacao = fields.Char(
        string='Unidade de tributação do produto original',
        size=6,
    )
    fator_quantidade = fields.Float(
        string='Fator de conversão da quantidade',
    )
    #quantidade_original = fields.Float(
        #string='Quantidade',
        #digits=(18, 4),
    #)
    #vr_unitario_original = fields.Float(
        #string='Valor unitário original',
        #digits=(18, 10),
    #)
    cfop_original_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP original',
        index=True,
    )

    credita_icms_proprio = fields.Boolean(
        string='Credita ICMS próprio?',
        index=True,
    )
    credita_icms_st = fields.Boolean(
        string='Credita ICMS ST?',
        index=True,
    )
    informa_icms_st = fields.Boolean(
        string='Informa ICMS ST?',
        index=True,
    )
    credita_ipi = fields.Boolean(
        string='Credita IPI?',
        index=True,
    )
    credita_pis_cofins = fields.Boolean(
        string='Credita PIS-COFINS?',
        index=True,
    )

    #
    # Campos para rateio de custo
    #
    # vr_frete_rateio = fields.function(
    #     _get_calcula_custo,
    #     type='float',
    #     string='Valor do frete',
    #     store=STORE_CUSTO,
    #     digits=(18, 2),
    # )
    # vr_seguro_rateio = fields.function(
    #     _get_calcula_custo,
    #     type='float',
    #     string='Valor do seguro',
    #     store=STORE_CUSTO,
    #     digits=(18, 2),
    # )
    # vr_outras_rateio = fields.function(
    #     _get_calcula_custo,
    #     type='float',
    #     string='Outras despesas acessórias',
    #     store=STORE_CUSTO,
    #     digits=(18, 2)
    # )
    # vr_desconto_rateio = fields.function(
    #     _get_calcula_custo,
    #     type='float',
    #     string='Valor do desconto',
    #     store=STORE_CUSTO,
    #     digits=(18, 2),
    # )
    vr_unitario_custo_comercial = fields.Float(
        string='Custo unitário comercial',
        compute='_compute_custo_comercial',
        store=True,
        digits=dp.get_precision('SPED - Valor Unitário'),
    )
    vr_custo_comercial = fields.Monetary(
        string='Custo comercial',
        compute='_compute_custo_comercial',
        store=True,
    )

    #
    # Diferencial de alíquota
    #
    calcula_difal = fields.Boolean(
        string='Calcula diferencial de alíquota?',
    )
    al_interna_destino = fields.Monetary(
        string='Alíquota interna do estado destino',
        currency_field='currency_aliquota_id',
    )
    al_difal = fields.Monetary(
        string='Alíquota diferencial ICMS próprio',
        currency_field='currency_aliquota_id',
    )
    vr_difal = fields.Monetary(
        string='Valor do diferencial de alíquota ICMS próprio',
    )
    al_partilha_estado_destino = fields.Monetary(
        string='Alíquota de partilha para o estado destino',
        currency_field='currency_aliquota_id',
    )
    vr_icms_estado_origem = fields.Monetary(
        string='Valor do ICMS para o estado origem',
    )
    vr_icms_estado_destino = fields.Monetary(
        string='Valor do ICMS para o estado origem',
    )

    #
    # Fundo de combate à pobreza
    #
    al_fcp = fields.Monetary(
        string='Alíquota do fundo de combate à pobreza',
        currency_field='currency_aliquota_id',
    )
    vr_fcp = fields.Monetary(
        string='Valor do fundo de combate à pobreza',
    )

    #
    # Automatização do preenchimento dos volumes
    #
    peso_bruto_unitario = fields.Monetary(
        string='Peso bruto unitário',
        currency_field='currency_peso_id',
    )
    peso_liquido_unitario = fields.Monetary(
        string='Peso líquido unitário',
        currency_field='currency_peso_id',
    )
    peso_bruto = fields.Monetary(
        string='Peso bruto',
        currency_field='currency_peso_id',
    )
    peso_liquido = fields.Monetary(
        string='Peso líquido',
        currency_field='currency_peso_id',
    )
    especie = fields.Char(
        string='Espécie/embalagem',
        size=60,
    )
    marca = fields.Char(
        string='Marca',
        size=60
    )
    fator_quantidade_especie = fields.Float(
        string='Quantidade por espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
    )
    quantidade_especie = fields.Float(
        string='Quantidade em espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
    )
    descricao_especie = fields.Char(
        string='Apresentação/embalagem',
        size=60,
        compute='_compute_descricao_especie',
        store=True,
    )
    #
    # Campos readonly
    #
    vr_unitario_readonly = fields.Monetary(
        string='Valor unitário',
        currency_field='currency_unitario_id',
        compute='_compute_readonly',
    )
    unidade_readonly_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade',
        ondelete='restrict',
        compute='_compute_readonly',
    )
    unidade_tributacao_readonly_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade para tributação',
        ondelete='restrict',
        compute='_compute_readonly',
    )
    vr_produtos_readonly = fields.Monetary(
        string='Valor do produto/serviço',
        compute='_compute_readonly',
    )
    vr_produtos_tributacao_readonly = fields.Monetary(
        string='Valor do produto/serviço para tributação',
        compute='_compute_readonly',
    )
    vr_operacao_readonly = fields.Monetary(
        string='Valor da operação',
        compute='_compute_readonly',
    )
    vr_operacao_tributacao_readonly = fields.Monetary(
        string='Valor da operação para tributação',
        compute='_compute_readonly',
    )
    vr_nf_readonly = fields.Monetary(
        string='Valor da NF',
        compute='_compute_readonly',
    )
    vr_fatura_readonly = fields.Monetary(
        string='Valor da fatura',
        compute='_compute_readonly',
    )
    vr_unitario_custo_comercial_readonly = fields.Float(
        string='Custo unitário comercial',
        compute='_compute_readonly',
        digits=dp.get_precision('SPED - Valor Unitário'),
    )
    vr_custo_comercial_readonly = fields.Monetary(
        string='Custo comercial',
        compute='_compute_readonly',
    )
    peso_bruto_readonly = fields.Monetary(
        string='Peso bruto',
        currency_field='currency_peso_id',
        compute='_compute_readonly',
    )
    peso_liquido_readonly = fields.Monetary(
        string='Peso líquido',
        currency_field='currency_peso_id',
        compute='_compute_readonly',
    )
    especie_readonly = fields.Char(
        string='Espécie/embalagem',
        size=60,
        compute='_compute_readonly',
    )
    marca_readonly = fields.Char(
        string='Marca',
        size=60,
        compute='_compute_readonly',
    )
    fator_quantidade_especie_readonly = fields.Float(
        string='Quantidade por espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
        compute='_compute_readonly',
    )
    quantidade_especie_readonly = fields.Float(
        string='Quantidade por espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
        compute='_compute_readonly',
    )
    permite_alteracao = fields.Boolean(
        string='Permite alteração?',
        compute='_compute_permite_alteracao',
    )

    tipo_item = fields.Selection(
        string='Produto ou serviço',
        selection=[
            ('P', 'Produto'),
            ('S', 'Serviço'),
            ('M', 'Mensalidade'),
        ],
        default='P',
        help='Indica o tipo do item',
    )

    #@api.depends('vr_desconto')
    #def _compute_al_desconto(self):
        #for item in self:
            #al_desconto = D(0)
            #if item.vr_produtos and item.vr_desconto:
                #al_desconto = D(item.vr_desconto) / D(item.vr_produtos)
                #al_desconto *= 100
            #item.al_desconto = al_desconto

    #def _inverse_al_desconto(self):
        #for item in self:
            #al_desconto = D(item.al_desconto) / 100
            #vr_desconto = D(item.vr_produtos) * al_desconto
            #vr_desconto = vr_desconto.quantize(D('0.01'))
            #item.vr_desconto = vr_desconto

    #
    # Funções para manter a sincronia entre as CSTs do PIS e COFINS para
    # entrada ou saída
    #
    @api.onchange('cst_ipi_entrada')
    def _onchange_cst_ipi_entrada(self):
        self.ensure_one()
        return {'value': {
            'cst_ipi': self.cst_ipi_entrada,
        }}

    @api.onchange('cst_ipi_saida')
    def _onchange_cst_ipi_saida(self):
        self.ensure_one()
        return {'value': {
            'cst_ipi': self.cst_ipi_saida,
        }}

    @api.onchange('cst_pis_entrada')
    def _onchange_cst_pis_entrada(self):
        self.ensure_one()
        return {'value': {
            'cst_pis': self.cst_pis_entrada,
            'cst_cofins_entrada': self.cst_pis_entrada,
        }}

    @api.onchange('cst_pis_saida')
    def _onchange_cst_pis_saida(self):
        self.ensure_one()
        return {'value': {
            'cst_pis': self.cst_pis_saida,
            'cst_cofins_saida': self.cst_pis_saida
        }}

    @api.onchange('cst_cofins_entrada')
    def _onchange_cst_cofins_entrada(self):
        self.ensure_one()
        return {'value': {
            'cst_cofins': self.cst_cofins_entrada,
            'cst_pis_entrada': self.cst_cofins_entrada
        }}

    @api.onchange('cst_cofins_saida')
    def _onchange_cst_cofins_saida(self):
        self.ensure_one()
        return {'value': {
            'cst_cofins': self.cst_cofins_saida,
            'cst_pis_saida': self.cst_cofins_saida
        }}

    #
    # Busca configurações, CSTs e alíquotas
    #
    def _estado_origem_estado_destino_destinatario(self):
        self.ensure_one()

        #
        # Determinamos as UFs de origem e destino
        #
        if self.modelo in MODELO_FISCAL_CONSUMIDOR_FINAL:
            #
            # Para documentos de venda a consumidor, a venda é sempre dentro
            # do estado
            #
            estado_origem = self.empresa_id.estado
            estado_destino = self.empresa_id.estado
            destinatario = self.participante_id

        else:
            if self.entrada_saida == ENTRADA_SAIDA_SAIDA:
                estado_origem = self.empresa_id.estado
                estado_destino = self.participante_id.estado

                if self.emissao == TIPO_EMISSAO_PROPRIA:
                    destinatario = self.participante_id
                else:
                    destinatario = self.empresa_id

            else:
                estado_origem = self.participante_id.estado
                estado_destino = self.empresa_id.estado

                if self.emissao == TIPO_EMISSAO_PROPRIA:
                    destinatario = self.empresa_id
                else:
                    destinatario = self.participante_id

        return (estado_origem, estado_destino, destinatario)

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        self.ensure_one()

        if self.emissao == TIPO_EMISSAO_PROPRIA:
            res = self._onchange_produto_id_emissao_propria()

            if hasattr(self, 'product_id'):
                self.product_id = self.produto_id.product_id.id
            if hasattr(self, 'product_uom'):
                self.product_uom = self.produto_id.unidade_id.uom_id
            if hasattr(self, 'uom_id'):
                self.uom_id = self.produto_id.unidade_id.uom_id
            return res
        elif self.emissao == TIPO_EMISSAO_TERCEIROS:
            if self.env.context.get('manual'):
                res = self._onchange_produto_id_emissao_propria()
            else:
                res = self._onchange_produto_id_recebimento()
            if hasattr(self, 'product_id'):
                self.product_id = self.produto_id.product_id.id
            if hasattr(self, 'product_uom'):
                self.product_uom = self.produto_id.unidade_id.uom_id
            if hasattr(self, 'uom_id'):
                self.uom_id = self.produto_id.unidade_id.uom_id
            return res

    def busca_operacao_item(self, domain_base):
        #
        # As variações abaixo, nos 3 laços for, garantem que todas as
        # possibilidades de variação dos critérios de pesquisa sejam atendidas
        # A ordem de anihamento dos laços é inversa à ordem de importância da
        # variação que queremos, ou seja, a primeira pesquisa é com/sem
        # contribuinte, a segunda com/sem protocolo, e assim por diante
        #
        for varia_tipo_produto_servico in [True, False]:
            for varia_protocolo in [True, False]:
                for varia_contribuinte in [True, False]:
                    variacao = {}
                    if not varia_contribuinte:
                        variacao['contribuinte'] = False
                    if not varia_protocolo:
                        variacao['protocolo_id'] = False
                    if not varia_tipo_produto_servico:
                        variacao['tipo_produto_servico'] = False

                    domain = domain_base.copy()
                    domain.update(variacao)

                    busca_item = [
                        ('operacao_id', '=', domain.get('operacao_id', False)),
                        ('tipo_protocolo', '=',
                             domain.get('tipo_protocolo', False)),
                        ('cfop_id.posicao', '=',
                             domain.get('cfop_id_posicao', False)),
                        ('contribuinte', '=',
                             domain.get('contribuinte', False)),
                        ('protocolo_id', '=',
                             domain.get('protocolo_id', False)),
                        ('tipo_produto_servico', '=',
                             domain.get('tipo_produto_servico', False)),
                    ]
                    operacao_item_ids = self.operacao_id.item_ids.search(
                        busca_item)

                    if operacao_item_ids:
                        return operacao_item_ids
        return False

        
    def _onchange_produto_id_recebimento(self):
        self.ensure_one()

        #
        # Aqui determinados o protocolo e o item da operação a ser seguido para
        # a operação, o produto e o NCM em questão
        #
        res = {}

        if not self.produto_id:
            return res

        #
        # Validamos alguns dos M2O necessários, vindos do documento
        #
        if not self.empresa_id:
            raise ValidationError(
                _('A empresa ativa não foi definida!')
            )

        if not self.participante_id:
            raise ValidationError(
                _('O destinatário/remetente não foi informado!')
            )

        if not self.operacao_id:
            raise ValidationError(_('A operação fiscal não foi informada!'))

        #
        # Se já ocorreu o preenchimento da descrição, não sobrepõe
        #
        if not self.produto_nome:
            self.produto_nome = self.produto_id.nome

        self.org_icms = (self.produto_id.org_icms or
                         ORIGEM_MERCADORIA_NACIONAL)
        self.unidade_id = self.produto_id.unidade_id.id


        if self.produto_id.unidade_tributacao_id:
            self.unidade_tributacao_id = \
                self.produto_id.unidade_tributacao_id.id
            self.fator_conversao_unidade_tributacao = \
                self.produto_id.fator_conversao_unidade_tributacao

        elif self.produto_id.unidade_tributacao_ncm_id:
            self.unidade_tributacao_id = \
                self.produto_id.unidade_tributacao_ncm_id.id
            self.fator_conversao_unidade_tributacao = \
                self.produto_id.fator_conversao_unidade_tributacao_ncm

        else:
            self.unidade_tributacao_id = self.produto_id.unidade_id.id
            self.fator_conversao_unidade_tributacao = 1

        if 'forca_vr_unitario' in self.env.context:
            self.vr_unitario = self.env.context['forca_vr_unitario']

        elif self.operacao_id.preco_automatico == 'V':
            self.vr_unitario = self.produto_id.preco_venda

        elif self.operacao_id.preco_automatico == 'C':
            self.vr_unitario = self.produto_id.preco_custo

        elif self.operacao_id.preco_automatico == 'T':
            self.vr_unitario = self.produto_id.preco_transferencia

        self.vr_unitario_readonly = self.vr_unitario

        self.peso_bruto_unitario = self.produto_id.peso_bruto
        self.peso_liquido_unitario = self.produto_id.peso_liquido
        self.especie = self.produto_id.especie
        self.fator_quantidade_especie = \
            self.produto_id.fator_quantidade_especie

        estado_origem, estado_destino, destinatario = \
            self._estado_origem_estado_destino_destinatario()

        if estado_origem == estado_destino:
            posicao_cfop = POSICAO_CFOP_ESTADUAL
        elif estado_origem == 'EX' or estado_destino == 'EX':
            posicao_cfop = POSICAO_CFOP_ESTRANGEIRO
        else:
            posicao_cfop = POSICAO_CFOP_INTERESTADUAL

        #
        # Determinamos o protocolo que vai ser aplicado à situação
        #
        protocolo = None

        if self.produto_id.protocolo_id:
            protocolo = self.produto_id.protocolo_id

        if (protocolo is None and self.produto_id.ncm_id and
                self.produto_id.ncm_id.protocolo_ids):
            busca_protocolo = [
                ('ncm_ids.ncm_id', '=', self.produto_id.ncm_id.id),
                '|',
                ('estado_ids', '=', False),
                ('estado_ids.uf', '=', estado_destino)
            ]
            protocolo_ids = self.env[
                'sped.protocolo.icms'].search(busca_protocolo)

            if len(protocolo_ids) != 0:
                protocolo = protocolo_ids[0]

        if protocolo is None and self.empresa_id.protocolo_id:
            protocolo = self.empresa_id.protocolo_id

        if (not protocolo) or (protocolo is None):
            raise ValidationError(
                _('O protocolo não foi definido!')
            )

        #
        # Tratando protocolos que só valem para determinados estados
        # Caso não seja possível usar o protocolo, por restrição dos
        # estados permitidos, usar a família global da empresa
        #
        if len(protocolo.estado_ids) > 0:
            estado_ids = protocolo.estado_ids.search(
                [('uf', '=', estado_destino)])

            #
            # O estado de destino não pertence ao protocolo, usamos então o
            # protocolo padrão da empresa
            #
            if len(estado_ids) == 0:
                if self.empresa_id.protocolo_id:
                    protocolo = self.empresa_id.protocolo_id

                else:
                    if self.produto_id.ncm_id:
                        mensagem_erro = \
                            'Não há protocolo padrão para a empresa, ' \
                            'e o protocolo “{protocolo}” não pode ' \
                            'ser usado para o estado “{estado}” ' \
                            '(produto “{produto}”, NCM “{ncm}”)!' \
                            .format(
                                protocolo=protocolo.descricao,
                                estado=estado_destino,
                                produto=self.produto_id.nome,
                                ncm=self.produto_id.ncm_id.codigo_formatado
                            )
                    else:
                        mensagem_erro = \
                            'Não há protocolo padrão para a empresa, ' \
                            'e o protocolo “{protocolo}” não pode ' \
                            'ser usado para o estado “{estado}” ' \
                            '(produto “{produto}”)!'\
                            .format(protocolo=protocolo.descricao,
                                    estado=estado_destino,
                                    produto=self.produto_id.nome)

                    raise ValidationError(_(mensagem_erro))

        #
        # Determinamos agora qual linha da operação será seguida.
        # Os critérios de busca vão variando entre o mais específico e o mais
        # genérico; esta variação está configurada mais abaixo, quais campos
        # devem ser pesquisados como False, e em qual ordem
        #
        domain_base = {
            'operacao_id': self.operacao_id.id,
            'tipo_protocolo': protocolo.tipo,
            'cfop_id_posicao': posicao_cfop,
            #
            # Os 3 critérios abaixo serão alternados entre o valor realmente,
            # ou False, no método busca_operacao_item
            #
            'contribuinte': self.participante_id.contribuinte,
            'protocolo_id': protocolo.id,
            'tipo_produto_servico': self.produto_id.tipo,
        }
        operacao_item_ids = self.busca_operacao_item(domain_base)

        #
        # Não tem item da operação mesmo, ou encontrou mais de um possível?
        #
        if not operacao_item_ids or len(operacao_item_ids) > 1:
            if not operacao_item_ids:
                mensagem_erro = \
                    'Não há nenhum item genérico na operação, ' \
                    'nem específico para o protocolo ' \
                    '“{protocolo}”, configurado para operações {estado}!'
            else:
                mensagem_erro = \
                    'Há mais de um item genérico na operação, ' \
                    'ou mais de um item específico para ' \
                    'o protocolo “{protocolo}”, ' \
                    'configurado para operações {estado}!'

            if posicao_cfop == POSICAO_CFOP_ESTADUAL:
                mensagem_erro = mensagem_erro.format(
                    protocolo=protocolo.descricao, estado='dentro do estado')

            elif posicao_cfop == POSICAO_CFOP_INTERESTADUAL:
                mensagem_erro = mensagem_erro.format(
                    protocolo=protocolo.descricao, estado='interestaduais')

            elif posicao_cfop == POSICAO_CFOP_ESTRANGEIRO:
                mensagem_erro = mensagem_erro.format(
                    protocolo=protocolo.descricao, estado='internacionais')

            raise ValidationError(_(mensagem_erro))

        #
        # Agora que temos o item da operação, definimos os valores do item
        #
        operacao_item = operacao_item_ids[0]

        self.operacao_item_id = operacao_item.id

        #
        # O protocolo alternativo no item da operação força o uso de
        # determinado protocolo, independente de validade no estado ou outras
        # validações
        #
        if operacao_item.protocolo_alternativo_id:
            self.protocolo_id = operacao_item.protocolo_alternativo_id.id

        else:
            self.protocolo_id = protocolo.id

        return res

    def _onchange_produto_id_emissao_propria(self):
        self.ensure_one()

        #
        # Aqui determinados o protocolo e o item da operação a ser seguido para
        # a operação, o produto e o NCM em questão
        #
        res = {}

        if not self.produto_id:
            return res

        #
        # Validamos alguns dos M2O necessários, vindos do documento
        #
        if not self.empresa_id:
            raise ValidationError(
                _('A empresa ativa não foi definida!')
            )

        if not self.participante_id:
            raise ValidationError(
                _('O destinatário/remetente não foi informado!')
            )

        if not self.operacao_id:
            raise ValidationError(_('A operação fiscal não foi informada!'))

        #
        # Se já ocorreu o preenchimento da descrição, não sobrepõe
        #
        if not self.produto_nome:
            self.produto_nome = self.produto_id.nome

        self.org_icms = (self.produto_id.org_icms or
                         ORIGEM_MERCADORIA_NACIONAL)
        self.unidade_id = self.produto_id.unidade_id.id


        if self.produto_id.unidade_tributacao_id:
            self.unidade_tributacao_id = \
                self.produto_id.unidade_tributacao_id.id
            self.fator_conversao_unidade_tributacao = \
                self.produto_id.fator_conversao_unidade_tributacao

        elif self.produto_id.unidade_tributacao_ncm_id:
            self.unidade_tributacao_id = \
                self.produto_id.unidade_tributacao_ncm_id.id
            self.fator_conversao_unidade_tributacao = \
                self.produto_id.fator_conversao_unidade_tributacao_ncm

        else:
            self.unidade_tributacao_id = self.produto_id.unidade_id.id
            self.fator_conversao_unidade_tributacao = 1

        if 'forca_vr_unitario' in self.env.context:
            self.vr_unitario = self.env.context['forca_vr_unitario']

        elif self.operacao_id.preco_automatico == 'V':
            self.vr_unitario = self.produto_id.preco_venda

        elif self.operacao_id.preco_automatico == 'C':
            self.vr_unitario = self.produto_id.preco_custo

        elif self.operacao_id.preco_automatico == 'T':
            self.vr_unitario = self.produto_id.preco_transferencia

        self.vr_unitario_readonly = self.vr_unitario

        self.peso_bruto_unitario = self.produto_id.peso_bruto
        self.peso_liquido_unitario = self.produto_id.peso_liquido
        self.especie = self.produto_id.especie
        self.fator_quantidade_especie = \
            self.produto_id.fator_quantidade_especie

        estado_origem, estado_destino, destinatario = \
            self._estado_origem_estado_destino_destinatario()

        if estado_origem == estado_destino:
            posicao_cfop = POSICAO_CFOP_ESTADUAL
        elif estado_origem == 'EX' or estado_destino == 'EX':
            posicao_cfop = POSICAO_CFOP_ESTRANGEIRO
        else:
            posicao_cfop = POSICAO_CFOP_INTERESTADUAL

        if self.operacao_id.calcular_tributacao in (
                'somente_calcula', 'manual'):
            return res
        #
        # Determinamos o protocolo que vai ser aplicado à situação
        #
        protocolo = None

        if self.produto_id.protocolo_id:
            protocolo = self.produto_id.protocolo_id

        if not protocolo and (
                self.produto_id.categ_id and
                self.produto_id.categ_id.protocolo_ids
        ):
            busca_protocolo = [
                ('categ_ids.id', '=', self.produto_id.categ_id.id),
                '|',
                ('estado_ids', '=', False),
                ('estado_ids.uf', '=', estado_destino)
            ]
            protocolo = self.env['sped.protocolo.icms'].search(
                busca_protocolo, limit=1
            )

        if not protocolo and (
                self.produto_id.ncm_id and
                self.produto_id.ncm_id.protocolo_ids
        ):
            busca_protocolo = [
                ('ncm_ids.ncm_id', '=', self.produto_id.ncm_id.id),
                '|',
                ('estado_ids', '=', False),
                ('estado_ids.uf', '=', estado_destino)
            ]
            protocolo = self.env['sped.protocolo.icms'].search(
                busca_protocolo, limit=1
            )

        if not protocolo and self.empresa_id.protocolo_id:
            protocolo = self.empresa_id.protocolo_id

        elif not protocolo:
            raise ValidationError(
                _('O protocolo não foi definido!')
            )

        #
        # Tratando protocolos que só valem para determinados estados
        # Caso não seja possível usar o protocolo, por restrição dos
        # estados permitidos, usar a família global da empresa
        #
        if len(protocolo.estado_ids) > 0:
            estado_ids = protocolo.estado_ids.search(
                [('uf', '=', estado_destino)])

            #
            # O estado de destino não pertence ao protocolo, usamos então o
            # protocolo padrão da empresa
            #
            if len(estado_ids) == 0:
                if self.empresa_id.protocolo_id:
                    protocolo = self.empresa_id.protocolo_id

                else:
                    if self.produto_id.ncm_id:
                        mensagem_erro = \
                            'Não há protocolo padrão para a empresa, ' \
                            'e o protocolo “{protocolo}” não pode ' \
                            'ser usado para o estado “{estado}” ' \
                            '(produto “{produto}”, NCM “{ncm}”)!' \
                            .format(
                                protocolo=protocolo.descricao,
                                estado=estado_destino,
                                produto=self.produto_id.nome,
                                ncm=self.produto_id.ncm_id.codigo_formatado
                            )
                    else:
                        mensagem_erro = \
                            'Não há protocolo padrão para a empresa, ' \
                            'e o protocolo “{protocolo}” não pode ' \
                            'ser usado para o estado “{estado}” ' \
                            '(produto “{produto}”)!'\
                            .format(protocolo=protocolo.descricao,
                                    estado=estado_destino,
                                    produto=self.produto_id.nome)

                    raise ValidationError(_(mensagem_erro))

        #
        # Determinamos agora qual linha da operação será seguida.
        # Os critérios de busca vão variando entre o mais específico e o mais
        # genérico; esta variação está configurada mais abaixo, quais campos
        # devem ser pesquisados como False, e em qual ordem
        #
        domain_base = {
            'operacao_id': self.operacao_id.id,
            'tipo_protocolo': protocolo.tipo,
            'cfop_id_posicao': posicao_cfop,
            #
            # Os 3 critérios abaixo serão alternados entre o valor realmente,
            # ou False, no método busca_operacao_item
            #
            'contribuinte': self.participante_id.contribuinte,
            'protocolo_id': protocolo.id,
            'tipo_produto_servico': self.produto_id.tipo,
        }
        operacao_item_ids = self.busca_operacao_item(domain_base)

        #
        # Não tem item da operação mesmo, ou encontrou mais de um possível?
        #
        if not operacao_item_ids or len(operacao_item_ids) > 1:
            if not operacao_item_ids:
                mensagem_erro = \
                    'Não há nenhum item genérico na operação, ' \
                    'nem específico para o protocolo ' \
                    '“{protocolo}”, configurado para operações {estado}!'
            else:
                mensagem_erro = \
                    'Há mais de um item genérico na operação, ' \
                    'ou mais de um item específico para ' \
                    'o protocolo “{protocolo}”, ' \
                    'configurado para operações {estado}!'

            if posicao_cfop == POSICAO_CFOP_ESTADUAL:
                mensagem_erro = mensagem_erro.format(
                    protocolo=protocolo.descricao, estado='dentro do estado')

            elif posicao_cfop == POSICAO_CFOP_INTERESTADUAL:
                mensagem_erro = mensagem_erro.format(
                    protocolo=protocolo.descricao, estado='interestaduais')

            elif posicao_cfop == POSICAO_CFOP_ESTRANGEIRO:
                mensagem_erro = mensagem_erro.format(
                    protocolo=protocolo.descricao, estado='internacionais')

            raise ValidationError(_(mensagem_erro))

        #
        # Agora que temos o item da operação, definimos os valores do item
        #
        operacao_item = operacao_item_ids[0]

        self.operacao_item_id = operacao_item.id

        #
        # O protocolo alternativo no item da operação força o uso de
        # determinado protocolo, independente de validade no estado ou outras
        # validações
        #
        if operacao_item.protocolo_alternativo_id:
            self.protocolo_id = operacao_item.protocolo_alternativo_id.id

        else:
            self.protocolo_id = protocolo.id

        return res

    @api.onchange('operacao_item_id')
    def _onchange_operacao_item_id(self):
        self.ensure_one()

        res = {}

        if not self.operacao_item_id:
            return res

        self.cfop_id = self.operacao_item_id.cfop_id.id
        self.compoe_total = self.operacao_item_id.compoe_total
        self.movimentacao_fisica = \
            self.operacao_item_id.movimentacao_fisica
        # self.bc_icms_proprio_com_ipi = \
        #    self.operacao_item_id.bc_icms_proprio_com_ipi
        # self.bc_icms_st_com_ipi = \
        #    self.operacao_item_id.bc_icms_st_com_ipi

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            self.cst_icms_sn = self.operacao_item_id.cst_icms_sn
            self.cst_icms = False

        else:
            self.cst_icms = self.operacao_item_id.cst_icms
            self.cst_icms_sn = False

        if self.entrada_saida == ENTRADA_SAIDA_ENTRADA:
            self.cst_ipi_entrada = self.operacao_item_id.cst_ipi_entrada
            self.cst_ipi = self.operacao_item_id.cst_ipi_entrada
        else:
            self.cst_ipi_saida = self.operacao_item_id.cst_ipi_saida
            self.cst_ipi = self.operacao_item_id.cst_ipi_saida

        self.enquadramento_ipi = self.operacao_item_id.enquadramento_ipi
        self.motivo_icms_desonerado = \
            self.operacao_item_id.motivo_icms_desonerado

        #
        # Busca agora as alíquotas do PIS e COFINS
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES and \
           self.operacao_item_id.cst_icms_sn != ST_ICMS_SN_OUTRAS:
            #
            # Força a CST do PIS, COFINS e IPI para o SIMPLES
            #
            # NF-e do SIMPLES não destaca IPI nunca, a não ser quando CSOSN 900
            self.cst_ipi = ''
            self.cst_ipi_entrada = ''
            self.cst_ipi_saida = ''
            al_pis_cofins = \
                self.env.ref('sped_imposto.ALIQUOTA_PIS_COFINS_SIMPLES')
            self.al_pis_cofins_id = al_pis_cofins.id
            self.codigo_natureza_receita_pis_cofins = ''

        else:
            #
            # Determina a alíquota do PIS-COFINS:
            # 1º - se o produto tem uma específica
            # 2º - se o NCM tem uma específica
            # 3º - a geral da empresa
            #
            if self.produto_id.al_pis_cofins_id:
                al_pis_cofins = self.produto_id.al_pis_cofins_id
            elif self.produto_id.ncm_id.al_pis_cofins_id:
                al_pis_cofins = self.produto_id.ncm_id.al_pis_cofins_id
            else:
                al_pis_cofins = self.empresa_id.al_pis_cofins_id

            #
            # Se por acaso a CST do PIS-COFINS especificada no item da operação
            # definir que não haverá cobrança de PIS-COFINS, usa a CST da
            # operação caso contrário, usa a definida acima
            #
            if (self.operacao_item_id.al_pis_cofins_id and not
                (self.operacao_item_id.al_pis_cofins_id.cst_pis_cofins_saida
                     in ST_PIS_CALCULA_ALIQUOTA or
                 self.operacao_item_id.al_pis_cofins_id.cst_pis_cofins_saida
                     in ST_PIS_CALCULA_QUANTIDADE)):
                al_pis_cofins = self.operacao_item_id.al_pis_cofins_id

            self.al_pis_cofins_id = al_pis_cofins.id

            #
            # Agora, pega a natureza da receita do PIS-COFINS, necessária
            # para o SPED Contribuições
            #
            if self.produto_id.codigo_natureza_receita_pis_cofins:
                self.codigo_natureza_receita_pis_cofins = \
                self.produto_id.codigo_natureza_receita_pis_cofins
            elif self.produto_id.ncm_id.al_pis_cofins_id and \
                self.produto_id.ncm_id.codigo_natureza_receita_pis_cofins:
                self.codigo_natureza_receita_pis_cofins = \
                    self.produto_id.ncm_id.codigo_natureza_receita_pis_cofins
            elif self.operacao_item_id.codigo_natureza_receita_pis_cofins:
                self.codigo_natureza_receita_pis_cofins = \
                    self.operacao_item_id.codigo_natureza_receita_pis_cofins
        return res

    @api.onchange('cfop_id')
    def _onchange_cfop_id(self):
        self.ensure_one()

        res = {}

        if not self.cfop_id:
            return res

        self.al_simples = 0
        self.calcula_difal = False
        self.bc_icms_proprio_com_ipi = False
        self.bc_icms_st_com_ipi = False

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cfop_id.calcula_simples_csll_irpj:
                if self.cfop_id.eh_venda_servico:
                    if self.empresa_id.simples_aliquota_servico_id:
                        self.al_simples = \
                            self.empresa_id.simples_aliquota_servico_id \
                                .al_simples
                    else:
                        self.al_simples = \
                            self.empresa_id.simples_aliquota_id.al_simples
                else:
                    self.al_simples = \
                        self.empresa_id.simples_aliquota_id.al_simples

        else:
            if (self.consumidor_final ==
                    TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL and
                    self.cfop_id.eh_venda):
                if self.cfop_id.posicao == POSICAO_CFOP_INTERESTADUAL:
                    self.calcula_difal = True

                    if '2016-' in self.data_emissao:
                        self.al_partilha_estado_destino = 40
                    elif '2017-' in self.data_emissao:
                        self.al_partilha_estado_destino = 60
                    elif '2018-' in self.data_emissao:
                        self.al_partilha_estado_destino = 80
                    else:
                        self.al_partilha_estado_destino = 100

                self.bc_icms_proprio_com_ipi = True
                self.bc_icms_st_com_ipi = True

        #
        # Busca a alíquota do IBPT quando venda
        #
        if self.cfop_id.eh_venda:
            if self.produto_id.ncm_id:
                ibpt = self.env['sped.ibptax.ncm']

                ibpt_ids = ibpt.search([
                    ('estado_id', '=',
                        self.empresa_id.municipio_id.estado_id.id),
                    ('ncm_id', '=', self.produto_id.ncm_id.id),
                ])

                if len(ibpt_ids) > 0:
                    self.al_ibpt = ibpt_ids[
                        0].al_ibpt_nacional + ibpt_ids[0].al_ibpt_estadual

                    if (self.operacao_item_id.cfop_id.posicao ==
                            POSICAO_CFOP_ESTRANGEIRO):
                        self.al_ibpt += ibpt_ids[0].al_ibpt_internacional

            #
            # NBS por ser mais detalhado tem prioridade sobre o código do
            # serviço
            #
            elif self.produto_id.nbs_id:
                ibpt = self.env['sped.ibptax.nbs']

                ibpt_ids = ibpt.search([
                    ('estado_id', '=',
                        self.empresa_id.municipio_id.estado_id.id),
                    ('nbs_id', '=', self.produto_id.nbs_id.id),
                ])

                if len(ibpt_ids) > 0:
                    self.al_ibpt = ibpt_ids[
                        0].al_ibpt_nacional + ibpt_ids[0].al_ibpt_municipal

                    if (self.operacao_item_id.cfop_id.posicao ==
                            POSICAO_CFOP_ESTRANGEIRO):
                        self.al_ibpt += ibpt_ids[0].al_ibpt_internacional

            elif self.produto_id.servico_id:
                ibpt = self.env['sped.ibptax.servico']

                ibpt_ids = ibpt.search([
                    ('estado_id', '=',
                        self.empresa_id.municipio_id.estado_id.id),
                    ('servico_id', '=', self.produto_id.servico_id.id),
                ])

                if len(ibpt_ids) > 0:
                    self.al_ibpt = ibpt_ids[
                        0].al_ibpt_nacional + ibpt_ids[0].al_ibpt_municipal

                    if (self.operacao_item_id.cfop_id.posicao ==
                            POSICAO_CFOP_ESTRANGEIRO):
                        self.al_ibpt += ibpt_ids[0].al_ibpt_internacional
        return res

    @api.onchange('al_pis_cofins_id')
    def _onchange_al_pis_cofins_id(self):
        self.ensure_one()

        res = {}

        if not self.al_pis_cofins_id:
            return res

        self.md_pis_proprio = self.al_pis_cofins_id.md_pis_cofins
        self.al_pis_proprio = self.al_pis_cofins_id.al_pis or 0

        self.md_cofins_proprio = self.al_pis_cofins_id.md_pis_cofins
        self.al_cofins_proprio = self.al_pis_cofins_id.al_cofins or 0

        if self.entrada_saida == ENTRADA_SAIDA_ENTRADA:
            self.cst_pis = self.al_pis_cofins_id.cst_pis_cofins_entrada
            self.cst_cofins = \
                self.al_pis_cofins_id.cst_pis_cofins_entrada
            self.cst_pis_entrada = \
                self.al_pis_cofins_id.cst_pis_cofins_entrada
            self.cst_cofins_entrada = \
                self.al_pis_cofins_id.cst_pis_cofins_entrada

        else:
            self.cst_pis = self.al_pis_cofins_id.cst_pis_cofins_saida
            self.cst_cofins = self.al_pis_cofins_id.cst_pis_cofins_saida
            self.cst_pis_saida = \
                self.al_pis_cofins_id.cst_pis_cofins_saida
            self.cst_cofins_saida = \
                self.al_pis_cofins_id.cst_pis_cofins_saida

        return res

    @api.onchange('cst_ipi')
    def _onchange_cst_ipi(self):
        self.ensure_one()

        res = {}

        if not self.cst_ipi:
            return res

        #
        # Na nota de terceiros, respeitamos o IPI enviado no XML original,
        # e não recalculamos
        #
        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res
        elif self.operacao_id.calcular_tributacao in (
                'somente_calcula', 'manual'):
            return res

        if (self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES and
                self.cst_icms_sn != ST_ICMS_SN_OUTRAS):
            self.cst_ipi = ''  # NF-e do SIMPLES não destaca IPI nunca
            # NF-e do SIMPLES não destaca IPI nunca
            self.cst_ipi_entrada = ''
            # NF-e do SIMPLES não destaca IPI nunca
            self.cst_ipi_saida = ''
            self.md_ipi = MODALIDADE_BASE_IPI_ALIQUOTA
            self.bc_ipi = 0
            self.al_ipi = 0
            self.vr_ipi = 0
            return res

        #
        # Determina a alíquota do IPI:
        # 1º - se o produto tem uma específica
        # 2º - se o NCM tem uma específica
        #
        if self.produto_id.al_ipi_id:
            al_ipi = self.produto_id.al_ipi_id
        elif self.produto_id.ncm_id.al_ipi_id:
            al_ipi = self.produto_id.ncm_id.al_ipi_id
        else:
            al_ipi = None

        if ((self.cst_ipi not in ST_IPI_CALCULA) or
                (not al_ipi) or (al_ipi is None)):
            self.md_ipi = MODALIDADE_BASE_IPI_ALIQUOTA
            self.bc_ipi = 0
            self.al_ipi = 0
            self.vr_ipi = 0

        else:
            self.md_ipi = al_ipi.md_ipi
            self.al_ipi = al_ipi.al_ipi

        return res

    @api.onchange('protocolo_id', 'cfop_id', 'calcula_difal',
                  'org_icms', 'cst_icms', 'cst_icms_sn', 'produto_id')
    def _onchange_cst_icms_cst_icms_sn(self):
        self.ensure_one()

        res = {}
        mensagens_complementares = ''
        avisos = {}
        res['warning'] = avisos

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res
        elif self.operacao_id.calcular_tributacao in (
                'somente_calcula', 'manual'):
            return res
        elif not self.protocolo_id:
            return res

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cst_icms_sn in ST_ICMS_SN_CALCULA_CREDITO:
                if not self.cfop_id.eh_venda:
                    avisos['title'] = 'Aviso!'
                    avisos['message'] = \
                        'Você selecionou uma CSOSN que dá direito a crédito, '\
                        'porém a CFOP não indica uma venda!'

                self.al_icms_sn = self.empresa_id.simples_aliquota_id \
                    .al_icms

            else:
                self.al_icms_sn = 0
                self.rd_icms_sn = 0

        else:
            self.al_icms_sn = 0
            self.rd_icms_sn = 0

        estado_origem, estado_destino, destinatario = \
            self._estado_origem_estado_destino_destinatario()

        #
        # Agora, buscamos as alíquotas necessárias
        #
        if (self.entrada_saida == ENTRADA_SAIDA_ENTRADA and
                self.participante_id.estado == 'EX'):
            mensagem, aliquota_origem_destino = \
                self.protocolo_id.busca_aliquota(
                estado_destino, estado_destino,
                self.data_emissao, self.empresa_id)
            if mensagem:
                mensagens_complementares += mensagem + '; '

        else:
            mensagem, aliquota_origem_destino = \
                self.protocolo_id.busca_aliquota(
                estado_origem, estado_destino,
                self.data_emissao, self.empresa_id)
            if mensagem:
                mensagens_complementares += mensagem + '; '

        #
        # Alíquota do ICMS próprio
        #
        if (self.org_icms in ORIGEM_MERCADORIA_ALIQUOTA_4 and
                self.cfop_id.posicao == POSICAO_CFOP_INTERESTADUAL):
            al_icms = self.env.ref('sped_imposto.ALIQUOTA_ICMS_PROPRIO_4')

        else:
            al_icms = aliquota_origem_destino.al_icms_proprio_id

        self.md_icms_proprio = al_icms.md_icms
        self.pr_icms_proprio = al_icms.pr_icms
        self.rd_icms_proprio = al_icms.rd_icms

        if self.cst_icms and (
                not self.cst_icms in ST_ICMS_DESONERADO_ZERA_ICMS_PROPRIO):
            self.al_icms_proprio = al_icms.al_icms

        self.al_interna_destino = 0
        self.al_difal = 0
        self.al_fcp = 0

        if self.calcula_difal:
            mensagem, aliquota_interna_destino = \
            self.protocolo_id.busca_aliquota(
                estado_destino, estado_destino,
                self.data_emissao, self.empresa_id)
            if mensagem:
                mensagens_complementares += mensagem + '; '

            if (aliquota_interna_destino.al_icms_proprio_id.al_icms >
                    al_icms.al_icms):
                al_difal = aliquota_interna_destino.al_icms_proprio_id.al_icms
                al_difal -= al_icms.al_icms

                self.al_difal = al_difal
                self.al_interna_destino = \
                    aliquota_interna_destino.al_icms_proprio_id.al_icms

                self.al_fcp = aliquota_interna_destino.al_fcp

        if mensagens_complementares:
            self.mensagens_complementares = mensagens_complementares
        #
        # Alíquota e MVA do ICMS ST, somente para quando não houver serviço
        # (serviço pode ter ICMS na nota conjugada [DF])
        #
        if ((self.cst_icms in ST_ICMS_CALCULA_ST or
                self.cst_icms_sn in ST_ICMS_SN_CALCULA_ST) and
                self.produto_id.tipo != TIPO_PRODUTO_SERVICO_SERVICOS):
            al_icms_st = aliquota_origem_destino.al_icms_st_id

            self.md_icms_st = al_icms_st.md_icms
            self.pr_icms_st = al_icms_st.pr_icms
            self.rd_icms_st = al_icms_st.rd_icms
            self.al_icms_st = al_icms_st.al_icms

            #
            # Verificamos a necessidade de se busca a MVA (ajustada ou não)
            #
            if (al_icms_st.md_icms ==
                    MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO and
                    (not al_icms_st.pr_icms)):
                protocolo_ncm = self.produto_id.ncm_id.busca_mva(
                    self.protocolo_id)

                if (protocolo_ncm is not None) and protocolo_ncm:
                    pr_icms_st = protocolo_ncm.mva

                    #
                    # SIMPLES não ajusta a MVA
                    #
                    # Atenção aqui, pois SC determina que é o regime tributário
                    # do destinatário que determina o ajuste
                    #
                    ajusta_mva = False
                    if (estado_origem == 'SC' or estado_destino == 'SC'):
                        if (destinatario.regime_tributario !=
                                REGIME_TRIBUTARIO_SIMPLES):
                            ajusta_mva = True

                    elif self.regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
                        ajusta_mva = True

                    if ajusta_mva:
                        al_icms_proprio = 100 - al_icms.al_icms
                        al_icms_proprio /= 100

                        al_icms_st = 100 - al_icms_st.al_icms
                        al_icms_st /= 100

                        pr_icms_st /= 100
                        pr_icms_st += 1
                        pr_icms_st *= al_icms_proprio / al_icms_st
                        pr_icms_st -= 1
                        pr_icms_st *= 100
                        pr_icms_st = D(pr_icms_st).quantize(D('0.0001'))

                    self.pr_icms_st = pr_icms_st

        return res

    @api.onchange('vr_unitario', 'quantidade', 'vr_unitario_tributacao',
                  'quantidade_tributacao', 'vr_frete',
                  'vr_seguro', 'vr_desconto', 'vr_outras',
                  'vr_ii',
                  'fator_conversao_unidade_tributacao',
                  'peso_bruto_unitario', 'peso_liquido_unitario',
                  'especie', 'fator_quantidade_especie')
    def _onchange_calcula_valor_operacao(self):
        self.ensure_one()

        res = {}

        if hasattr(self, 'price_unit'):
            self.price_unit = self.vr_unitario
        if hasattr(self, 'quantity'):
            self.quantity = self.quantidade
        if hasattr(self, 'product_qty'):
            self.product_qty = self.quantidade
        if hasattr(self, 'product_uom_qty'):
            self.product_uom_qty = self.quantidade

        # if self.emissao != TIPO_EMISSAO_PROPRIA and not \
        #         self.env.context.get('manual'):
        #     return res

        #
        # Cupom Fiscal só aceita até 3 casas decimais no valor unitário
        #
        if self.modelo == '2D':
            self.vr_unitario = self.vr_unitario.quantize(D('0.001'))
            self.vr_unitario_tributacao = self.vr_unitario_tributacao.quantize(
                D('0.001'))

            # self.vr_unitario = self.vr_unitario
            # self.vr_unitario_tributacao = self.vr_unitario_tributacao

        #
        # Calcula o valor dos produtos
        #
        vr_produtos = D(self.quantidade) * D(self.vr_unitario)
        vr_produtos = vr_produtos.quantize(D('0.01'))

        #if self.al_desconto:
            #al_desconto = D(self.al_desconto) / 100
            #vr_desconto = vr_produtos * al_desconto
            #self.vr_desconto = vr_desconto

        #
        # Até segunda ordem, a quantidade e valor unitário para tributação não
        # mudam
        #
        quantidade_tributacao = self.quantidade * \
            self.fator_conversao_unidade_tributacao

        if quantidade_tributacao > 0:
            vr_unitario_tributacao = vr_produtos / quantidade_tributacao
        else:
            vr_unitario_tributacao = D(self.vr_unitario)

        vr_unitario_tributacao = vr_unitario_tributacao.quantize(
            D('0.0000000001'))
        vr_produtos_tributacao = quantidade_tributacao * vr_unitario_tributacao
        vr_produtos_tributacao = vr_produtos_tributacao
        self.quantidade_tributacao = quantidade_tributacao
        self.vr_unitario_tributacao = vr_unitario_tributacao

        if self.fator_conversao_unidade_tributacao != 1:
            self.exibe_tributacao = True
        else:
            self.exibe_tributacao = False

        vr_operacao = vr_produtos + self.vr_frete + \
            self.vr_seguro + self.vr_outras - self.vr_desconto
        vr_operacao_tributacao = \
            vr_produtos_tributacao + self.vr_frete + self.vr_seguro + \
            self.vr_outras - self.vr_desconto + self.vr_ii

        self.vr_produtos = vr_produtos
        self.vr_produtos_tributacao = vr_produtos_tributacao
        self.vr_operacao = vr_operacao
        self.vr_operacao_tributacao = vr_operacao_tributacao

        #
        # Preenchimento automático de volumes
        #
        peso_bruto = D(self.quantidade) * D(self.peso_bruto_unitario)
        peso_bruto = peso_bruto.quantize(D('0.0001'))
        peso_liquido = D(self.quantidade) * D(self.peso_liquido_unitario)
        peso_liquido = peso_liquido.quantize(D('0.0001'))

        if self.fator_quantidade_especie > 0 and self.especie:
            quantidade_especie = D(self.quantidade) / \
                D(self.fator_quantidade_especie)
            quantidade_especie = quantidade_especie.quantize(D('0.0001'))

        else:
            quantidade_especie = 0

        self.peso_bruto = peso_bruto
        self.peso_liquido = peso_liquido
        self.quantidade_especie = quantidade_especie

        return res

    @api.onchange('vr_operacao_tributacao', 'quantidade_tributacao',
                  'cst_ipi', 'md_ipi', 'bc_ipi', 'al_ipi', 'vr_ipi')
    def _onchange_calcula_ipi(self):
        res = {}

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res
        elif self.operacao_id.calcular_tributacao == 'manual':
            return res

        self.bc_ipi = 0
        self.vr_ipi = 0

        #
        # SIMPLES não tem IPI
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            self.cst_ipi = ''
            self.md_ipi = MODALIDADE_BASE_IPI_ALIQUOTA
            self.al_ipi = 0
            return res

        if self.cst_ipi not in ST_IPI_CALCULA:
            self.al_ipi = 0
            return res

        bc_ipi = D(0)
        vr_ipi = D(0)

        if self.md_ipi == MODALIDADE_BASE_IPI_ALIQUOTA:
            bc_ipi = D(self.vr_operacao_tributacao)
            vr_ipi = bc_ipi * D(self.al_ipi) / 100

        elif self.md_ipi == MODALIDADE_BASE_IPI_QUANTIDADE:
            bc_ipi = 0
            vr_ipi = D(self.quantidade_tributacao) * D(self.al_ipi)

        vr_ipi = vr_ipi.quantize(D('0.01'))

        self.bc_ipi = bc_ipi
        self.vr_ipi = vr_ipi

        return res

    @api.onchange('vr_operacao_tributacao', 'rd_icms_sn',
                  'cst_icms_sn', 'al_icms_sn', 'vr_icms_sn',
                  'bc_icms_proprio_com_ipi')
    def _onchange_calcula_icms_sn(self):
        res = {}

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res
        elif self.operacao_id.calcular_tributacao == 'manual':
            return res

        self.vr_icms_sn = 0

        #
        # Só SIMPLES tem crédito de ICMS SN
        #
        if self.regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
            self.cst_icms_sn = False
            self.rd_icms_sn = 0
            self.al_icms_sn = 0
            return res

        if self.cst_icms_sn not in ST_ICMS_SN_CALCULA_CREDITO:
            self.rd_icms_sn = 0
            self.al_icms_sn = 0
            return res

        al_icms_sn = D(self.al_icms_sn)

        #
        # Aplica a redução da alíquota quando houver
        #
        if self.rd_icms_sn:
            al_icms_sn = al_icms_sn - (al_icms_sn * D(self.rd_icms_sn) / 100)
            al_icms_sn = al_icms_sn.quantize(D('0.01'))

        vr_icms_sn = D(self.vr_operacao_tributacao) * al_icms_sn / 100
        vr_icms_sn = vr_icms_sn.quantize(D('0.01'))

        self.vr_icms_sn = vr_icms_sn

        return res

    @api.onchange('vr_operacao_tributacao', 'quantidade_tributacao',
                  'cst_pis', 'cst_cofins', 'md_pis_proprio',
                  'md_cofins_proprio', 'bc_pis_proprio', 'al_pis_proprio',
                  'vr_pis_proprio', 'bc_cofins_proprio',
                  'al_cofins_proprio', 'vr_cofins_proprio')
    def _onchange_calcula_pis_cofins(self):
        res = {}

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res
        elif self.operacao_id.calcular_tributacao == 'manual':
            return res

        if (self.cst_pis in ST_PIS_CALCULA or
                self.cst_pis in ST_PIS_CALCULA_CREDITO or
                (self.cst_pis == ST_PIS_AQUIS_SEM_CREDITO and
                 self.emissao == TIPO_EMISSAO_PROPRIA)):

            md_pis_proprio = 0
            bc_pis_proprio = 0
            vr_pis_proprio = 0
            md_cofins_proprio = 0
            bc_cofins_proprio = 0
            vr_cofins_proprio = 0

            if self.cst_pis in ST_PIS_CALCULA_ALIQUOTA:
                md_pis_proprio = MODALIDADE_BASE_PIS_ALIQUOTA
                bc_pis_proprio = D(self.vr_operacao_tributacao)
                vr_pis_proprio = bc_pis_proprio * \
                    D(self.al_pis_proprio) / 100

                md_cofins_proprio = MODALIDADE_BASE_COFINS_ALIQUOTA
                bc_cofins_proprio = D(self.vr_operacao_tributacao)
                vr_cofins_proprio = bc_cofins_proprio * \
                    D(self.al_cofins_proprio) / 100

            else:
                md_pis_proprio = MODALIDADE_BASE_PIS_QUANTIDADE
                bc_pis_proprio = 0
                vr_pis_proprio = \
                    D(self.quantidade_tributacao) * D(self.al_pis_proprio)

                md_cofins_proprio = MODALIDADE_BASE_COFINS_QUANTIDADE
                bc_cofins_proprio = 0
                vr_cofins_proprio = \
                    D(self.quantidade_tributacao) * D(self.al_cofins_proprio)

            vr_pis_proprio = vr_pis_proprio.quantize(D('0.01'))
            vr_cofins_proprio = vr_cofins_proprio.quantize(D('0.01'))

            self.md_pis_proprio = md_pis_proprio
            self.bc_pis_proprio = bc_pis_proprio
            self.vr_pis_proprio = vr_pis_proprio

            self.md_cofins_proprio = md_cofins_proprio
            self.bc_cofins_proprio = bc_cofins_proprio
            self.vr_cofins_proprio = vr_cofins_proprio

        return res

    @api.onchange('vr_operacao_tributacao', 'quantidade_tributacao',
                  'vr_ipi', 'vr_outras', 'cst_icms', 'cst_icms_sn',
                  'md_icms_proprio', 'pr_icms_proprio', 'rd_icms_proprio',
                  'bc_icms_proprio_com_ipi', 'bc_icms_proprio',
                  'al_icms_proprio', 'vr_icms_proprio', 'md_icms_st',
                  'pr_icms_st', 'rd_icms_st', 'bc_icms_st_com_ipi',
                  'bc_icms_st', 'al_icms_st', 'vr_icms_st',
                  'calcula_difal', 'vr_icms_desonerado',
                  )
    def _onchange_calcula_icms(self):
        self.ensure_one()

        res = {}

        self._onchange_calcula_icms_proprio()
        self._onchange_calcula_icms_st()

        return res

    def _onchange_calcula_icms_proprio(self):
        self.ensure_one()

        #
        # Aliquota efetivamente utilizada, campo do cf-e
        #
        self.al_efetiva_icms_proprio = (1 - self.rd_icms_proprio/100) * self.al_icms_proprio

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return
        elif self.operacao_id.calcular_tributacao in (
                'somente_calcula', 'manual'):
            return

        self.bc_icms_proprio = 0
        self.vr_icms_proprio = 0
        self.vr_icms_desonerado = 0

        #
        # Baseado no valor da situação tributária, calcular o ICMS próprio
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if not ((self.cst_icms_sn in ST_ICMS_SN_CALCULA_ST) or
                    (self.cst_icms_sn in ST_ICMS_SN_CALCULA_PROPRIO) or
                    (self.cst_icms_sn == ST_ICMS_SN_ANTERIOR)):
                return

        elif self.cst_icms in ST_ICMS_CALCULA_PROPRIO_COM_MOTIVO_DESONERACAO:
            if not self.motivo_icms_desonerado:
                return

        elif self.cst_icms not in ST_ICMS_CALCULA_PROPRIO:
            if self.cst_icms in ST_ICMS_ZERA_ICMS_PROPRIO:
                self.al_icms_proprio = D(0)
                self.bc_icms_proprio = D(0)
                self.vr_icms_proprio = D(0)
            return

        if not self.md_icms_proprio:
            return

        if self.md_icms_proprio in \
                (MODALIDADE_BASE_ICMS_PROPRIO_PAUTA,
                 MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO):
            bc_icms_proprio = D(self.quantidade_tributacao) * \
                D(self.pr_icms_proprio)

        else:
            bc_icms_proprio = D(self.vr_operacao_tributacao)

        #
        # Nas notas de importação o ICMS é "por fora"
        #
        if (self.cfop_id.posicao == POSICAO_CFOP_ESTRANGEIRO and
                self.entrada_saida == ENTRADA_SAIDA_ENTRADA):
            bc_icms_proprio = D(bc_icms_proprio) / \
                D(1 - D(self.al_icms_proprio) / 100)

        #
        # Nas devoluções de compra de empresa que não destaca IPI, o valor do
        # IPI é informado em outras depesas acessórias;
        # nesses casos, inverter a consideração da soma do valor do IPI, pois o
        # valor de outras despesas já entrou no valor tributável
        #
        if self.cfop_id.eh_devolucao_compra or self.cfop_id.eh_retorno_saida:
            if not self.bc_icms_proprio_com_ipi:
                if (not self.vr_ipi) and self.vr_outras:
                    bc_icms_proprio -= D(self.vr_outras)

        elif self.bc_icms_proprio_com_ipi:
            bc_icms_proprio += D(self.vr_ipi)

        #
        # Agora que temos a base final, aplicamos a margem caso necessário
        #
        if (self.md_icms_proprio ==
                MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO):
            bc_icms_proprio = bc_icms_proprio * \
                D(1 + (D(self.pr_icms_proprio) / 100))

        #
        # Vai haver redução da base de cálculo?
        # Aqui também, no caso da situação 30 e 60, calculamos a redução,
        # quando houver
        #
        if (self.cst_icms in ST_ICMS_COM_REDUCAO or
                self.cst_icms_sn in ST_ICMS_SN_CALCULA_ST):
            bc_icms_proprio = bc_icms_proprio.quantize(D('0.01'))
            bc_icms_proprio = bc_icms_proprio * \
                D(1 - (D(self.rd_icms_proprio) / 100))

        bc_icms_proprio = D(bc_icms_proprio).quantize(D('0.01'))

        vr_icms_proprio = bc_icms_proprio * D(self.al_icms_proprio) / 100
        vr_icms_proprio = vr_icms_proprio.quantize(D('0.01'))

        #
        # ICMS desonerado
        #
        if self.motivo_icms_desonerado and self.cst_icms in ST_ICMS_DESONERADO:
            if self.cst_icms in ST_ICMS_DESONERADO_TOTAL:
                vr_icms_desonerado = vr_icms

                if self.cst_icms in ST_ICMS_DESONERADO_ZERA_ICMS_PROPRIO:
                    bc_icms_proprio = D(0)
                    vr_icms_proprio = D(0)
                self.vr_icms_desonerado = vr_icms_desonerado

        self.bc_icms_proprio = bc_icms_proprio
        self.vr_icms_proprio = vr_icms_proprio

    def _onchange_calcula_icms_st(self):
        self.ensure_one()

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return

        self.bc_icms_st = 0
        self.vr_icms_st = 0

        #
        # Baseado no valor da situação tributária, calcular o ICMS ST
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cst_icms_sn not in ST_ICMS_SN_CALCULA_ST:
                return

        else:
            if self.cst_icms not in ST_ICMS_CALCULA_ST:
                return

        if not self.md_icms_st:
            return

        if self.md_icms_st == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
            bc_icms_st = D(self.vr_operacao_tributacao)

        else:
            bc_icms_st = D(self.quantidade) * D(self.pr_icms_st)

        #
        # Nas devoluções de compra de empresa que não destaca IPI, o valor do
        # IPI é informado em outras depesas acessórias;
        # nesses casos, inverter a consideração da soma do valor do IPI, pois o
        # valor de outras despesas já entrou no valor tributável
        #
        if self.cfop_id.eh_devolucao_compra:
            if not self.bc_icms_st_com_ipi:
                if (not self.vr_ipi) and self.vr_outras:
                    bc_icms_st -= D(self.vr_outras)

        elif self.bc_icms_st_com_ipi:
            bc_icms_st += D(self.vr_ipi)

        #
        # Agora que temos a base final, aplicamos a margem caso necessário
        #
        if self.md_icms_st == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
            bc_icms_st = bc_icms_st * (1 + (D(self.pr_icms_st) / 100))

        #
        # Vai haver redução da base de cálculo?
        #
        if self.rd_icms_st:
            bc_icms_st = bc_icms_st.quantize(D('0.01'))
            bc_icms_st = bc_icms_st * (1 - (D(self.rd_icms_st) / 100))

        bc_icms_st = bc_icms_st.quantize(D('0.01'))

        vr_icms_st = bc_icms_st * (D(self.al_icms_st) / 100)
        vr_icms_st = vr_icms_st.quantize(D('0.01'))
        vr_icms_st -= D(self.vr_icms_proprio)

        self.bc_icms_st = bc_icms_st
        self.vr_icms_st = vr_icms_st

        #
        # ICMS desonerado
        #
        if self.motivo_icms_desonerado and \
            self.cst_icms in ST_ICMS_DESONERADO_TOTAL:
            self.bc_icms_proprio = 0
            self.vr_icms_proprio = 0

        elif ((self.cst_icms in ST_ICMS_ZERA_ICMS_PROPRIO) or
            ((self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES) and
                (self.cst_icms_sn not in ST_ICMS_SN_CALCULA_PROPRIO) and
                (self.cst_icms_sn not in ST_ICMS_SN_CALCULA_ST))):
            self.bc_icms_proprio = 0
            self.vr_icms_proprio = 0

    @api.onchange('vr_operacao_tributacao', 'calcula_difal',
                  'al_icms_proprio', 'al_interna_destino', 'al_fcp',
                  'al_partilha_estado_destino')
    def _onchange_calcula_difal(self):
        self.ensure_one()

        res = {}

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res

        self.al_difal = 0
        self.vr_difal = 0
        self.vr_icms_estado_origem = 0
        self.vr_icms_estado_destino = 0
        self.vr_fcp = 0

        if self.calcula_difal:
            al_difal = D(self.al_interna_destino) - D(self.al_icms_proprio)
            vr_difal = D(self.vr_operacao_tributacao) * al_difal / 100
            vr_difal = vr_difal.quantize(D('0.01'))
            self.al_difal = al_difal
            self.vr_difal = vr_difal

            vr_icms = D(self.vr_operacao_tributacao)
            vr_icms *= D(self.al_interna_destino)
            vr_icms /= 100
            vr_icms = vr_icms.quantize(D('0.01'))
            vr_icms_estado_destino = vr_icms * \
                D(self.al_partilha_estado_destino) / 100
            vr_icms_estado_destino = vr_icms_estado_destino.quantize(D('0.01'))
            vr_icms_estado_origem = vr_icms - \
                vr_icms_estado_destino

            self.vr_icms_estado_destino = vr_icms_estado_destino
            self.vr_icms_estado_origem = vr_icms_estado_origem

            vr_fcp = D(self.vr_operacao_tributacao) * D(self.al_fcp) / 100
            vr_fcp = vr_fcp.quantize(D('0.01'))
            self.vr_fcp = vr_fcp

        return res

    @api.onchange('vr_fatura', 'al_simples')
    def _onchange_calcula_simples(self):
        self.ensure_one()

        res = {}

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res

        if self.al_simples:
            vr_simples = D(self.vr_fatura) * D(self.al_simples) / 100
            vr_simples = vr_simples.quantize(D('0.01'))
            self.vr_simples = vr_simples

        return res

    @api.onchange('vr_operacao_tributacao', 'al_ibpt')
    def _onchange_calcula_ibpt(self):
        self.ensure_one()

        res = {}

        if self.emissao != TIPO_EMISSAO_PROPRIA and not \
                self.env.context.get('manual'):
            return res

        if self.al_ibpt:
            vr_ibpt = D(self.vr_operacao_tributacao) * D(self.al_ibpt) / 100
            vr_ibpt = vr_ibpt.quantize(D('0.01'))
            self.vr_ibpt = vr_ibpt

        return res

    @api.onchange('vr_operacao', 'vr_icms_proprio',
                  'vr_icms_st', 'vr_ipi', 'vr_ii')
    def _onchange_calcula_total(self):
        self.ensure_one()

        res = {}

        # if self.emissao != TIPO_EMISSAO_PROPRIA and not \
        #         self.env.context.get('manual'):
        #     return res

        vr_nf = self.vr_operacao + self.vr_ipi + self.vr_icms_st + self.vr_ii
        vr_nf -= self.vr_icms_desonerado

        #
        # Nas importações o ICMS é somado no total da nota
        #
        if self.vr_ii > 0:
            vr_nf += self.vr_icms_proprio

        self.vr_nf = vr_nf

        if self.compoe_total:
            self.vr_fatura = vr_nf

        else:
            #
            # Não concordo com o valor do item não compor o total da NF, mas
            # enfim...
            #
            self.vr_nf = 0
            self.vr_fatura = 0

        return res

    @api.depends('vr_nf', 'vr_simples', 'vr_difal', 'vr_icms_proprio',
                 'vr_icms_sn', 'credita_icms_proprio',
                 'cfop_id', 'vr_ipi', 'credita_ipi', 'vr_pis_proprio',
                 'vr_cofins_proprio', 'credita_pis_cofins', 'quantidade')
    def _compute_custo_comercial(self):
        for item in self:
            vr_custo = item.vr_nf

            if item.emissao == TIPO_EMISSAO_PROPRIA:
                vr_custo += item.vr_simples

            vr_custo += item.vr_difal
            vr_custo += item.vr_fcp

            #
            # Abate do custo os créditos de impostos
            #
            if item.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                if (item.credita_icms_proprio and
                        (item.vr_icms_proprio or item.vr_icms_sn)):
                    #
                    # Crédito de ICMS para compra do ativo imobilizado é
                    # recebido em 48 × por isso, como a empresa pode não
                    # receber esse crédito de fato, não considera o abatimento
                    # do crédito na formação do custo
                    #
                    if not item.cfop_id.eh_compra_ativo:
                        vr_custo -= item.vr_icms_proprio
                        vr_custo -= item.vr_icms_sn

                if item.credita_ipi and item.vr_ipi:
                    vr_custo -= item.vr_ipi

                if (item.credita_pis_cofins and
                        (item.vr_pis_proprio or item.vr_cofins_proprio)):
                    vr_custo -= item.vr_pis_proprio
                    vr_custo -= item.vr_cofins_proprio

                # TODO: Rateio do custo do cabecalho da nota

            item.vr_custo_comercial = vr_custo
            item.vr_unitario_custo_comercial = vr_custo / \
                (item.quantidade or 1)

    def _seta_valores(self, res):
        self.ensure_one()
        print (res)
        if not (res and res.get('value')):
            return

        valores = res['value']
        valores.pop('id', None)
        self.update({campo: valor for campo,
                     valor in valores.iteritems() if campo in self._fields})

    @api.depends('modelo', 'emissao')
    def _compute_permite_alteracao(self):
        for item in self:
            item.permite_alteracao = True

    @api.depends('vr_unitario', 'unidade_id', 'unidade_tributacao_id',
                 'vr_produtos', 'vr_operacao',
                 'vr_produtos_tributacao', 'vr_operacao_tributacao',
                 'vr_nf', 'vr_fatura',
                 'vr_unitario_custo_comercial', 'vr_custo_comercial',
                 'peso_bruto', 'peso_liquido',
                 'especie', 'marca', 'fator_quantidade_especie',
                 'quantidade_especie')
    def _compute_readonly(self):
        for item in self:
            item.vr_unitario_readonly = item.vr_unitario

            item.unidade_readonly_id = \
                item.unidade_id.id if item.unidade_id else False
            if item.unidade_tributacao_id:
                item.unidade_tributacao_readonly_id = \
                    item.unidade_tributacao_id.id
            else:
                item.unidade_tributacao_readonly_id = False

            item.vr_produtos_readonly = item.vr_produtos
            item.vr_operacao_readonly = item.vr_operacao
            item.vr_produtos_tributacao_readonly = item.vr_produtos_tributacao
            item.vr_operacao_tributacao_readonly = item.vr_operacao_tributacao
            item.vr_nf_readonly = item.vr_nf
            item.vr_fatura_readonly = item.vr_fatura
            item.vr_unitario_custo_comercial_readonly = \
                item.vr_unitario_custo_comercial
            item.vr_custo_comercial_readonly = item.vr_custo_comercial
            item.peso_bruto_readonly = item.peso_bruto
            item.peso_liquido_readonly = item.peso_liquido
            item.especie_readonly = item.especie
            item.marca_readonly = item.marca
            item.fator_quantidade_especie_readonly = \
                item.fator_quantidade_especie
            item.quantidade_especie_readonly = item.quantidade_especie

    @api.depends('especie', 'fator_quantidade_especie', 'unidade_id')
    def _compute_descricao_especie(self):
        casas_decimais = self.env.ref('l10n_br_base.CASAS_DECIMAIS_QUANTIDADE')

        for item in self:
            descricao_especie = ''

            if item.especie and item.fator_quantidade_especie:
                descricao_especie = item.especie
                descricao_especie += ' com '
                descricao_especie += \
                    formata_valor(item.fator_quantidade_especie,
                                  casas_decimais=casas_decimais.digits)
                descricao_especie += ' '
                descricao_especie += item.unidade_id.codigo

            item.descricao_especie = descricao_especie

    def calcula_impostos(self):
        self.ensure_one()

        #
        # Busca configurações, CSTs e alíquotas
        #

        if not self.data_emissao:
            self.data_emissao = fields.Date.context_today(self)

        if self.env.context.get('gera_documento'):
            self._onchange_produto_id()
            self._onchange_operacao_item_id()
            self._onchange_cfop_id()

            #
            # Determina as aliquotas
            #

            self._onchange_al_pis_cofins_id()
            self._onchange_cst_ipi()
            self._onchange_cst_icms_cst_icms_sn()

        #
        # Faz os cálculos propriamente ditos
        #
        self._onchange_calcula_valor_operacao()
        self._onchange_calcula_ipi()
        self._onchange_calcula_icms_sn()
        self._onchange_calcula_pis_cofins()
        self._onchange_calcula_icms()
        self._onchange_calcula_difal()
        self._onchange_calcula_total()
        self._onchange_calcula_simples()
        self._onchange_calcula_ibpt()

        return

    def prepara_dados_documento_item(self):
        self.ensure_one()
        result = {}
        if self.numero_fci:
            result.update({'numero_fci': self.numero_fci})
        return result

    def _mantem_sincronia_cadastros(self, dados):
        dados = \
            super(SpedCalculoImpostoItem,
                  self)._mantem_sincronia_cadastros(dados)

        #
        # Outros campos não many2one
        #
        CAMPOS = [
            ['price_unit', 'vr_unitario'],
            ['quantity', 'quantidade'],
            ['product_qty', 'quantidade'],
            ['product_uom_qty', 'quantidade'],
        ]
        for campo_original, campo_brasil in CAMPOS:
            if campo_original in dados and not campo_brasil in dados:
                dados[campo_brasil] = dados[campo_original]

        return dados
