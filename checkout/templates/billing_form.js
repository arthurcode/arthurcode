// the same-as-shipping-address checkbox only works when javascript is enabled, so hide it unless
// javascript is enabled
var same_as_shipping = Y.one('form div.same-as-shipping');
if (same_as_shipping != null) {
    same_as_shipping.removeClass('hidden');
}

function set_form_value(form, input_id, value) {
    var input = form.one('#' + input_id);
    if (value != null) {
        input.setAttribute('value', value);
    } else {
        input.removeAttribute('value');
    }
}

function select_country(form, select_id, code) {
    var select = form.one('#' + select_id);
    var options = select.all('option');

    for (var i=0; i < options.size(); i++) {
        var option = options.item(i);
        if (option.getAttribute('value') == code) {
            option.setAttribute('selected', '');
            break;
        }
    }
}

function set_form_values(form) {
    set_form_value(form, 'id_name', "{{ shipping_address.name|escapejs }}");
    set_form_value(form, 'id_line1', "{{ shipping_address.line1|escapejs }}");
    set_form_value(form, 'id_line2', "{{ shipping_address.line2|escapejs }}");
    set_form_value(form, 'id_city', "{{ shipping_address.city|escapejs }}");
    set_form_value(form, 'id_region', "{{ shipping_address.region|escapejs }}");
    set_form_value(form, 'id_post_code', "{{ shipping_address.post_code|escapejs }}");

}

function clear_form(form) {
    set_form_value(form, 'id_name', null);
    set_form_value(form, 'id_line1', null);
    set_form_value(form, 'id_line2', null);
    set_form_value(form, 'id_city', null);
    set_form_value(form, 'id_city', null);
    set_form_value(form, 'id_region', null);
    set_form_value(form, 'id_post_code', null);
    // TODO: find a way to 'unset' the country
}

// install a click handler for the checkbox field
same_as_shipping.delegate('click', function(e) {
    var checked = e.target.get('checked');
    var form = e.target.ancestor('form');

    if (checked) {
        set_form_values(form);
        select_country(form, 'id_country', "{{ shipping_address.country }}");
    } else {
        clear_form(form);
    }
}, 'input');
