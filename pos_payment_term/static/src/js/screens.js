/*****************************************************************************
* © 2016 KMEE INFORMATICA LTDA (<http://kmee.com.br>)
* Luiz Felipe do Divino <luiz.divino@kmee.com.br>
* License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
******************************************************************************/

function pos_payment_term_screens(instance, module) {

    module.PaymentScreenWidget = module.PaymentScreenWidget.extend({
        bind_events: function() {
            if(this.old_order){
                this.old_order.unbind(null,null,this);
            }
            var order = this.pos.get('selectedOrder');
                order.bind('change:selected_paymentline',this.focus_selected_line,this);

            this.old_order = order;

            if(this.old_paymentlines){
                this.old_paymentlines.unbind(null,null,this);
            }
            var paymentlines = order.get('paymentLines');
                paymentlines.bind('add', this.add_paymentline, this);
                paymentlines.bind('change:amount', function(line){
                        if(!line.selected && line.node){
                            line.node.value = line.amount.toFixed(this.pos.currency.decimals);
                        }
                        this.update_payment_summary();
                    },this);
                paymentlines.bind('change:amount', function(line){
                        if(!line.selected && line.node){
                            line.node.value = line.amount.toFixed(this.pos.currency.decimals);
                        }
                        this.update_payment_summary();
                    },this);
                paymentlines.bind('remove', this.remove_paymentline, this);
                paymentlines.bind('all', this.update_payment_summary, this);

            this.old_paymentlines = paymentlines;

            if(this.old_orderlines){
                this.old_orderlines.unbind(null,null,this);
            }
            var orderlines = order.get('orderLines');
                orderlines.bind('all', this.update_payment_summary, this);

            this.old_orderlines = orderlines;
        },
        validate_order: function(options) {
            var self = this;
            options = options || {};

            var currentOrder = this.pos.get('selectedOrder');

            if(currentOrder.get('orderLines').models.length === 0){
                this.pos_widget.screen_selector.show_popup('error',{
                    'message': _t('Empty Order'),
                    'comment': _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }

            var plines = currentOrder.get('paymentLines').models;
            var payment_terms_lines = [];
            this.$('.payment_term').each(function(){
                payment_terms_lines.push(this.value);
            });
            console.log("payment term");
            console.log(payment_terms_lines);
            for (var i = 0; i < plines.length; i++) {
                plines[i].set_payment_term(payment_terms_lines[i]);
                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        'message': _t('Negative Bank Payment'),
                        'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                    });
                    return;
                }
            }
        }
     });

 }