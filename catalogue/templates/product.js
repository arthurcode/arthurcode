// configure image selector
var images = Y.all('div.other-views img');
images.each(function(image) {
    image.on("click", function(e) {
        e.preventDefault();
        var src = image.get('src');
        var alt = image.get('alt');
        var primary_image = Y.one('#primary-img img');
        if (primary_image) {
            primary_image.set('src', src);
            primary_image.set('alt', alt);
            var primary_link = primary_image.ancestor('a');
            var clicked_link = image.ancestor('a');
            if (primary_link && clicked_link) {
                primary_link.set('href', clicked_link.get('href'));
            }
        }
    });
});

// load a high resolution image in a panel when the primary image is clicked
var primary_image = Y.one('#primary-img img');
if (primary_image) {
    primary_image.on("click", function(e) {
        var parent_link = primary_image.ancestor('a');
        if (parent_link) {
            // default behaviour is to link to the high-res image in a new window
            e.preventDefault();
            var detail_src = parent_link.get('href');
            var bodyContent = '<img src="' + detail_src + '">';
            var panel = new Y.Panel({
                headerContent: "{{ product.name }}",
                bodyContent: bodyContent,
                centered: true,
                zIndex: 100,
                modal: true,
                render: true
            });
        }
    });
}

Y.Custom.radioImageForm(Y.one('.add-to-cart form'));

var option_to_stock_map = JSON.parse('{{ option_to_stock_map|escapejs }}');  // parse to javascript map

function check_option_stock() {
    var options = Y.all('.radio-image');

    options.each(function() {
        this.removeClass('unavailable'); // start fresh

        var id = this.getAttribute('id');
        if (!option_to_stock_map[id]) {
            // option is out of stock
            this.addClass('unavailable');
        }
    });

    var fieldsets = Y.all('.add-to-cart div.radio fieldset');
    if (fieldsets.size() == 2) {
        // the only amount of option categories we can handle right now I'm afraid
        var set_1 = fieldsets.item(0);
        var set_2 = fieldsets.item(1);
        var selected_1 = set_1.one('.radio-image.selected');
        var selected_2 = set_2.one('.radio-image.selected');
        if (selected_1 || selected_2) {
            if (selected_1) {
                var id = selected_1.getAttribute('id');
                var display = set_1.one('.chosen-radio');
                set_2.all('.radio-image').each(function() {
                    var key = id + "," + this.getAttribute('id');
                    if (!(key in option_to_stock_map) || option_to_stock_map[key] == 0) {
                        this.addClass('unavailable');
                    }
                });
            }
            if (selected_2) {
                var id = selected_2.getAttribute('id');
                var display = set_2.one('.chosen-radio');
                set_1.all('.radio-image').each(function() {
                    var key = id + "," + this.getAttribute('id');
                    if (!(key in option_to_stock_map) || option_to_stock_map[key] == 0) {
                        this.addClass('unavailable');
                    }
                });
            }
        }
    }

    // set the display value
    fieldsets.each(function() {
        var display = this.one('.chosen-radio');
        var selected = this.one('.radio-image.selected');
        if (selected) {
            display.setHTML(Y.Custom.get_radio_image_display(selected));
        }
    });
}

var option_to_image_map = JSON.parse('{{ option_to_image_map|escapejs }}');  // parse to javascript map

Y.all('.radio-image').each(function(radio) {
    radio.on('click', function(e) {
        check_option_stock();
        var id = radio.getAttribute('id');
        // if this option is linked to an alternate product image, load it.
        if (id in option_to_image_map) {
            var image_id = option_to_image_map[id];
            var image = Y.one('div.other-views img#image-' + image_id);
            if (image) {
                image.simulate("click");
            }
        }
    });
});
check_option_stock();


// hook up increment & decrement buttons for the quantity field
var field = Y.one('.add-to-cart input#id_quantity').ancestor('.field');
if (field) {
    var incrementor = Y.Node.create("<button type='button'>+</button>");
    var decrementor = Y.Node.create("<button type='button'>-</button>");
    field.one('.column1').append(incrementor);
    field.one('.column1').append(decrementor);

    incrementor.on("click", function(e) {
        var input = field.one("input");
        var currentValue = input.get('value');
        var newValue = currentValue*1 + 1;
        if (newValue) {
            input.set('value', newValue);
        }
    });

    decrementor.on("click", function(e) {
        var input = field.one("input");
        var currentValue = input.get('value');
        var newValue = currentValue*1 - 1;
        if (newValue) {
            if (newValue < 1) {
                newValue = 1;
            }
            input.set('value', newValue);
        }
    })
}

// custom add-to-cart form validation + AJAX
var form = Y.one('.add-to-cart form');
if (form) {
    var button = form.one('button.action');
    if (button) {
        button.on('click', function(e) {
            var found_error = false;
            form.all('fieldset').each(function(fieldset) {
                // make sure that an option has been selected
                var selected = fieldset.one('.radio-image.selected');
                if (!selected) {
                    found_error = true;
                    var message = "Please " + fieldset.one('legend').getHTML().toLowerCase();
                    Y.Custom.setFieldError(fieldset.ancestor('.field'), message, true);
                }
            });
            var quantity_input = form.one('input#id_quantity');
            var quantity = quantity_input.get('value');
            var field = quantity_input.ancestor('.field');

            if (!quantity) {
                found_error = true;
                Y.Custom.setFieldError(field, "Please enter a quantity", true);
            } else {
                var int_quantity = parseInt(quantity);
                if (!int_quantity || int_quantity < 1) {
                    found_error = true;
                    Y.Custom.setFieldError(field, "Please enter a number larger than zero", true);
                }
            }
            if (found_error) {
                e.preventDefault()
            } else {
                // there were no errors in the form, submit via ajax
                var uri = '{% url ajax_add_product_to_cart %}';
                var cfg = Y.Custom.ajax_form_submit_cfg(form);

                // customize the configuration object
                cfg.on.success = function(id, o, args) {
                    // only prevent the default form submit if the ajax submit was successful
                    e.preventDefault();
                    refresh_cart_summary();
                    var panel = Y.Custom.ajax_result_panel(o);
                    panel.render();
                };
                cfg.data = 'product_id={{ product.id }}';
                Y.io(uri, cfg);
            }
        });
    }

    // make all errors in the add-to-cart form pop up like tooltips
    form.all('.field.error').each(function(field) {
        Y.Custom.popupFieldError(field);
    });
}

// wishlist popup select
var wishlist_button = Y.one('button#add-to-wishlist');
if (wishlist_button) {
    var wishlist_field = Y.one('.field.wishlist');
    if (wishlist_field) {
        wishlist_field.addClass('hidden');
        var options = wishlist_field.all('option');

        // when there is only one option available the user should be able to simply click on the
        // 'Add to Wish List' button and have the form submit, no extra javascript required.
        if (options.size() > 1) {
            // make a copy of the submit button visible, hide the original
            var wishlist_button_copy = wishlist_button.cloneNode(true);
            var add_to_cart_form = wishlist_button.ancestor('form');
            wishlist_button.addClass('hidden');
            add_to_cart_form.appendChild(wishlist_button_copy);

            var panel_div = Y.Node.create('<ul class="select-wish-list"></ul>');
            // when the "Add to Wish List" button is clicked, prompt the user to choose from the available
            // wishlists, or create a new one.
            // When they click on a choice the corresponding option should be selected, AND the form
            // should be submitted.
            options.each(function(option) {
                var button = Y.Node.create('<li>' + option.getHTML() + '</li>');
                button.on('click', function(e) {
                    option.setAttribute('selected', 'true');
                    // submit the form via ajax
                    var cfg = Y.Custom.ajax_form_submit_cfg(add_to_cart_form);
                    cfg.data = "product_id={{ product.id}}";
                    cfg.on.success = function(id, o, args) {
                        // display the HTML result in a panel
                        e.preventDefault();
                        var panel = Y.Custom.ajax_result_panel(o);
                        panel.render();
                    };
                    cfg.on.failure = function(id, o, args) {
                        // go ahead and submit the form normally
                        wishlist_button.simulate('click');
                    };
                    Y.io('{% url ajax_add_item_to_wishlist %}', cfg);
                });
                panel_div.appendChild(button);
            });
            panel_div.addClass('hidden');
            add_to_cart_form.appendChild(panel_div);

            wishlist_button_copy.on('click', function(e) {
                e.preventDefault();
                panel_div.toggleClass('hidden');
                if (panel_div.hasClass('hidden')) {
                    wishlist_button_copy.setHTML('Add to Wish List');
                } else {
                    wishlist_button_copy.setHTML('Select a Wish List');
                }
            })
        }
    }
}
