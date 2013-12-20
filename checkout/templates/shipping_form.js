/**
 * Created with PyCharm.
 * User: rhyanarthur
 * Date: 2013-12-20
 * Time: 10:48 AM
 * To change this template use File | Settings | File Templates.
 */

// the same-as-shipping-address checkbox only works when javascript is enabled, so hide it unless
// javascript is enabled
var ship_to_me = Y.one('form div.ship-to-me');
if (ship_to_me != null) {
    ship_to_me.removeClass('hidden');
}

function set_form_value(form, input_id, value) {
    var input = form.one('#' + input_id);
    if (!input) return;
    if (value != null) {
        input.setAttribute('value', value);
    } else {
        input.removeAttribute('value');
    }
}


function set_form_values(form) {
    set_form_value(form, 'id_nickname', "Me");
    set_form_value(form, 'id_name', "{{ order.first_name|escapejs }} {{ order.last_name|escapejs }}");
    set_form_value(form, 'id_phone', "{{ order.phone|escapejs }}");
}

function clear_form(form) {
    set_form_value(form, 'id_nickname', null);
    set_form_value(form, 'id_name', null);
    set_form_value(form, 'id_phone', null);
}

// install a click handler for the checkbox field
ship_to_me.delegate('click', function(e) {
    var checked = e.target.get('checked');
    var form = e.target.ancestor('form');

    if (checked) {
        set_form_values(form);
    } else {
        clear_form(form);
    }
}, 'input');
