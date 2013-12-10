var form = Y.one('form.add-gift-card');
if (form && form.hasClass('hidden')) {
    // give the user a way to toggle form visibility
    var node_text = '<span class="toggle-gift-card subtle">Click here to redeem a gift card</span>';
    var node = Y.Node.create(node_text);
    node.on("click", function(e) {
        form.toggleClass('hidden');
        node.addClass('hidden');
    });
    form.ancestor().prepend(node);
}

var payment_form_ajax = function(form) {
    if (form) {
        var button = form.one('button');
        var payment_div = Y.one('div.payment-info');
        if (button && payment_div) {
            button.on('click', function(e) {
                // submit the form via ajax
                var uri = '{% url ajax_redeem_gift_card %}';
                var cfg = Y.Custom.ajax_form_submit_cfg(form);
                cfg.on.success = function(id, o, args) {
                    e.preventDefault();
                    payment_div.setHTML(o.responseText);
                    run_js();
                };
                Y.io(uri, cfg);
            });
        }
    }
};

payment_form_ajax(Y.one('form.add-gift-card'));

Y.all('form.remove-gift-card').each(function(form) {
    payment_form_ajax(form);
});
