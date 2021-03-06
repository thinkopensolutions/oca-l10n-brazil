# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import base64
from StringIO import StringIO

from odoo import api, fields, models
from odoo.exceptions import Warning as UserError
from pybrasil.data import parse_datetime, formata_data
from pybrasil.febraban import RetornoBoleto
from pybrasil.valor.decimal import Decimal as D

from ..constantes import *


class finan_retorno_item(models.Model):
    _name = b'finan.retorno_item'
    _description = 'Item de retorno de cobrança'
    _order = 'retorno_id, divida_id'
    _rec_name = 'divida_id'

    retorno_id = fields.Many2one(
        comodel_name='finan.retorno',
        string='Arquivo de remessa',
        ondelete='cascade',
        readonly=True,
    )

    comando = fields.Selection(
        selection=[
            ('L', 'Liquidação conciliada'),
            ('Q', 'Liquidaçaõ a conciliar'),
            ('B', 'Baixa'),
            ('N', 'Liquidação a conciliar - cliente negativado'),
            ('R', 'Registro do boleto'),
        ],
        string='Comando',
        default='L',
        readonly=True,
    )

    divida_id = fields.Many2one(
        comodel_name='finan.lancamento',
        string='Lançamento Financeiro (Dívida)',
        readonly=True,
    )

    pagamento_id = fields.Many2one(
        comodel_name='finan.lancamento',
        string='Lançamento Financeiro (Pagamento)',
        readonly=True,
    )

    quitacao_duplicada = fields.Boolean(
        string='Quitação duplicada?',
        readonly=True,
    )

    data_vencimento = fields.Date(
        related='divida_id.data_vencimento',
        string='Data de vencimento',
        readonly=True,
    )

    nosso_numero = fields.Char(
        related='divida_id.nosso_numero',
        string = 'Nosso número',
        readonly=True,
    )

    partner_id = fields.Many2one(
        related='divida_id.partner_id',
        comodel_name='res.partner',
        string='Participante',
        readonly=True,
    )

    data_pagamento = fields.Date(
        related='divida_id.data_pagamento',
        string='Data quitação',
        readonly=True,
    )

    data = fields.Date(
        string='Data conciliação',
        readonly=True,
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        readonly=True,
    )

    vr_documento = fields.Monetary(
        related='divida_id.vr_documento',
        string='Valor documento',
        readonly=True,
    )

    valor_multa = fields.Float(
        string='Multa',
        readonly=True,
    )

    valor_juros = fields.Float(
        string='Juros',
        readonly=True,
    )

    valor_desconto = fields.Float(
        string='Desconto',
        readonly=True,
    )

    outros_debitos = fields.Float(
        string='Tarifas',
        readonly=True,
    )

    valor = fields.Float(
        string='Valor',
        readonly=True,
    )

    @api.multi
    def compute_valor_multa(self, nome_campo):
        """

        :param nome_campo:
        :return:
        """
        res = {}
        for item_obj in self:
            valor = D(0)

            if item_obj.comando in ['L', 'Q']:
                if nome_campo in ['valor', 'valor_multa',
                                  'valor_juros', 'valor_desconto'
                                  ] and item_obj.comando == 'L':
                    valor = getattr(item_obj.lancamento_id, nome_campo, D(0))
                elif nome_campo not in ['valor', 'valor_multa', 'valor_juros',
                                        'valor_desconto']:
                    valor = getattr(item_obj.lancamento_id, nome_campo, D(0))

            res[item_obj.id] = valor

        return res

class finan_retorno(models.Model):
    _name = b'finan.retorno'
    _description = 'Retornos de cobrança'
    _order = 'data desc, numero_arquivo desc'
    _rec_name = 'numero_arquivo'

    carteira_id = fields.Many2one(
        comodel_name='finan.carteira',
        string='Carteira',
        required=True,
        index=True,
    )

    numero_arquivo = fields.Integer(
        string='Número do arquivo',
    )

    data = fields.Date(
        string='Data',
        default=fields.Date.today,
        required=True,
    )

    retorno_item_ids = fields.One2many(
        comodel_name='finan.retorno_item',
        inverse_name='retorno_id',
        string='Boletos no retorno',
    )

    arquivo_binario = fields.Binary(
        string='Arquivo',
    )

    lancamento_ids = fields.Many2many(
        comodel_name='finan.lancamento',
        relation='finan_retorno_lancamento',
        column1='retorno_id',
        column2='lancamento_id',
        string='Itens do Retorno',
    )

    @api.multi
    def gerar_relatorio(self, arquivo_retorno):
        """
        Gerar relatório (francesinha) do arquivo de retorno do banco 
        1 - Gerar PDF da francesinha (arquivo de retorno)
        2 - Excluir anexos antigos
        3 - Anexar novo PDF gerado
        """
        # imports para geracao do PDF
        import sh
        from io import BytesIO
        import tempfile
        from py3o.template import Template
        import os
        CURDIR = os.path.dirname(os.path.abspath(__file__))

        lista_boletos = arquivo_retorno.boletos

        # template da francesinha
        arquivo_template_boleto_geral = os.path.join(
            CURDIR, '../reports', 'report_py3o_finan_retorno.odt'
        )

        template_boleto = BytesIO()
        template_boleto.write(open(arquivo_template_boleto_geral, 'rb').read())
        template_boleto.seek(0)

        arquivo_renderizado = tempfile.NamedTemporaryFile(delete=False)
        arquivo_pdf = arquivo_renderizado.name + '.pdf'
        template = Template(template_boleto, arquivo_renderizado.name)

        comandos_boletos =\
                sorted(set(map(lambda x: (x.comando_retorno_descricao),
                               lista_boletos)))

        template.render({'boletos': lista_boletos,
                         'sequencia': arquivo_retorno.sequencia,
                         'data':
                             arquivo_retorno.data_hora.strftime('%d/%m/%Y'),
                         'nome_beneficiario':
                             arquivo_retorno.beneficiario.nome,
                         'banco_codigo': arquivo_retorno.banco.codigo_digito,
                         'cnpj_beneficiario':
                             arquivo_retorno.beneficiario.cnpj_cpf,
                         'codigo_beneficiario':
                             arquivo_retorno.beneficiario.\
                        agencia_codigo_beneficiario,
                         'conta_beneficiario':
                             arquivo_retorno.beneficiario.agencia_conta,
                         'logo': lista_boletos[0].banco.logo,
                         'comandos': comandos_boletos,
                         })

        # comando para o libreoffice gerar o pdf
        sh.libreoffice(
            '--headless', '--invisible', '--convert-to',
            'pdf', '--outdir', '/tmp', arquivo_renderizado.name
        )

        pdf = open(arquivo_pdf, 'rb').read()

        # remover arquivos temporários
        os.remove(arquivo_pdf)
        os.remove(arquivo_renderizado.name)

        attachment_obj = self.env.get('ir.attachment')

        # Busca pelo anexos com mesmo nome nesse registro
        attachment_ids = attachment_obj.search([
                ('res_model', '=', 'finan.retorno'),
                ('res_id', '=', self.id),
                ('name', '=', 'francesinha.pdf')
        ])

        # Apaga os boletos anteriores com o mesmo nome
        attachment_ids.unlink()

        # Criar dados para anexar o pdf gerado ao finan.retorno
        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'francesinha.pdf',
            'datas_fname': 'francesinha.pdf',
            'res_model': 'finan.retorno',
            'res_id': self.id,
            'file_type': 'application/pdf',
        }
        # Gerar o anexo do registro
        attachment_obj.create(dados)

    @api.multi
    def gerar_pagamento(
            self, finan_retorno_item_id, divida_id, boleto, comando):
        """
        Gerar lancamento financeiro do tipo pagamento 
        a partir do boleto e do seu comando
        :param divida_id: 
        :param boleto: 
        :param comando: 
        :return: 
        """

        # Se o comando for:
        # ('B', 'Baixa'),
        # ('R', 'Registro do boleto'),
        if comando in ('B', 'R'):
            pass

        # Se
        # ('L', 'Liquidação conciliada'),
        # ('Q', 'Liquidaçaõ a conciliar'),
        # ('N', 'Liquidação a conciliar - cliente negativado'),
        else:
            #
            # Cria agora o pagamento em si
            #
            dados_pagamento = {
                'tipo': 'pagamento',
                'divida_id': divida_id.id,
                'retorno_item_id': finan_retorno_item_id.id,
                'retorno_id': self.id,
                'company_id': divida_id.company_id.id,
                'participante_id': divida_id.participante_id.id,
                'data_vencimento':divida_id.data_vencimento,
                'numero': divida_id.numero,
                'vr_documento': divida_id.vr_documento,
                'data_pagamento': str(boleto.data_ocorrencia)[:10],
                'data_juros': str(boleto.data_ocorrencia)[:10],
                'data_multa': str(boleto.data_ocorrencia)[:10],
                'data_desconto': str(boleto.data_ocorrencia)[:10],
                'vr_desconto': boleto.valor_desconto,
                'vr_juros': boleto.valor_juros,
                'vr_multa': boleto.valor_multa,
                'outros_debitos': boleto.valor_despesa_cobranca,
                'vr_total': boleto.valor_recebido,
                'banco_id': self.carteira_id.banco_id.id,
                'carteira_id': self.carteira_id.id,
                'forma_pagamento_id': divida_id.forma_pagamento_id.id,
                'conta_id': 275, # Receitas Operacionais
            }

            if comando == 'L':
                dados_pagamento['data'] = str(boleto.data_credito)[:10]
                dados_pagamento['conciliado'] = True

            # dados_pagamento['baixa_boleto'] = True
            lancamento_obj = self.env.get('finan.lancamento')
            finan_pagamento_id = lancamento_obj.create(dados_pagamento)
            return finan_pagamento_id

    @api.multi
    def atualizar_divida(self, divida_id, boleto, comando):
        """
        Dado o comando e o boleto, atualizar as informações da Dívida
        :param divida_id: finan.lancamento
        :param boleto: instancia do boleto da pybrasil
        :param comando: string indicando o comando do boleto
        :return: 
        """
        # Se o comando for
        # ('B', 'Baixa'),
        # ('N', 'Liquidação a conciliar - cliente negativado'),
        # ('R', 'Registro do boleto'),
        #  Guardar a data de baixa
        if comando in ('B', 'N', 'R'):
            pass
            # dados = {'data_baixa': str(boleto.data_ocorrencia)[:10],}

        # Se o comando for:
        # ('L', 'Liquidação conciliada'),
        # ('Q', 'Liquidaçaõ a conciliar')
        # Atualizar o lancamento com informacoes do boleto retornado
        else:

            dados = {
                'valor_desconto': boleto.valor_desconto,
                'valor_juros': boleto.valor_juros,
                'valor_multa': boleto.valor_multa,
                'outros_debitos': boleto.valor_despesa_cobranca,
                'valor': boleto.valor_recebido,
                'data_pagamento': str(boleto.data_ocorrencia)[:10],
            }

            if comando == 'L':
                dados['data'] = str(boleto.data_credito)[:10]
                dados['conciliado'] = True

        dados['baixa_boleto'] = True
        divida_id.write(dados)

    @api.multi
    def get_comando(self, boleto, arquivo_retorno):
        """
        Identifica qual o comando para tratar o retorno do boleto
        :param boleto: 
        :param arquivo_retorno: 
        :return: string - comando
        """
        comando = ''
        #
        # Trata aqui a liquidação sem data de crédito do SICOOB
        # (título antecipado pelo banco)
        #
        if arquivo_retorno.banco.codigo == FINAN_BANCO_SICOOB and \
                        boleto.comando == '06' and \
                        boleto.data_credito is None:
            boleto.comando += '.1'

        if boleto.comando in arquivo_retorno.banco.comandos_liquidacao:
            if arquivo_retorno.banco.comandos_liquidacao[boleto.comando]:
                comando = 'L'
            else:
                comando = 'Q'

        elif boleto.comando in arquivo_retorno.banco.comandos_baixa:
            comando = 'B'

        # banco emite - banco que da o nosso numero
        elif self.carteira_id.banco_emite and boleto.comando == '02':
            comando = 'R'

        return comando

    @api.multi
    def get_divida(self, boleto):
        """
        Dado o retorno de um boleto buscar a divida (finan.lancamento) 
        correspondente no sistema
        :param boleto: 
        :return: finan.lancamento
        """
        lancamento_obj = self.env.get('finan.lancamento')

        # Se a identificacao do retorno do boleto começa com N
        if boleto.identificacao.upper().startswith('N'):
            # Remover a letra N e pegar o ID do lancamento no sistema
            id_lancamento = int(boleto.identificacao.upper().replace('N', ''))
            lancamento_ids = lancamento_obj.search([
                ('carteira_id', '=', self.carteira_id.id),
                ('id', '=', id_lancamento),
            ])

        elif boleto.identificacao.upper().startswith('ID'):
            # Remover o 'ID', converter para int em base 36 para
            # pegar o ID do lancamento no sistema
            id_lancamento = \
                int(boleto.identificacao.upper().replace('ID', ''), 36)
            lancamento_ids = lancamento_obj.search([
                ('carteira_id', '=', self.carteira_id.id),
                ('id', '=', id_lancamento),
            ])

        else:
            # Se nao encontrar pela identificacao buscar pelo nosso numero
            lancamento_ids = lancamento_obj.search([
                ('carteira_id', '=', self.carteira_id.id),
                ('nosso_numero', '=', boleto.nosso_numero)
            ], order='data_vencimento desc')

        return lancamento_ids[0] if lancamento_ids else False

    @api.multi
    def remover_pagamentos_anteriores(self):
        """
        Remover os pagamentos efetuados apartir desse retorno bancario
        Substituido pelo ondelete='cascade',                
        """
        pass
        # pagamento_ids = self.env.get('finan.lancamento').search([
        #     ('tipo', '=', 'pagamento'),
        #     ('divida_id', '=', divida_id.id),
        #     ('retorno_id', '=', self.id),
        #     ('retorno_item_id', '=', item_id),
        # ])
        # pagamento_ids.unlink()

    @api.multi
    def remover_finan_retorno_itens_anteriores(self):
        """
        Remover Itens de retorno desse CNAB anteriores
        :param arquivo_retorno: 
        :return: 
        """
        self.retorno_item_ids.unlink()

        #
        # Exclui os retornos já existentes deste arquivo
        #
        # self._cr.execute("update finan_lancamento set numero_documento = "
        #                  "'QUERO EXCLUIR' where tipo = 'PR' and retorno_id"
        #                  " = " + str(retorno_id.id) + ";")
        # self._cr.execute("delete from finan_lancamento where tipo = 'PR' "
        #                  "and retorno_id = " + str(retorno_id.id) + ";")
        # self._cr.commit()

    @api.multi
    def adicionar_comandos_retorno(self, arquivo_retorno):
        """
        Adiciona os comandos separados para baixa/Liquidação de cliente
        negativado
        """
        arq_comandos_retorno = arquivo_retorno.banco.descricao_comandos_retorno
        for comando in arquivo_retorno.banco.comandos_liquidacao:
            if comando + '-N' not in arq_comandos_retorno:
                arq_comandos_retorno[comando + '-N'] = \
                    arq_comandos_retorno[comando] + ' - cliente negativado'

    @api.multi
    def validacao_existencia_retorno(self, arquivo_retorno):
        """
        Validar se ja existe um arquivo com mesma sequencia e carteira
        :param arquivo_retorno: 
        :return: 
        """
        arquivo_retorno_ids = self.search([
            ('numero_arquivo', '=', arquivo_retorno.sequencia),
            ('carteira_id', '=', self.carteira_id.id),
        ])

        if arquivo_retorno_ids:
            raise UserError(
                'Arquivo já existente - Nº {numero_arquivo}!'.format(
                    numero_arquivo=arquivo_retorno.sequencia))

    @api.multi
    def validacao_beneficiario(self, arquivo_retorno):
        """
        Validacao do beneficiario do arquivo de retorno é igual ao 
        beneficiario da carteira
        :param arquivo_retorno: 
        :return: 
        """
        if arquivo_retorno.banco.codigo != FINAN_BANCO_BRASIL:

            # Se o CNPJ do banco for diferente tratar validar sacador
            #
            if arquivo_retorno.beneficiario.cnpj_cpf != \
                    self.carteira_id.banco_id.titular_id.cnpj_cpf:

                # Se na carteira for definido um sacador, o cnpj do
                # beneficiario do arquivo de retorno devera ser igual ao
                # cnpj do sacador da carteira
                #
                if self.carteira_id.sacador_id:
                    if arquivo_retorno.beneficiario.cnpj_cpf != \
                            self.carteira_id.sacador_id.cnpj_cpf:

                        erro = 'O arquivo é de outro beneficiário! \n ' \
                               'Arquivo retorno: {name_ret} - {cnpj_ret} \n' \
                               'Carteira: {name_cart} - {cnpj_cart}'.format(
                            name_ret=arquivo_retorno.beneficiario.nome,
                            cnpj_ret=arquivo_retorno.beneficiario.cnpj_cpf,
                            name_cart=self.carteira_id.sacador_id.cnpj_cpf,
                            cnpj_cart=self.carteira_id.sacador_id.nome
                        )


                        raise UserError(erro)

                # Se tiver cnpj diferentes e nao for definido o sacador
                #
                else:
                    titular = arquivo_retorno.carteira_id.banco_id.titular_id
                    erro = \
                        'O arquivo é de outro beneficiário! \n ' \
                        'Arquivo retorno: {name_ret} - {cnpj_ret} \n' \
                        'Carteira: {name_cart} - {cnpj_cart}'.format(
                            name_ret=titular.nome,
                            cnpj_ret=titular.cnpj_cpf,
                            name_cart=self.beneficiario.name,
                            cnpj_cart=self.beneficiario.cnpj_cpf
                        )
                    raise UserError(erro)

        # Se o codigo do beneficiario for diferente na carteira e no arq.
        if arquivo_retorno.beneficiario.codigo.numero != \
                self.carteira_id.beneficiario:

            # Se o arq de retorno tiver numero_beneficiario_unicred
            unicred = hasattr(
                arquivo_retorno.boletos[1],
                'numero_beneficiario_unicred') and \
                      arquivo_retorno.boletos[1].numero_beneficiario_unicred
            if len(arquivo_retorno.boletos) > 1 and unicred:

                # O beneficiario unicred devera ser igual ao beneficiario
                # da carteira
                beneciario_carteira = self.carteira_id.beneficiario
                beneficiario_unicred = \
                    arquivo_retorno.boletos[1].numero_beneficiario_unicred

                if beneficiario_unicred != beneciario_carteira:
                    msg_erro = \
                        'O codigo de beneficiario da carteira cadastrado' \
                        ' no sistema ({beneficiario}), difere do codigo ' \
                        ' de beneficiario Unicred do arquivo: {unicred}.' \
                        '\nO código do beneficiario do arquivo retorno é:' \
                        '{retorno_beneficiario}'. \
                            format(
                                beneficiario=beneciario_carteira,
                                unicred=beneficiario_unicred,
                                retorno_beneficiario=
                                    arquivo_retorno.beneficiario.codigo.numero,
                        )
                    raise UserError(msg_erro)
            else:
                try:
                    num_beneficiario = \
                        arquivo_retorno.beneficiario.codigo_beneficiario
                    num_beneficiario = int(num_beneficiario.numero)

                    if num_beneficiario != int(self.carteira_id.beneficiario):
                        beneficiario_id = arquivo_retorno.beneficiario
                        num = beneficiario_id.codigo_beneficiario.numero
                        erro = \
                            'O arquivo é de outra código beneficiário - ' \
                            '{beneficiario}!'.format(beneficiario=num)
                        raise UserError(erro)
                except:
                    raise UserError('O arquivo é de outra código '
                                    'beneficiário - {bene}!'.format(
                        bene=arquivo_retorno.beneficiario.codigo.numero))

    @api.multi
    def validacao_agencia_conta(self, arquivo_retorno):
        """
        Validacao da agencia e conta do arquivo de retorno com a carteira sele
        :param arquivo_retorno: 
        :return: 
        """
        if arquivo_retorno.banco.codigo not in ('748', '104','001'):

            if arquivo_retorno.beneficiario.agencia.numero != \
                    self.carteira_id.banco_id.agencia:
                erro = 'O arquivo é de outra agência! \n' \
                       'Agência do beneficiario: {agencia_ben} \n' \
                       'Arquivo de retorno: {agencia_ret} \n'.format(
                    agencia_ben=self.carteira_id.banco_id.agencia,
                    agencia_ret=arquivo_retorno.beneficiario.agencia.numero
                )
                raise UserError(erro)

            if arquivo_retorno.beneficiario.conta.numero != self.\
                    carteira_id.banco_id.agencia:
                try:
                    if int(arquivo_retorno.beneficiario.conta.numero) != int(
                            self.carteira_id.banco_id.conta):
                        raise UserError('O arquivo é de outra conta - '
                                        '{conta}!'.format(conta=arquivo_retorno.
                                                          beneficiario.
                                                          conta.numero))
                except:
                    raise UserError('O arquivo é de outra conta - {conta}!'
                                    ''.format(conta=arquivo_retorno.beneficiario.
                                              conta.numero))

    @api.multi
    def validacao_banco_carteira(self, arquivo_retorno):
        """
        Validar se o arquivo de retorno tem o mesmo banco da carteira
        """
        # Se o código do banco for diferente
        if arquivo_retorno.banco.codigo != self.carteira_id.banco_id.banco:

            # Se for do caso que o unicred gera o boleto pelo banco bradesco
            # FINAN_BANCO_UNICRED == 136
            # FINAN_BANCO_BRADESCO == 237
            if arquivo_retorno.banco.codigo == FINAN_BANCO_BRADESCO and \
                        self.carteira_id.banco_id.banco != FINAN_BANCO_UNICRED:

                # TODO: Melhorar mensagem de erro exibindo o nome do banco
                #
                raise UserError('O arquivo é de outro banco - {banco}!'.
                                format(banco=arquivo_retorno.banco.codigo))

    @api.multi
    def get_arquivo(self):
        """
        Método para obter o arquivo apartir do arquivo retornado peo banco
        """
        # Rotina para validar a existencia do arquivo
        if not self.arquivo_binario:
            raise UserError('Nenhum arquivo informado!')

        # Criando um arquivo baseado no arquivo enviado pelo cliente
        arquivo_texto = base64.decodestring(self.arquivo_binario)
        arquivo = StringIO()
        arquivo.write(arquivo_texto)
        arquivo.seek(0)

        # Classe de retorno de boletos utilizada pela pybrasil
        arquivo_retorno = RetornoBoleto()

        # Validação da instancia da classe baseada no arquivo de retorno
        if not arquivo_retorno.arquivo_retorno(arquivo):
            raise UserError('Formato do arquivo incorreto ou inválido!')

        return arquivo_retorno

    @api.multi
    def processar_retorno(self):
        """
        Método para processamento do CNAB
        """
        self.ensure_one()

        # Gerar objeto apartir do arquivo upado
        arquivo_retorno = self.get_arquivo()

        # Validar se o banco é igual na carteira e no arquivo de retorno
        self.validacao_banco_carteira(arquivo_retorno)

        # Validar Beneficiário
        self.validacao_beneficiario(arquivo_retorno)

        # Validação de Agência - conta
        self.validacao_agencia_conta(arquivo_retorno)

        # Validar se ja foi gerado um retorno com mesma sequencia e da
        # mesma carteira
        self.validacao_existencia_retorno(arquivo_retorno)

        # Escrever o numero do arquivo e a data que foi gerado
        self.write({
            'numero_arquivo': arquivo_retorno.sequencia,
            'data': str(arquivo_retorno.data_hora),
        })

        # Remover os pagamentos efetuados anteriormente por esse arquivo CNAB
        # self.remover_pagamentos_anteriores()

        # Remover os itens de retorno gerados anteriormente
        self.remover_finan_retorno_itens_anteriores()

        # Adicionar os comandos para baixa/Liquidação de clientes negativados
        self.adicionar_comandos_retorno(arquivo_retorno)

        # Processa os boletos do arquivo
        for boleto in arquivo_retorno.boletos:

            # verifica se o boleto é duplicado
            if boleto.pagamento_duplicado:
                boleto.pagamento_duplicado = 'SIM'
            else:
                boleto.pagamento_duplicado = 'NÃO'

            # verifica exixtencia de data de crédito e inverte se existir
            if boleto.data_credito:
                boleto.data_credito_fmt = formata_data(boleto.data_credito)
            else:
                boleto.data_credito_fmt = ''

            # verifica exixtencia de data de ocorrencia e inverte se existir
            if boleto.data_ocorrencia:
                boleto.data_ocorrencia_fmt = formata_data(
                    boleto.data_ocorrencia)
            else:
                boleto.data_ocorrencia_fmt = ''

            # buscar lancamento correspondente (divida) do boleto
            divida_id = self.get_divida(boleto)

            # buscar o comando do boleto
            comando = self.get_comando(boleto, arquivo_retorno)

            # Atualizar informações no boleto para francesinha
            if divida_id:
                boleto.pagador.cnpj_cpf = divida_id.participante_id.cnpj_cpf
                boleto.pagador.nome = divida_id.participante_id.name
                boleto.documento.numero = divida_id.numero
                #
                # Cliente negativado não baixa automático o boleto
                # if comando != 'B' and \
                #         divida_id.forma_pagamento_id and \
                #         divida_id.forma_pagamento_id.cliente_negativado:
                #     comando = 'N'
                #     boleto.comando += '-N'

                # Se o banco emitiu/mudou o nosso numero, atualizar na divida
                if self.carteira_id.banco_emite and comando == 'R':
                    divida_id.nosso_numero = boleto.nosso_numero

            # Criar um item de retorno do CNAB
            if divida_id and comando:

                # Criar item de retorno de retorno
                dados = {
                    'retorno_id': self.id,
                    'comando': comando,
                    'divida_id': divida_id.id,
                    'currency_id': divida_id.currency_id.id,
                    'valor': boleto.documento.valor,
                    'valor_multa': boleto.valor_multa,
                    'quitacao_duplicada': boleto.pagamento_duplicado,
                    'data': boleto.data_ocorrencia,
                    'outros_debitos': boleto.valor_outras_despesas,
                    'valor_juros':boleto.valor_juros,
                    'desconto': boleto.valor_desconto,
                }
                finan_retorno_item_id = \
                    self.env.get('finan.retorno_item').create(dados)

                # Não processa se já estiver quitado e atualiza informação no
                # boleto para gerar o relatório (francesinha)
                if divida_id.state not in \
                        ['A vencer', 'Vencido', 'Vence hoje']:
                    data_baixa_diferente = \
                        divida_id.data_baixa and \
                        (parse_datetime(divida_id.data_baixa).date() !=
                         boleto.data_ocorrencia)
                    if data_baixa_diferente:
                        # indicar no item que o pagamento foi duplicado
                        finan_retorno_item_id.quitacao_duplicada =  True
                        # indicar no boleto que o pagamento foi duplicado
                        boleto.pagamento_duplicado = True
                        continue

                # Dado o comando e o boleto, atualizar as informações do
                # finan_lancamento
                self.atualizar_divida(divida_id, boleto, comando)

                # Dado o comando e o boleto, gerar um finan_lancamento
                finan_lancamento_id = \
                pagamento_id = self.gerar_pagamento(
                    finan_retorno_item_id, divida_id, boleto, comando)

                # relaciona o pagamento gerado ao item criado
                finan_retorno_item_id.pagamento_id = pagamento_id.id

        # Gera a francesinha e anexa ao registro
        self.gerar_relatorio(arquivo_retorno)
