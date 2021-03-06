/**
 * Created with PyCharm.
 * User: rhyanarthur
 * Date: 2013-08-07
 * Time: 1:05 PM
 * To change this template use File | Settings | File Templates.
 */

YUI.add('custom', function(Y) {

    Y.Custom = {
        DEFAULT_AJAX_TIMEOUT: 15*1000,

        AJAX_GH: {
            /*
            IO General Event Handler
             */
            loadingPanel: new Y.Panel({
                centered: true,
                modal: true,
                draggable: false,
                visible: false,
                render: true,
                zIndex: 50,
                close: false,
                bodyContent: '<div class="loader-panel"><img src="/static/gifs/ajax-loader.gif" /></div>',
                buttons: {}
            }),

            /* AJAX general event handler */
            start: function(id, args) {
                this.loadingPanel.show();
            },

            end: function(id, args) {
                this.loadingPanel.hide();
            }
        },

        init_ajax_general_handler: function() {
            Y.on('io:start', this.AJAX_GH.start, this.AJAX_GH);
            Y.on('io:end', this.AJAX_GH.end, this.AJAX_GH);
        },

        show_loading_panel: function() {
            this.AJAX_GH.loadingPanel.show();
        },

        hide_loading_panel: function() {
            this.AJAX_GH.loadingPanel.hide();
        },

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
            var text = radio_image.one('span.name').getHTML();
            if (radio_image.hasClass('unavailable')) {
                text = text + " <span class='error'>(sold out)</span>";
            }
            return text;
        },

        radioImageForm: function(form) {
            if (!form) {
                return;
            }

            // hide all of the ugly radio buttons in the form, except the first one
            form.all('div.radio label.choice').each(function(o) {
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
        },

        popupFieldError: function(field, alignPoints) {
            /* Takes a field with an error already set on it, and makes the error message 'pop-up' in a tooltip-like
               panel.
             */

            if (!field) {
                return;
            }

            if (!field.hasClass('error')) {
                return;
            }

            if (!alignPoints) {
                // by default align the error with the bottom left side of the input
                alignPoints = [Y.WidgetPositionAlign.TL, Y.WidgetPositionAlign.BL]
            }

            var errorSpans = field.all('span.error');
            var errorMessage = null;
            if (errorSpans.size() > 0) {
                errorMessage = errorSpans.item(0).getHTML();  // Should have the same message in all spans
            }
            if (!errorMessage) {
                errorMessage = "unknown error";  /* ugh the user should never see this */
            }

            /* arg, this is the only way I could find to get the panel to render with a custom class */
            var panelNode = Y.Node.create('<div class="field-error"><div class="yui3-widget-bd"><p><span>' + errorMessage + "</span></p></div></div>");

            var errorPanel = new Y.Panel({
                modal: false,
                srcNode: panelNode,
                zIndex: 100,
                draggable: false,
                buttons: {},

                hideOn: [
                    {
                        eventName: 'clickoutside'
                    }
                ]
            });

            var alignTo = field;

            if (field.hasClass("text")) {
                // align to the input
                var input = field.one('input');
                if (input) {
                    alignTo = input;
                }
            } else if (field.hasClass("radio")) {
                // align to the label
                var label = field.one('label');
                if (label) {
                    alignTo = label;
                }
            }
            errorPanel.align(alignTo, alignPoints);
            errorSpans.each(function(span) {
                span.addClass('hidden');
            });
            errorPanel.render();
        },

        setFieldError: function(field, errorMessage, popup) {
            if (!field) {
                return;
            }
            field.addClass("error");
            var errorSpans = field.all("span.error");
            if (errorSpans.size() > 0) {
                // span(s) already exists, just swap out the message
                errorSpans.each(function(span) {
                    span.setHTML(errorMessage);
                });
            } else {
                var label = field.one('label');
                if (label) {
                    var errorSpan = Y.Node.create("<span class='error'>" + errorMessage + "</span>");
                    label.appendChild(errorSpan);
                }
                Y.Custom.positionFieldError(field);
            }
            if (popup) {
                Y.Custom.popupFieldError(field);
            }
        },

        positionFieldError: function(field) {
            /*
            Takes a field with an error and clones the error span so that there is one span ideal for screen readers
            and one span ideal for visual positioning.
             */
            var errorSpan = field.one('label span.error');
            if (!errorSpan) {
                return;
            }
            var newErrorSpan = Y.Node.create('<span class="error">' + errorSpan.getHTML() + '</span>');
            var column1 = field.one('.column1');
            if (column1) {
                column1.appendChild(newErrorSpan);
            }
            errorSpan.addClass('hidden');  // TODO: should be visible to screen readers but not occupy space in DOM
        },

        ajax_reload: function(node, uri, extraData) {
            /*
            Uses AJAX to reload the html contents of the given node, from the html response of the given URI.
            Errors are silently ignored, although some logging may take place on the server side.
             */
            var cfg = {
                timeout: Y.Custom.DEFAULT_AJAX_TIMEOUT,
                context: node,
                on: {
                    success: function(id, o, args) {
                        node.setHTML(o.responseText);
                    }
                },
                data: extraData
            };
            Y.io(uri, cfg);
        },

        ajax_result_panel: function(o) {
            /*
            Returns a Panel object suitable for rendering the responseText of the given ajax result object, o.
            The panel is modal, centered, and will be closed when clicked outside or on a special button with the
            'close panel' class.
             */
            var panel_div = Y.Node.create('<div class="panel-div">' + o.responseText + '</div>');
            return new Y.Panel({
                srcNode: panel_div,
                centered: true,
                visible: true,
                modal: true,
                zIndex: 100,
                hideOn: [
                    {
                        eventName: 'clickoutside'
                    },
                    {
                        node: panel_div.one('close-panel'),
                        eventName: 'click'
                    }
                ]
            });
        },

        ajax_form_submit_cfg: function(form) {
            return {
                method: 'POST',
                sync: true,
                timeout: Y.Custom.DEFAULT_AJAX_TIMEOUT,
                form: {
                    id: form
                },
                on: {

                }
            };
        }
    };
}, '0.0.1', {
    requires: ['node', 'event', 'panel', 'node-event-simulate', 'io-base']
});
