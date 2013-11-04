/**
 * Created with PyCharm.
 * User: rhyanarthur
 * Date: 2013-11-04
 * Time: 12:10 PM
 * To change this template use File | Settings | File Templates.
 */

var form = Y.one('form.buy-gc');
if (form) {
    var button = form.one('button.action');
    if (button) {
        button.on('click', function(e) {
            var cfg = Y.Custom.ajax_form_submit_cfg(form);
            cfg.on.success = function(id, o, args) {
                e.preventDefault();
                var panel = Y.Custom.ajax_result_panel(o);
                panel.render();
                refresh_cart_summary();
            };
            var uri = '{% url ajax_add_gift_card_to_cart %}';
            Y.io(uri, cfg);
        });
    }
}
