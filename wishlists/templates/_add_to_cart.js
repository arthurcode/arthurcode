Y.all('form.add-to-cart').each(function(form) {
    var button = form.one('button.action');
    button.on('click', function(e) {
        // submit the form via ajax
        var uri = '{% url ajax_add_wishlist_item_to_cart %}';
        var cfg = Y.Custom.ajax_form_submit_cfg(form);
        cfg.on.success = function(id, o, args) {
            e.preventDefault();
            refresh_cart_summary();
            var panel = Y.Custom.ajax_result_panel(o);
            panel.render();
            var parentNode = form.ancestor();
            var uri = '{% url ajax_wishlist_item_status %}';
            var instance_id = form.one('input#id_instance_id').getAttribute('value');
            Y.Custom.ajax_reload(parentNode, uri, 'instance_id=' + instance_id);
        };
        Y.io(uri, cfg);
    });
});
