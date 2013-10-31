Y.all('form.add-to-cart').each(function(form) {
    var button = form.one('button.action');
    button.on('click', function(e) {
        // submit the form via ajax
        var uri = '{% url ajax_add_wishlist_item_to_cart %}';
        var cfg = Y.Custom.ajax_form_submit_cfg(form);
        cfg.on.success = function(id, o, args) {
            e.preventDefault();
            Y.all('.cart-summary').each(function(node) {
                Y.Custom.ajax_reload(node, '{% url ajax_cart_summary %}');
            });
            // remove the add-to-cart form and replace it with the 'already in your cart' dialogue
            // This isn't DRY, is there a way to fix it?


            var panel = Y.Custom.ajax_result_panel(o);
            panel.render();
        };
        Y.io(uri, cfg);
    });
});
