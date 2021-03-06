odoo.define('sped_cfe.cfe_sat', function (require) {
    "use strict";

    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var Model = require('web.Model');
    var Session = require('web.Session');

    var Cfe_sat = Widget.extend({
        template: "Cfe-sat-status",
        init: function (parent, options) {
           this._super(parent);
        },
        start: function() {
            this._super(this);
            this.configs = {
                'sat_path': "",
                'numero_caixa': ""
            };
            var self = this;
            var session = openerp.session;
            new Model('pdv.config').call("search_read", [[['create_uid', '=', session.uid]], ["ip", "numero_caixa"]]).then(function (res) {
                self.configs["sat_path"] = res[0].ip;
                self.configs["numero_caixa"] = res[0].numero_caixa;
                // self.keepalive();
                return self;
            }).fail(function (error) {
                alert(error);
                return self;
            });
        },
        connect: function (url) {
            return new Session(undefined, url, {use_cors: true});
        },
        keepalive : function(){
            var self = this;

            function status(){
                var url = "/hub/v1/consultarsat";
                var resposta_api_cfe = self.chamada_api_cfe_sat({'numero_caixa': self.configs['numero_caixa']}, url);
                resposta_api_cfe.done(function (result) {
                    var retorno_sat = result["retorno"].split('|');
                    if (retorno_sat[2] == "SAT em Operação") {
                        $(".cfe_sat_status").css("color", "green");
                    } else {
                        $(".cfe_sat_status").css("color", "red");
                    }
                }).fail(function (error) {
                    $(".cfe_sat_status").css("color", "red");
                }).always(function (){
                    setTimeout(status, 5000);
                });
            }

            if(!this.keptalive){
                this.keptalive = true;
                // status();
            }
        },
        chamada_api_cfe_sat: function (params, url){
            var self = this;
            var host = this.configs["sat_path"];
            self.connection = self.connect(host);
            var session_id = self.session.session_id;
            var parameters = params || {};
            var url_session = host + url + "?session_id=" + session_id;
            return $.ajax({
                url: url_session,
                data: parameters,
                type: "POST",
                dataType: 'json',
                traditional: true,
                contentType: "application/x-www-form-urlencoded",
                xhrFields: {
                    withCredentials: false
                },
                crossDomain: true
            })
        },
        consultar_cfe_sat: function (params) {
            var self = this;
            var url = "/hub/v1/consultarsat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        enviar_dados_venda: function (params) {
            var self = this;
            var url = "/hub/v1/enviardadosvenda";
            new Model('sped.documento').call('processar_venda_cfe', [params["venda_id"]]).then(function (result) {
                params["dados_venda"] = result;
                var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
                resposta_api_cfe.done(function (response) {
                    new Model('sped.documento').call('processar_resposta_cfe', [params["venda_id"], response]).then(function (result) {
                        location.reload(true);
                    }, function (error) {
                        alert(error.data.message);
                    });
                }).fail(function (error) {
                    alert(error.statusText);
                });
            }, function (error) {
                alert(error.data.message);
            });
        },
        cancelar_ultima_venda: function (params) {
            var self = this;
            var url = "/hub/v1/cancelarultimavenda";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        comunicar_certificado_icpbrasil: function (params) {
            var self = this;
            var url = "/hub/v1/comunicarcertificadoicpbrasil";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        teste_fim_a_fim: function (params) {
            var self = this;
            var url = "/hub/v1/testefimafim";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        consultar_status_operacional: function (params) {
            var self = this;
            var url = "/hub/v1/consultarstatusoperacional";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        consultar_numero_sessao: function (params) {
            var self = this;
            var url = "/hub/v1/consultarnumerosessao";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        configurar_interface_de_rede: function (params) {
            var self = this;
            var url = "/hub/v1/configurarinterfacederede";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        associar_assinatura: function (params) {
            var self = this;
            var url = "/hub/v1/associarassinatura";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        atualizar_software_sat: function (params) {
            var self = this;
            var url = "/hub/v1/atualizarsoftwaresat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        extrair_logs: function (params) {
            var self = this;
            var url = "/hub/v1/extrairlogs";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        bloquear_sat: function (params) {
            var self = this;
            var url = "/hub/v1/bloquearsat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        desbloquear_sat: function (params) {
            var self = this;
            var url = "/hub/v1/desbloquearsat";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },
        trocar_codigo_de_ativacao: function (params) {
            var self = this;
            var url = "/hub/v1/trocarcodigodeativacao";
            var resposta_api_cfe = self.chamada_api_cfe_sat(params, url);
            resposta_api_cfe.done(function (response) {
                alert(response.funcao + ": " + response.retorno);
            }).fail(function (error) {
                alert(error.statusText);
            });
        },

    });

    SystrayMenu.Items.push(Cfe_sat);

    return Cfe_sat;
});