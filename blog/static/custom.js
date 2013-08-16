/**
 * Created with PyCharm.
 * User: rhyanarthur
 * Date: 2013-08-07
 * Time: 1:05 PM
 * To change this template use File | Settings | File Templates.
 */

YUI.add('custom', function(Y) {
    Y.Custom = {
        messageBox: function(message, header) {
            var panel = new Y.Panel({
                modal: true,
                bodyContent: message,
                headerContent: header,
                centered: true,
                zIndex: 100
            });
            var okButton = {
                value: "OK",
                action: function(e) {
                    e.preventDefault();
                    panel.destroy();
                },
                section: Y.WidgetStdMod.FOOTER
            };
            panel.addButton(okButton);
            return panel;
        },

        get_radio_image_display: function(radio_image) {
            var text = radio_image.one('span').getHTML();
            if (radio_image.hasClass('unavailable')) {
                text = text + " <span class='error'>(unavailable)</span>";
            }
            return text;
        },

        radioImageForm: function(form) {
            if (!form) {
                return;
            }

            // hide all of the ugly radio buttons in the form
            form.all('div.radio label').each(function(o) {
                o.addClass('hidden');
            });

            form.all('div.radio input').each(function(o) {
                o.addClass('hidden');
            });

            form.all('.radio-image').each(function(radio) {
                radio.removeClass('hidden');
                var fieldset = radio.ancestor('fieldset');
                var display = fieldset.one('.chosen-radio');
                var defaultDisplayText = display.getHTML();

                radio.on('click', function(e) {
                    // when a radio image is clicked, propagate the click to the corresponding radio input button
                    var id = radio.getAttribute('id');
                    var input = fieldset.one('input[value="' + id + '"]');
                    if (input) {
                        input.simulate("click");
                        radio.addClass('selected');
                        radio.siblings().each(function(r) {
                            r.removeClass('selected');
                        });
                    }
                });

                // when the mouse rolls over the image display the image text in the chosen-radio span
                radio.on('mouseover', function(e) {
                    if (display) {
                        display.setHTML(Y.Custom.get_radio_image_display(radio));
                    }
                });

                // reset the chosen-radio span when the mouse rolls out
                radio.on('mouseout', function(e) {
                    var selected = fieldset.one('.selected');
                    if (display) {
                        if (selected) {
                            display.setHTML(Y.Custom.get_radio_image_display(selected));
                        } else {
                            display.setHTML(defaultDisplayText);
                        }
                    }
                });
            });

            // if the add-to-cart form is bound make sure that the appropriate radio-images are 'clicked' at start
            form.all('div.radio fieldset').each(function(fieldset) {
                var selected = fieldset.one('input[type="radio"]:checked');
                if (selected) {
                    var id = selected.getAttribute('value');
                    var radio = fieldset.one('[id="' + id + '"]');               // firefox has an issue with numeric ids! (even though they are valid in html5)
                    radio.simulate('click');
                }
            });
        }
    };
}, '0.0.1', {
    requires: ['node', 'event', 'panel', 'node-event-simulate']
});
